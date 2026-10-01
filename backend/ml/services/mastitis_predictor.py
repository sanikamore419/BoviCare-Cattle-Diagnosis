"""
Mastitis specialist predictor (Model B).
Loads trained Pipeline (StandardScaler + RandomForest).
Returns binary mastitis prediction with probability.
Target labels from dataset: 0 = No Mastitis, 1 = Mastitis
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"

MODEL_VERSION = "bovicare-mastitis-v1"

LABEL_MAP = {0: "No Mastitis", 1: "Mastitis"}


@dataclass
class MastitisPredictionResult:
    model: str
    model_version: str
    condition: str
    probability: float
    risk_level: str


def _risk_from_probability(prob: float) -> str:
    """
    Indicative AI confidence risk band — NOT a clinical threshold.
      >= 0.70  -> high
      >= 0.40  -> moderate
      <  0.40  -> low
    """
    if prob >= 0.70:
        return "high"
    if prob >= 0.40:
        return "moderate"
    return "low"


class MastitisPredictor:
    def __init__(self) -> None:
        self._pipeline = None
        self._feature_cols: list[str] | None = None

    def _load(self) -> None:
        if self._pipeline is not None:
            return
        self._pipeline     = joblib.load(MODELS_DIR / "mastitis_model.joblib")
        self._feature_cols = joblib.load(MODELS_DIR / "mastitis_feature_cols.joblib")

    @property
    def feature_cols(self) -> list[str]:
        self._load()
        return self._feature_cols

    def predict(self, milk_data: dict) -> MastitisPredictionResult:
        """
        milk_data keys (all float/int):
          Milk_Temperature, Milk_pH, Milk_Conductivity,
          Somatic_Cell_Count, Milk_Yield, Clotting
        """
        self._load()
        x = np.array(
            [float(milk_data.get(col, 0.0)) for col in self._feature_cols],
            dtype=np.float64,
        ).reshape(1, -1)

        proba_positive = float(self._pipeline.predict_proba(x)[0][1])
        predicted_class = int(self._pipeline.predict(x)[0])
        condition = LABEL_MAP[predicted_class]

        return MastitisPredictionResult(
            model="mastitis_specialist",
            model_version=MODEL_VERSION,
            condition=condition,
            probability=round(proba_positive, 4),
            risk_level=_risk_from_probability(proba_positive),
        )

    def is_available(self) -> bool:
        try:
            self._load()
            return True
        except Exception:
            return False


mastitis_predictor = MastitisPredictor()
