"""
scorer.py — ClauseGuard Risk Scoring Engine

Computes an overall 0–100 risk score and per-category breakdown from
the classified clause list produced by classifier.py.

Scoring model:
  For each of the 6 risk categories:
    1. Find the highest risk level detected across all clauses in that category
    2. Map to a base score:  LOW → 25,  MEDIUM → 60,  HIGH → 100
    3. Apply a small bonus (up to +10) if multiple clauses were detected
       (more clauses = more pervasive issue)
    4. Cap category score at 100

  Overall score = weighted average of all 6 category scores
  Weights are defined in categories.py and sum to 1.0

Risk tiers (for labeling):
  HIGH   ≥ 70
  MEDIUM  40–69
  LOW    < 40

Why this model?
  The weighted-category design means a single High-risk data_sharing clause
  (weight 0.25) has more impact than a High-risk liability clause (weight 0.10),
  which mirrors real-world privacy risk priorities. The multi-clause bonus
  reflects that a document with 5 data-sharing clauses is more aggressive
  than one with only 1.
"""

from categories import CATEGORIES, RISK_LEVEL_ORDER, RISK_LEVEL_SCORES


def compute_risk_score(classified_clauses: list[dict]) -> dict:
    """
    Computes overall and per-category risk scores.

    Args:
        classified_clauses: Output of RuleBasedClassifier.classify_document()

    Returns:
        {
            "overall_score":      72,          # int, 0–100
            "overall_risk_level": "HIGH",      # "LOW" | "MEDIUM" | "HIGH"
            "category_scores": {
                "data_sharing": {
                    "score":          100,
                    "max_risk_level": "HIGH",
                    "clause_count":   3,
                    "label":          "Data Sharing",
                    "weight":         0.25
                },
                ...
            }
        }
    """
    # Aggregate per category: track max risk level + clause count
    category_max_risk: dict[str, str] = {}
    category_clause_counts: dict[str, int] = {cat: 0 for cat in CATEGORIES}

    for clause in classified_clauses:
        for match in clause.get("all_matches", []):
            cat = match["category"]
            risk = match["risk_level"]

            category_clause_counts[cat] = category_clause_counts.get(cat, 0) + 1

            if cat not in category_max_risk:
                category_max_risk[cat] = risk
            elif RISK_LEVEL_ORDER[risk] > RISK_LEVEL_ORDER[category_max_risk[cat]]:
                category_max_risk[cat] = risk

    # Compute per-category scores
    category_scores: dict[str, int] = {}
    for cat_id in CATEGORIES:
        if cat_id not in category_max_risk:
            category_scores[cat_id] = 0
            continue

        base = RISK_LEVEL_SCORES[category_max_risk[cat_id]]

        # Multi-clause bonus: +5 per additional clause, max +10
        extra_clauses = max(category_clause_counts[cat_id] - 1, 0)
        bonus = min(extra_clauses * 5, 10)

        category_scores[cat_id] = min(base + bonus, 100)

    # Weighted average → overall score
    weighted_sum = sum(
        category_scores[cat_id] * CATEGORIES[cat_id]["weight"]
        for cat_id in CATEGORIES
    )
    total_weight = sum(cat["weight"] for cat in CATEGORIES.values())
    overall_score = round(weighted_sum / total_weight)

    # Risk tier
    if overall_score >= 70:
        overall_risk_level = "HIGH"
    elif overall_score >= 40:
        overall_risk_level = "MEDIUM"
    else:
        overall_risk_level = "LOW"

    return {
        "overall_score": overall_score,
        "overall_risk_level": overall_risk_level,
        "category_scores": {
            cat_id: {
                "score": category_scores[cat_id],
                "max_risk_level": category_max_risk.get(cat_id, "NONE"),
                "clause_count": category_clause_counts[cat_id],
                "label": CATEGORIES[cat_id]["label"],
                "weight": CATEGORIES[cat_id]["weight"],
            }
            for cat_id in CATEGORIES
        },
    }


def generate_summary(score_result: dict, classified_clauses: list[dict]) -> str:
    """
    Generates a concise human-readable risk summary for the API response
    and eventual extension popup.

    Args:
        score_result:       Output of compute_risk_score()
        classified_clauses: Output of RuleBasedClassifier.classify_document()

    Returns:
        A plain-text summary string.
    """
    score = score_result["overall_score"]
    level = score_result["overall_risk_level"]
    total_detected = len(classified_clauses)
    category_scores = score_result["category_scores"]

    # Collect categories by severity for the summary
    high_cats  = [v["label"] for v in category_scores.values() if v["max_risk_level"] == "HIGH"]
    medium_cats = [v["label"] for v in category_scores.values() if v["max_risk_level"] == "MEDIUM"]

    lines: list[str] = []

    # Opening line
    lines.append(
        f"ClauseGuard detected {total_detected} risk-relevant clause(s). "
        f"Overall risk score: {score}/100 ({level})."
    )

    # High-risk callouts
    if high_cats:
        lines.append(f"⚠ High-risk areas: {', '.join(high_cats)}.")

    # Medium-risk callouts (only if no high)
    elif medium_cats:
        lines.append(f"⚡ Moderate concerns: {', '.join(medium_cats)}.")

    # Verdict
    verdicts = {
        "HIGH": (
            "This agreement contains significant privacy and security concerns. "
            "Review carefully — or consider not accepting."
        ),
        "MEDIUM": (
            "This agreement has moderate risks. Review the flagged clauses "
            "before accepting."
        ),
        "LOW": (
            "This agreement appears relatively standard. A few clauses are "
            "worth noting but pose limited risk."
        ),
    }
    lines.append(verdicts[level])

    return " ".join(lines)
