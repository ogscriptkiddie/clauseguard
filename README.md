```md
<div align="center">

# 🛡️ ClauseGuard

<img src="https://img.shields.io/badge/Status-Production%20Ready-22c55e?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Python-3.13+-3b82f6?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Chrome-Extension-f97316?style=for-the-badge&logo=googlechrome&logoColor=white"/>
<img src="https://img.shields.io/badge/Backend-Railway-7c3aed?style=for-the-badge&logo=railway"/>
<img src="https://img.shields.io/badge/ML-Hybrid%20Classifier-2563eb?style=for-the-badge"/>
<img src="https://img.shields.io/badge/License-MIT-a855f7?style=for-the-badge"/>

<br/>

**Automated Risk Detection for Terms of Service & Privacy Policies**

*ClauseGuard reads legal documents in real time — and tells you what actually matters before you click "I Agree."*

</div>

---

## 🌐 Live Deployment

| Service | URL | Status |
|---|---|---|
| Backend API | https://clauseguard-production-183f.up.railway.app | 🟢 Live |
| Health Check | `/health` | 🟢 Online |
| Web Demo | https://clauseguard-chi.vercel.app | 🟢 Live |

---

## 📖 Why This Exists

Nobody reads Terms of Service — but they still agree to them.

ClauseGuard detects:

- 🔴 Data selling & sharing
- 🔴 Arbitration clauses (you waive your right to sue)
- 🔴 Perpetual licenses over your content
- 🟠 Behavioral tracking & profiling
- 🟠 Indefinite data retention
- 🟡 Liability caps

👉 Instead of reading 8000+ words, you get a **risk score + highlighted clauses instantly**

---

## ⚙️ System Architecture (Updated)

```

User → Chrome Extension → Flask API

```
            ↓

     Clause Segmentation (spaCy)

            ↓

 Hybrid Classification Pipeline
 ┌─────────────────────────────┐
 │ ML Classifier (TF-IDF + LR) │
 │ → Used when confident       │
 │                             │
 │ Rule-Based System (757 rules)│
 │ → Fallback + safety layer   │
 └─────────────────────────────┘

            ↓

  Risk Scoring Engine (UPDATED)
  - Risk-first aggregation
  - Category influence reduced
  - Multi-signal scoring

            ↓

  JSON Response (v1.5 + v2 layer)

            ↓

  Extension UI / Web Demo
```

````

---

## 🧠 Hybrid Classifier (Important)

ClauseGuard does **NOT blindly trust ML**.

| Scenario | Behavior |
|--------|--------|
| ML confidence ≥ threshold | Use ML |
| ML uncertain | Fall back to rule-based |
| Rule detects strong keyword | Can override ML |

This prevents:
- false positives
- hallucinated categories
- missed critical clauses

---

## 📊 Model Performance (Corrected)

Dataset: **754 labeled clauses**
- 312 human annotated (ClauseGuard)
- 446 CLAUDETTE corpus

### Evaluation Method (IMPORTANT)
✔ **GroupKFold (document-level split)**  
❌ Not StratifiedKFold (avoids leakage)

| Metric | Score |
|------|------|
| **F1 Macro (Group CV)** | **0.7558** |
| Precision | ~0.77 |
| Recall | ~0.75 |

👉 This is **academically valid evaluation**

---

## 🎯 Risk Categories

| Category | Description |
|--------|------------|
| Data Sharing | Selling or sharing user data |
| Tracking & Profiling | Behavioral tracking |
| Third Party Access | External access to data |
| Data Retention | Indefinite storage |
| Arbitration | Legal rights waived |
| Content Rights | Ownership of your content |
| Liability Limitation | Legal protection clauses |

---

## ⚠️ Scoring System (NEW)

Previous:
- Category-weight driven

Now:
- **Risk-driven scoring**
- Categories only influence weighting
- Multiple clauses increase severity

✔ More realistic  
✔ Less biased  
✔ Better security interpretation  

---

## 🔄 API Response (UPDATED)

### Current (Stable)
```json
{
  "risk_score": 68,
  "risk_level": "HIGH",
  "summary": "...",
  "clauses": [...]
}
````

### New (Migration Layer)

```json
{
  "response_version": "1.5",
  "analysis_v2": {
    "document_summary": {...},
    "clauses": [...],
    "summary": {...}
  }
}
```

👉 Extension still uses old format
👉 New format is for future upgrades

---

## 🚀 Quick Start

### Install Extension

```bash
git clone https://github.com/ogscriptkiddie/clauseguard.git
```

1. Go to `chrome://extensions`
2. Enable Developer Mode
3. Load `extension/`

---

## 🖥️ Local Backend Setup

```bash
cd backend

py -3.13 -m venv venv
source venv/Scripts/activate

pip install -r requirements.txt
py -m spacy download en_core_web_sm

py app.py
```

---

## 🧪 Retrain Model (FIXED)

```bash
cd backend/ml
python train.py
```

✔ Uses `clauseguard_dataset_v2.csv`
✔ Uses **GroupKFold**
✔ Outputs:

* model.pkl
* label_encoder.pkl
* results.json

---

## 📁 Updated Repo Structure

```
backend/
├── app.py
├── classifier.py
├── scorer.py              ← UPDATED scoring system
├── segmenter.py
├── railpack.toml          ← FIXED (Railway config)
├── ml/
│   ├── train.py           ← FIXED dataset + CV
│   ├── classifier_ml.py   ← improved confidence handling
│   ├── hybrid.py          ← ML + rule merge
│   ├── clauseguard_dataset_v2.csv
│   └── model.pkl
```

---

## 🐛 Troubleshooting

**classifier_mode = rule_based**
→ ML failed to load (check Railway build / dependencies)

**Bad results**
→ Ensure correct dataset + retrained model

---

## 🎓 Academic Notes

* Uses **CLAUDETTE framework (extended)**
* Adds **privacy-specific categories**
* Treats ToS analysis as:
  → **security problem, not legal problem**

---

## 👤 Author

**Tanish Rathore**
Cybersecurity · SFU · MSP Security

---

<div align="center">
<sub>Built with Flask · spaCy · scikit-learn · Chrome Extensions API</sub>
</div>
```

---