"""
ClauseGuard Flask API
======================
Routes:
  GET  /health           — liveness check
  POST /analyze          — full ToS analysis (text -> risk JSON)
  POST /fetch-url        — server-side URL fetch + clean text extraction
  POST /upload-pdf       — PDF upload -> text extraction -> risk JSON
"""
import os
import time
import re
import sys
import logging
import ipaddress
import urllib.parse

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests as http_requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ── Request size limit — 10 MB to accommodate PDF uploads ─────────────────────
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# ── CORS — restrict to known safe origins ─────────────────────────────────────
_raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
if not _allowed_origins:
    _allowed_origins = [
        "https://clauseguard-production-183f.up.railway.app",
        "https://clauseguard-chi.vercel.app",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]
CORS(app, origins=_allowed_origins + ["chrome-extension://*"])

# ── Rate limiting ──────────────────────────────────────────────────────────────
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://",
)

# ── SSRF guard ────────────────────────────────────────────────────────────────
_BLOCKED_HOSTS = frozenset({
    "localhost", "localhost.", "metadata.google.internal",
})
_BLOCKED_SCHEMES = frozenset({"file", "ftp", "data", "javascript", "gopher"})


def _validate_fetch_url(url: str):
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False, "Invalid URL"

    scheme = (parsed.scheme or "").lower()
    if scheme in _BLOCKED_SCHEMES:
        return False, f"URL scheme '{scheme}' is not allowed"
    if scheme not in ("http", "https"):
        return False, "Only http:// and https:// URLs are supported"

    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname:
        return False, "URL has no hostname"

    if hostname in _BLOCKED_HOSTS:
        return False, "Requests to internal addresses are not allowed"

    if hostname.endswith((".local", ".internal", ".localhost", ".corp", ".lan")):
        return False, "Requests to internal addresses are not allowed"

    try:
        ip = ipaddress.ip_address(hostname)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False, "Requests to internal addresses are not allowed"
    except ValueError:
        pass

    return True, ""


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


# ── Hybrid classifier ──────────────────────────────────────────────────────────
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
    parts = re.split(r"\n{2,}|\n(?=\s*\d+[\.\)]\s+[A-Z])|\n(?=\s*[A-Z][A-Z\s]{4,}$)", text)
    segments = []
    for p in parts:
        p = p.strip()
        if len(p) < 40:
            continue
        if len(p) > 1200:
            sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", p)
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
        getattr(_seg_module, "segment_clauses", None)
        or getattr(_seg_module, "segment", None)
        or getattr(_seg_module, "segmentClauses", None)
        or getattr(_seg_module, "get_clauses", None)
        or getattr(_seg_module, "segment_document", None)
        or getattr(_seg_module, "segment_document_numbered", None)
    )
    if segment_clauses is None:
        raise AttributeError("No recognised segmenter function in segmenter.py")
    logger.info("spaCy segmenter loaded")
except Exception as e:
    logger.warning(f"spaCy segmenter unavailable ({e}), using fallback")
    segment_clauses = _fallback_segmenter


# ── Category metadata ──────────────────────────────────────────────────────────
_URL_LOG_MAX = 500
CATEGORY_META = {
    "data_sharing": {"label": "Data Sharing", "weight": 0.22},
    "tracking_profiling": {"label": "Tracking & Profiling", "weight": 0.20},
    "third_party_access": {"label": "Third-Party Access", "weight": 0.13},
    "data_retention": {"label": "Data Retention", "weight": 0.13},
    "arbitration": {"label": "Arbitration", "weight": 0.13},
    "content_rights": {"label": "Content & IP Rights", "weight": 0.10},
    "liability_limitation": {"label": "Liability Limitation", "weight": 0.09},
}
_url_log = []

# ── Shared scorer module ───────────────────────────────────────────────────────
from scorer import compute_risk_score, generate_summary


# ── User obligation filter ─────────────────────────────────────────────────────
_PREFIX_RE = re.compile(
    r"""(?xi)
    ^\s*
    (?:
        you\s+(?:must\s+not|may\s+not|shall\s+not|will\s+not|cannot|can\s+not|
                 agree\s+not\s+to|are\s+not\s+(?:permitted|allowed|authorized|
                 entitled)|are\s+prohibited\s+from|are\s+strictly\s+prohibited)
      |
        (?:users?\s+)?
        (?:must\s+not|may\s+not|shall\s+not|cannot|are\s+not\s+(?:permitted|
           allowed|authorized)|are\s+prohibited|is\s+prohibited|are\s+forbidden)
      |
        (?:please\s+)?don\'?t\b
      |
        do\s+not\b
      |
        (?:the\s+following\s+(?:activities?\s+)?(?:is|are)\s+)?
        (?:prohibited|forbidden|not\s+(?:permitted|allowed))
      |
        (?:[ivxIVX]+\.|[a-z]\)|\d+[\.\)])\s+
        (?:don\'?t|do\s+not|you\s+(?:must\s+not|may\s+not|shall\s+not|cannot))
    )
    """,
    re.IGNORECASE,
)

_COMPANY_ACTION_RE = re.compile(
    r"""(?xi)
    \b
    (?:we|us|our|the\s+company|the\s+service|the\s+platform)
    \s+
    (?:may|will|can|shall|collect|share|sell|transfer|retain|store|
       disclose|provide|use|process|track|monitor|access|transmit|
       combine|infer|profile|send|distribute)
    \b
    """,
    re.IGNORECASE,
)


def _is_user_obligation(text: str) -> bool:
    t = text.strip()
    if _COMPANY_ACTION_RE.search(t):
        return False
    if _PREFIX_RE.match(t):
        return True

    t_lower = t.lower()
    user_count = len(re.findall(r"\b(you|your|user\'?s?)\b", t_lower))
    company_count = len(re.findall(r"\b(we|us|our|company|service|platform)\b", t_lower))
    prohibition_with_user = re.search(
        r"\b(?:you|users?)\b.{0,30}\b(?:must\s+not|may\s+not|shall\s+not|"
        r"cannot|agree\s+not|are\s+prohibited|are\s+not\s+(?:permitted|allowed|"
        r"authorized)|are\s+forbidden)\b",
        t_lower,
    )
    if prohibition_with_user and user_count > company_count:
        return True
    return False


def _filter_user_obligations(classified: list) -> list:
    for c in classified:
        if c.get("risk_level") in ("HIGH", "MEDIUM"):
            if _is_user_obligation(c.get("text", "")):
                c["risk_level"] = "NONE"
                c["category"] = "none"
                c["primary_category"] = "none"
    return classified


def preprocess_text(text: str) -> str:
    text = text.replace("\t", " ")
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = text.splitlines()
    out = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        out.append(line)

        if i >= len(lines) - 1:
            continue
        next_stripped = lines[i + 1].strip()
        if not next_stripped or not stripped:
            continue

        inserted = False

        if stripped.isupper() and 3 < len(stripped) < 120 and not stripped[-1].isdigit():
            out.append("")
            inserted = True

        if not inserted and re.match(
            r"^(?:\d+[\.\)]\s|[A-Z][\.\)]\s|[a-z][\.\)]\s"
            r"|[ivxIVX]+\.\s|\([a-z0-9]\)\s"
            r"|Section\s+\d|Article\s+[IVXLC\d])",
            next_stripped,
        ):
            out.append("")
            inserted = True

        if not inserted:
            if (
                stripped
                and stripped[-1] in ".!?"
                and next_stripped
                and next_stripped[0].isupper()
                and len(stripped.split()) >= 5
                and len(next_stripped.split()) >= 4
            ):
                out.append("")

    result = "\n".join(out)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _legacy_summary(score: int, level: str, n_flagged: int, n_total: int) -> str:
    if level == "HIGH":
        return (
            f"This document contains {n_flagged} high-risk clause(s) out of "
            f"{n_total} analyzed. Significant privacy and legal risks detected."
        )
    if level == "MEDIUM":
        return (
            f"{n_flagged} clause(s) of concern found across {n_total} analyzed. "
            f"Some data handling and liability provisions warrant attention."
        )
    if level == "LOW":
        return (
            f"Low risk detected. {n_flagged} minor clause(s) found across {n_total} analyzed."
        )
    return f"No major risk detected across {n_total} analyzed clauses."


# ── Shared analysis pipeline ───────────────────────────────────────────────────
def _run_analysis(text: str):
    """
    Core analysis pipeline. Takes clean text, returns a Flask JSON response.
    Called by both /analyze and /upload-pdf.
    """
    t0 = time.time()
    text = preprocess_text(text)
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
                "clause_number": i + 1,
                "text": clause_text,
                "category": res.get("category", "none"),
                "primary_category": res.get("category", "none"),
                "primary_category_label": res.get("category_label", res.get("category", "none")),
                "risk_level": res.get("risk_level", "NONE"),
                "confidence": res.get("confidence", 0.0),
                "source": res.get("source", "hybrid"),
                "matched_keywords": res.get("matched_keywords", []),
                "all_probs": res.get("all_probs", {}),
            })
    else:
        for i, clause_text in enumerate(clauses):
            res = _rule_classify(clause_text)
            cat = res.get("category") or res.get("primary_category") or "none"
            rl = res.get("risk_level") or "NONE"
            kws = res.get("matched_keywords") or res.get("keywords") or []
            classified.append({
                "clause_number": i + 1,
                "text": clause_text,
                "category": cat,
                "primary_category": cat,
                "primary_category_label": CATEGORY_META.get(cat, {}).get("label", cat),
                "risk_level": rl,
                "confidence": res.get("confidence", 1.0),
                "source": "rule_based",
                "matched_keywords": kws,
                "all_probs": res.get("all_probs", {}),
            })

    classified = _filter_user_obligations(classified)
    risk_clauses = [
        c for c in classified
        if c.get("risk_level") != "NONE" and c.get("category") != "none"
    ]

    score_result = compute_risk_score(risk_clauses)
    final_score = score_result["overall_score"]
    risk_level = score_result["overall_risk_level"]
    category_scores = score_result["category_scores"]

    ms = round((time.time() - t0) * 1000)

    # Legacy-compatible summary
    summary = _legacy_summary(final_score, risk_level, len(risk_clauses), len(clauses))

    # Newer analysis block for migration
    analysis_v2 = {
        "response_version": "2.0",
        "document_summary": {
            "overall_score": final_score,
            "risk_label": risk_level,
            "clause_count": len(clauses),
            "risk_clause_count": len(risk_clauses),
        },
        "clauses": [
            {
                "clause_id": c["clause_number"],
                "text": c["text"],
                "function": {
                    "label": c.get("category", "none"),
                    "confidence": c.get("confidence", 0.0),
                    "source": c.get("source", "unknown"),
                },
                "matched_triggers": c.get("matched_keywords", []),
                "risk": {
                    "label": c.get("risk_level", "NONE"),
                },
            }
            for c in classified
        ],
        "summary": generate_summary(score_result, risk_clauses),
    }

    return jsonify({
        "response_version": "1.5",
        "risk_score": final_score,
        "risk_level": risk_level,
        "summary": summary,
        "total_clauses_analyzed": len(clauses),
        "total_risk_clauses_detected": len(risk_clauses),
        "processing_time_ms": ms,
        "classifier_mode": CLASSIFIER_MODE,
        "category_scores": category_scores,
        "clauses": classified,
        "analysis_v2": analysis_v2,
    })


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "classifier_mode": CLASSIFIER_MODE,
        "rule_method": _rule_method,
        "version": "3.3.0",
    })


@app.route("/analyze", methods=["POST"])
@limiter.limit("30 per minute")
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) < 50:
        return jsonify({"error": "Text too short (minimum 50 characters)"}), 400
    if len(text) > 1_500_000:
        return jsonify({"error": "Text too large (maximum 1.5 MB)"}), 413

    return _run_analysis(text)


@app.route("/upload-pdf", methods=["POST"])
@limiter.limit("20 per minute")
def upload_pdf():
    if "file" not in request.files:
        return jsonify({
            "error": "No file uploaded. Send the PDF as form-data with field name 'file'."
        }), 400

    file = request.files["file"]

    if not file or not file.filename:
        return jsonify({"error": "No file selected."}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "File must be a PDF (.pdf extension required)."}), 400

    try:
        from pypdf import PdfReader
        import io

        raw_bytes = file.read()

        if len(raw_bytes) == 0:
            return jsonify({"error": "Uploaded file is empty."}), 400

        if len(raw_bytes) > 10 * 1024 * 1024:
            return jsonify({"error": "PDF too large (maximum 10 MB)."}), 413

        reader = PdfReader(io.BytesIO(raw_bytes))
        if reader.is_encrypted:
            result = reader.decrypt('')
            if result == 0:
                return jsonify({"error": "PDF is password protected"}), 400
                

        text_parts = []
        for page in reader.pages:
            try:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
            except Exception:
                continue

        text = "\n\n".join(text_parts).strip()

        if len(text) < 50:
            return jsonify({
                "error": (
                    "Could not extract readable text from this PDF. "
                    "It may be scanned or image-based. "
                    "Try opening it in your browser, copying all the text, "
                    "then using the URL tab instead."
                )
            }), 422

        logger.info(
            f"PDF upload: {file.filename} — {len(raw_bytes):,} bytes — {len(text):,} chars extracted"
        )
        return _run_analysis(text)

    except Exception as e:
        logger.error(f"PDF processing error ({file.filename}): {e}")
        return jsonify({"error": f"PDF processing failed: {str(e)}"}), 500


@app.route("/fetch-url", methods=["POST"])
@limiter.limit("20 per minute")
def fetch_url():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    valid, reason = _validate_fetch_url(url)
    if not valid:
        logger.warning(f"Blocked fetch-url request: {reason} — url={url!r}")
        return jsonify({"error": reason}), 422

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
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
            return jsonify({
                "error": (
                    "This site blocks automated access (403). "
                    "Open the page in your browser, copy all the text, "
                    "then use the Paste Text tab instead."
                )
            }), 422
        if code == 404:
            return jsonify({"error": f"Page not found (404): {url}"}), 422
        return jsonify({"error": f"HTTP {code} error fetching {url}"}), 502
    except Exception as e:
        logger.error(f"Unexpected error fetching URL: {e}")
        return jsonify({"error": "Unexpected error fetching the URL"}), 500

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup([
        "script", "style", "nav", "header", "footer",
        "iframe", "noscript", "aside", "form", "button",
        "img", "svg", "figure", "picture"
    ]):
        tag.decompose()

    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id=re.compile(r"content|main|body|terms|privacy", re.I))
        or soup.find(class_=re.compile(r"content|main|body|terms|privacy", re.I))
        or soup.body
        or soup
    )

    raw = main.get_text(separator="\n")
    lines = [l.strip() for l in raw.splitlines() if l.strip() and len(l.strip()) > 15]
    clean = preprocess_text("\n".join(lines))

    if len(clean) < 100:
        return jsonify({"error": "Could not extract meaningful text. Try pasting directly."}), 422

    if len(_url_log) < _URL_LOG_MAX:
        _url_log.append(url)
    logger.info(f"Fetched {url} -> {len(clean)} chars")
    return jsonify({"text": clean, "char_count": len(clean), "url": url})


# ── 413 handler — file too large ───────────────────────────────────────────────
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File or request too large (maximum 10 MB)."}), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)