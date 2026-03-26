"""
app.py — ClauseGuard Flask API

Endpoints:
  GET  /health       → Liveness check
  POST /analyze      → Full ToS analysis (text input)
  POST /fetch-url    → Fetch a ToS page by URL, log it, return text

Running locally:
  python app.py  →  http://localhost:5000

Running in production (Railway):
  gunicorn app:app --bind 0.0.0.0:$PORT
"""

import os
import time
import logging
import datetime

import requests as http_requests
from bs4 import BeautifulSoup

from flask import Flask, request, jsonify
from flask_cors import CORS

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CORS headers on every response
# ---------------------------------------------------------------------------

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ---------------------------------------------------------------------------
# Pipeline imports
# ---------------------------------------------------------------------------

from segmenter import segment_document, segment_document_numbered
from classifier import RuleBasedClassifier
from scorer import compute_risk_score, generate_summary

classifier = RuleBasedClassifier()

MAX_TEXT_LENGTH = 500_000
MIN_TEXT_LENGTH = 50

# ---------------------------------------------------------------------------
# URL log — saved alongside app.py, persists within a Railway deploy session
# Viewable in Railway logs and downloadable from dashboard
# ---------------------------------------------------------------------------

URL_LOG_PATH = os.path.join(os.path.dirname(__file__), "submitted_urls.txt")

def log_url(url: str, status: str = "ok", char_count: int = 0):
    """Append a submitted URL to the log file and Railway stdout."""
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"{timestamp}\t{status}\t{char_count}\t{url}\n"
    try:
        with open(URL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass
    logger.info(f"[URL_LOG] {status.upper()} | {char_count} chars | {url}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "ClauseGuard API",
        "status": "ok",
        "version": "1.0.0",
        "endpoints": {
            "health":    "GET  /health",
            "analyze":   "POST /analyze",
            "fetch_url": "POST /fetch-url",
        }
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ClauseGuard API", "version": "1.0.0"}), 200


@app.route("/fetch-url", methods=["POST", "OPTIONS"])
def fetch_url():
    """
    Fetches a ToS / Privacy Policy page by URL, extracts its text,
    logs the URL for future dataset use, and returns the plain text.

    Request body (JSON):
      { "url": "https://discord.com/privacy" }

    Response (JSON):
      { "text": "...", "char_count": 12345, "url": "..." }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True)
    if not data or "url" not in data:
        return _error("Missing required field: 'url'.", 400)

    url = str(data["url"]).strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info(f"Fetching URL: {url}")

    try:
        resp = http_requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                )
            },
            allow_redirects=True,
        )
        resp.raise_for_status()
    except http_requests.exceptions.Timeout:
        log_url(url, "timeout")
        return _error("Request timed out. The page took too long to respond.", 504)
    except http_requests.exceptions.RequestException as e:
        log_url(url, "error")
        return _error(f"Could not fetch URL: {str(e)}", 502)

    # Extract readable text with BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove nav, header, footer, script, style — keep body prose
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "form", "button", "noscript", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Collapse excessive blank lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    text = "\n".join(lines)

    if len(text) < MIN_TEXT_LENGTH:
        log_url(url, "too_short", len(text))
        return _error(
            "Page text too short after extraction. "
            "This page may require JavaScript or block automated access.", 422
        )

    log_url(url, "ok", len(text))

    return jsonify({
        "url":        url,
        "text":       text[:MAX_TEXT_LENGTH],
        "char_count": len(text),
    }), 200


@app.route("/submitted-urls", methods=["GET"])
def submitted_urls():
    """
    Returns all URLs submitted via /fetch-url.
    Useful for harvesting new ToS documents for Phase 3 dataset expansion.
    Protected by a simple token — set URL_LOG_TOKEN env var on Railway.
    """
    token = os.environ.get("URL_LOG_TOKEN", "")
    if token and request.args.get("token") != token:
        return _error("Unauthorized.", 401)

    try:
        if not os.path.exists(URL_LOG_PATH):
            return jsonify({"urls": [], "count": 0}), 200
        with open(URL_LOG_PATH, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        entries = []
        for line in lines:
            parts = line.split("\t")
            if len(parts) == 4:
                entries.append({
                    "timestamp":  parts[0],
                    "status":     parts[1],
                    "char_count": int(parts[2]) if parts[2].isdigit() else 0,
                    "url":        parts[3],
                })
        return jsonify({"urls": entries, "count": len(entries)}), 200
    except Exception as e:
        return _error(f"Could not read log: {str(e)}", 500)


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    start = time.time()
    data = request.get_json(silent=True)

    if not data:
        return _error("Request body must be valid JSON.", 400)
    if "text" not in data:
        return _error("Missing required field: 'text'.", 400)

    text = data["text"]
    if not isinstance(text, str):
        return _error("Field 'text' must be a string.", 400)

    text = text.strip()

    if len(text) < MIN_TEXT_LENGTH:
        return _error(f"Text too short (minimum {MIN_TEXT_LENGTH} characters).", 400)
    if len(text) > MAX_TEXT_LENGTH:
        return _error(f"Text too large (maximum {MAX_TEXT_LENGTH:,} characters).", 413)

    try:
        numbered_clauses = segment_document_numbered(text)
        total_clauses = len(numbered_clauses)
        logger.info(f"Segmented into {total_clauses} clauses.")

        if not numbered_clauses:
            return _error("Document could not be segmented.", 422)

        clause_texts  = [c["text"] for c in numbered_clauses]
        clause_numbers = {c["text"]: c["clause_number"] for c in numbered_clauses}

        classified = classifier.classify_document(clause_texts)
        logger.info(f"Detected {len(classified)} risk-relevant clauses.")

        for result in classified:
            result["clause_number"] = clause_numbers.get(result["text"], None)

        score_result = compute_risk_score(classified)
        summary      = generate_summary(score_result, classified)
        elapsed_ms   = round((time.time() - start) * 1000)

        return jsonify({
            "risk_score":                  score_result["overall_score"],
            "risk_level":                  score_result["overall_risk_level"],
            "summary":                     summary,
            "total_clauses_analyzed":      total_clauses,
            "total_risk_clauses_detected": len(classified),
            "category_scores":             score_result["category_scores"],
            "clauses":                     classified,
            "processing_time_ms":          elapsed_ms,
        }), 200

    except Exception as exc:
        logger.exception("Unhandled error during analysis.")
        return _error(f"Internal analysis error: {str(exc)}", 500)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error(message: str, status_code: int):
    return jsonify({"error": message}), status_code


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)