"""
ClauseGuard Flask API
======================
Routes:
  GET  /health           — liveness check
  POST /analyze          — full ToS analysis (text -> risk JSON)
  POST /fetch-url        — server-side URL fetch + clean text extraction
  GET  /submitted-urls   — log of every URL analyzed
"""
import os, time, json, re, sys, logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests as http_requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ── Rule-based classifier ──────────────────────────────────────────────────────
from classifier import RuleBasedClassifier
rule_classifier = RuleBasedClassifier()

# Auto-detect method name (classifier.py may use classify_clause, predict, etc.)
_rule_method = None
for _m in ["classify", "classify_clause", "classify_text", "predict", "run", "analyse", "analyze"]:
    if hasattr(rule_classifier, _m) and callable(getattr(rule_classifier, _m)):
        _rule_method = _m
        logger.info(f"RuleBasedClassifier method: .{_m}()")
        break
if _rule_method is None:
    for _m in dir(rule_classifier):
        if not _m.startswith("_") and callable(getattr(rule_classifier, _m)):
            _rule_method = _m
            logger.warning(f"RuleBasedClassifier fallback method: .{_m}()")
            break

def _rule_classify(text):
    if _rule_method is None:
        return {}
    try:
        result = getattr(rule_classifier, _rule_method)(text)
        # classify_clause returns a list of matches — take the highest-confidence one
        if isinstance(result, list):
            if not result:
                return {}
            # Sort by confidence descending, take first
            result = sorted(result, key=lambda x: x.get("confidence", 0), reverse=True)[0]
        return result or {}
    except Exception as e:
        logger.warning(f"Rule classify error: {e}")
        return {}

# ── Hybrid classifier (ML + rule fallback) ─────────────────────────────────────
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ml.hybrid import HybridClassifier
    classifier = HybridClassifier(rule_based_classifier=rule_classifier)
    logger.info("HybridClassifier loaded (ML + rule-based fallback)")
    CLASSIFIER_MODE = "hybrid"
except Exception as e:
    logger.warning(f"HybridClassifier unavailable ({e}), rule-based only")
    classifier = None
    CLASSIFIER_MODE = "rule_based"

# ── spaCy segmenter ────────────────────────────────────────────────────────────
def _fallback_segmenter(text):
    """
    Robust fallback segmenter when spaCy is unavailable.
    Splits on blank lines, numbered headings, or lettered sub-items.
    Merges short fragments with the next segment.
    """
    # Split on double newlines or before numbered/lettered list items
    parts = re.split(r'\n{2,}|\n(?=\s*\d+[\.\)]\s+[A-Z])|\n(?=\s*[A-Z][A-Z\s]{4,}$)', text)
    segments = []
    for p in parts:
        p = p.strip()
        if len(p) < 40:
            continue
        # Further split very long single paragraphs on sentence boundaries
        if len(p) > 1200:
            sents = re.split(r'(?<=[.!?])\s+(?=[A-Z])', p)
            buf = ""
            for sent in sents:
                buf += " " + sent
                if len(buf) >= 300:
                    segments.append(buf.strip())
                    buf = ""
            if buf.strip():
                segments.append(buf.strip())
        else:
            segments.append(p)
    return segments if segments else [text[:2000]]

try:
    import segmenter as _seg_module
    segment_clauses = (
        getattr(_seg_module, "segment_clauses", None) or
        getattr(_seg_module, "segment", None) or
        getattr(_seg_module, "segmentClauses", None) or
        getattr(_seg_module, "get_clauses", None) or
        getattr(_seg_module, "segment_document", None) or
        getattr(_seg_module, "segment_document_numbered", None)
    )
    if segment_clauses is None:
        raise AttributeError("No recognised segmenter function in segmenter.py")
    logger.info("spaCy segmenter loaded")
except Exception as e:
    logger.warning(f"spaCy segmenter unavailable ({e}), using fallback")
    segment_clauses = _fallback_segmenter

# ── Category metadata ──────────────────────────────────────────────────────────
CATEGORY_META = {
    "data_sharing":         {"label": "Data Sharing",         "weight": 0.22},
    "tracking_profiling":   {"label": "Tracking & Profiling", "weight": 0.20},
    "third_party_access":   {"label": "Third-Party Access",   "weight": 0.13},
    "data_retention":       {"label": "Data Retention",       "weight": 0.13},
    "arbitration":          {"label": "Arbitration",          "weight": 0.13},
    "content_rights":       {"label": "Content & IP Rights",  "weight": 0.10},
    "liability_limitation": {"label": "Liability Limitation", "weight": 0.09},
}
RISK_SCORE = {"HIGH": 100, "MEDIUM": 60, "LOW": 25, "NONE": 0}
_url_log = []

# ── Scoring ────────────────────────────────────────────────────────────────────
def _score_from_clauses(risk_clauses):
    cat_scores = {k: {"clauses": [], "score": 0} for k in CATEGORY_META}
    for c in risk_clauses:
        cat = c.get("category", "none")
        if cat not in cat_scores:
            continue
        base  = RISK_SCORE.get(c.get("risk_level", "NONE"), 0)
        cat_scores[cat]["clauses"].append(c)
        n     = len(cat_scores[cat]["clauses"])
        bonus = min((n - 1) * 5, 10)
        cat_scores[cat]["score"] = min(base + bonus, 100)

    total_weight = sum(CATEGORY_META[k]["weight"] for k in cat_scores)
    weighted_sum = sum(cat_scores[k]["score"] * CATEGORY_META[k]["weight"] for k in cat_scores)
    final_score  = round(weighted_sum / total_weight) if total_weight else 0
    risk_level   = "HIGH" if final_score >= 60 else "MEDIUM" if final_score >= 30 else "LOW"
    return final_score, risk_level, cat_scores

def _max_risk(clauses):
    for r in ["HIGH", "MEDIUM", "LOW", "NONE"]:
        if any(c.get("risk_level") == r for c in clauses):
            return r
    return "NONE"

def _summary(score, level, n_flagged, n_total):
    if level == "HIGH":
        return (f"This document contains {n_flagged} high-risk clause(s) out of "
                f"{n_total} analyzed. Significant privacy and legal risks detected.")
    if level == "MEDIUM":
        return (f"{n_flagged} clause(s) of concern found across {n_total} analyzed. "
                f"Some data handling and liability provisions warrant attention.")
    return (f"Low risk detected. {n_flagged} minor clause(s) found across {n_total} analyzed.")

def preprocess_text(text: str) -> str:
    """
    Universal text normalizer — runs on ALL input paths (URL fetch, paste,
    extension DOM) before the segmenter sees the text.

    The core problem: copy-paste and DOM extraction produce single newlines
    between paragraphs. The segmenter's primary split needs double newlines.
    Without this, pasted text produces ~30% fewer clauses and a lower score
    than the same document fetched server-side.

    This function is a lightweight safety net on top of segmenter._normalize_text().
    It handles cases specific to each input format:

      1. Tab characters → spaces (extension DOM sometimes emits these)
      2. Windows smart quotes / dashes → ASCII equivalents
      3. Legal section headers in ALL CAPS with no surrounding blank lines
         → ensure blank line before them
      4. Lines that look like "X. Title" or "(a) Title" starting a new section
         → ensure blank line before them
      5. Sentences ending in .!? followed by a capital on the next line
         → insert blank line (paragraph break)
    """
    import re

    # Normalize encoding artifacts
    text = text.replace('\t', ' ')
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2013', '-').replace('\u2014', '-')
    text = re.sub(r'\r\n|\r', '\n', text)

    # Collapse 3+ blank lines early
    text = re.sub(r'\n{3,}', '\n\n', text)

    lines = text.splitlines()
    out = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        out.append(line)

        # Don't insert after the last line or before an already-blank line
        if i >= len(lines) - 1:
            continue
        next_stripped = lines[i + 1].strip()
        if not next_stripped or not stripped:
            continue

        inserted = False

        # Rule A: current line is ALL CAPS section header
        if (stripped.isupper()
                and 3 < len(stripped) < 120
                and not stripped[-1].isdigit()):
            out.append('')
            inserted = True

        # Rule B: next line opens a numbered/lettered section
        if not inserted and re.match(
            r'^(?:\d+[\.\)]\s|[A-Z][\.\)]\s|[a-z][\.\)]\s'
            r'|[ivxIVX]+\.\s|\([a-z0-9]\)\s'
            r'|Section\s+\d|Article\s+[IVXLC\d])',
            next_stripped
        ):
            out.append('')
            inserted = True

        # Rule C: sentence boundary — current ends sentence, next starts capital
        if not inserted:
            if (stripped and stripped[-1] in '.!?'
                    and next_stripped and next_stripped[0].isupper()
                    and len(stripped.split()) >= 5
                    and len(next_stripped.split()) >= 4):
                out.append('')

    result = '\n'.join(out)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "classifier_mode": CLASSIFIER_MODE,
        "rule_method": _rule_method,
        "version": "3.1.0",
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
    text = preprocess_text(text)
    clauses = segment_clauses(text)
    # Cap clause count to prevent timeout on very large documents
    CLAUSE_CAP = 300
    if len(clauses) > CLAUSE_CAP:
        logger.info(f"Segmented into {len(clauses)} clauses — capping at {CLAUSE_CAP}")
        clauses = clauses[:CLAUSE_CAP]
    else:
        logger.info(f"Segmented into {len(clauses)} clauses")

    classified = []
    if CLASSIFIER_MODE == "hybrid" and classifier:
        results = classifier.classify_batch(clauses)
        for i, (clause_text, res) in enumerate(zip(clauses, results)):
            classified.append({
                "clause_number":          i + 1,
                "text":                   clause_text,
                "category":               res["category"],
                "primary_category":       res["category"],
                "primary_category_label": res.get("category_label", res["category"]),
                "risk_level":             res["risk_level"],
                "confidence":             res["confidence"],
                "source":                 res["source"],
                "matched_keywords":       res.get("matched_keywords", []),
            })
    else:
        # Rule-based only
        for i, clause_text in enumerate(clauses):
            res  = _rule_classify(clause_text)
            cat  = res.get("category") or res.get("primary_category") or "none"
            rl   = res.get("risk_level") or "NONE"
            kws  = res.get("matched_keywords") or res.get("keywords") or []
            classified.append({
                "clause_number":          i + 1,
                "text":                   clause_text,
                "category":               cat,
                "primary_category":       cat,
                "primary_category_label": CATEGORY_META.get(cat, {}).get("label", ""),
                "risk_level":             rl,
                "confidence":             1.0,
                "source":                 "rule_based",
                "matched_keywords":       kws,
            })

    risk_clauses = [c for c in classified
                    if c["risk_level"] != "NONE" and c["category"] != "none"]

    final_score, risk_level, cat_scores = _score_from_clauses(risk_clauses)
    ms = round((time.time() - t0) * 1000)

    category_scores = {
        cat: {
            "label":         meta["label"],
            "weight":        meta["weight"],
            "clause_count":  len(cat_scores[cat]["clauses"]),
            "score":         cat_scores[cat]["score"],
            "max_risk_level": _max_risk(cat_scores[cat]["clauses"]),
        }
        for cat, meta in CATEGORY_META.items()
    }

    return jsonify({
        "risk_score":                  final_score,
        "risk_level":                  risk_level,
        "summary":                     _summary(final_score, risk_level, len(risk_clauses), len(clauses)),
        "total_clauses_analyzed":      len(clauses),
        "total_risk_clauses_detected": len(risk_clauses),
        "processing_time_ms":          ms,
        "classifier_mode":             CLASSIFIER_MODE,
        "category_scores":             category_scores,
        "clauses":                     classified,
    })

@app.route("/fetch-url", methods=["POST"])
def fetch_url():
    data = request.get_json(silent=True) or {}
    url  = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml",
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
        code = e.response.status_code
        if code == 403:
            return jsonify({"error": (
                "This site blocks automated access (403). "
                "Open the page in your browser, copy all the text, "
                "then use the Paste Text tab instead."
            )}), 422
        if code == 404:
            return jsonify({"error": f"Page not found (404): {url}"}), 422
        return jsonify({"error": f"HTTP {code} error fetching {url}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script","style","nav","header","footer",
                     "iframe","noscript","aside","form","button",
                     "img","svg","figure","picture"]):
        tag.decompose()

    main = (soup.find("main") or soup.find("article") or
            soup.find(id=re.compile(r"content|main|body|terms|privacy", re.I)) or
            soup.find(class_=re.compile(r"content|main|body|terms|privacy", re.I)) or
            soup.body or soup)

    raw   = main.get_text(separator="\n")
    lines = [l.strip() for l in raw.splitlines() if l.strip() and len(l.strip()) > 15]
    clean = preprocess_text("\n".join(lines))

    if len(clean) < 100:
        return jsonify({"error": "Could not extract meaningful text. Try pasting directly."}), 422

    _url_log.append(url)
    logger.info(f"Fetched {url} -> {len(clean)} chars")
    return jsonify({"text": clean, "char_count": len(clean), "url": url})

@app.route("/submitted-urls", methods=["GET"])
def submitted_urls():
    return jsonify({"urls": _url_log, "count": len(_url_log)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)