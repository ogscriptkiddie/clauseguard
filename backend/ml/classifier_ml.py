"""
ClauseGuard ML Classifier
=========================
Wraps the trained TF-IDF + calibrated classifier model.

Current behavior:
- Returns label prediction + confidence
- Keeps backward-compatible `category` key
- Adds neutral `label` key for future migration away from category-based naming
- Fails gracefully if model artifacts are missing
"""
import os
import pickle
from typing import Dict, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_model_bundle = None
_label_encoder = None
_model_load_error = None


def _load():
    global _model_bundle, _label_encoder, _model_load_error

    if _model_bundle is not None or _model_load_error is not None:
        return

    model_path = os.path.join(SCRIPT_DIR, "model.pkl")
    le_path = os.path.join(SCRIPT_DIR, "label_encoder.pkl")

    try:
        with open(model_path, "rb") as f:
            _model_bundle = pickle.load(f)
        with open(le_path, "rb") as f:
            _label_encoder = pickle.load(f)
    except Exception as e:
        _model_load_error = str(e)
        _model_bundle = None
        _label_encoder = None


class MLClassifier:
    """
    Lazy-loads model on first call.

    classify(text) -> {
        "label": str,
        "category": str,
        "confidence": float,
        "source": "ml",
        "all_probs": {...}
    }
    """

    def __init__(self):
        _load()
        self.available = _model_bundle is not None and _label_encoder is not None
        self.load_error = _model_load_error

        if self.available:
            self.tfidf = _model_bundle["tfidf"]
            self.classifier = _model_bundle["classifier"]
            self.le = _label_encoder
        else:
            self.tfidf = None
            self.classifier = None
            self.le = None

    def _empty_result(self) -> Dict:
        return {
            "label": "none",
            "category": "none",
            "confidence": 0.0,
            "source": "ml_unavailable",
            "all_probs": {},
            "error": self.load_error,
        }

    def classify(self, text: str) -> Dict:
        """Classify a single clause. Returns a backward-compatible dict."""
        if not self.available:
            return self._empty_result()

        vec = self.tfidf.transform([text])
        probs = self.classifier.predict_proba(vec)[0]
        idx = probs.argmax()
        label = self.le.inverse_transform([idx])[0]

        return {
            "label": label,
            "category": label,  # backward compatibility
            "confidence": float(probs[idx]),
            "source": "ml",
            "all_probs": {
                cat: round(float(p), 4)
                for cat, p in zip(self.le.classes_, probs)
            },
        }

    def classify_batch(self, texts: List[str]) -> List[Dict]:
        """Classify multiple clauses at once."""
        if not self.available:
            return [self._empty_result() for _ in texts]

        vecs = self.tfidf.transform(texts)
        probs = self.classifier.predict_proba(vecs)
        results = []

        for prob_row in probs:
            idx = prob_row.argmax()
            label = self.le.inverse_transform([idx])[0]
            results.append({
                "label": label,
                "category": label,  # backward compatibility
                "confidence": float(prob_row[idx]),
                "source": "ml",
                "all_probs": {
                    cat: round(float(p), 4)
                    for cat, p in zip(self.le.classes_, prob_row)
                },
            })

        return results