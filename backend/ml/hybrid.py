"""
ClauseGuard Hybrid Classifier

Safer intermediate version:
- Keeps backward-compatible output shape
- Uses ML for label prediction
- Uses rule fallback when ML confidence is low
- Infers risk from explicit textual evidence first, not category alone
- Avoids defaulting arbitration/liability to HIGH without trigger language
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.classifier_ml import MLClassifier

CONFIDENCE_THRESHOLD = 0.60

CATEGORY_LABELS = {
    "data_sharing": "Data Sharing",
    "tracking_profiling": "Tracking & Profiling",
    "third_party_access": "Third-Party Access",
    "data_retention": "Data Retention",
    "arbitration": "Arbitration",
    "content_rights": "Content & IP Rights",
    "liability_limitation": "Liability Limitation",
    "none": "None",
}

RISK_ORDER = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}

HIGH_SIGNALS = [
    "binding arbitration",
    "class action waiver",
    "waive your right to sue",
    "waive right to sue",
    "exclusive jurisdiction",
    "exclusive forum",
    "shall not exceed",
    "not liable",
    "no liability",
    "liability shall be limited",
    "consequential damages",
    "indirect damages",
    "without warranty",
    "as is",
    "royalty-free",
    "irrevocable",
    "perpetual",
    "sublicensable",
    "sell your personal information",
    "sell personal information",
    "sell or share",
]

MEDIUM_SIGNALS = [
    "arbitration",
    "dispute resolution",
    "third parties",
    "third-party",
    "partners",
    "affiliates",
    "share personal information",
    "disclose personal information",
    "cookies",
    "analytics",
    "tracking technologies",
    "profiling",
    "retain",
    "retention",
]

LOW_SIGNALS = [
    "we do not sell",
    "we will not sell",
    "we never sell",
    "you retain ownership",
    "you keep ownership",
    "opt out",
    "you may delete",
    "you can delete",
    "upon request",
    "limited purpose",
    "only to provide",
    "solely to",
    "will not share",
    "do not share",
    "does not sell",
]


class HybridClassifier:
    """Combines ML and rule-based classifiers."""

    def __init__(self, rule_based_classifier=None):
        self.ml = MLClassifier()
        self.rule = rule_based_classifier

    def _empty_rule_result(self):
        return {
            "category": "none",
            "category_label": "None",
            "risk_level": "NONE",
            "matched_keywords": [],
            "confidence": 0.0,
            "source": "rule_based",
        }

    def _normalize_rule_result(self, rule_result):
        """Normalize rule output to one stable dict."""
        if not rule_result:
            return self._empty_rule_result()

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
                return self._empty_rule_result()

            best = max(
                dict_items,
                key=lambda m: (
                    RISK_ORDER.get(m.get("risk_level", "NONE"), 0),
                    m.get("confidence", 0.0),
                ),
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

        return self._empty_rule_result()

    def _run_rule_fallback(self, text: str) -> dict:
        if self.rule is None:
            return self._empty_rule_result()

        if hasattr(self.rule, "classify") and callable(getattr(self.rule, "classify")):
            return self._normalize_rule_result(self.rule.classify(text))

        if hasattr(self.rule, "classify_clause") and callable(getattr(self.rule, "classify_clause")):
            return self._normalize_rule_result(self.rule.classify_clause(text))

        return self._empty_rule_result()

    def _detect_signals(self, text: str):
        lower = text.lower()

        matched_high = [s for s in HIGH_SIGNALS if s in lower]
        matched_medium = [s for s in MEDIUM_SIGNALS if s in lower]
        matched_low = [s for s in LOW_SIGNALS if s in lower]

        return matched_high, matched_medium, matched_low

    def _infer_risk(self, text: str, category: str) -> str:
        matched_high, matched_medium, matched_low = self._detect_signals(text)

        if matched_low and not matched_high and not matched_medium:
            return "LOW"

        if len(matched_high) >= 2:
            return "HIGH"

        if len(matched_high) == 1:
            return "HIGH"

        if len(matched_medium) >= 2:
            return "MEDIUM"

        if len(matched_medium) == 1:
            return "LOW"

        # No explicit harmful trigger found:
        # keep category as topic label, but do not auto-escalate to scary risk
        if category == "none":
            return "NONE"

        return "LOW"

    def _build_output(self, category, risk_level, confidence, source, matched_keywords, all_probs):
        return {
            "category": category,
            "category_label": CATEGORY_LABELS.get(category, category),
            "risk_level": risk_level,
            "confidence": round(float(confidence), 4),
            "source": source,
            "matched_keywords": matched_keywords,
            "all_probs": all_probs or {},
        }

    def classify(self, text: str) -> dict:
        ml_result = self.ml.classify(text)
        ml_conf = ml_result.get("confidence", 0.0)
        ml_cat = ml_result.get("category", "none")

        matched_high, matched_medium, matched_low = self._detect_signals(text)
        evidence_matches = matched_high + matched_medium + matched_low

        if ml_conf >= CONFIDENCE_THRESHOLD and ml_cat != "none":
            return self._build_output(
                category=ml_cat,
                risk_level=self._infer_risk(text, ml_cat),
                confidence=ml_conf,
                source=ml_result.get("source", "ml"),
                matched_keywords=evidence_matches,
                all_probs=ml_result.get("all_probs", {}),
            )

        rule_result = self._run_rule_fallback(text)
        rule_cat = rule_result.get("category", "none")

        if rule_cat != "none":
            inferred_risk = self._infer_risk(text, rule_cat)
            rule_keywords = rule_result.get("matched_keywords", [])
            all_keywords = list(dict.fromkeys(rule_keywords + evidence_matches))

            return self._build_output(
                category=rule_cat,
                risk_level=inferred_risk,
                confidence=max(ml_conf, rule_result.get("confidence", 0.0)),
                source="rule_based",
                matched_keywords=all_keywords,
                all_probs=ml_result.get("all_probs", {}),
            )

        if evidence_matches:
            return self._build_output(
                category=ml_cat if ml_cat != "none" else "none",
                risk_level=self._infer_risk(text, ml_cat),
                confidence=ml_conf,
                source="evidence_only" if ml_cat == "none" else ml_result.get("source", "ml"),
                matched_keywords=evidence_matches,
                all_probs=ml_result.get("all_probs", {}),
            )

        return self._build_output(
            category="none",
            risk_level="NONE",
            confidence=ml_conf,
            source="none",
            matched_keywords=[],
            all_probs=ml_result.get("all_probs", {}),
        )

    def classify_batch(self, texts: list) -> list:
        return [self.classify(text) for text in texts]