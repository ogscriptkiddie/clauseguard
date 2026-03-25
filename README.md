# 🛡️ ClauseGuard
**Automated Detection and Risk Classification of Security & Privacy Clauses in Web Agreements**

> A browser-integrated system that analyzes Terms of Service and Privacy Policies in real time, flagging security and privacy risks ordinary users never read.

---

## Why This Exists

The average Terms of Service document is ~8,000 words long. Nobody reads them. Yet they routinely authorize data selling, behavioral profiling, mandatory arbitration, indefinite data retention, and perpetual content licensing — all with legal force the moment you click "I Agree."

ClauseGuard reads them for you.

---

## How It Works

```
You visit a ToS or Privacy Policy page
              ↓
Chrome Extension detects the document (badge fires)
              ↓
Flask API receives the full text
              ↓
Clause Segmenter splits it into legal units (spaCy)
              ↓
Risk Classification Engine analyzes each clause
              ↓
Weighted Risk Score (0–100) computed
              ↓
Flagged clauses shown as plain-English cards in the popup
```

---

## Risk Categories Detected

| Category | Weight | What It Catches |
|---|---|---|
| Data Sharing | 22% | Selling or sharing your data with third parties, affiliates, or the public |
| Tracking & Profiling | 20% | Behavioral tracking, cross-site monitoring, inference, ad profiling |
| Third-Party Access | 13% | Partners, advertisers, law enforcement, or employers accessing your data |
| Data Retention | 13% | Indefinite storage, no deletion guarantees, post-account retention |
| Arbitration | 13% | Waiving your right to sue, class action waivers, binding dispute clauses |
| Content & IP Rights | 10% | Perpetual licenses over your content, moral rights waivers, AI training use |
| Liability Limitation | 9% | Damages caps, indemnification, "you shall not sue" waivers |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Browser Extension | JavaScript — Chrome Manifest V3 |
| Backend API | Python + Flask |
| Clause Segmentation | spaCy |
| Rule-Based Engine | 757-rule keyword classifier with proximity-based negation detection |
| ML Classifier | scikit-learn — TF-IDF + Logistic Regression (Phase 3) |
| Dataset | 214 human-labeled clauses across 12 real ToS/Privacy documents |

---

## Project Status

| Phase | Status | Description |
|---|---|---|
| 1 — Backend Engine | ✅ Complete | Flask API, spaCy segmenter, rule-based classifier, risk scorer |
| 2 — Chrome Extension + Dataset | ✅ Complete | MV3 extension, popup UI, badge alerts, SPA detection, 214-clause annotated dataset |
| 3 — ML Classifier | 🔜 In Progress | scikit-learn model trained on annotated dataset, hybrid pipeline |
| 4 — Evaluation | 🔜 Planned | Precision / recall / F1 vs rule-based baseline, user study |

---

## Local Setup

### Prerequisites

- Python 3.10+
- Google Chrome

### 1 — Start the backend

```bash
cd clauseguard/backend
pip install -r requirements.txt
python app.py
# → Running on http://127.0.0.1:5000
```

### 2 — Load the extension

1. Open Chrome and navigate to `chrome://extensions`
2. Toggle **Developer mode** on (top right)
3. Click **Load unpacked** and select the `clauseguard/extension/` folder
4. The ClauseGuard shield icon appears in your toolbar

### 3 — Test it

Navigate to any Terms of Service or Privacy Policy page. The red **!** badge fires on the icon when a document is detected. Click the icon to open the risk card popup.

---

## Repository Structure

```
clauseguard/
├── backend/
│   ├── app.py              Flask API — /health and /analyze endpoints
│   ├── categories.py       7 risk categories + 757 keyword rules
│   ├── segmenter.py        Document → clause segmentation (spaCy)
│   ├── classifier.py       Rule-based classifier with negation detection
│   ├── scorer.py           Weighted 0–100 risk scoring engine
│   └── requirements.txt
├── extension/
│   ├── manifest.json       Manifest V3 configuration
│   ├── content.js          ToS detection (4-signal heuristic + MutationObserver)
│   ├── background.js       Service worker — badge state management
│   ├── popup.html          Extension popup UI
│   ├── popup.js            Risk card rendering + progressive disclosure
│   └── icons/              Extension icons (16 / 48 / 128 px)
├── data/
│   ├── raw/                Plain-text ToS and Privacy Policy documents
│   └── annotated/          Hand-labeled clause CSVs with justification notes
├── ml/                     ML Classifier — Phase 3
├── evaluation/             Evaluation results and metrics — Phase 4
└── README.md
```

---

## Dataset

The annotation dataset covers **12 documents** from major platforms:

| Platform | Documents |
|---|---|
| Meta, Uber, Discord, Reddit | Privacy Policies |
| Spotify, Amazon, Apple, LinkedIn | Privacy Policy + Terms of Service |
| Microsoft, Google | Terms of Service |

**214 clauses** are human-labeled with category, risk level, and written justification. The dataset drives both rule development and ML training in Phase 3.

---

## Background

Built as a capstone security research project at **Simon Fraser University**. ClauseGuard sits at the intersection of NLP, cybersecurity risk modeling, and privacy rights — treating legal document analysis as a defensive security problem rather than a legal one. The goal is to surface the risks that ordinary users agree to every day without realising it.

---

## Author

**Tanish Rathore** — Security Researcher · SFU · MSP Security Technician

[LinkedIn](https://linkedin.com/in/tanish-rathore) · [Portfolio](https://ogscriptkiddie.github.io/personal_portfolio/) · [GitHub](https://github.com/ogscriptkiddie/clauseguard)
