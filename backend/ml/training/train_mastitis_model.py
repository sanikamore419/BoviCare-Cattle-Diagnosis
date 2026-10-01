"""
Model B — Mastitis Specialist Model
Dataset: https://www.kaggle.com/datasets/amithadityacp/cow-mastitisfrom-milk
File: cow_milk_mastitis_dataset.csv
800 rows, features: Milk_Temperature, Milk_pH, Milk_Conductivity,
                    Somatic_Cell_Count, Milk_Yield, Clotting
Target: class1 (binary: 0=no mastitis, 1=mastitis)
Class distribution: 631 negative (0), 169 positive (1)

Algorithm selection: Random Forest and Logistic Regression compared via 5-fold CV.
StandardScaler applied for Logistic Regression; not required for RF but included
in a Pipeline for consistent inference.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score, roc_auc_score
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODELS_DIR.mkdir(exist_ok=True)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "cow_milk_mastitis_dataset.csv"

FEATURE_COLS = [
    "Milk_Temperature", "Milk_pH", "Milk_Conductivity",
    "Somatic_Cell_Count", "Milk_Yield", "Clotting"
]
TARGET = "class1"
LABELS = {0: "No Mastitis", 1: "Mastitis"}


def main():
    print("=== Model B — Mastitis Specialist Training ===\n")

    # ── Load data ────────────────────────────────────────────────────────────
    if not DATA_PATH.exists():
        print(f"ERROR: Dataset not found at {DATA_PATH}")
        print("Download from https://www.kaggle.com/datasets/amithadityacp/cow-mastitisfrom-milk")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"Shape: {df.shape}")
    print(f"Features: {FEATURE_COLS}")
    print(f"Target: {TARGET}")
    print(f"Class distribution:\n{df[TARGET].value_counts().to_string()}")
    print(f"Missing values: {df[FEATURE_COLS + [TARGET]].isnull().sum().sum()}")

    X = df[FEATURE_COLS].values.astype(np.float64)
    y = df[TARGET].values.astype(np.int32)

    # ── Train/test split (stratified) ────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain: {len(X_train)}  Test: {len(X_test)}")

    # ── Algorithm comparison via 5-fold stratified CV ────────────────────────
    print("\n--- Algorithm comparison (5-fold stratified CV, macro F1) ---")
    candidates = {
        "RandomForest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1,
                                           class_weight="balanced")),
        ]),
        "LogisticRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=42,
                                       class_weight="balanced")),
        ]),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    best_name, best_score, best_pipeline = None, -1, None
    for name, pipe in candidates.items():
        scores = cross_val_score(pipe, X_train, y_train, cv=cv,
                                 scoring="f1_macro", n_jobs=-1)
        mean_f1 = scores.mean()
        print(f"  {name:22s}  macro-F1 = {mean_f1:.4f}  (std={scores.std():.4f})")
        if mean_f1 > best_score:
            best_score, best_name, best_pipeline = mean_f1, name, pipe

    print(f"\nSelected: {best_name} (CV macro-F1 = {best_score:.4f})")

    # ── Train final model on full training split ─────────────────────────────
    print("\nTraining final model on training split...")
    best_pipeline.fit(X_train, y_train)

    # ── Evaluate on held-out test split ──────────────────────────────────────
    y_pred      = best_pipeline.predict(X_test)
    y_prob      = best_pipeline.predict_proba(X_test)[:, 1]
    acc         = accuracy_score(y_test, y_pred)
    macro_f1    = f1_score(y_test, y_pred, average="macro")
    roc_auc     = roc_auc_score(y_test, y_prob)

    print(f"\n=== Test-set evaluation ({len(y_test)} samples) ===")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Macro F1:  {macro_f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print("\nPer-class report:")
    print(classification_report(y_test, y_pred,
                                 target_names=["No Mastitis", "Mastitis"]))

    # ── Save artifacts ───────────────────────────────────────────────────────
    joblib.dump(best_pipeline, MODELS_DIR / "mastitis_model.joblib")
    joblib.dump(FEATURE_COLS,  MODELS_DIR / "mastitis_feature_cols.joblib")

    print(f"\nArtifacts saved to {MODELS_DIR}/")
    print("  mastitis_model.joblib  (includes scaler + classifier)")
    print("  mastitis_feature_cols.joblib")
    print("\nModel B training complete.")


if __name__ == "__main__":
    main()
