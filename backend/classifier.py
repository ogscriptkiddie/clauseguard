"""
classifier.py — ClauseGuard Rule-Based Classifier

Classifies segmented clauses into security/privacy risk categories using
keyword matching with context-awareness and negation detection.

Architecture note:
  This rule-based engine serves two roles in the ClauseGuard system:
    1. Primary classifier in Phase 1 (this file)
    2. Label generator for the Phase 2 ML training set

  Because of role #2, precision matters more than recall here. We want
  the labels we generate to be correct — even if that means missing some
  clauses — so the ML model learns from clean signal.

Negation handling:
  Naive keyword matching produces false positives on negated clauses, e.g.
  "We do NOT sell your data" should NOT be flagged as data_sharing HIGH.
  A simple negation window (10 words before the keyword match) catches the
  most common patterns.
"""

import re
import logging
from categories import CATEGORIES, RISK_LEVEL_ORDER

logger = logging.getLogger(__name__)

# Window (in words) to search for negation signals before a keyword match
NEGATION_WINDOW = 10

NEGATION_SIGNALS = [
    "not", "never", "no", "don't", "do not", "will not", "won't",
    "doesn't", "does not", "cannot", "can't", "shall not", "we don't",
    "we do not", "we will not", "we never", "without",
]


class RuleBasedClassifier:
    """
    Classifies text clauses into security/privacy risk categories.

    Usage:
        clf = RuleBasedClassifier()

        # Classify a single clause → list of category matches
        matches = clf.classify_clause("We may share your data with advertisers.")

        # Classify a full document (list of clause strings)
        results = clf.classify_document(clauses)
    """

    def classify_clause(self, clause_text: str) -> list[dict]:
        """
        Classifies a single clause across all categories.

        A clause can match multiple categories (e.g., one clause might address
        both data_sharing and third_party_access). Each match is returned
        independently so the scorer can weight them separately.

        Returns:
            List of match dicts, one per matched category:
            [
                {
                    "category":         "data_sharing",
                    "category_label":   "Data Sharing",
                    "risk_level":       "HIGH",
                    "matched_keywords": ["sell your data"],
                    "confidence":       0.85,
                    "negated":          False
                },
                ...
            ]
        """
        text_lower = clause_text.lower()
        matches: list[dict] = []

        for category_id, category_info in CATEGORIES.items():
            result = self._find_best_match(text_lower, category_info["rules"])
            if result is None:
                continue

            risk_level, matched_keywords = result

            # Check negation: if the match appears to be negated, skip it
            if self._is_negated(text_lower, matched_keywords):
                logger.debug(
                    f"Skipping negated match: category={category_id}, "
                    f"keywords={matched_keywords}"
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

    def classify_document(self, clauses: list[str]) -> list[dict]:
        """
        Classifies a list of clause strings.
        Only clauses that match at least one risk category are returned.

        Returns:
            List of enriched clause dicts:
            [
                {
                    "text":                   "We may sell your data...",
                    "primary_category":       "data_sharing",
                    "primary_category_label": "Data Sharing",
                    "risk_level":             "HIGH",
                    "matched_keywords":       ["sell your data"],
                    "confidence":             0.85,
                    "all_matches":            [...]   ← all category matches for this clause
                },
                ...
            ]
        """
        results: list[dict] = []

        for clause_text in clauses:
            clause_text = clause_text.strip()
            if not clause_text:
                continue

            matches = self.classify_clause(clause_text)
            if not matches:
                continue

            # Primary match = highest risk level; tie-break on confidence
            primary = max(
                matches,
                key=lambda m: (RISK_LEVEL_ORDER[m["risk_level"]], m["confidence"])
            )

            results.append({
                "text": clause_text,
                "primary_category": primary["category"],
                "primary_category_label": primary["category_label"],
                "risk_level": primary["risk_level"],
                "matched_keywords": primary["matched_keywords"],
                "confidence": primary["confidence"],
                "all_matches": matches,
            })

        return results

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _find_best_match(
        self, text_lower: str, rules: dict[str, list[str]]
    ) -> tuple[str, list[str]] | None:
        """
        Searches for keyword matches across all risk levels for one category.
        Checks HIGH → MEDIUM → LOW and returns the first (highest severity) match.

        Returns:
            Tuple of (risk_level, [matched_keywords]) or None if no match.
        """
        for risk_level in ["HIGH", "MEDIUM", "LOW"]:
            keywords = rules.get(risk_level, [])
            matched = [kw for kw in keywords if self._keyword_match(kw, text_lower)]
            if matched:
                return risk_level, matched
        return None

    def _keyword_match(self, keyword: str, text_lower: str) -> bool:
        """
        Matches a keyword/phrase against lowercased clause text.

        Multi-word phrases: substring match (more specific, less noise)
        Single words:       word-boundary regex (avoids partial matches like
                            "track" matching "contract")
        """
        keyword = keyword.lower()
        if ' ' in keyword:
            return keyword in text_lower
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text_lower))

    def _is_negated(self, text_lower: str, matched_keywords: list[str]) -> bool:
        """
        Checks whether matched keywords appear in a negated context.

        Strategy: For each matched keyword, look at the N words immediately
        before it in the text. If any negation signal appears in that window,
        consider the match negated.

        This is deliberately simple — it catches the most common ToS negation
        patterns ("we do not sell", "we never share") without false positives.
        """
        words = text_lower.split()

        for keyword in matched_keywords:
            keyword_lower = keyword.lower()
            # Find positions of this keyword in the word list
            keyword_words = keyword_lower.split()
            n = len(keyword_words)

            for i in range(len(words) - n + 1):
                if words[i:i + n] == keyword_words:
                    # Look at the window before this match
                    window_start = max(0, i - NEGATION_WINDOW)
                    window = ' '.join(words[window_start:i])

                    for signal in NEGATION_SIGNALS:
                        if signal in window:
                            return True
        return False

    def _compute_confidence(self, matched_keywords: list[str], text_lower: str) -> float:
        """
        Estimates classification confidence for a match.

        Factors:
          - Keyword specificity: longer/more-word phrases are more specific
          - Match count: more matching keywords = higher confidence
          - Phrase density: what fraction of keywords in that level matched

        Returns a float in [0.0, 1.0].
        """
        if not matched_keywords:
            return 0.0

        # Average word count of matched keywords (longer = more specific)
        avg_phrase_len = sum(len(kw.split()) for kw in matched_keywords) / len(matched_keywords)
        specificity_score = min(avg_phrase_len / 5.0, 1.0)  # normalize, cap at 1

        # Number of distinct keyword matches (more = more confident)
        match_count_score = min(len(matched_keywords) / 3.0, 1.0)

        confidence = 0.6 * specificity_score + 0.4 * match_count_score
        return round(min(confidence, 1.0), 3)
