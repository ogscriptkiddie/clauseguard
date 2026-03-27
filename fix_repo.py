"""
fix_repo.py — ClauseGuard Repo Updater

Run from the clauseguard repo root:
    python fix_repo.py

Applies all Phase 2 completion updates:
  - Root README.md: badges, dataset table, TikTok note, phase status
  - demo/index.html: stats strip (214->300, 12->20)
  - docs/git-workflow.md: YOUR_USERNAME->ogscriptkiddie, UFV->SFU
  - data/raw/README.md, evaluation/README.md, extension/README.md, ml/README.md:
    UFV->SFU, status table, category weights, author info
"""

import os

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
changes = []


def fix_file(filepath, substitutions, description):
    full_path = os.path.join(REPO_ROOT, filepath)
    if not os.path.exists(full_path):
        print(f"  SKIP: {filepath} not found")
        return False
    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    original = content
    for old, new in substitutions:
        content = content.replace(old, new)
    if content != original:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  FIXED: {filepath} -- {description}")
        changes.append(filepath)
        return True
    else:
        print(f"  OK:    {filepath} -- already up to date")
        return False


print("\n" + "=" * 60)
print("  ClauseGuard Repo Updater -- Phase 2 Completion")
print("=" * 60 + "\n")

# 1. Root README.md
fix_file("README.md", [
    ("Dataset-214%20Labeled%20Clauses", "Dataset-300%20Labeled%20Clauses"),
    ("Documents-12%20Processed", "Documents-20%20Processed"),
    ("214 human-labeled clauses across 12 real documents",
     "300 human-labeled clauses across 20 real documents"),
    ("The annotation dataset covers **12 documents** from major platforms:",
     "The annotation dataset covers **20 documents** from major platforms:"),
    ("| Privacy Policies | Terms of Service |\n|---|---|\n| Meta \xb7 Uber \xb7 Discord \xb7 Reddit | Spotify \xb7 Amazon \xb7 LinkedIn |\n| Spotify \xb7 Apple | Apple \xb7 Microsoft \xb7 Google |",
     "| Privacy Policies | Terms of Service |\n|---|---|\n| Meta \xb7 Uber \xb7 Discord \xb7 Reddit | Spotify \xb7 Amazon \xb7 LinkedIn \xb7 DoorDash |\n| Spotify \xb7 Apple \xb7 Instagram | Apple \xb7 Microsoft \xb7 Google \xb7 Coinbase |\n| | Disney+ \xb7 Airbnb \xb7 TikTok \xb7 X (Twitter) \xb7 Snapchat |"),
    ("**214 human-labeled clauses**", "**300 human-labeled clauses**"),
    ("> \u26a0\ufe0f **TikTok ToS** was planned for Phase 2 but the official URL returned a 404 error at collection time. It will be processed in Phase 3 to strengthen the arbitration and content-rights categories.",
     "> \u2705 **TikTok ToS** was unavailable during early Phase 2 (404 error) but was successfully processed later along with 7 additional platforms (DoorDash, Airbnb, Coinbase, Disney+, X/Twitter, Snapchat, Instagram) to complete the dataset."),
    ("| **Phase 3** \xb7 ML Classifier | \U0001f504 **In Progress** | scikit-learn model, hybrid pipeline, inter-rater reliability check |",
     "| **Phase 3** \xb7 ML Classifier | \U0001f51c **Up Next** | scikit-learn model, hybrid pipeline, inter-rater reliability check |"),
], "Updated badges, dataset (300/20), TikTok note, phase status")

# 2. demo/index.html
fix_file("demo/index.html", [
    ('<div class="stat-n">214</div>', '<div class="stat-n">300</div>'),
    ('<div class="stat-n">12</div>', '<div class="stat-n">20</div>'),
], "Updated stats strip (214->300, 12->20)")

# 3. docs/git-workflow.md
fix_file("docs/git-workflow.md", [
    ("YOUR_USERNAME", "ogscriptkiddie"),
    ("#Python #CyberSecurity #NLP #OpenSource #UFV",
     "#Python #CyberSecurity #NLP #OpenSource #SFU"),
], "Fixed YOUR_USERNAME and UFV->SFU")

# 4-7. Sub-folder READMEs
SUB_README = '''# ClauseGuard

**Automated Detection and Risk Classification of Security & Privacy Clauses in Web Agreements**

> A browser-integrated system that analyzes Terms of Service and Privacy Policies in real time, flagging security and privacy risks ordinary users never read.

---

## Risk Categories Detected

| Category | Weight | What It Catches |
|----------|--------|-----------------|
| Data Sharing | 22% | Selling or sharing your data with third parties |
| Tracking & Profiling | 20% | Behavioral tracking, cross-site monitoring, ad profiling |
| Third-Party Access | 13% | Partners, advertisers, or governments accessing your account |
| Data Retention | 13% | Indefinite data storage, no deletion guarantees |
| Arbitration | 13% | Waiving your right to sue or join class actions |
| Content & IP Rights | 10% | Perpetual licenses over your content, moral rights waivers, AI training |
| Liability Limitation | 9% | The company disclaiming responsibility for harm |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Browser Extension | JavaScript (Chrome Manifest V3) |
| Backend API | Python + Flask |
| Clause Segmentation | spaCy |
| Rule-Based Engine | Custom keyword classifier with negation detection |
| ML Classifier | scikit-learn (Logistic Regression + TF-IDF) |

---

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| 1 -- Backend Engine | Complete | Flask API, rule-based classifier (757 rules), risk scoring |
| 2 -- Extension + Dataset | Complete | MV3 extension, popup UI, 300-clause annotated dataset, Railway deployment |
| 3 -- ML Classifier | Up Next | scikit-learn model, hybrid pipeline, inter-rater reliability check |
| 4 -- Evaluation | Planned | F1 / precision / recall vs. rule-based baseline |

---

## Background

Built as a **capstone security research project** at **Simon Fraser University**. ClauseGuard explores the intersection of NLP, cybersecurity risk modeling, and privacy rights -- approaching legal document analysis as a defensive security problem.

---

## Author

**Tanish Rathore** -- Security Researcher | Simon Fraser University | MSP Security Technician

[LinkedIn](https://linkedin.com/in/tanish-rathore) | [Portfolio](https://ogscriptkiddie.github.io/personal_portfolio/)
'''

for folder in ["data/raw", "evaluation", "extension", "ml"]:
    readme_path = os.path.join(REPO_ROOT, folder, "README.md")
    folder_path = os.path.join(REPO_ROOT, folder)
    if os.path.exists(folder_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(SUB_README)
        print(f"  FIXED: {folder}/README.md -- Replaced (SFU, 7 categories, current status)")
        changes.append(f"{folder}/README.md")
    else:
        print(f"  SKIP: {folder}/ not found")

# Summary
print(f"\n{'=' * 60}")
print(f"  Updated {len(changes)} file(s).")
print(f"\n  Next steps:")
print(f"    git add .")
print(f'    git commit -m "Phase 2 complete: Update docs to 300 labels, 20 documents, fix SFU references"')
print(f"    git push")
print(f"{'=' * 60}\n")
