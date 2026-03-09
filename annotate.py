"""
annotate.py — ClauseGuard Annotation Helper

Takes a raw .txt ToS/Privacy Policy file, segments it into clauses,
runs the rule-based classifier to suggest labels, and outputs a CSV
ready for manual review and correction.

WHY THIS EXISTS:
  Manual annotation from scratch is slow and error-prone.
  This script does the mechanical work — splitting the document,
  pre-filling category and risk level suggestions from the rule-based
  engine — so you only need to REVIEW and CORRECT, not start from zero.

  IMPORTANT: The suggestions are a starting point only. You must read
  every clause and either confirm or override the label. Blindly
  accepting the suggestions defeats the entire purpose of annotation
  and is exactly what your instructor warned against.

USAGE:
  # Annotate a single file
  python annotate.py data/raw/google_privacy.txt

  # Annotate and save to a custom output path
  python annotate.py data/raw/spotify_privacy.txt -o data/annotated/spotify.csv

  # Annotate all .txt files in data/raw/ at once
  python annotate.py --all

OUTPUT CSV COLUMNS:
  clause_id         Auto-generated unique ID
  source_document   Filename of the source document
  clause_text       The raw clause text (do not edit this)
  suggested_cat     Rule-based engine suggestion (YOUR REFERENCE ONLY)
  suggested_risk    Rule-based risk level suggestion (YOUR REFERENCE ONLY)
  category          YOUR FINAL label — fill this in
  risk_level        YOUR FINAL risk level — fill this in
  annotator_notes   WHY you assigned this label — required for research
  confidence        Engine confidence score (your reference only)
  matched_keywords  What the engine matched on (helps you decide)

VALID CATEGORY VALUES:
  data_sharing | tracking_profiling | third_party_access |
  data_retention | arbitration | liability_limitation | none

VALID RISK LEVEL VALUES:
  HIGH | MEDIUM | LOW | NONE
"""

import sys
import os
import csv
import argparse
import glob
from pathlib import Path

# Ensure we can import backend modules regardless of where script is run from
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

from segmenter import segment_document
from classifier import RuleBasedClassifier


# ─── Config ──────────────────────────────────────────────────────────────────
DEFAULT_INPUT_DIR  = os.path.join(SCRIPT_DIR, "data", "raw")
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "data", "annotated")

VALID_CATEGORIES = [
    "data_sharing", "tracking_profiling", "third_party_access",
    "data_retention", "arbitration", "liability_limitation", "none"
]
VALID_RISK_LEVELS = ["HIGH", "MEDIUM", "LOW", "NONE"]

CSV_FIELDS = [
    "clause_id",
    "source_document",
    "clause_text",
    "suggested_cat",
    "suggested_risk",
    "category",          # ← YOU FILL THIS
    "risk_level",        # ← YOU FILL THIS
    "annotator_notes",   # ← YOU FILL THIS
    "confidence",
    "matched_keywords",
]


# ─── Core logic ───────────────────────────────────────────────────────────────

def annotate_file(input_path: str, output_path: str, clf: RuleBasedClassifier) -> int:
    """
    Processes one ToS text file → outputs annotation CSV.
    Returns number of clauses written.
    """
    source_name = Path(input_path).name

    print(f"\n  Reading: {source_name}")
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        raw_text = f.read()

    if not raw_text.strip():
        print(f"  ⚠  File is empty — skipping.")
        return 0

    # Segment
    clauses = segment_document(raw_text)
    print(f"  Segmented into {len(clauses)} clauses.")

    # Classify each clause
    rows = []
    for i, clause_text in enumerate(clauses, 1):
        matches = clf.classify_clause(clause_text)

        if matches:
            # Pick the highest-confidence match as the suggestion
            best = max(matches, key=lambda m: m["confidence"])
            suggested_cat  = best["category"]
            suggested_risk = best["risk_level"]
            confidence     = best["confidence"]
            keywords       = "; ".join(best["matched_keywords"])
        else:
            suggested_cat  = "none"
            suggested_risk = "NONE"
            confidence     = ""
            keywords       = ""

        rows.append({
            "clause_id":       f"{Path(input_path).stem}_{i:04d}",
            "source_document": source_name,
            "clause_text":     clause_text.replace("\n", " ").strip(),
            "suggested_cat":   suggested_cat,
            "suggested_risk":  suggested_risk,
            "category":        "",   # annotator fills this
            "risk_level":      "",   # annotator fills this
            "annotator_notes": "",   # annotator fills this
            "confidence":      confidence,
            "matched_keywords": keywords,
        })

    # Write CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # If file already exists, append (don't overwrite previous work)
    file_exists = os.path.exists(output_path)
    mode = "a" if file_exists else "w"

    with open(output_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    flagged = sum(1 for r in rows if r["suggested_cat"] != "none")
    print(f"  Written {len(rows)} clauses to: {output_path}")
    print(f"  Engine flagged {flagged} as potentially risky ({len(rows) - flagged} as clean).")
    print(f"  → Open the CSV and fill in 'category', 'risk_level', and 'annotator_notes' for each row.")

    return len(rows)


def annotate_all(input_dir: str, output_dir: str, clf: RuleBasedClassifier):
    """Annotates all .txt files in input_dir."""
    txt_files = glob.glob(os.path.join(input_dir, "*.txt"))

    if not txt_files:
        print(f"\n  No .txt files found in {input_dir}")
        print(f"  Add ToS documents there first (see data/raw/README.md)")
        return

    print(f"\n  Found {len(txt_files)} file(s) to annotate.")
    total = 0
    for txt_file in sorted(txt_files):
        stem = Path(txt_file).stem
        output_path = os.path.join(output_dir, f"{stem}_annotation.csv")
        total += annotate_file(txt_file, output_path, clf)

    print(f"\n  ✓ Done. Total clauses written: {total}")
    print(f"  Open the CSV files in Excel or Google Sheets to annotate.")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ClauseGuard Annotation Helper — generates annotation CSVs from raw ToS text files."
    )
    parser.add_argument(
        "input_file", nargs="?",
        help="Path to a single .txt ToS document to annotate."
    )
    parser.add_argument(
        "-o", "--output",
        help="Output CSV path (default: data/annotated/<filename>_annotation.csv)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help=f"Annotate all .txt files in {DEFAULT_INPUT_DIR}"
    )

    args = parser.parse_args()

    if not args.input_file and not args.all:
        parser.print_help()
        print("\n  Example usage:")
        print("    python annotate.py data/raw/google_privacy.txt")
        print("    python annotate.py --all")
        sys.exit(0)

    clf = RuleBasedClassifier()
    print("\n" + "=" * 55)
    print("  ClauseGuard Annotation Helper")
    print("=" * 55)

    if args.all:
        annotate_all(DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, clf)
    else:
        if not os.path.exists(args.input_file):
            print(f"\n  Error: File not found: {args.input_file}")
            sys.exit(1)

        stem = Path(args.input_file).stem
        output_path = args.output or os.path.join(
            DEFAULT_OUTPUT_DIR, f"{stem}_annotation.csv"
        )
        annotate_file(args.input_file, output_path, clf)

    print("\n" + "=" * 55)
    print("  REMINDER: Suggestions are a starting point only.")
    print("  Read every clause. Override anything that looks wrong.")
    print("  Fill in annotator_notes for every labeled row.")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
