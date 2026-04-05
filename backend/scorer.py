"""
scorer.py — ClauseGuard Risk Scoring Engine

Safer intermediate version:
- Supports both legacy rule-based clause outputs and newer hybrid outputs
- Reduces category-forced scoring
- Computes overall score from per-clause evidence first
- Still returns category_scores for backward compatibility

Expected supported clause shapes:
1) Legacy:
   {
     "all_matches": [
       {"category": "...", "risk_level": "...", ...},
       ...
     ]
   }

2) Hybrid/intermediate:
   {
     "category": "arbitration",
     "risk_level": "LOW",
     "matched_keywords": ["binding arbitration"],
     ...
   }
"""

from collections import defaultdict

from categories import CATEGORIES

RISK_LEVEL_ORDER = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}

# Per-clause evidence-first scoring
CLAUSE_BASE_SCORES = {
    "NONE": 0,
    "LOW": 18,
    "MEDIUM": 45,
    "HIGH": 78,
}


def _normalize_clause_matches(clause: dict) -> list[dict]:
    """
    Normalize both old and newer clause output shapes into a list of matches:
    [
      {
        "category": str,
        "risk_level": str,
        "matched_keywords": list[str]
      }
    ]
    """
    if "all_matches" in clause and isinstance(clause["all_matches"], list):
        normalized = []
        for match in clause["all_matches"]:
            if not isinstance(match, dict):
                continue
            normalized.append({
                "category": match.get("category", "none"),
                "risk_level": match.get("risk_level", "NONE"),
                "matched_keywords": match.get("matched_keywords", []),
            })
        return normalized

    if "category" in clause:
        return [{
            "category": clause.get("category", "none"),
            "risk_level": clause.get("risk_level", "NONE"),
            "matched_keywords": clause.get("matched_keywords", []),
        }]

    return []


def _score_single_clause_match(match: dict) -> int:
    """
    Evidence-first clause scoring.
    """
    risk_level = match.get("risk_level", "NONE")
    keywords = match.get("matched_keywords", []) or []
    category = match.get("category", "none")

    base = CLAUSE_BASE_SCORES.get(risk_level, 0)

    # Small evidence bonus based on explicit matched signals
    keyword_bonus = min(len(keywords) * 6, 18)

    # Small category adjustment only when there is already some evidence/risk
    category_bonus = 0
    if risk_level != "NONE":
        if category in {"arbitration", "liability_limitation"}:
            category_bonus = 5
        elif category in {"data_sharing", "tracking_profiling", "third_party_access"}:
            category_bonus = 3

    return min(base + keyword_bonus + category_bonus, 100)


def compute_risk_score(classified_clauses: list[dict]) -> dict:
    """
    Computes overall and per-category risk scores.

    Returns:
        {
            "overall_score": 42,
            "overall_risk_level": "MEDIUM",
            "category_scores": {
                "data_sharing": {
                    "score": 51,
                    "max_risk_level": "MEDIUM",
                    "clause_count": 2,
                    "label": "Data Sharing",
                    "weight": 0.25
                },
                ...
            }
        }
    """
    category_max_risk = {}
    category_clause_counts = {cat: 0 for cat in CATEGORIES}
    category_match_scores = defaultdict(list)

    clause_scores = []

    for clause in classified_clauses:
        matches = _normalize_clause_matches(clause)

        if not matches:
            continue

        # Score clause from its strongest normalized match
        per_match_scores = []
        for match in matches:
            cat = match.get("category", "none")
            risk = match.get("risk_level", "NONE")

            if cat in CATEGORIES:
                category_clause_counts[cat] = category_clause_counts.get(cat, 0) + 1

                if cat not in category_max_risk:
                    category_max_risk[cat] = risk
                elif RISK_LEVEL_ORDER.get(risk, 0) > RISK_LEVEL_ORDER.get(category_max_risk[cat], 0):
                    category_max_risk[cat] = risk

            match_score = _score_single_clause_match(match)
            per_match_scores.append(match_score)

            if cat in CATEGORIES:
                category_match_scores[cat].append(match_score)

        if per_match_scores:
            clause_scores.append(max(per_match_scores))

    # Per-category scores
    category_scores = {}
    for cat_id, cat_meta in CATEGORIES.items():
        scores = category_match_scores.get(cat_id, [])
        clause_count = category_clause_counts.get(cat_id, 0)

        if not scores:
            category_scores[cat_id] = {
                "score": 0,
                "max_risk_level": "NONE",
                "clause_count": 0,
                "label": cat_meta["label"],
                "weight": cat_meta["weight"],
            }
            continue

        base_score = max(scores)

        # smaller multi-clause bonus than before
        extra_clauses = max(clause_count - 1, 0)
        prevalence_bonus = min(extra_clauses * 4, 8)

        final_cat_score = min(base_score + prevalence_bonus, 100)

        category_scores[cat_id] = {
            "score": final_cat_score,
            "max_risk_level": category_max_risk.get(cat_id, "NONE"),
            "clause_count": clause_count,
            "label": cat_meta["label"],
            "weight": cat_meta["weight"],
        }

    # Overall score:
    # primarily based on average strength of flagged clauses,
    # with a small weighted-category contribution for continuity
    if clause_scores:
        clause_average = sum(clause_scores) / len(clause_scores)
    else:
        clause_average = 0.0

    weighted_category_average = 0.0
    total_weight = sum(cat["weight"] for cat in CATEGORIES.values()) or 1.0
    weighted_category_average = sum(
        category_scores[cat_id]["score"] * CATEGORIES[cat_id]["weight"]
        for cat_id in CATEGORIES
    ) / total_weight

    overall_score = round((0.7 * clause_average) + (0.3 * weighted_category_average))

    if overall_score >= 70:
        overall_risk_level = "HIGH"
    elif overall_score >= 40:
        overall_risk_level = "MEDIUM"
    elif overall_score > 0:
        overall_risk_level = "LOW"
    else:
        overall_risk_level = "NONE"

    return {
        "overall_score": overall_score,
        "overall_risk_level": overall_risk_level,
        "category_scores": category_scores,
    }


def generate_summary(score_result: dict, classified_clauses: list[dict]) -> str:
    """
    Generates a concise human-readable risk summary.
    """
    score = score_result["overall_score"]
    level = score_result["overall_risk_level"]
    category_scores = score_result["category_scores"]

    # Count only clauses that actually have some risk signal
    total_detected = 0
    for clause in classified_clauses:
        matches = _normalize_clause_matches(clause)
        if any(m.get("risk_level", "NONE") != "NONE" for m in matches):
            total_detected += 1

    high_cats = [v["label"] for v in category_scores.values() if v["max_risk_level"] == "HIGH"]
    medium_cats = [v["label"] for v in category_scores.values() if v["max_risk_level"] == "MEDIUM"]
    low_cats = [v["label"] for v in category_scores.values() if v["max_risk_level"] == "LOW"]

    lines = []

    lines.append(
        f"ClauseGuard detected {total_detected} risk-relevant clause(s). "
        f"Overall risk score: {score}/100 ({level})."
    )

    if high_cats:
        lines.append(f"⚠ High-risk areas: {', '.join(high_cats)}.")
    elif medium_cats:
        lines.append(f"⚡ Moderate concerns: {', '.join(medium_cats)}.")
    elif low_cats:
        lines.append(f"ℹ Notable low-risk areas: {', '.join(low_cats)}.")

    verdicts = {
        "HIGH": (
            "This agreement contains significant concerns supported by explicit risky language. "
            "Review carefully before accepting."
        ),
        "MEDIUM": (
            "This agreement has some meaningful concerns. Review the flagged clauses before accepting."
        ),
        "LOW": (
            "This agreement contains a few limited concerns, but no major high-risk pattern was detected."
        ),
        "NONE": (
            "No major risk signals were detected in the flagged clauses."
        ),
    }
    lines.append(verdicts[level])

    return " ".join(lines)