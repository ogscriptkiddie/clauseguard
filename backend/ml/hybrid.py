"""
ClauseGuard Hybrid Classifier
==============================
Pipeline:
  1. Run ML classifier (TF-IDF + Calibrated LR)
  2. If ML confidence >= CONFIDENCE_THRESHOLD → use ML prediction
  3. If ML confidence <  CONFIDENCE_THRESHOLD → fall back to rule-based classifier
  4. If neither fires → clause is clean (NONE)

The threshold 0.40 was chosen because:
  - Random baseline for 7 classes = 1/7 ≈ 0.143
  - Below 0.40 the ML model is uncertain; rule-based is more reliable
  - Above 0.40 the ML model consistently outperforms rules on held-out data
"""
import sys
import os

# Allow importing from parent directory (backend/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.classifier_ml import MLClassifier

CONFIDENCE_THRESHOLD = 0.40

CATEGORY_LABELS = {
    "data_sharing":        "Data Sharing",
    "tracking_profiling":  "Tracking & Profiling",
    "third_party_access":  "Third-Party Access",
    "data_retention":      "Data Retention",
    "arbitration":         "Arbitration",
    "content_rights":      "Content & IP Rights",
    "liability_limitation":"Liability Limitation",
}

CATEGORY_RISK_WEIGHT = {
    "data_sharing":        0.22,
    "tracking_profiling":  0.20,
    "third_party_access":  0.13,
    "data_retention":      0.13,
    "arbitration":         0.13,
    "content_rights":      0.10,
    "liability_limitation":0.09,
}


class HybridClassifier:
    """
    Combines ML and rule-based classifiers.
    Falls back to rule-based when ML confidence is low.
    """

    def __init__(self, rule_based_classifier=None):
        """
        Args:
            rule_based_classifier: instance of RuleBasedClassifier from classifier.py
                                   If None, ML-only mode (no fallback).
        """
        self.ml  = MLClassifier()
        self.rule = rule_based_classifier

    def classify(self, text: str) -> dict:
        """
        Classify a single clause using the hybrid pipeline.

        Returns:
            {
                "category":        str,   # e.g. "data_sharing"
                "category_label":  str,   # e.g. "Data Sharing"
                "risk_level":      str,   # "HIGH" | "MEDIUM" | "LOW" | "NONE"
                "confidence":      float, # ML confidence (0-1)
                "source":          str,   # "ml" | "rule_based" | "none"
                "matched_keywords":list,  # from rule-based (if used)
            }
        """
        # Step 1: ML classification
        ml_result = self.ml.classify(text)
        ml_conf   = ml_result["confidence"]
        ml_cat    = ml_result["category"]

        if ml_conf >= CONFIDENCE_THRESHOLD:
            # ML is confident → use it
            return {
                "category":        ml_cat,
                "category_label":  CATEGORY_LABELS.get(ml_cat, ml_cat),
                "risk_level":      _infer_risk(text, ml_cat),
                "confidence":      round(ml_conf, 4),
                "source":          "ml",
                "matched_keywords":[],
                "all_probs":       ml_result.get("all_probs", {}),
            }

        # Step 2: ML is uncertain → try rule-based fallback
        if self.rule is not None:
            rule_result = self.rule.classify(text)
            if rule_result.get("category") and rule_result["category"] != "none":
                rule_cat = rule_result["category"]
                return {
                    "category":        rule_cat,
                    "category_label":  CATEGORY_LABELS.get(rule_cat, rule_cat),
                    "risk_level":      rule_result.get("risk_level", "LOW"),
                    "confidence":      round(ml_conf, 4),  # ML conf was low
                    "source":          "rule_based",
                    "matched_keywords":rule_result.get("matched_keywords", []),
                    "all_probs":       ml_result.get("all_probs", {}),
                }

        # Step 3: Neither fired → clean clause
        return {
            "category":        "none",
            "category_label":  "None",
            "risk_level":      "NONE",
            "confidence":      round(ml_conf, 4),
            "source":          "none",
            "matched_keywords":[],
            "all_probs":       ml_result.get("all_probs", {}),
        }

    def classify_batch(self, texts: list) -> list:
        """Classify a list of clauses efficiently."""
        ml_results = self.ml.classify_batch(texts)
        output = []
        for text, ml_result in zip(texts, ml_results):
            ml_conf = ml_result["confidence"]
            ml_cat  = ml_result["category"]

            if ml_conf >= CONFIDENCE_THRESHOLD:
                output.append({
                    "category":        ml_cat,
                    "category_label":  CATEGORY_LABELS.get(ml_cat, ml_cat),
                    "risk_level":      _infer_risk(text, ml_cat),
                    "confidence":      round(ml_conf, 4),
                    "source":          "ml",
                    "matched_keywords":[],
                    "all_probs":       ml_result.get("all_probs", {}),
                })
                continue

            if self.rule is not None:
                rule_result = self.rule.classify(text)
                if rule_result.get("category") and rule_result["category"] != "none":
                    rule_cat = rule_result["category"]
                    output.append({
                        "category":        rule_cat,
                        "category_label":  CATEGORY_LABELS.get(rule_cat, rule_cat),
                        "risk_level":      rule_result.get("risk_level", "LOW"),
                        "confidence":      round(ml_conf, 4),
                        "source":          "rule_based",
                        "matched_keywords":rule_result.get("matched_keywords", []),
                        "all_probs":       ml_result.get("all_probs", {}),
                    })
                    continue

            output.append({
                "category":        "none",
                "category_label":  "None",
                "risk_level":      "NONE",
                "confidence":      round(ml_conf, 4),
                "source":          "none",
                "matched_keywords":[],
                "all_probs":       ml_result.get("all_probs", {}),
            })
        return output


# ── Risk inference ────────────────────────────────────────────────────────────
# ML predicts category but not risk level.
# We infer risk level from keyword signals in the text.

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
    """Heuristic risk level inference from clause text."""
    lower = text.lower()

    low_hits  = sum(1 for s in LOW_SIGNALS  if s in lower)
    high_hits = sum(1 for s in HIGH_SIGNALS if s in lower)

    if low_hits > 0 and high_hits == 0:
        return "LOW"
    if high_hits >= 2:
        return "HIGH"
    if high_hits == 1:
        return "MEDIUM"

    # Category-based defaults
    HIGH_DEFAULT_CATS = {"arbitration", "liability_limitation"}
    LOW_DEFAULT_CATS  = {"data_retention"}

    if category in HIGH_DEFAULT_CATS:
        return "HIGH"
    if category in LOW_DEFAULT_CATS:
        return "LOW"
    return "MEDIUM"
