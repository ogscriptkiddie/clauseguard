"""
ClauseGuard Flask API
======================
Routes:
  GET  /health           — liveness check
  POST /analyze          — full ToS analysis (text -> risk JSON)
  POST /fetch-url        — server-side URL fetch + clean text extraction
  GET  /submitted-urls   — log of every URL analyzed

v3.2.0 — /fetch-url now tries Playwright (headless Chromium) first so that
          JS-rendered content like Meta's accordion vendor lists is captured.
          Falls back to requests+BeautifulSoup if Playwright is unavailable
          or the page times out.
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

# ── Playwright availability check ──────────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    logger.info("Playwright available — JS-rendered pages will be fully expanded")
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available — falling back to requests+BS4")

# ── Rule-based classifier ──────────────────────────────────────────────────────
from classifier import RuleBasedClassifier
rule_classifier = RuleBasedClassifier()

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
        if isinstance(result, list):
            if not result:
                return {}
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
    parts = re.split(r'\n{2,}|\n(?=\s*\d+[\.\)]\s+[A-Z])|\n(?=\s*[A-Z][A-Z\s]{4,}$)', text)
    segments = []
    for p in parts:
        p = p.strip()
        if len(p) < 40:
            continue
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

# ── Text cleaning helper (shared by both fetch methods) ───────────────────────
def _clean_fetched_text(raw):
    """Normalize raw extracted text into clean lines for analysis."""
    lines = [l.strip() for l in raw.splitlines() if l.strip() and len(l.strip()) > 15]
    return "\n".join(lines)

# ── Playwright fetch (JS-rendered pages, accordion expansion) ─────────────────
def _fetch_with_playwright(url):
    """
    Launch a headless Chromium browser, load the page, expand all collapsed
    disclosure elements (accordions, <details>, aria-expanded sections),
    then extract the full visible text.

    Returns: (clean_text: str, expanded_count: int)
    Raises:  Exception on timeout or navigation failure
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
            ]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()

        try:
            # Navigate — wait for DOM to be interactive, not full network idle
            # (network idle can hang on pages with long-polling or analytics)
            page.goto(url, wait_until="domcontentloaded", timeout=20000)

            # Extra wait for JS frameworks to finish rendering
            page.wait_for_timeout(1800)

            # ── Step 1: Open all native <details> elements directly ──────────
            page.evaluate("""
                document.querySelectorAll('details:not([open])').forEach(d => {
                    d.open = true;
                });
            """)

            # ── Step 2: Click collapsed ARIA / framework accordion triggers ──
            # Covers: standard ARIA, Radix UI, Headless UI patterns
            COLLAPSED_SELECTORS = ", ".join([
                '[aria-expanded="false"]',
                '[data-state="closed"]',
                '[data-headlessui-state="closed"]',
            ])

            triggers = page.query_selector_all(COLLAPSED_SELECTORS)
            clicked = 0
            MAX_CLICKS = 60  # safety cap

            for trigger in triggers:
                if clicked >= MAX_CLICKS:
                    break
                try:
                    # Skip invisible elements (zero bounding box)
                    box = trigger.bounding_box()
                    if not box or (box["width"] == 0 and box["height"] == 0):
                        continue
                    # Skip submit/reset buttons
                    el_type = trigger.get_attribute("type") or ""
                    if el_type.lower() in ("submit", "reset"):
                        continue
                    trigger.click(timeout=1000)
                    clicked += 1
                except Exception:
                    pass  # unclickable — skip silently

            # Wait for React/Vue re-renders after all clicks
            if clicked > 0:
                page.wait_for_timeout(800)

            logger.info(f"Playwright: expanded {clicked} accordion(s) on {url}")

            # ── Step 3: Extract text — remove noise, prefer main content ─────
            text = page.evaluate("""
                () => {
                    const NOISE = [
                        'script','style','noscript','nav','header',
                        'footer','iframe','aside','figure','picture',
                        'svg','img','button','form',
                        '[role="navigation"]','[role="banner"]',
                        '.cookie-banner','#cookie-consent','.navbar',
                    ];
                    NOISE.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => el.remove());
                    });
                    const PREFER = [
                        'main','article','[role="main"]',
                        '.legal-content','.terms-content','.privacy-content',
                        '#legal','#terms','#privacy','#content','.content',
                    ];
                    for (const sel of PREFER) {
                        const el = document.querySelector(sel);
                        if (el && (el.innerText || '').trim().length > 500) {
                            return el.innerText;
                        }
                    }
                    return document.body.innerText;
                }
            """)

            clean = _clean_fetched_text(text or "")
            return clean, clicked

        finally:
            browser.close()

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "classifier_mode": CLASSIFIER_MODE,
        "rule_method": _rule_method,
        "playwright": PLAYWRIGHT_AVAILABLE,
        "version": "3.2.0",
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
    clauses = segment_clauses(text)
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
            "label":          meta["label"],
            "weight":         meta["weight"],
            "clause_count":   len(cat_scores[cat]["clauses"]),
            "score":          cat_scores[cat]["score"],
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

    _url_log.append(url)

    # ── Strategy 1: Playwright (JS-rendered, accordion expansion) ─────────────
    if PLAYWRIGHT_AVAILABLE:
        try:
            clean, expanded = _fetch_with_playwright(url)
            if len(clean) >= 100:
                logger.info(f"Playwright fetch OK: {url} -> {len(clean)} chars, {expanded} expanded")
                return jsonify({
                    "text":       clean,
                    "char_count": len(clean),
                    "url":        url,
                    "method":     "playwright",
                    "expanded":   expanded,
                })
            else:
                logger.warning(f"Playwright extracted too little text ({len(clean)} chars), falling back")
        except Exception as e:
            logger.warning(f"Playwright fetch failed ({e}), falling back to requests")

    # ── Strategy 2: requests + BeautifulSoup (static HTML fallback) ──────────
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

    clean = _clean_fetched_text(main.get_text(separator="\n"))

    if len(clean) < 100:
        return jsonify({"error": "Could not extract meaningful text. Try pasting directly."}), 422

    logger.info(f"requests fetch OK: {url} -> {len(clean)} chars")
    return jsonify({
        "text":       clean,
        "char_count": len(clean),
        "url":        url,
        "method":     "requests",
        "expanded":   0,
    })

@app.route("/submitted-urls", methods=["GET"])
def submitted_urls():
    return jsonify({"urls": _url_log, "count": len(_url_log)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
