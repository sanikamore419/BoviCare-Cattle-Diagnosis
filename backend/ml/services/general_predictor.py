"""
General cattle disease predictor (Model A).
Loads trained Random Forest + LabelEncoder + feature list.
Returns top-5 ranked disease predictions with probabilities.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"

MODEL_VERSION = "bovicare-general-v1"


@dataclass
class DiseasePrediction:
    rank: int
    disease: str
    probability: float


@dataclass
class GeneralPredictionResult:
    model: str
    model_version: str
    predictions: list[DiseasePrediction]
    risk_level: str


def _risk_from_top_probability(prob: float) -> str:
    """
    Indicative AI confidence risk band — NOT a clinical threshold.
    Defined transparently:
      >= 0.70  -> high    (model strongly associates symptoms with one disease)
      >= 0.40  -> moderate
      <  0.40  -> low     (probability spread across many classes)
    These bands reflect model confidence only and require veterinary validation.
    """
    if prob >= 0.70:
        return "high"
    if prob >= 0.40:
        return "moderate"
    return "low"


class GeneralPredictor:
    def __init__(self) -> None:
        self._model = None
        self._le = None
        self._feature_cols: Optional[list[str]] = None

    def _load(self) -> None:
        if self._model is not None:
            return
        self._model        = joblib.load(MODELS_DIR / "general_model.joblib")
        self._le           = joblib.load(MODELS_DIR / "general_label_encoder.joblib")
        self._feature_cols = joblib.load(MODELS_DIR / "general_feature_cols.joblib")

    @property
    def feature_cols(self) -> list[str]:
        self._load()
        return self._feature_cols

    def predict(self, symptoms: list[str]) -> GeneralPredictionResult:
        """
        symptoms: list of symptom name strings matching the dataset feature columns.
        Unknown symptom names are silently ignored (treated as 0).
        """
        self._load()

        # Build binary feature vector
        symptom_set = {s.lower().strip().replace(" ", "_") for s in symptoms}
        x = np.array(
            [1 if col.lower() in symptom_set else 0 for col in self._feature_cols],
            dtype=np.int8,
        ).reshape(1, -1)

        proba = self._model.predict_proba(x)[0]
        classes = self._le.classes_

        # Sort by probability descending, take top 5
        top_indices = np.argsort(proba)[::-1][:5]
        predictions = [
            DiseasePrediction(
                rank=rank + 1,
                disease=classes[i],
                probability=round(float(proba[i]), 4),
            )
            for rank, i in enumerate(top_indices)
            if proba[i] > 0.0
        ]

        top_prob = predictions[0].probability if predictions else 0.0
        return GeneralPredictionResult(
            model="general_cattle_disease",
            model_version=MODEL_VERSION,
            predictions=predictions,
            risk_level=_risk_from_top_probability(top_prob),
        )

    def is_available(self) -> bool:
        try:
            self._load()
            return True
        except Exception:
            return False


general_predictor = GeneralPredictor()
