"""
ClauseGuard ML Classifier
==========================
Wraps the trained TF-IDF + CalibratedLogisticRegression model.
Returns category prediction + confidence score for each clause.
"""
import os
import pickle

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_model_bundle = None
_label_encoder = None


def _load():
    global _model_bundle, _label_encoder
    if _model_bundle is None:
        model_path = os.path.join(SCRIPT_DIR, "model.pkl")
        le_path    = os.path.join(SCRIPT_DIR, "label_encoder.pkl")
        with open(model_path, "rb") as f:
            _model_bundle = pickle.load(f)
        with open(le_path, "rb") as f:
            _label_encoder = pickle.load(f)


class MLClassifier:
    """
    Lazy-loads model on first call.
    classify(text) → {"category": str, "confidence": float, "source": "ml"}
    """

    def __init__(self):
        _load()
        self.tfidf      = _model_bundle["tfidf"]
        self.classifier = _model_bundle["classifier"]
        self.le         = _label_encoder

    def classify(self, text: str) -> dict:
        """Classify a single clause. Returns dict with category and confidence."""
        vec   = self.tfidf.transform([text])
        probs = self.classifier.predict_proba(vec)[0]
        idx   = probs.argmax()
        return {
            "category":   self.le.inverse_transform([idx])[0],
            "confidence": float(probs[idx]),
            "source":     "ml",
            "all_probs":  {
                cat: round(float(p), 4)
                for cat, p in zip(self.le.classes_, probs)
            },
        }

    def classify_batch(self, texts: list) -> list:
        """Classify multiple clauses at once (faster than looping classify)."""
        vecs  = self.tfidf.transform(texts)
        probs = self.classifier.predict_proba(vecs)
        results = []
        for prob_row in probs:
            idx = prob_row.argmax()
            results.append({
                "category":   self.le.inverse_transform([idx])[0],
                "confidence": float(prob_row[idx]),
                "source":     "ml",
                "all_probs":  {
                    cat: round(float(p), 4)
                    for cat, p in zip(self.le.classes_, prob_row)
                },
            })
        return results
