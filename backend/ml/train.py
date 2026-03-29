"""
ClauseGuard ML Training Pipeline
=================================
Run from backend/ml/ directory:
    python train.py

Trains TF-IDF + Logistic Regression with CalibratedClassifierCV (isotonic, cv=5).
Saves: model.pkl, label_encoder.pkl, results.json
"""
import os, sys, json, pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, classification_report

# ── Locate dataset ────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_CANDIDATES = [
    os.path.join(SCRIPT_DIR, "clauseguard_dataset.csv"),
    os.path.join(SCRIPT_DIR, "..", "clauseguard_dataset.csv"),
    os.path.join(SCRIPT_DIR, "..", "data", "clauseguard_dataset.csv"),
]
DATASET_PATH = next((p for p in DATASET_CANDIDATES if os.path.exists(p)), None)
if DATASET_PATH is None:
    sys.exit("ERROR: clauseguard_dataset.csv not found. Place it in backend/ml/ or backend/.")

print(f"Loading dataset from: {DATASET_PATH}")
df = pd.read_csv(DATASET_PATH)
print(f"Loaded {len(df)} labeled clauses across {df['source_document'].nunique()} documents")

X = df["clause_text"].astype(str).tolist()
y = df["category"].tolist()

# ── Label encoding ─────────────────────────────────────────────────────────────
le = LabelEncoder()
y_enc = le.fit_transform(y)
print(f"Classes: {list(le.classes_)}")

# ── Vectorize ──────────────────────────────────────────────────────────────────
print("\nFitting TF-IDF vectorizer...")
tfidf = TfidfVectorizer(
    ngram_range=(1, 3),
    max_features=15000,
    sublinear_tf=True,
    min_df=1,
    strip_accents="unicode",
)
X_tfidf = tfidf.fit_transform(X)
print(f"Feature matrix: {X_tfidf.shape}")

# ── 5-fold stratified cross-validation ────────────────────────────────────────
print("\nRunning 5-fold stratified cross-validation...")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_macro, cv_weighted = [], []

for fold, (tr, val) in enumerate(skf.split(X_tfidf, y_enc)):
    lr = LogisticRegression(C=1.0, class_weight="balanced",
                            solver="lbfgs", max_iter=1000)
    lr.fit(X_tfidf[tr], y_enc[tr])
    pred = lr.predict(X_tfidf[val])
    mac = f1_score(y_enc[val], pred, average="macro")
    wt  = f1_score(y_enc[val], pred, average="weighted")
    cv_macro.append(mac)
    cv_weighted.append(wt)
    print(f"  Fold {fold+1}: macro={mac:.4f}  weighted={wt:.4f}")

print(f"\nCV F1 Macro    mean={np.mean(cv_macro):.4f}  std={np.std(cv_macro):.4f}")
print(f"CV F1 Weighted mean={np.mean(cv_weighted):.4f}  std={np.std(cv_weighted):.4f}")

# ── Train final calibrated model on ALL data ───────────────────────────────────
print("\nTraining final calibrated model on full dataset...")
final_lr = LogisticRegression(C=1.0, class_weight="balanced",
                               solver="lbfgs", max_iter=1000)
calibrated = CalibratedClassifierCV(final_lr, method="isotonic", cv=5)
calibrated.fit(X_tfidf, y_enc)

# Full-dataset report (train == test — shows memorization, expected at 312 samples)
y_full_pred = calibrated.predict(X_tfidf)
full_report = classification_report(
    y_enc, y_full_pred, target_names=le.classes_, output_dict=True
)
print(f"Full-dataset F1 macro: {full_report['macro avg']['f1-score']:.4f} (memorized — not the real metric)")

# ── Top features per category ──────────────────────────────────────────────────
plain_lr = LogisticRegression(C=1.0, class_weight="balanced",
                               solver="lbfgs", max_iter=1000)
plain_lr.fit(X_tfidf, y_enc)
fn = tfidf.get_feature_names_out()
top_features = {}
print("\nTop features per category:")
for i, cat in enumerate(le.classes_):
    idx = np.argsort(plain_lr.coef_[i])[::-1][:10]
    top_features[cat] = [fn[j] for j in idx]
    print(f"  {cat}: {top_features[cat][:6]}")

# ── Save artifacts ─────────────────────────────────────────────────────────────
with open(os.path.join(SCRIPT_DIR, "model.pkl"), "wb") as f:
    pickle.dump({"tfidf": tfidf, "classifier": calibrated}, f)

with open(os.path.join(SCRIPT_DIR, "label_encoder.pkl"), "wb") as f:
    pickle.dump(le, f)

results = {
    "cv_f1_macro_mean":      round(float(np.mean(cv_macro)), 4),
    "cv_f1_macro_std":       round(float(np.std(cv_macro)), 4),
    "cv_f1_weighted_mean":   round(float(np.mean(cv_weighted)), 4),
    "cv_f1_weighted_std":    round(float(np.std(cv_weighted)), 4),
    "full_dataset_f1_macro": round(full_report["macro avg"]["f1-score"], 4),
    "n_samples":  len(df),
    "n_classes":  int(df["category"].nunique()),
    "n_folds":    5,
    "model":      "TF-IDF(1-3gram,15k) + LogisticRegression(C=1,balanced) + CalibratedClassifierCV(isotonic,cv=5)",
    "top_features":     top_features,
    "per_class_report": {
        k: {m: round(v, 4) for m, v in v2.items()}
        for k, v2 in full_report.items() if isinstance(v2, dict)
    },
    "category_counts": df["category"].value_counts().to_dict(),
}
with open(os.path.join(SCRIPT_DIR, "results.json"), "w") as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*50}")
print(f"  ✅ Saved: model.pkl, label_encoder.pkl, results.json")
print(f"{'='*50}")
print(f"  CV F1 Macro:    {results['cv_f1_macro_mean']:.4f} ± {results['cv_f1_macro_std']:.4f}")
print(f"  CV F1 Weighted: {results['cv_f1_weighted_mean']:.4f} ± {results['cv_f1_weighted_std']:.4f}")
print(f"  Training samples: {results['n_samples']}")
print(f"{'='*50}")
