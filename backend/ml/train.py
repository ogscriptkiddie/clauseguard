"""
ClauseGuard ML Training Pipeline
=================================
Run from backend/ml/ directory:
    python train.py

Trains TF-IDF + Logistic Regression with CalibratedClassifierCV (isotonic, cv=5).
Saves: model.pkl, label_encoder.pkl, results.json

Notes:
- Prefers clauseguard_dataset_v2.csv when present
- Uses GroupKFold when source_document is available to avoid document leakage
- Falls back to StratifiedKFold only when grouping metadata is unavailable
"""
import os
import sys
import json
import pickle

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.preprocessing import LabelEncoder


N_SPLITS = 5
RANDOM_STATE = 42


def find_dataset(script_dir: str) -> str:
    """
    Prefer the newer v2 dataset, but keep backward-compatible fallbacks.
    """
    dataset_candidates = [
        os.path.join(script_dir, "clauseguard_dataset_v2.csv"),
        os.path.join(script_dir, "..", "clauseguard_dataset_v2.csv"),
        os.path.join(script_dir, "..", "data", "clauseguard_dataset_v2.csv"),
        os.path.join(script_dir, "clauseguard_dataset.csv"),
        os.path.join(script_dir, "..", "clauseguard_dataset.csv"),
        os.path.join(script_dir, "..", "data", "clauseguard_dataset.csv"),
    ]

    dataset_path = next((p for p in dataset_candidates if os.path.exists(p)), None)
    if dataset_path is None:
        sys.exit(
            "ERROR: No dataset found. Expected clauseguard_dataset_v2.csv "
            "or clauseguard_dataset.csv in backend/ml/ or backend/."
        )
    return dataset_path


def validate_columns(df: pd.DataFrame) -> None:
    required = {"clause_text", "category"}
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"ERROR: Dataset is missing required columns: {sorted(missing)}")


def get_groups(df: pd.DataFrame):
    """
    Return grouping column if available and useful.
    """
    candidate_group_cols = ["source_document", "source_doc_id", "document_id"]
    for col in candidate_group_cols:
        if col in df.columns:
            groups = df[col].astype(str)
            if groups.nunique() >= N_SPLITS:
                return col, groups
    return None, None


def build_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=15000,
        sublinear_tf=True,
        min_df=1,
        strip_accents="unicode",
    )


def build_lr() -> LogisticRegression:
    return LogisticRegression(
        C=1.0,
        class_weight="balanced",
        solver="lbfgs",
        max_iter=1000,
    )


def get_top_features(model: LogisticRegression, tfidf: TfidfVectorizer, classes):
    fn = tfidf.get_feature_names_out()
    top_features = {}

    # multinomial / OvR coef shape: [n_classes, n_features]
    for i, cat in enumerate(classes):
        idx = np.argsort(model.coef_[i])[::-1][:10]
        top_features[cat] = [fn[j] for j in idx]

    return top_features


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = find_dataset(script_dir)

    print(f"Loading dataset from: {dataset_path}")
    df = pd.read_csv(dataset_path)
    validate_columns(df)

    group_col, groups = get_groups(df)
    if group_col:
        print(
            f"Loaded {len(df)} labeled clauses across "
            f"{df[group_col].nunique()} documents/groups using '{group_col}'"
        )
    else:
        print(f"Loaded {len(df)} labeled clauses (no document grouping column found)")

    X = df["clause_text"].astype(str).tolist()
    y = df["category"].astype(str).tolist()

    # Label encoding
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    print(f"Classes: {list(le.classes_)}")

    # Vectorize once for cross-validation and final training
    print("\nFitting TF-IDF vectorizer...")
    tfidf = build_vectorizer()
    X_tfidf = tfidf.fit_transform(X)
    print(f"Feature matrix: {X_tfidf.shape}")

    # Cross-validation
    cv_macro, cv_weighted = [], []

    if groups is not None:
        splitter = GroupKFold(n_splits=N_SPLITS)
        split_iter = splitter.split(X_tfidf, y_enc, groups=groups)
        cv_method = f"GroupKFold(n_splits={N_SPLITS}, group_col='{group_col}')"
        print(f"\nRunning {cv_method}...")
    else:
        splitter = StratifiedKFold(
            n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE
        )
        split_iter = splitter.split(X_tfidf, y_enc)
        cv_method = f"StratifiedKFold(n_splits={N_SPLITS}, shuffle=True, random_state={RANDOM_STATE})"
        print(f"\nRunning {cv_method}...")

    for fold, (tr, val) in enumerate(split_iter, start=1):
        lr = build_lr()
        lr.fit(X_tfidf[tr], y_enc[tr])
        pred = lr.predict(X_tfidf[val])

        mac = f1_score(y_enc[val], pred, average="macro")
        wt = f1_score(y_enc[val], pred, average="weighted")
        cv_macro.append(mac)
        cv_weighted.append(wt)

        print(f"  Fold {fold}: macro={mac:.4f}  weighted={wt:.4f}")

    cv_macro_mean = float(np.mean(cv_macro))
    cv_macro_std = float(np.std(cv_macro))
    cv_weighted_mean = float(np.mean(cv_weighted))
    cv_weighted_std = float(np.std(cv_weighted))

    print(f"\nCV F1 Macro    mean={cv_macro_mean:.4f}  std={cv_macro_std:.4f}")
    print(f"CV F1 Weighted mean={cv_weighted_mean:.4f}  std={cv_weighted_std:.4f}")

    # Train final calibrated model on all data
    print("\nTraining final calibrated model on full dataset...")
    final_lr = build_lr()
    calibrated = CalibratedClassifierCV(final_lr, method="isotonic", cv=5)
    calibrated.fit(X_tfidf, y_enc)

    # Full-dataset report (training-set performance only; not the real eval metric)
    y_full_pred = calibrated.predict(X_tfidf)
    full_report = classification_report(
        y_enc, y_full_pred, target_names=le.classes_, output_dict=True
    )
    full_dataset_f1_macro = float(full_report["macro avg"]["f1-score"])
    print(
        f"Full-dataset F1 macro: {full_dataset_f1_macro:.4f} "
        "(training-set metric only — not the real evaluation metric)"
    )

    # Top features per category
    plain_lr = build_lr()
    plain_lr.fit(X_tfidf, y_enc)
    top_features = get_top_features(plain_lr, tfidf, le.classes_)

    print("\nTop features per category:")
    for cat in le.classes_:
        print(f"  {cat}: {top_features[cat][:6]}")

    # Save artifacts
    with open(os.path.join(script_dir, "model.pkl"), "wb") as f:
        pickle.dump({"tfidf": tfidf, "classifier": calibrated}, f)

    with open(os.path.join(script_dir, "label_encoder.pkl"), "wb") as f:
        pickle.dump(le, f)

    results = {
        "dataset_path": os.path.basename(dataset_path),
        "cv_method": cv_method,
        "cv_f1_macro_mean": round(cv_macro_mean, 4),
        "cv_f1_macro_std": round(cv_macro_std, 4),
        "cv_f1_weighted_mean": round(cv_weighted_mean, 4),
        "cv_f1_weighted_std": round(cv_weighted_std, 4),
        "full_dataset_f1_macro": round(full_dataset_f1_macro, 4),
        "n_samples": int(len(df)),
        "n_classes": int(df["category"].nunique()),
        "n_folds": N_SPLITS,
        "group_column": group_col,
        "model": "TF-IDF(1-3gram,15k) + LogisticRegression(C=1,balanced) + CalibratedClassifierCV(isotonic,cv=5)",
        "top_features": top_features,
        "per_class_report": {
            k: {m: round(v, 4) for m, v in v2.items()}
            for k, v2 in full_report.items()
            if isinstance(v2, dict)
        },
        "category_counts": df["category"].value_counts().to_dict(),
    }

    with open(os.path.join(script_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 50}")
    print("  ✅ Saved: model.pkl, label_encoder.pkl, results.json")
    print(f"{'=' * 50}")
    print(f"  Dataset:        {results['dataset_path']}")
    print(f"  CV method:      {results['cv_method']}")
    print(f"  CV F1 Macro:    {results['cv_f1_macro_mean']:.4f} ± {results['cv_f1_macro_std']:.4f}")
    print(f"  CV F1 Weighted: {results['cv_f1_weighted_mean']:.4f} ± {results['cv_f1_weighted_std']:.4f}")
    print(f"  Training samples: {results['n_samples']}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()