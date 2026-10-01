"""
Model A — General Cattle Disease Model
Dataset: https://github.com/thyagarajank/Cattle-disease-prediction-using-Machine-Learning
Training.csv: 2044 rows, 93 binary symptom features, 26 disease classes, target=prognosis
Testing.csv:  26 rows (one per class)

Algorithm selection: Random Forest chosen after comparing RF, Logistic Regression, and
Gradient Boosting on stratified 5-fold CV. RF handles binary feature matrices well,
supports predict_proba natively, and is robust to the mild class imbalance present.
"""
import io, sys, urllib.request
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODELS_DIR.mkdir(exist_ok=True)

TRAIN_URL = "https://raw.githubusercontent.com/thyagarajank/Cattle-disease-prediction-using-Machine-Learning/main/Training.csv"
TEST_URL  = "https://raw.githubusercontent.com/thyagarajank/Cattle-disease-prediction-using-Machine-Learning/main/Testing.csv"


def fetch_csv(url: str) -> pd.DataFrame:
    req = urllib.request.Request(url, headers={"User-Agent": "BoviCare/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return pd.read_csv(io.StringIO(r.read().decode("utf-8")))


def main():
    print("=== Model A — General Cattle Disease Training ===\n")

    # ── Load data ────────────────────────────────────────────────────────────
    print("Loading Training.csv...")
    df_train = fetch_csv(TRAIN_URL)
    print(f"Training shape: {df_train.shape}")

    print("Loading Testing.csv...")
    df_test = fetch_csv(TEST_URL)
    print(f"Testing shape:  {df_test.shape}")

    TARGET = "prognosis"
    feature_cols = [c for c in df_train.columns if c != TARGET]

    X_train = df_train[feature_cols].values.astype(np.int8)
    y_train_raw = df_train[TARGET].str.strip().values

    X_test  = df_test[feature_cols].values.astype(np.int8)
    y_test_raw  = df_test[TARGET].str.strip().values

    # ── Label encoding ───────────────────────────────────────────────────────
    le = LabelEncoder()
    le.fit(y_train_raw)
    y_train = le.transform(y_train_raw)
    y_test  = le.transform(y_test_raw)

    print(f"\nFeatures: {len(feature_cols)}")
    print(f"Classes ({len(le.classes_)}): {list(le.classes_)}")

    # ── Algorithm comparison via 5-fold stratified CV ────────────────────────
    print("\n--- Algorithm comparison (5-fold stratified CV, macro F1) ---")
    candidates = {
        "RandomForest":       RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1),
        "GradientBoosting":   GradientBoostingClassifier(n_estimators=100, random_state=42),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    best_name, best_score, best_clf = None, -1, None
    for name, clf in candidates.items():
        scores = cross_val_score(clf, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=-1)
        mean_f1 = scores.mean()
        print(f"  {name:22s}  macro-F1 = {mean_f1:.4f}  (std={scores.std():.4f})")
        if mean_f1 > best_score:
            best_score, best_name, best_clf = mean_f1, name, clf

    print(f"\nSelected: {best_name} (CV macro-F1 = {best_score:.4f})")

    # ── Train final model on full training set ───────────────────────────────
    print("\nTraining final model on full training set...")
    best_clf.fit(X_train, y_train)

    # ── Evaluate on held-out test set ────────────────────────────────────────
    y_pred = best_clf.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")

    print(f"\n=== Test-set evaluation ({len(y_test)} samples) ===")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Macro F1:  {macro_f1:.4f}")
    print("\nPer-class report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    # ── Save artifacts ───────────────────────────────────────────────────────
    joblib.dump(best_clf,      MODELS_DIR / "general_model.joblib")
    joblib.dump(le,            MODELS_DIR / "general_label_encoder.joblib")
    joblib.dump(feature_cols,  MODELS_DIR / "general_feature_cols.joblib")

    print(f"\nArtifacts saved to {MODELS_DIR}/")
    print("  general_model.joblib")
    print("  general_label_encoder.joblib")
    print("  general_feature_cols.joblib")
    print("\nModel A training complete.")


if __name__ == "__main__":
    main()
