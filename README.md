<div align="center">

# 🛡️ ClauseGuard

<img src="https://img.shields.io/badge/Status-Phase%202%20Complete-22c55e?style=for-the-badge&logo=checkmarx&logoColor=white"/>
<img src="https://img.shields.io/badge/Python-3.10+-3b82f6?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Chrome-Extension-f97316?style=for-the-badge&logo=googlechrome&logoColor=white"/>
<img src="https://img.shields.io/badge/Flask-Backend-64748b?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-a855f7?style=for-the-badge"/>

<br/>
<br/>

**Automated Detection and Risk Classification of Security & Privacy Clauses in Web Agreements**

*A browser-integrated system that reads Terms of Service and Privacy Policies in real time —
flagging the risks ordinary users never see before clicking "I Agree."*

<br/>

[![Dataset](https://img.shields.io/badge/Dataset-214%20Labeled%20Clauses-2563eb?style=flat-square)](data/annotated/)
[![Rules](https://img.shields.io/badge/Classifier-757%20Rules-7c3aed?style=flat-square)](backend/categories.py)
[![Documents](https://img.shields.io/badge/Documents-12%20Processed-0891b2?style=flat-square)](data/raw/)
[![Categories](https://img.shields.io/badge/Risk%20Categories-7-16a34a?style=flat-square)](backend/categories.py)
[![SFU](https://img.shields.io/badge/Simon%20Fraser%20University-Capstone-dc2626?style=flat-square)](https://www.sfu.ca/)

</div>

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
│         Flask API receives the full document text           │
│                           │                                 │
│       spaCy Segmenter splits it into legal clauses          │
│                           │                                 │
│      ┌────────────────────┴────────────────────┐            │
│      │         Risk Classification Engine       │            │
│      │   757 rules · 7 categories · negation   │            │
│      └────────────────────┬────────────────────┘            │
│                           │                                 │
│        Weighted Risk Score (0–100) computed                 │
│                           │                                 │
│    Plain-English risk cards shown in extension popup        │
└─────────────────────────────────────────────────────────────┘
```

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
| ![Flask](https://img.shields.io/badge/-Flask%20API-64748b?style=flat-square&logo=flask&logoColor=white) | Python · Flask | REST backend — `/analyze` endpoint |
| ![spaCy](https://img.shields.io/badge/-spaCy-09a3d5?style=flat-square) | spaCy NLP | Document → legal clause segmentation |
| ![Rules](https://img.shields.io/badge/-Rule%20Engine-7c3aed?style=flat-square) | Custom Python | 757-rule keyword classifier with negation detection |
| ![ML](https://img.shields.io/badge/-ML%20Classifier-2563eb?style=flat-square&logo=scikitlearn&logoColor=white) | scikit-learn | TF-IDF + Logistic Regression *(Phase 3)* |
| ![Dataset](https://img.shields.io/badge/-Dataset-16a34a?style=flat-square) | CSV + Python | 214 human-labeled clauses across 12 real documents |

</div>

---

## 📊 Project Status

<div align="center">

| Phase | Status | Description |
|---|:---:|---|
| **Phase 1** · Backend Engine | ✅ **Complete** | Flask API, spaCy segmenter, rule-based classifier (757 rules), risk scorer |
| **Phase 2** · Extension + Dataset | ✅ **Complete** | MV3 extension, popup UI, badge alerts, SPA detection, 214-clause annotated dataset |
| **Phase 3** · ML Classifier | 🔄 **In Progress** | scikit-learn model, hybrid pipeline, inter-rater reliability check |
| **Phase 4** · Evaluation | 🔜 **Planned** | F1 / precision / recall vs. rule-based baseline, user study (n = 10) |

</div>

---

## 🚀 Local Setup

### Prerequisites

Make sure you have the following installed:

- <kbd>Python 3.10+</kbd> — [python.org](https://www.python.org/downloads/)
- <kbd>Git</kbd> — [git-scm.com](https://git-scm.com/)
- <kbd>Google Chrome</kbd>

---

### Step 1 — Clone the repository

Open **Git Bash** and run:

```bash
git clone https://github.com/ogscriptkiddie/clauseguard.git
cd clauseguard
```

---

### Step 2 — Set up a virtual environment

```bash
cd backend
python -m venv venv
source venv/Scripts/activate      # Git Bash on Windows
# If that fails, try:
# source venv/bin/activate        # macOS / Linux
```

You should see `(venv)` appear at the start of your prompt.

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

### Step 4 — Start the Flask backend

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Leave this terminal running.

---

### Step 5 — Load the Chrome Extension

1. Open **Chrome** and go to <kbd>chrome://extensions</kbd>
2. Toggle **Developer mode** ON (switch in the top-right corner)
3. Click **Load unpacked**
4. Navigate to your cloned folder and select the **`extension/`** directory
5. The ClauseGuard shield icon 🛡️ appears in your Chrome toolbar

---

### Step 6 — Test it

Navigate to any Terms of Service or Privacy Policy page, for example:

```
https://www.spotify.com/us/legal/end-user-agreement/
https://discord.com/privacy
https://policies.google.com/terms
```

- The **red `!` badge** fires on the icon when a document is detected
- Click the icon to open the **risk card popup**
- Press **Scan This Page** to analyze the document

---

<details>
<summary><b>🐛 Troubleshooting</b></summary>

<br/>

**Backend not running / extension shows no results**
```bash
# Make sure the virtual environment is active and backend is running
cd clauseguard/backend
source venv/Scripts/activate
python app.py
```

**spaCy model missing**
```bash
python -m spacy download en_core_web_sm
```

**Extension not detecting the page**
- Hard-refresh the page after loading the extension (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>)
- Make sure the URL contains ToS-related keywords (terms, privacy, legal, conditions)

**Port conflict on 5000**
```bash
# Run on a different port
python app.py --port 5001
# Then update the API URL in popup.js to match
```

</details>

<details>
<summary><b>🔄 Updating the extension after code changes</b></summary>

<br/>

After modifying any JavaScript files in `extension/`:

1. Go to <kbd>chrome://extensions</kbd>
2. Find ClauseGuard and click the **refresh icon** ↻
3. Hard-refresh the page you're testing on

After modifying Python backend files, restart the Flask server:
```bash
# Ctrl+C to stop, then:
python app.py
```

</details>

---

## 📁 Repository Structure

```
clauseguard/
│
├── 📂 backend/
│   ├── app.py              ← Flask API  (/health + /analyze endpoints)
│   ├── categories.py       ← 7 risk categories + 757 keyword rules
│   ├── segmenter.py        ← Document → clause segmentation (spaCy)
│   ├── classifier.py       ← Rule-based classifier with negation detection
│   ├── scorer.py           ← Weighted 0–100 risk scoring engine
│   └── requirements.txt
│
├── 📂 extension/
│   ├── manifest.json       ← Manifest V3 configuration
│   ├── content.js          ← ToS detection (4-signal + MutationObserver)
│   ├── background.js       ← Service worker · badge state
│   ├── popup.html          ← Extension popup UI
│   ├── popup.js            ← Risk card rendering + progressive disclosure
│   └── icons/              ← 16px / 48px / 128px extension icons
│
├── 📂 data/
│   ├── raw/                ← Plain-text ToS + Privacy Policy documents
│   └── annotated/          ← Hand-labeled clause CSVs with justification notes
│
├── 📂 ml/                  ← ML Classifier (Phase 3)
├── 📂 evaluation/          ← Evaluation results + metrics (Phase 4)
└── README.md
```

---

## 📚 Dataset

The annotation dataset covers **12 documents** from major platforms across two document types:

<div align="center">

| Privacy Policies | Terms of Service |
|---|---|
| Meta · Uber · Discord · Reddit | Spotify · Amazon · LinkedIn |
| Spotify · Apple | Apple · Microsoft · Google |

**214 human-labeled clauses** · written justification on every label · 7 risk categories

</div>

> ⚠️ **TikTok ToS** was planned for Phase 2 but the official URL returned a 404 error at collection time.
> It will be processed in Phase 3 to strengthen the arbitration and content-rights categories.

---

## 🎓 Background

Built as a **capstone security research project** at **Simon Fraser University**.

ClauseGuard sits at the intersection of NLP, cybersecurity risk modeling, and privacy rights — treating legal document analysis as a **defensive security problem** rather than a legal one. The goal is to surface the risks that ordinary users agree to every day without realising it.

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
<sub>Built with Python · Flask · spaCy · Chrome Extensions API · scikit-learn</sub>
</div>
