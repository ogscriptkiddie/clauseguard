"""
classifier.py — ClauseGuard Rule-Based Classifier

Fixed version:
- Adds a compatibility `classify()` method that returns one normalized dict.
- Keeps existing `classify_clause()` behavior for Phase 1 / label generation.
- Lets HybridClassifier safely call into the rule engine.
"""

import re
import logging
from categories import CATEGORIES, RISK_LEVEL_ORDER

logger = logging.getLogger(__name__)

NEGATION_WINDOW = 10

NEGATION_SIGNALS = [
    "we do not", "we don't", "we will not", "we won't", "we never",
    "we do not sell", "we do not share", "we will not sell", "we will not share",
    "we do not collect", "we do not use", "we do not disclose",
    "does not sell", "does not share", "does not collect",
    "tiktok does not", "spotify does not", "we are not",
    "will not be shared", "will not be sold", "will not be used",
    "is not shared", "is not sold", "are not shared", "are not sold",
    "shall not be shared", "shall not be sold",
]


class RuleBasedClassifier:
    """
    Classifies text clauses into security/privacy risk categories.

    Interfaces:
      - classify_clause(text) -> list[dict]  # all matches
      - classify(text) -> dict               # best single match (compatibility)
      - classify_document(clauses) -> list[dict]
    """

    def classify_clause(self, clause_text: str) -> list[dict]:
        """
        Classifies a single clause across all categories.

        Returns a list of category match dicts.
        """
        text_lower = clause_text.lower()
        matches: list[dict] = []

        for category_id, category_info in CATEGORIES.items():
            result = self._find_best_match(text_lower, category_info["rules"])
            if result is None:
                continue

            risk_level, matched_keywords = result

            if self._is_negated(text_lower, matched_keywords):
                logger.debug(
                    "Skipping negated match: category=%s, keywords=%s",
                    category_id,
                    matched_keywords,
                )
                continue

            matches.append({
                "category": category_id,
                "category_label": category_info["label"],
                "risk_level": risk_level,
                "matched_keywords": matched_keywords,
                "confidence": self._compute_confidence(matched_keywords, text_lower),
                "negated": False,
            })

        return matches

    def classify(self, clause_text: str) -> dict:
        """
        Compatibility wrapper for HybridClassifier.

        Returns one normalized best-match dict instead of a list.
        If nothing matches, returns a stable "none" record.
        """
        matches = self.classify_clause(clause_text)
        if not matches:
            return {
                "category": "none",
                "category_label": "None",
                "risk_level": "NONE",
                "matched_keywords": [],
                "confidence": 0.0,
                "negated": False,
                "source": "rule_based",
                "all_matches": [],
            }

        primary = max(
            matches,
            key=lambda m: (RISK_LEVEL_ORDER[m["risk_level"]], m["confidence"]),
        )

        return {
            "category": primary["category"],
            "category_label": primary["category_label"],
            "risk_level": primary["risk_level"],
            "matched_keywords": primary["matched_keywords"],
            "confidence": primary["confidence"],
            "negated": primary.get("negated", False),
            "source": "rule_based",
            "all_matches": matches,
        }

    def classify_document(self, clauses: list[str]) -> list[dict]:
        """
        Classifies a list of clause strings.
        Only clauses that match at least one risk category are returned.
        """
        results: list[dict] = []

        for clause_text in clauses:
            clause_text = clause_text.strip()
            if not clause_text:
                continue

            primary = self.classify(clause_text)
            if primary["category"] == "none":
                continue

            results.append({
                "text": clause_text,
                "primary_category": primary["category"],
                "primary_category_label": primary["category_label"],
                "risk_level": primary["risk_level"],
                "matched_keywords": primary["matched_keywords"],
                "confidence": primary["confidence"],
                "all_matches": primary.get("all_matches", []),
            })

        return results

    def _find_best_match(self, text_lower: str, rules: dict[str, list[str]]) -> tuple[str, list[str]] | None:
        for risk_level in ["HIGH", "MEDIUM", "LOW"]:
            keywords = rules.get(risk_level, [])
            matched = [kw for kw in keywords if self._keyword_match(kw, text_lower)]
            if matched:
                return risk_level, matched
        return None

    def _keyword_match(self, keyword: str, text_lower: str) -> bool:
        keyword = keyword.lower()
        words = keyword.split()

        if len(words) == 1:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            return bool(re.search(pattern, text_lower))
        elif len(words) <= 3:
            return keyword in text_lower
        else:
            return self._proximity_match(words, text_lower, window=10)

    def _proximity_match(self, keyword_words: list[str], text_lower: str, window: int = 10) -> bool:
        text_words = text_lower.split()
        n = len(text_words)
        kw_count = len(keyword_words)

        for start in range(n - kw_count + 1):
            segment = text_words[start:start + window]
            ki = 0
            for word in segment:
                if ki < kw_count and word == keyword_words[ki]:
                    ki += 1
            if ki == kw_count:
                return True
        return False

    def _is_negated(self, text_lower: str, matched_keywords: list[str]) -> bool:
        words = text_lower.split()

        sentence_start = ' '.join(words[:6])
        for signal in NEGATION_SIGNALS:
            if signal in sentence_start:
                return True

        for keyword in matched_keywords:
            keyword_lower = keyword.lower()
            keyword_words = keyword_lower.split()
            n = len(keyword_words)

            for i in range(len(words) - n + 1):
                if words[i:i + n] == keyword_words:
                    window_start = max(0, i - NEGATION_WINDOW)
                    window = ' '.join(words[window_start:i])
                    for signal in NEGATION_SIGNALS:
                        if signal in window:
                            return True
        return False

    def _compute_confidence(self, matched_keywords: list[str], text_lower: str) -> float:
        if not matched_keywords:
            return 0.0

        avg_phrase_len = sum(len(kw.split()) for kw in matched_keywords) / len(matched_keywords)
        specificity_score = min(avg_phrase_len / 5.0, 1.0)
        match_count_score = min(len(matched_keywords) / 3.0, 1.0)

        confidence = 0.6 * specificity_score + 0.4 * match_count_score
        return round(min(confidence, 1.0), 3)
