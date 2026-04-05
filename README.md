<div align="center">

# 🛡️ ClauseGuard

<img src="https://img.shields.io/badge/Status-Active%20Development-22c55e?style=for-the-badge&logo=checkmarx&logoColor=white"/>
<img src="https://img.shields.io/badge/Python-3.13+-3b82f6?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Chrome-Extension-f97316?style=for-the-badge&logo=googlechrome&logoColor=white"/>
<img src="https://img.shields.io/badge/Backend-Live%20on%20Railway-7c3aed?style=for-the-badge&logo=railway&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-a855f7?style=for-the-badge"/>

<br/>
<br/>

**Automated Detection and Risk Classification of Security & Privacy Clauses in Web Agreements**

*A browser-integrated system that reads Terms of Service and Privacy Policies in real time, helping users spot clauses that may affect privacy, liability, dispute resolution, and data rights before clicking “I Agree.”*

<br/>

[![Dataset](https://img.shields.io/badge/Dataset-754%20Labeled%20Clauses-2563eb?style=flat-square)](data/annotated/)
[![Categories](https://img.shields.io/badge/Risk%20Categories-7-16a34a?style=flat-square)](backend/categories.py)
[![Documents](https://img.shields.io/badge/Documents-21%20Processed-0891b2?style=flat-square)](data/raw/)
[![API](https://img.shields.io/badge/API-Live-22c55e?style=flat-square)](https://clauseguard-production-183f.up.railway.app/health)
[![Demo](https://img.shields.io/badge/Demo-Live-22c55e?style=flat-square)](https://clauseguard-chi.vercel.app)
[![SFU](https://img.shields.io/badge/Simon%20Fraser%20University-Cybersecurity%20Lab%20II-dc2626?style=flat-square)](https://www.sfu.ca/)

</div>

---

## 🌐 Live Deployment

| Service | URL | Status |
|---|---|---|
| **Backend API** | `https://clauseguard-production-183f.up.railway.app` | 🟢 Live |
| **Health Check** | [`/health`](https://clauseguard-production-183f.up.railway.app/health) | 🟢 Online |
| **Web Demo** | [`clauseguard-chi.vercel.app`](https://clauseguard-chi.vercel.app) | 🟢 Live |
| **Analyze Endpoint** | `POST /analyze` | 🟢 Ready |
| **PDF Upload Endpoint** | `POST /upload-pdf` | 🟢 Ready |

---

## 📖 Why This Exists

Most users do not read Terms of Service or Privacy Policies in full, even though those documents often define how their data is shared, how disputes are handled, and how much liability a company accepts.

ClauseGuard was built to turn long legal documents into a faster, more understandable risk view by:
- detecting potentially important clauses
- assigning risk labels
- surfacing the original text
- giving a plain-English summary of why the clause matters

Examples of what it looks for include:
- third-party data sharing
- arbitration and class action waiver language
- liability limitation clauses
- broad content licenses
- tracking and profiling language
- long-term or indefinite data retention

---

## ⚙️ How It Works

```text
User opens a Terms of Service or Privacy Policy page
        ↓
Chrome extension detects likely policy/legal pages
        ↓
Text is sent to the hosted Flask backend
        ↓
Document is segmented into clauses
        ↓
Hybrid classification runs:
  - ML classifier predicts a likely clause label
  - Rule-based logic acts as fallback / support
        ↓
Evidence-aware risk scoring is applied
        ↓
Clause summaries and risk cards are returned
        ↓
Extension popup or web demo displays the results