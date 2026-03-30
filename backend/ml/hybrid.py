"""
ClauseGuard Hybrid Classifier

Fixed version:
- Safely interoperates with rule engines exposing either `classify()` or
  `classify_clause()`.
- Normalizes rule fallback results into one stable dict.
- Prevents AttributeError when RuleBasedClassifier lacks `.classify()`.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.classifier_ml import MLClassifier

CONFIDENCE_THRESHOLD = 0.40

CATEGORY_LABELS = {
    "data_sharing": "Data Sharing",
    "tracking_profiling": "Tracking & Profiling",
    "third_party_access": "Third-Party Access",
    "data_retention": "Data Retention",
    "arbitration": "Arbitration",
    "content_rights": "Content & IP Rights",
    "liability_limitation": "Liability Limitation",
}

RISK_ORDER = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}


class HybridClassifier:
    """Combines ML and rule-based classifiers."""

    def __init__(self, rule_based_classifier=None):
        self.ml = MLClassifier()
        self.rule = rule_based_classifier

    def _normalize_rule_result(self, rule_result):
        """Normalize rule output to one stable dict."""
        if not rule_result:
            return {
                "category": "none",
                "category_label": "None",
                "risk_level": "NONE",
                "matched_keywords": [],
                "confidence": 0.0,
                "source": "rule_based",
            }

        if isinstance(rule_result, dict):
            return {
                "category": rule_result.get("category", "none"),
                "category_label": rule_result.get(
                    "category_label",
                    CATEGORY_LABELS.get(rule_result.get("category", "none"), "None"),
                ),
                "risk_level": rule_result.get("risk_level", "NONE"),
                "matched_keywords": rule_result.get("matched_keywords", []),
                "confidence": rule_result.get("confidence", 0.0),
                "source": rule_result.get("source", "rule_based"),
            }

        if isinstance(rule_result, list):
            dict_items = [x for x in rule_result if isinstance(x, dict)]
            if not dict_items:
                return {
                    "category": "none",
                    "category_label": "None",
                    "risk_level": "NONE",
                    "matched_keywords": [],
                    "confidence": 0.0,
                    "source": "rule_based",
                }

            best = max(
                dict_items,
                key=lambda m: (RISK_ORDER.get(m.get("risk_level", "NONE"), 0), m.get("confidence", 0.0)),
            )
            return {
                "category": best.get("category", "none"),
                "category_label": best.get(
                    "category_label",
                    CATEGORY_LABELS.get(best.get("category", "none"), "None"),
                ),
                "risk_level": best.get("risk_level", "NONE"),
                "matched_keywords": best.get("matched_keywords", []),
                "confidence": best.get("confidence", 0.0),
                "source": best.get("source", "rule_based"),
            }

        return {
            "category": "none",
            "category_label": "None",
            "risk_level": "NONE",
            "matched_keywords": [],
            "confidence": 0.0,
            "source": "rule_based",
        }

    def _run_rule_fallback(self, text: str) -> dict:
        if self.rule is None:
            return self._normalize_rule_result(None)

        if hasattr(self.rule, "classify") and callable(getattr(self.rule, "classify")):
            return self._normalize_rule_result(self.rule.classify(text))

        if hasattr(self.rule, "classify_clause") and callable(getattr(self.rule, "classify_clause")):
            return self._normalize_rule_result(self.rule.classify_clause(text))

        return self._normalize_rule_result(None)

    def classify(self, text: str) -> dict:
        ml_result = self.ml.classify(text)
        ml_conf = ml_result["confidence"]
        ml_cat = ml_result["category"]

        if ml_conf >= CONFIDENCE_THRESHOLD:
            return {
                "category": ml_cat,
                "category_label": CATEGORY_LABELS.get(ml_cat, ml_cat),
                "risk_level": _infer_risk(text, ml_cat),
                "confidence": round(ml_conf, 4),
                "source": "ml",
                "matched_keywords": [],
                "all_probs": ml_result.get("all_probs", {}),
            }

        rule_result = self._run_rule_fallback(text)
        if rule_result.get("category") and rule_result["category"] != "none":
            rule_cat = rule_result["category"]
            return {
                "category": rule_cat,
                "category_label": CATEGORY_LABELS.get(rule_cat, rule_cat),
                "risk_level": rule_result.get("risk_level", "LOW"),
                "confidence": round(ml_conf, 4),
                "source": "rule_based",
                "matched_keywords": rule_result.get("matched_keywords", []),
                "all_probs": ml_result.get("all_probs", {}),
            }

        return {
            "category": "none",
            "category_label": "None",
            "risk_level": "NONE",
            "confidence": round(ml_conf, 4),
            "source": "none",
            "matched_keywords": [],
            "all_probs": ml_result.get("all_probs", {}),
        }

    def classify_batch(self, texts: list) -> list:
        ml_results = self.ml.classify_batch(texts)
        output = []

        for text, ml_result in zip(texts, ml_results):
            ml_conf = ml_result["confidence"]
            ml_cat = ml_result["category"]

            if ml_conf >= CONFIDENCE_THRESHOLD:
                output.append({
                    "category": ml_cat,
                    "category_label": CATEGORY_LABELS.get(ml_cat, ml_cat),
                    "risk_level": _infer_risk(text, ml_cat),
                    "confidence": round(ml_conf, 4),
                    "source": "ml",
                    "matched_keywords": [],
                    "all_probs": ml_result.get("all_probs", {}),
                })
                continue

            rule_result = self._run_rule_fallback(text)
            if rule_result.get("category") and rule_result["category"] != "none":
                rule_cat = rule_result["category"]
                output.append({
                    "category": rule_cat,
                    "category_label": CATEGORY_LABELS.get(rule_cat, rule_cat),
                    "risk_level": rule_result.get("risk_level", "LOW"),
                    "confidence": round(ml_conf, 4),
                    "source": "rule_based",
                    "matched_keywords": rule_result.get("matched_keywords", []),
                    "all_probs": ml_result.get("all_probs", {}),
                })
                continue

            output.append({
                "category": "none",
                "category_label": "None",
                "risk_level": "NONE",
                "confidence": round(ml_conf, 4),
                "source": "none",
                "matched_keywords": [],
                "all_probs": ml_result.get("all_probs", {}),
            })

        return output


HIGH_SIGNALS = [
    "irrevocable", "perpetual", "binding arbitration", "class action waiver",
    "sell your", "sell or share", "shall not exceed", "not liable",
    "as is", "without warranty", "indefinitely", "without limit",
    "law enforcement", "without notice", "royalty-free", "sublicensable",
    "waive your right", "no right to", "permanently barred",
]

LOW_SIGNALS = [
    "we do not sell", "we will not sell", "we never sell",
    "you retain ownership", "you keep ownership", "opt out",
    "you may delete", "you can delete", "upon request",
    "limited purpose", "only to provide", "solely to",
    "will not share", "do not share", "does not sell",
]


def _infer_risk(text: str, category: str) -> str:
    lower = text.lower()

    low_hits = sum(1 for s in LOW_SIGNALS if s in lower)
    high_hits = sum(1 for s in HIGH_SIGNALS if s in lower)

    if low_hits > 0 and high_hits == 0:
        return "LOW"
    if high_hits >= 2:
        return "HIGH"
    if high_hits == 1:
        return "MEDIUM"

    high_default_cats = {"arbitration", "liability_limitation"}
    low_default_cats = {"data_retention"}

    if category in high_default_cats:
        return "HIGH"
    if category in low_default_cats:
        return "LOW"
    return "MEDIUM"
