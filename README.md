<div align="center">

# 🛡️ ClauseGuard

<img src="https://img.shields.io/badge/Status-Phase%203%20Complete-22c55e?style=for-the-badge&logo=checkmarx&logoColor=white"/>
<img src="https://img.shields.io/badge/Python-3.13+-3b82f6?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Chrome-Extension-f97316?style=for-the-badge&logo=googlechrome&logoColor=white"/>
<img src="https://img.shields.io/badge/Backend-Live%20on%20Railway-7c3aed?style=for-the-badge&logo=railway&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-a855f7?style=for-the-badge"/>

<br/>
<br/>

**Automated Detection and Risk Classification of Security & Privacy Clauses in Web Agreements**

*A browser-integrated system that reads Terms of Service and Privacy Policies in real time —
flagging the risks ordinary users never see before clicking "I Agree."*

<br/>

[![Dataset](https://img.shields.io/badge/Dataset-754%20Labeled%20Clauses-2563eb?style=flat-square)](data/annotated/)
[![Rules](https://img.shields.io/badge/Classifier-757%20Rules%20%2B%20ML-7c3aed?style=flat-square)](backend/categories.py)
[![Documents](https://img.shields.io/badge/Documents-21%20Processed-0891b2?style=flat-square)](data/raw/)
[![Categories](https://img.shields.io/badge/Risk%20Categories-7-16a34a?style=flat-square)](backend/categories.py)
[![F1](https://img.shields.io/badge/CV%20F1%20Macro-0.7646-f59e0b?style=flat-square)](backend/ml/results.json)
[![API](https://img.shields.io/badge/API-Live-22c55e?style=flat-square)](https://clauseguard-production-183f.up.railway.app/health)
[![Demo](https://img.shields.io/badge/Demo-Live-22c55e?style=flat-square)](https://clauseguard-chi.vercel.app)
[![SFU](https://img.shields.io/badge/Simon%20Fraser%20University-Capstone-dc2626?style=flat-square)](https://www.sfu.ca/)

</div>

---

## 🌐 Live Deployment

| Service | URL | Status |
|---|---|---|
| **Backend API** | `https://clauseguard-production-183f.up.railway.app` | 🟢 Live |
| **Health Check** | [`/health`](https://clauseguard-production-183f.up.railway.app/health) | 🟢 Online |
| **Web Demo** | [`clauseguard-chi.vercel.app`](https://clauseguard-chi.vercel.app) | 🟢 Live |
| **Analyze Endpoint** | `POST /analyze` | 🟢 Ready |

---

## 📖 Why This Exists

The average Terms of Service document is **~8,000 words** long. Nobody reads them. Yet they routinely authorize:

| What you don't know you agreed to | Example |
|---|---|
| 🔴 **Data selling** | "We may share your information with commercial partners" |
| 🔴 **Perpetual content licenses** | "A worldwide, irrevocable, royalty-free license to use your content" |
| 🔴 **Mandatory arbitration** | "You waive your right to a jury trial or class action" |
| 🟠 **Behavioral profiling** | "We infer your interests and preferences from your usage" |
| 🟠 **Indefinite data retention** | "We keep your data for as long as necessary for business purposes" |
| 🟡 **Liability caps** | "Our total liability shall not exceed $10.00" |

**ClauseGuard reads them for you** — in real time, before you agree.

---

## ⚙️ How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    You visit a ToS page                     │
│                           │                                 │
│         Chrome Extension detects the document               │
│              (4-signal heuristic + MutationObserver)        │
│                           │                                 │
│     Hosted Flask API receives the full document text        │
│       (Railway — clauseguard-production-183f.railway.app)   │
│                           │                                 │
│       spaCy Segmenter splits it into legal clauses          │
│                           │                                 │
│      ┌────────────────────┴────────────────────┐            │
│      │        Hybrid Classification Engine      │            │
│      │                                          │            │
│      │  ML (TF-IDF + Logistic Regression)       │            │
│      │       confidence ≥ 0.40 → use ML         │            │
│      │       confidence < 0.40 → rule-based     │            │
│      │  757 rules · 7 categories · negation     │            │
│      └────────────────────┬────────────────────┘            │
│                           │                                 │
│        Weighted Risk Score (0–100) computed                 │
│                           │                                 │
│    Plain-English risk cards shown in extension popup        │
│         + Web demo at clauseguard-chi.vercel.app            │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 ML Classifier Performance (Phase 3)

Trained on **312 human-labeled clauses** across **21 real platform documents**.

| Metric | ML Classifier | Rule-Based Baseline | Improvement |
|---|---|---|---|
| **F1 Macro** | **0.7646** | 0.6172 | +14.76 pp |
| **F1 Weighted** | **0.7626** | 0.6086 | +15.40 pp |
| **Precision** | **0.7732** | 0.6854 | +8.77 pp |
| **Recall** | **0.7675** | 0.6102 | +15.74 pp |
| **False Positive Rate** | **3.88%** | 6.71% | −42% |

*Evaluated using 5-fold stratified cross-validation.*

### Per-Category F1

| Category | ML | Rule-Based | Δ |
|---|---|---|---|
| Arbitration | **0.95** | 0.86 | +0.09 |
| Liability Limitation | **0.90** | 0.70 | +0.20 |
| Data Retention | **0.83** | 0.79 | +0.04 |
| Content & IP Rights | **0.81** | 0.70 | +0.11 |
| Tracking & Profiling | **0.75** | 0.47 | +0.28 |
| Third-Party Access | **0.59** | 0.39 | +0.20 |
| Data Sharing | **0.53** | 0.41 | +0.12 |

---

## 🎯 Risk Categories Detected

<div align="center">

| # | Category | Weight | What It Catches |
|:---:|---|:---:|---|
| 🔵 | **Data Sharing** | `22%` | Selling or sharing data with third parties, affiliates, or the public |
| 🟣 | **Tracking & Profiling** | `20%` | Behavioral tracking, cross-site monitoring, inference, ad profiling |
| 🟠 | **Third-Party Access** | `13%` | Partners, advertisers, law enforcement, or employers accessing your data |
| 🟡 | **Data Retention** | `13%` | Indefinite storage, no deletion guarantee, post-account retention |
| 🔴 | **Arbitration** | `13%` | Waiving your right to sue, class action waivers, binding dispute clauses |
| 🟢 | **Content & IP Rights** | `10%` | Perpetual licenses over your content, moral rights waivers, AI training use |
| ⚫ | **Liability Limitation** | `9%` | Damages caps, indemnification, "you shall not sue" waivers |

</div>

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology | Purpose |
|---|---|---|
| ![Chrome](https://img.shields.io/badge/-Chrome%20Extension-f97316?style=flat-square&logo=googlechrome&logoColor=white) | JavaScript · Manifest V3 | ToS detection, badge alerts, popup UI |
| ![Flask](https://img.shields.io/badge/-Flask%20API-64748b?style=flat-square&logo=flask&logoColor=white) | Python · Flask | REST backend — `/analyze`, `/fetch-url` endpoints |
| ![Railway](https://img.shields.io/badge/-Railway-7c3aed?style=flat-square&logo=railway&logoColor=white) | Railway.app | Cloud hosting — always-on, no local server needed |
| ![Vercel](https://img.shields.io/badge/-Vercel-171717?style=flat-square&logo=vercel&logoColor=white) | Vercel | Web demo hosting — clauseguard-chi.vercel.app |
| ![spaCy](https://img.shields.io/badge/-spaCy-09a3d5?style=flat-square) | spaCy NLP | Document → legal clause segmentation |
| ![ML](https://img.shields.io/badge/-ML%20Classifier-2563eb?style=flat-square&logo=scikitlearn&logoColor=white) | TF-IDF + Logistic Regression + CalibratedClassifierCV | CV F1 Macro: 0.7646 |
| ![Rules](https://img.shields.io/badge/-Rule%20Engine-7c3aed?style=flat-square) | Custom Python | 757-rule keyword classifier with negation detection |
| ![Dataset](https://img.shields.io/badge/-Dataset-16a34a?style=flat-square) | CSV + Python | 754 labeled clauses — 312 hand-annotated (ClauseGuard) + 446 from CLAUDETTE corpus (Drawzeski et al. 2021) |

</div>

---

## 📊 Project Status

<div align="center">

| Phase | Status | Description |
|---|:---:|---|
| **Phase 1** · Backend Engine | ✅ **Complete** | Flask API, spaCy segmenter, rule-based classifier (757 rules), risk scorer |
| **Phase 2** · Extension + Dataset | ✅ **Complete** | MV3 extension, popup UI, badge alerts, SPA detection, 312-clause annotated dataset |
| **Phase 3** · ML Classifier | ✅ **Complete** | TF-IDF + LR hybrid pipeline, Group CV F1=0.7558, trained on 754 clauses (ClauseGuard + CLAUDETTE) |
| **Phase 4** · Final Report | ✅ **Complete** | Precision/recall/F1/FPR evaluation, ML vs baseline comparison, technical report |

</div>

---

## 🚀 Quick Start — Install the Extension

The backend is already live. You just need to install the extension.

### Option A — Load from this repo (Developer Mode)

```bash
git clone https://github.com/ogscriptkiddie/clauseguard.git
```

1. Open Chrome → go to `chrome://extensions`
2. Toggle **Developer mode** ON (top right)
3. Click **Load unpacked** → select the `extension/` folder
4. The ClauseGuard 🛡️ icon appears in your toolbar

Navigate to any ToS page — the extension calls the live hosted API automatically.

### Option B — Web Demo (no install needed)

Visit **[clauseguard-chi.vercel.app](https://clauseguard-chi.vercel.app)** — paste any ToS URL or text directly in the browser.

---

## 🧪 Test It

Once the extension is installed, try these pages:

```
https://discord.com/privacy
https://www.spotify.com/us/legal/end-user-agreement/
https://policies.google.com/terms
https://www.reddit.com/policies/privacy-policy
https://www.linkedin.com/legal/user-agreement
https://www.microsoft.com/en-ca/servicesagreement
```

- The **red `!` badge** fires when a ToS/Privacy Policy is detected
- Click the icon → **Scan This Page**
- Risk cards appear with plain-English summaries and the actual clause text

---

## 🖥️ Local Development Setup

Only needed if you want to modify the backend. The extension works out of the box with the hosted API.

### Prerequisites

- <kbd>Python 3.13</kbd> — use `py` on Windows
- <kbd>Git</kbd>
- <kbd>Google Chrome</kbd>

### Run the backend locally

```bash
git clone https://github.com/ogscriptkiddie/clauseguard.git
cd clauseguard/backend

# Create virtual environment
py -3.13 -m venv venv
source venv/Scripts/activate        # Git Bash on Windows
# source venv/bin/activate          # macOS / Linux

# Install dependencies
pip install -r requirements.txt --only-binary :all:
py -m spacy download en_core_web_sm

# Start the server
py app.py
# → Running on http://127.0.0.1:5000
```

### Retrain the ML model

```bash
cd clauseguard/backend/ml
python train.py
# Outputs: model.pkl, label_encoder.pkl, results.json
```

To point the extension at your local backend instead of Railway, change line 6 in `extension/popup.js`:

```javascript
// Local development
const API_URL = 'http://127.0.0.1:5000';

// Production (default)
const API_URL = 'https://clauseguard-production-183f.up.railway.app';
```

---

<details>
<summary><b>🐛 Troubleshooting</b></summary>

<br/>

**Extension shows "Analysis failed" or HTTP error**
```
→ Check https://clauseguard-production-183f.up.railway.app/health
→ Should return: {"status": "ok", "classifier_mode": "hybrid"}
→ If classifier_mode is "rule_based", libgomp1 may not be installed on Railway
```

**Badge not appearing on a ToS page**
```
→ Hard-refresh the page: Ctrl+Shift+R
→ Make sure the URL contains: terms, privacy, legal, or conditions
→ Try: discord.com/privacy — always reliably detected
```

**spaCy model missing (local dev only)**
```bash
py -m spacy download en_core_web_sm
```

**Extension not updating after code changes**
```
→ chrome://extensions → click ↻ refresh on ClauseGuard
→ Hard-refresh the test page
```

</details>

<details>
<summary><b>🔄 Deploying backend changes</b></summary>

<br/>

The backend auto-deploys to Railway on every push to `main`:

```bash
git add .
git commit -m "Your change description"
git pull --rebase origin main
git push
# → Railway detects the push and redeploys automatically
```

</details>

---

## 📁 Repository Structure

```
clauseguard/
│
├── 📂 backend/
│   ├── app.py              ← Flask API (/health, /analyze, /fetch-url)
│   ├── categories.py       ← 7 risk categories + 757 keyword rules
│   ├── segmenter.py        ← Document → clause segmentation (spaCy)
│   ├── classifier.py       ← Rule-based classifier with negation detection
│   ├── scorer.py           ← Weighted 0–100 risk scoring engine
│   ├── nixpacks.toml       ← Railway system dependencies (libgomp1)
│   ├── Procfile            ← Railway start command
│   ├── runtime.txt         ← Python version for Railway
│   ├── requirements.txt
│   └── 📂 ml/
│       ├── train.py            ← Retrain the ML model
│       ├── classifier_ml.py    ← MLClassifier wrapper
│       ├── hybrid.py           ← HybridClassifier (ML + rule fallback)
│       ├── model.pkl           ← Trained TF-IDF + Calibrated LR (4.7MB)
│       ├── label_encoder.pkl   ← Category label encoder
│       ├── results.json        ← CV evaluation results
│       └── clauseguard_dataset.csv ← 312-clause training dataset
│
├── 📂 extension/
│   ├── manifest.json       ← Manifest V3 configuration
│   ├── content.js          ← ToS detection (4-signal + MutationObserver)
│   ├── background.js       ← Service worker · badge state
│   ├── popup.html          ← Extension popup UI
│   ├── popup.js            ← Risk card rendering + progressive disclosure
│   └── icons/              ← 16px / 48px / 128px extension icons
│
├── 📂 demo/
│   └── index.html          ← Web demo (Three.js, Playfair Display)
│
├── 📂 data/
│   ├── raw/                ← Plain-text ToS + Privacy Policy documents
│   └── annotated/          ← Hand-labeled clause CSVs with justification notes
│
└── README.md
```

---

## 📚 Dataset

The training dataset contains **754 labeled clauses** from two sources:

### Source 1 — ClauseGuard Hand-Annotated Dataset (312 clauses)

<div align="center">

| Platform | Documents |
|---|---|
| Meta, Uber, Discord, Reddit, Spotify, Apple | Privacy Policies |
| Spotify, Amazon, LinkedIn, DoorDash, Apple, Microsoft | Terms of Service |
| Google, Coinbase, Disney+, Airbnb, TikTok, X/Twitter, Snapchat, Instagram | Terms of Service |

</div>

312 clauses annotated by Tanish Rathore using a **human-in-the-loop methodology**: the rule-based classifier pre-labeled each clause, then every label was independently reviewed and adjudicated — with a ~35% override rate. Written justification provided for every label.

> ✅ Documents were selected to include platforms involved in real legal cases (McGinty v. Uber, Coinbase v. Suski, Kadrey v. Meta) to strengthen academic credibility.

### Source 2 — CLAUDETTE Corpus (446 clauses)

<div align="center">

| Category mapped | CLAUDETTE tag | Clauses |
|---|---|---|
| liability_limitation | `<ltd>` | 218 |
| data_retention | `<ter>` | 92 |
| arbitration | `<a>`, `<j>` | 88 |
| content_rights | `<cr>` | 48 |

</div>

446 English clauses extracted from the **CLAUDETTE multilingual corpus** (Drawzeski et al., 2021), covering 25 Terms of Service documents from platforms including Uber, Spotify, LinkedIn, Snapchat, Google, Facebook, Dropbox, Tinder, and others. Expert-annotated by legal researchers at the University of Bologna.

**Full citation:**
> Drawzeski, K., Galassi, A., Jablonowska, A., Lagioia, F., Lippi, M., Micklitz, H.W., Sartor, G., Tagiuri, G., & Torroni, P. (2021). A Corpus for Multilingual Analysis of Online Terms of Service. *Proceedings of the Natural Legal Language Processing Workshop 2021 (NLLP@EMNLP)*, 1–8. https://aclanthology.org/2021.nllp-1.1

**Hugging Face:** `joelniklaus/online_terms_of_service`

> **Note:** The CLAUDETTE corpus is used strictly for research and educational purposes under academic fair use. All credit for the CLAUDETTE annotations belongs to the original authors (Drawzeski et al. 2021 and the broader CLAUDETTE project team at the University of Bologna). ClauseGuard's novel contribution is the privacy-specific categories (`data_sharing`, `tracking_profiling`, `third_party_access`) which do not exist in the CLAUDETTE schema.

---

## 🎓 Background

Built as a **capstone security research project** at **Simon Fraser University**.

ClauseGuard sits at the intersection of NLP, cybersecurity risk modeling, and privacy rights — treating legal document analysis as a **defensive security problem** rather than a legal one. The goal is to surface the risks that ordinary users agree to every day without realising it.

The 7-category schema is grounded in:
- **CLAUDETTE** (Lippi et al., 2019; Drawzeski et al., 2021) — academic baseline for unfair contract clause detection in ToS. ClauseGuard extends CLAUDETTE's schema with three privacy-specific categories (`data_sharing`, `tracking_profiling`, `third_party_access`) not present in the original work.
- **PIPEDA / GDPR** — Canadian and EU privacy law frameworks defining what requires informed user consent
- Patterns observed across 21 real platform documents including legally significant cases

**CLAUDETTE project:** https://claudette.eui.eu/ — University of Bologna, European University Institute

---

## 👤 Author

<div align="center">

**Tanish Rathore**

*Security Researcher · Simon Fraser University · MSP Security Technician*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-2563eb?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/tanish-rathore)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-7c3aed?style=for-the-badge&logo=github&logoColor=white)](https://ogscriptkiddie.github.io/personal_portfolio/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-171717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ogscriptkiddie)

</div>

---

<div align="center">
<sub>Built with Python · Flask · spaCy · scikit-learn · Chrome Extensions API · Three.js · Hosted on Railway + Vercel</sub>
</div>
