"""
ClauseGuard Flask API
======================
Routes:
  GET  /health           — liveness check
  POST /analyze          — full ToS analysis (text → risk JSON)
  POST /fetch-url        — server-side URL fetch + clean text extraction
  GET  /submitted-urls   — log of every URL analyzed
"""
import os
import time
import json
import re
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests as http_requests
from bs4 import BeautifulSoup

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── App setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ── Load classifiers ───────────────────────────────────────────────────────────
# Rule-based (always available — no model file needed)
from classifier import RuleBasedClassifier
rule_classifier = RuleBasedClassifier()

# Hybrid (ML + rule-based fallback)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ml.hybrid import HybridClassifier
    classifier = HybridClassifier(rule_based_classifier=rule_classifier)
    logger.info("✅ HybridClassifier loaded (ML + rule-based fallback)")
    CLASSIFIER_MODE = "hybrid"
except Exception as e:
    logger.warning(f"⚠️  HybridClassifier unavailable ({e}), falling back to rule-based only")
    classifier = None
    CLASSIFIER_MODE = "rule_based"

# ── spaCy segmenter ────────────────────────────────────────────────────────────
try:
    from segmenter import segment_clauses
    logger.info("✅ spaCy segmenter loaded")
except Exception as e:
    logger.warning(f"⚠️  spaCy segmenter unavailable ({e}), using fallback")
    def segment_clauses(text):
        """Simple fallback segmenter: split on double newlines or numbered items."""
        parts = re.split(r'\n{2,}|\n(?=\d+\.|\([a-z]\))', text)
        return [p.strip() for p in parts if len(p.strip()) > 40]

# ── Category metadata ──────────────────────────────────────────────────────────
CATEGORY_META = {
    "data_sharing":        {"label": "Data Sharing",        "weight": 0.22},
    "tracking_profiling":  {"label": "Tracking & Profiling","weight": 0.20},
    "third_party_access":  {"label": "Third-Party Access",  "weight": 0.13},
    "data_retention":      {"label": "Data Retention",      "weight": 0.13},
    "arbitration":         {"label": "Arbitration",         "weight": 0.13},
    "content_rights":      {"label": "Content & IP Rights", "weight": 0.10},
    "liability_limitation":{"label": "Liability Limitation","weight": 0.09},
}

RISK_SCORE = {"HIGH": 100, "MEDIUM": 60, "LOW": 25, "NONE": 0}

# ── URL log ────────────────────────────────────────────────────────────────────
_url_log = []

# ── Helpers ────────────────────────────────────────────────────────────────────
def _score_from_clauses(clauses_with_risk):
    """Compute 0-100 risk score from a list of classified clauses."""
    cat_scores = {k: {"clauses": [], "score": 0} for k in CATEGORY_META}

    for c in clauses_with_risk:
        cat = c.get("category", "none")
        if cat not in cat_scores:
            continue
        base = RISK_SCORE.get(c.get("risk_level", "NONE"), 0)
        cat_scores[cat]["clauses"].append(c)
        # Bonus +5 per extra clause in same category, capped at +10
        n = len(cat_scores[cat]["clauses"])
        bonus = min((n - 1) * 5, 10)
        cat_scores[cat]["score"] = min(base + bonus, 100)

    # Weighted average
    total_weight = sum(CATEGORY_META[k]["weight"] for k in cat_scores)
    weighted_sum = sum(
        cat_scores[k]["score"] * CATEGORY_META[k]["weight"]
        for k in cat_scores
    )
    final_score = round(weighted_sum / total_weight) if total_weight else 0

    if final_score >= 60:
        risk_level = "HIGH"
    elif final_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return final_score, risk_level, cat_scores


def _max_risk_in_cat(clauses):
    order = ["HIGH", "MEDIUM", "LOW", "NONE"]
    found = [c.get("risk_level", "NONE") for c in clauses]
    for r in order:
        if r in found:
            return r
    return "NONE"


def _build_summary(score, risk_level, n_flagged, n_total):
    if risk_level == "HIGH":
        return (f"This document contains {n_flagged} high-risk clause(s) out of "
                f"{n_total} analyzed. Significant privacy and legal risks were detected "
                f"that may limit your rights or expose your data.")
    if risk_level == "MEDIUM":
        return (f"{n_flagged} clause(s) of concern were found across {n_total} analyzed. "
                f"Some data handling and liability provisions warrant attention.")
    return (f"Low risk detected. {n_flagged} minor clause(s) found across "
            f"{n_total} analyzed. This document appears relatively user-friendly.")


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":          "ok",
        "classifier_mode": CLASSIFIER_MODE,
        "version":         "3.0.0",
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) < 50:
        return jsonify({"error": "Text too short (minimum 50 characters)"}), 400

    t0 = time.time()

    # 1. Segment
    clauses = segment_clauses(text)
    logger.info(f"Segmented into {len(clauses)} clauses")

    # 2. Classify
    classified = []
    if CLASSIFIER_MODE == "hybrid" and classifier:
        results = classifier.classify_batch(clauses)
        for i, (clause_text, res) in enumerate(zip(clauses, results)):
            classified.append({
                "clause_number":         i + 1,
                "text":                  clause_text,
                "category":              res["category"],
                "primary_category":      res["category"],
                "primary_category_label":res.get("category_label", res["category"]),
                "risk_level":            res["risk_level"],
                "confidence":            res["confidence"],
                "source":                res["source"],
                "matched_keywords":      res.get("matched_keywords", []),
            })
    else:
        # Rule-based only fallback
        for i, clause_text in enumerate(clauses):
            res = rule_classifier.classify(clause_text)
            classified.append({
                "clause_number":         i + 1,
                "text":                  clause_text,
                "category":              res.get("category", "none"),
                "primary_category":      res.get("category", "none"),
                "primary_category_label":CATEGORY_META.get(
                    res.get("category", ""), {}).get("label", ""),
                "risk_level":            res.get("risk_level", "NONE"),
                "confidence":            1.0,
                "source":                "rule_based",
                "matched_keywords":      res.get("matched_keywords", []),
            })

    # 3. Filter to only risk clauses for the response
    risk_clauses = [c for c in classified if c["risk_level"] != "NONE"
                    and c["category"] != "none"]

    # 4. Score
    final_score, risk_level, cat_scores = _score_from_clauses(risk_clauses)
    ms = round((time.time() - t0) * 1000)

    # 5. Build category_scores response
    category_scores = {}
    for cat, meta in CATEGORY_META.items():
        cat_clauses = cat_scores[cat]["clauses"]
        category_scores[cat] = {
            "label":         meta["label"],
            "weight":        meta["weight"],
            "clause_count":  len(cat_clauses),
            "score":         cat_scores[cat]["score"],
            "max_risk_level": _max_risk_in_cat(cat_clauses),
        }

    return jsonify({
        "risk_score":                final_score,
        "risk_level":                risk_level,
        "summary":                   _build_summary(
            final_score, risk_level, len(risk_clauses), len(clauses)
        ),
        "total_clauses_analyzed":    len(clauses),
        "total_risk_clauses_detected": len(risk_clauses),
        "processing_time_ms":        ms,
        "classifier_mode":           CLASSIFIER_MODE,
        "category_scores":           category_scores,
        "clauses":                   classified,  # all clauses (frontend filters)
    })


@app.route("/fetch-url", methods=["POST"])
def fetch_url():
    data = request.get_json(silent=True) or {}
    url  = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept":          "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = http_requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
    except http_requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out after 15 seconds"}), 504
    except http_requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to {url}"}), 502
    except http_requests.exceptions.HTTPError as e:
        return jsonify({"error": f"HTTP {e.response.status_code}: {url}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    soup = BeautifulSoup(resp.text, "lxml")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "iframe", "noscript", "aside", "form", "button",
                     "img", "svg", "figure", "picture"]):
        tag.decompose()

    # Try to find main content block
    main = (soup.find("main") or
            soup.find("article") or
            soup.find(id=re.compile(r"content|main|body|terms|privacy", re.I)) or
            soup.find(class_=re.compile(r"content|main|body|terms|privacy", re.I)) or
            soup.body or
            soup)

    raw_text = main.get_text(separator="\n")

    # Clean up whitespace
    lines = [l.strip() for l in raw_text.splitlines()]
    lines = [l for l in lines if l and len(l) > 15]
    clean_text = "\n".join(lines)

    if len(clean_text) < 100:
        return jsonify({"error": "Could not extract meaningful text from this URL. "
                                  "Try pasting the text directly."}), 422

    _url_log.append(url)
    logger.info(f"Fetched {url} → {len(clean_text)} chars")

    return jsonify({
        "text":       clean_text,
        "char_count": len(clean_text),
        "url":        url,
    })


@app.route("/submitted-urls", methods=["GET"])
def submitted_urls():
    return jsonify({"urls": _url_log, "count": len(_url_log)})


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
