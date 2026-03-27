# ClauseGuard

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
