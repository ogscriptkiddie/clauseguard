# 🛡️ ClauseGuard

**Automated Detection and Risk Classification of Security & Privacy Clauses in Web Agreements**

> A browser-integrated system that analyzes Terms of Service and Privacy Policies in real time, flagging security and privacy risks ordinary users never read.

---

## Why This Exists

The average Terms of Service document is ~8,000 words long. Nobody reads them. Yet they routinely authorize data selling, behavioral profiling, mandatory arbitration, and indefinite data retention — all with legal force once you click "I Agree."

ClauseGuard reads them for you.

---

## How It Works

```
You visit a ToS page
        ↓
Chrome Extension extracts the text
        ↓
Flask API receives the document
        ↓
Clause Segmenter splits it into legal units
        ↓
Risk Classification Engine analyzes each clause
        ↓
Risk Score (0–100) returned to your browser
        ↓
Risky clauses highlighted in-page
```

---

## Risk Categories Detected

| Category | Weight | What It Catches |
|----------|--------|-----------------|
| Data Sharing | 25% | Selling or sharing your data with third parties |
| Tracking & Profiling | 20% | Behavioral tracking, cross-site monitoring, ad profiling |
| Third-Party Access | 15% | Partners, advertisers, or governments accessing your account |
| Data Retention | 15% | Indefinite data storage, no deletion guarantees |
| Arbitration | 15% | Waiving your right to sue or join class actions |
| Liability Limitation | 10% | The company disclaiming responsibility for harm |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Browser Extension | JavaScript (Chrome Manifest V3) |
| Backend API | Python + Flask |
| Clause Segmentation | spaCy |
| Rule-Based Engine | Custom keyword classifier with negation detection |
| ML Classifier | scikit-learn (Logistic Regression / SVM + TF-IDF) |

---

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| 1 — Backend Engine | ✅ Complete | Flask API, rule-based classifier, risk scoring |
| 2 — Chrome Extension | 🔜 In Progress | Content script + popup UI |
| 3 — ML Classifier | 🔜 Planned | scikit-learn model trained on annotated dataset |
| 4 — Evaluation | 🔜 Planned | Precision / recall / F1 vs rule-based baseline |

---

## Local Setup

### Prerequisites
- Python 3.10+
- Google Chrome (for the extension)

### Backend

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/clauseguard.git
cd clauseguard/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Verify everything works (no server needed)
python test_engine.py

# Start the API server
python app.py
# → http://localhost:5000
```

### Test the API

```bash
curl http://localhost:5000/health

curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "We may share your data with advertisers. You waive your right to a jury trial."}'
```

---

## Repository Structure

```
clauseguard/
├── backend/
│   ├── app.py              Flask API entry point
│   ├── categories.py       Risk category definitions + keyword rules
│   ├── segmenter.py        Document → clause segmentation (spaCy)
│   ├── classifier.py       Rule-based classifier with negation detection
│   ├── scorer.py           Weighted 0–100 risk scoring engine
│   ├── test_engine.py      Local test suite
│   └── requirements.txt
├── extension/              Chrome Extension (Phase 2)
├── ml/                     ML Classifier (Phase 3)
├── data/
│   ├── raw/                Raw ToS documents (.txt)
│   └── annotated/          Hand-labeled clause dataset (.csv)
├── evaluation/             Evaluation results + metrics (Phase 4)
└── README.md
```

---

## Background

Built as a capstone security research project at the University of the Fraser Valley. ClauseGuard explores the intersection of NLP, cybersecurity risk modeling, and privacy rights — approaching legal document analysis as a defensive security problem.

---

## Author

**Tanish Rathore** — Security Researcher | UFV Graduate | MSP Security Technician

[LinkedIn](https://linkedin.com/in/tanish-rathore) · [Portfolio](https://ogscriptkiddie.github.io/personal_portfolio/)
