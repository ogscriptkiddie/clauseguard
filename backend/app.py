"""
app.py — ClauseGuard Flask API

Exposes the classification pipeline as an HTTP API for the Chrome extension.

Endpoints:
  GET  /health       → Liveness check
  POST /analyze      → Full ToS analysis (text input)

Running locally:
  python app.py  →  http://localhost:5000

Running in production (Railway / Render / Fly.io):
  gunicorn app:app --bind 0.0.0.0:$PORT
"""

import os
import time
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS

# ---------------------------------------------------------------------------
# App setup  ← app must be created BEFORE any decorators that reference it
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CORS — ensure all responses carry the right headers (handles preflight too)
# ---------------------------------------------------------------------------

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ---------------------------------------------------------------------------
# Pipeline imports  ← after app is created so any app-context code works
# ---------------------------------------------------------------------------

from segmenter import segment_document, segment_document_numbered
from classifier import RuleBasedClassifier
from scorer import compute_risk_score, generate_summary

# Instantiate once at startup (not per-request)
classifier = RuleBasedClassifier()

# Input limits
MAX_TEXT_LENGTH = 500_000   # ~125k words — covers even the longest ToS docs
MIN_TEXT_LENGTH = 50        # Reject trivially short inputs


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    """Liveness check."""
    return jsonify({"status": "ok", "service": "ClauseGuard API", "version": "1.0.0"}), 200


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    """Analyzes a ToS or Privacy Policy document for security and privacy risks."""

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return jsonify({}), 200

    start = time.time()

    # --- Input validation ---------------------------------------------------
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

    # --- Pipeline -----------------------------------------------------------
    try:
        numbered_clauses = segment_document_numbered(text)
        total_clauses = len(numbered_clauses)
        logger.info(f"Segmented into {total_clauses} clauses.")

        if not numbered_clauses:
            return _error("Document could not be segmented. Check input formatting.", 422)

        clause_texts = [c["text"] for c in numbered_clauses]
        clause_numbers = {c["text"]: c["clause_number"] for c in numbered_clauses}

        classified = classifier.classify_document(clause_texts)
        logger.info(f"Detected {len(classified)} risk-relevant clauses.")

        for result in classified:
            result["clause_number"] = clause_numbers.get(result["text"], None)

        score_result = compute_risk_score(classified)
        summary = generate_summary(score_result, classified)
        elapsed_ms = round((time.time() - start) * 1000)

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
