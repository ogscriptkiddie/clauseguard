<div align="center">

<br/>

<img src="https://raw.githubusercontent.com/ogscriptkiddie/clauseguard/main/extension/icons/icon128.png" width="72" alt="ClauseGuard Logo"/>

# ClauseGuard

**Legal Risk Intelligence for Terms of Service & Privacy Policies**

*ClauseGuard reads the fine print you skip — and tells you exactly what you're agreeing to.*

<br/>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://clauseguard-chi.vercel.app)
[![Backend](https://img.shields.io/badge/Backend-Railway-7c3aed?style=for-the-badge&logo=railway&logoColor=white)](https://clauseguard-production-183f.up.railway.app/health)
[![Python](https://img.shields.io/badge/Python-3.13+-3b82f6?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Extension-f97316?style=for-the-badge&logo=googlechrome&logoColor=white)](#-quick-start)
[![License](https://img.shields.io/badge/License-MIT-a855f7?style=for-the-badge)](LICENSE)

<br/>

| 🔢 Metric | 📊 Value |
|:---|:---:|
| Classifier Rules | **757** |
| Human-Labeled Clauses | **312** |
| Total Dataset Size | **754** |
| Real ToS Documents | **21** |
| Risk Categories | **7** |
| Group CV F1 Score | **0.7558** |

</div>

---

## 📌 Overview

Nobody reads Terms of Service — and platforms count on that.

**ClauseGuard** is a cybersecurity capstone project from **Simon Fraser University (2026)** that treats legal document analysis as a *defensive security problem*. Feed it any Terms of Service or Privacy Policy — via URL, PDF, or paste — and get back a risk score, flagged clauses, and plain-English explanations in seconds.

> "The clauses designed to be invisible — made visible."

---

## 🌐 Deployment

| Service | URL | Status |
|:---|:---|:---:|
| Web Demo | [clauseguard-chi.vercel.app](https://clauseguard-chi.vercel.app) | 🟢 Live |
| Backend API | [clauseguard-production-183f.up.railway.app](https://clauseguard-production-183f.up.railway.app) | 🟢 Live |
| Health Endpoint | `/health` | 🟢 Online |

---

## 🎯 What It Detects

| Risk Category | Weight | What It Flags |
|:---|:---:|:---|
| 🔴 Data Sharing | 22% | Selling or sharing personal data with third parties |
| 🔴 Tracking & Profiling | 20% | Cross-site behavioral tracking and inferred profiles |
| 🟠 Third-Party Access | 13% | External parties accessing your data or communications |
| 🟠 Data Retention | 13% | Indefinite storage, even after account deletion |
| 🟠 Arbitration | 13% | Forced arbitration — waiving your right to sue |
| 🟡 Content & IP Rights | 10% | Perpetual, royalty-free licenses over your content |
| 🟡 Liability Limitation | 9% | Damage caps (sometimes as low as $10) |

---

## 🏗️ Architecture

```
User Input (URL / PDF / Paste)
         │
         ▼
  Flask Backend (Railway)
  ┌──────────────────────────────────┐
  │  Extraction Layer                │
  │  ├─ URL  → Playwright (JS-heavy) │
  │  ├─ PDF  → pypdf                 │
  │  └─ Text → direct                │
  │                                  │
  │  Segmentation → spaCy            │
  │                                  │
  │  Hybrid Classification Pipeline  │
  │  ┌────────────────────────────┐  │
  │  │ TF-IDF + Logistic          │  │
  │  │ Regression (calibrated)    │  │
  │  │  ↓ confidence ≥ 0.60       │  │
  │  │    → use ML prediction     │  │
  │  │  ↓ confidence < 0.60       │  │
  │  │    → 757-rule fallback     │  │
  │  └────────────────────────────┘  │
  │                                  │
  │  Weighted Risk Scoring Engine    │
  └──────────────────────────────────┘
         │
         ▼
  JSON Response → Web Demo / Extension
```

---

## 🧠 ML Model

ClauseGuard uses a **hybrid classification pipeline** — ML handles confident predictions, the rule-based system catches the rest.

### Dataset
- **754 labeled clauses** total
  - 312 hand-annotated from 21 real ToS documents (2024–2025 legal cases)
  - 442 from the [CLAUDETTE corpus](https://claudette.eui.eu/) (Drawzeski et al., 2021)

### Model
| Component | Detail |
|:---|:---|
| Vectorizer | TF-IDF (n-gram 1–3) |
| Classifier | Logistic Regression + `CalibratedClassifierCV` |
| Confidence threshold | 0.60 |
| Fallback | 757-rule rule-based system |

### Evaluation — GroupKFold (document-level)

> ⚠️ Standard random splits inflate F1 by leaking document context. ClauseGuard uses **GroupKFold** for academically valid evaluation.

| Metric | Score |
|:---|:---:|
| **F1 Macro (Group CV)** | **0.7558** |
| Precision | ~0.77 |
| Recall | ~0.75 |
| vs. rule-based baseline | **+13.9 pp** |
| False positive reduction | **42%** |

---

## 🚀 Quick Start

### Chrome Extension

```bash
git clone https://github.com/ogscriptkiddie/clauseguard.git
```

1. Open `chrome://extensions` in Chrome
2. Enable **Developer Mode** (top right)
3. Click **Load unpacked** → select the `extension/` folder

> Browse to any Terms of Service page and click the ClauseGuard icon.

---

### Local Backend

```bash
cd backend

# Create and activate virtualenv
py -3.13 -m venv venv
source venv/Scripts/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run
py app.py
```

Backend starts at `http://localhost:5000`.

---

### Retrain the Model

```bash
cd backend/ml
python train.py
```

Reads `clauseguard_dataset_v2.csv`, runs GroupKFold CV, and outputs:

```
ml/
├── model.pkl
├── label_encoder.pkl
└── results.json
```

---

## 📁 Repository Structure

```
clauseguard/
├── backend/
│   ├── app.py                      # Flask API (analyze, fetch-url, upload-pdf)
│   ├── classifier.py               # Rule-based classifier (757 rules)
│   ├── scorer.py                   # Risk-first weighted scoring engine
│   ├── segmenter.py                # spaCy clause segmentation
│   ├── railpack.toml               # Railway deployment config
│   └── ml/
│       ├── train.py                # GroupKFold training pipeline
│       ├── classifier_ml.py        # TF-IDF + calibrated LR
│       ├── hybrid.py               # ML + rule-based merge logic
│       ├── clauseguard_dataset_v2.csv
│       ├── model.pkl
│       └── label_encoder.pkl
│
├── extension/
│   ├── manifest.json               # Manifest V3
│   ├── popup.html / popup.js       # Extension UI
│   ├── content.js                  # DOM extraction + accordion expansion
│   ├── background.js               # Re-injection for SPAs
│   └── icons/
│
└── index.html                      # Web demo (Vercel)
```

---

## 🔌 API Reference

### `POST /analyze`

```json
{
  "text": "Full Terms of Service text here..."
}
```

**Response:**

```json
{
  "risk_score": 74,
  "risk_level": "HIGH",
  "summary": "This document contains high-risk arbitration and data sharing clauses.",
  "total_clauses_analyzed": 42,
  "total_risk_clauses_detected": 11,
  "processing_time_ms": 280,
  "category_scores": { "...": {} },
  "clauses": [
    {
      "text": "...",
      "risk_level": "HIGH",
      "primary_category": "arbitration",
      "matched_keywords": ["binding arbitration", "class action waiver"]
    }
  ]
}
```

### `POST /fetch-url`

```json
{ "url": "https://discord.com/privacy" }
```

Returns extracted text via Playwright (handles JS-rendered pages and accordions).

### `POST /upload-pdf`

Multipart form upload. Returns extracted text via `pypdf`.

---

## ⚠️ Known Limitations

- **Extraction consistency:** The Chrome extension (DOM-based) and the web demo (server-side Playwright) can produce different clause sets for the same URL — this is an architectural tradeoff, not a bug, and is documented intentionally.
- **ML scope:** The model is trained on English-language ToS documents. Non-English or heavily domain-specific documents may fall back to rule-based classification more often.
- **Confidence threshold:** At the 0.60 threshold, borderline clauses route to the rule-based fallback. Lowering this increases recall at the cost of precision.

---

## 🐛 Troubleshooting

| Symptom | Cause | Fix |
|:---|:---|:---|
| `classifier_mode: rule_based` in response | ML model failed to load | Check Railway build logs; `libgomp.so.1` may be missing — verify `railpack.toml` |
| Results differ between extension and web demo | DOM vs. server-side extraction | Expected behavior — documented limitation |
| `lxml` parser errors on Railway | Railway environment incompatibility | Use `html.parser` instead |
| Poor classification results | Stale model | Retrain with `python train.py` |

---

## 🎓 Academic Context

ClauseGuard is a **Simon Fraser University cybersecurity capstone project** (2026) by Tanish Rathore.

- Extends the **CLAUDETTE framework** (Drawzeski et al., 2021) with privacy-specific risk categories
- Evaluates ToS risk as a **defensive security problem** rather than a legal compliance exercise
- Uses GroupKFold cross-validation to prevent document-level data leakage — a methodological distinction important for academic validity
- Dataset sourced from real 2024–2025 legal cases (McGinty v. Uber, Disney+ arbitration, Coinbase v. Suski, Kadrey v. Meta)

---

## 👤 Author

**Tanish Rathore** — Cybersecurity · Simon Fraser University

[![GitHub](https://img.shields.io/badge/GitHub-ogscriptkiddie-181717?style=flat-square&logo=github)](https://github.com/ogscriptkiddie)
[![Portfolio](https://img.shields.io/badge/Portfolio-ogscriptkiddie.github.io-0ea5e9?style=flat-square)](https://ogscriptkiddie.github.io/personal_portfolio/)

---

<div align="center">

<sub>Built with Flask · spaCy · scikit-learn · Three.js · Chrome Extensions API · Playwright · Railway · Vercel</sub>

<br/><br/>

<sub>SFU Capstone 2026 — Tanish Rathore</sub>

</div>