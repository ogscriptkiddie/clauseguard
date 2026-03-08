"""
test_engine.py — ClauseGuard Engine Test Script

Tests the full classification pipeline locally without needing Flask running.
Run this first to verify your setup before testing via HTTP.

Usage:
    cd backend
    python test_engine.py

What it tests:
  1. Segmentation of a synthetic ToS-like document
  2. Per-clause classification
  3. Risk scoring
  4. Negation detection (should NOT flag "we do not sell your data")
  5. Edge cases (empty text, very short text)
"""

import json
import sys
import os

# Ensure we can import from the backend directory
sys.path.insert(0, os.path.dirname(__file__))

from segmenter import segment_document
from classifier import RuleBasedClassifier
from scorer import compute_risk_score, generate_summary

# ---------------------------------------------------------------------------
# Synthetic test document — written to exercise all 6 categories
# ---------------------------------------------------------------------------

SAMPLE_TOS = """
Terms of Service — AcmeCorp

Last Updated: January 1, 2025

1. Data Sharing

We may share your personal data with third parties for marketing and advertising purposes.
We may also share with affiliates and business partners who may use it to send you offers.
Note: We do not sell your data to data brokers.

2. Tracking and Profiling

We use cookies and web beacons to track your activity across websites.
Our advertising partners may engage in behavioral advertising based on your browsing history.
We may build a profile of your interests to serve you personalized advertising.
We also use pixel tags to measure ad performance.

3. Third-Party Access

Third-party applications integrated with our platform may collect your usage data.
We may grant third parties access to your account data when you use connected services.
We may be required to disclose your data to law enforcement access without notice under applicable law.

4. Data Retention

We retain your personal data for as long as necessary to fulfill the purposes described.
Backup copies may persist even after account deletion.
We have no obligation to delete data from our archival systems immediately upon request.

5. Arbitration

By using our services, you agree to binding arbitration for any disputes.
You waive your right to a jury trial and agree that all claims will be resolved through individual arbitration.
You also agree to a class action waiver — meaning you cannot participate in class action lawsuits against us.

6. Liability

Our services are provided as-is without warranty of any kind.
In no event shall AcmeCorp be liable for any damages arising from your use of the service.
We disclaim all warranties, express or implied, including but not limited to merchantability.

7. Contact Us

If you have questions, contact privacy@acmecorp.example.com.
"""

# ---------------------------------------------------------------------------
# Negation test cases
# ---------------------------------------------------------------------------

NEGATION_TESTS = [
    {
        "text": "We do not sell your data to any third parties.",
        "should_flag": False,
        "note": "Explicit negation — should NOT be flagged",
    },
    {
        "text": "We will never share your personal data with advertisers.",
        "should_flag": False,
        "note": "Future negation — should NOT be flagged",
    },
    {
        "text": "We may share your personal data with advertisers for targeted campaigns.",
        "should_flag": True,
        "note": "No negation — SHOULD be flagged",
    },
    {
        "text": "We cannot guarantee deletion of backup copies after account closure.",
        "should_flag": True,
        "note": "Data retention risk — SHOULD be flagged",
    },
]


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def print_header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_section(title: str):
    print(f"\n--- {title} ---")


def run_full_pipeline_test():
    print_header("TEST 1: Full Pipeline — Synthetic ToS Document")

    clf = RuleBasedClassifier()

    # Step 1: Segmentation
    print_section("Segmentation")
    clauses = segment_document(SAMPLE_TOS)
    print(f"Total clauses extracted: {len(clauses)}")
    for i, clause in enumerate(clauses[:5], 1):
        preview = clause[:80] + "..." if len(clause) > 80 else clause
        print(f"  [{i}] {preview}")
    if len(clauses) > 5:
        print(f"  ... and {len(clauses) - 5} more")

    # Step 2: Classification
    print_section("Classification")
    classified = clf.classify_document(clauses)
    print(f"Risk-relevant clauses detected: {len(classified)}")

    for i, result in enumerate(classified, 1):
        print(f"\n  Clause {i}:")
        print(f"    Text:     {result['text'][:70]}...")
        print(f"    Category: {result['primary_category_label']}")
        print(f"    Risk:     {result['risk_level']}")
        print(f"    Keywords: {result['matched_keywords']}")
        print(f"    Confidence: {result['confidence']}")

    # Step 3: Scoring
    print_section("Risk Scoring")
    score_result = compute_risk_score(classified)
    print(f"Overall Score: {score_result['overall_score']}/100")
    print(f"Overall Risk Level: {score_result['overall_risk_level']}")
    print("\nCategory Breakdown:")
    for cat_id, info in score_result["category_scores"].items():
        bar = "█" * (info["score"] // 10) + "░" * (10 - info["score"] // 10)
        print(
            f"  {info['label']:<30} [{bar}] {info['score']:>3}/100  "
            f"({info['max_risk_level']}, {info['clause_count']} clause(s))"
        )

    # Step 4: Summary
    print_section("Generated Summary")
    summary = generate_summary(score_result, classified)
    print(f"  {summary}")


def run_negation_tests():
    print_header("TEST 2: Negation Detection")
    clf = RuleBasedClassifier()
    passed = 0
    failed = 0

    for test in NEGATION_TESTS:
        matches = clf.classify_clause(test["text"])
        was_flagged = len(matches) > 0
        expected = test["should_flag"]
        status = "PASS ✓" if was_flagged == expected else "FAIL ✗"

        if was_flagged == expected:
            passed += 1
        else:
            failed += 1

        print(f"\n  [{status}] {test['note']}")
        print(f"    Text:     {test['text']}")
        print(f"    Expected: {'flagged' if expected else 'not flagged'}")
        print(f"    Got:      {'flagged' if was_flagged else 'not flagged'}")
        if was_flagged:
            print(f"    Matches:  {[m['category'] + '/' + m['risk_level'] for m in matches]}")

    print(f"\n  Results: {passed} passed, {failed} failed")
    return failed == 0


def run_edge_case_tests():
    print_header("TEST 3: Edge Cases")

    clf = RuleBasedClassifier()

    # Empty text
    result = segment_document("")
    assert result == [], f"Expected [], got {result}"
    print("  [PASS ✓] Empty string → no clauses")

    # Very short text
    result = segment_document("Hi.")
    assert result == [], f"Expected [], got {result}"
    print("  [PASS ✓] Very short text → no clauses")

    # No risk clauses
    benign = "Thank you for using our service. We hope you have a great experience with us today."
    clauses = segment_document(benign)
    classified = clf.classify_document(clauses)
    score = compute_risk_score(classified)
    assert score["overall_score"] == 0, f"Expected score 0, got {score['overall_score']}"
    print("  [PASS ✓] Benign text → score 0")

    print("\n  All edge case tests passed.")


def run_all():
    print("\n" + "=" * 60)
    print("  ClauseGuard Engine Test Suite")
    print("=" * 60)

    run_full_pipeline_test()
    negation_ok = run_negation_tests()
    run_edge_case_tests()

    print("\n" + "=" * 60)
    print("  Test suite complete.")
    if not negation_ok:
        print("  ⚠  Some negation tests failed — review NEGATION_SIGNALS in classifier.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all()
