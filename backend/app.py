"""
app.py — ClauseGuard Flask API

Exposes the classification pipeline as an HTTP API for the Chrome extension.

Endpoints:
  GET  /health       → Liveness check
  POST /analyze      → Full ToS analysis (text input)

CORS is enabled globally so the Chrome extension can call the API from
any origin. When deploying publicly, restrict CORS to your extension ID.

Running locally:
  python app.py
  → http://localhost:5000

Running in production (Render / Railway / Fly.io):
  gunicorn app:app --bind 0.0.0.0:$PORT
"""

import time
import logging

from flask import Flask, request, jsonify
from flask_cors import CORS

from segmenter import segment_document, segment_document_numbered
from classifier import RuleBasedClassifier
from scorer import compute_risk_score, generate_summary

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
    """Liveness check. Used by uptime monitors and the extension's init check."""
    return jsonify({"status": "ok", "service": "ClauseGuard API", "version": "1.0.0"}), 200


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyzes a ToS or Privacy Policy document for security and privacy risks.

    Request body (JSON):
    {
        "text": "<full document text>"
    }

    Response (JSON):
    {
        "risk_score":                  72,
        "risk_level":                  "HIGH",
        "summary":                     "ClauseGuard detected 12 risk-relevant...",
        "total_clauses_analyzed":      87,
        "total_risk_clauses_detected": 12,
        "category_scores": {
            "data_sharing": {
                "score": 100, "max_risk_level": "HIGH",
                "clause_count": 3, "label": "Data Sharing", "weight": 0.25
            },
            ...
        },
        "clauses": [
            {
                "text":                   "We may sell your data to advertisers.",
                "primary_category":       "data_sharing",
                "primary_category_label": "Data Sharing",
                "risk_level":             "HIGH",
                "matched_keywords":       ["sell your data"],
                "confidence":             0.85,
                "all_matches":            [...]
            },
            ...
        ],
        "processing_time_ms": 142
    }
    """
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
        return _error(
            f"Text too short (minimum {MIN_TEXT_LENGTH} characters).", 400
        )

    if len(text) > MAX_TEXT_LENGTH:
        return _error(
            f"Text too large (maximum {MAX_TEXT_LENGTH:,} characters).", 413
        )

    # --- Pipeline -----------------------------------------------------------
    try:
        # Step 1: Segment document into numbered clauses
        numbered_clauses = segment_document_numbered(text)
        total_clauses = len(numbered_clauses)
        logger.info(f"Segmented into {total_clauses} clauses.")

        if not numbered_clauses:
            return _error("Document could not be segmented. Check input formatting.", 422)

        # Step 2: Classify each clause — pass text only, keep number for reference
        clause_texts = [c["text"] for c in numbered_clauses]
        clause_numbers = {c["text"]: c["clause_number"] for c in numbered_clauses}

        classified = classifier.classify_document(clause_texts)
        logger.info(f"Detected {len(classified)} risk-relevant clauses.")

        # Attach clause number to each classified result
        for result in classified:
            result["clause_number"] = clause_numbers.get(result["text"], None)

        # Step 3: Compute risk score
        score_result = compute_risk_score(classified)

        # Step 4: Human-readable summary
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
    """Returns a standardized JSON error response."""
    return jsonify({"error": message}), status_code


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
