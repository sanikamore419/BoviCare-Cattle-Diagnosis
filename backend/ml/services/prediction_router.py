"""
Prediction routing layer.
Scenario A: symptoms only       -> Model A (general disease)
Scenario B: milk_data only      -> Model B (mastitis specialist)
Scenario C: both available      -> both models independently
Scenario D: neither             -> validation error

Models are never combined into a single score.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ml.services.general_predictor import GeneralPredictionResult, general_predictor
from ml.services.mastitis_predictor import MastitisPredictionResult, mastitis_predictor


@dataclass
class RoutedPrediction:
    general: Optional[GeneralPredictionResult] = None
    mastitis: Optional[MastitisPredictionResult] = None
    # Combined risk: highest of the two individual risk levels
    combined_risk_level: str = "low"
    models_used: list[str] = field(default_factory=list)


_RISK_ORDER = {"low": 0, "moderate": 1, "medium": 1, "high": 2}


def _max_risk(*levels: str) -> str:
    ranked = sorted(levels, key=lambda r: _RISK_ORDER.get(r, 0), reverse=True)
    return ranked[0] if ranked else "low"


def route_prediction(
    symptoms: list[str] | None,
    milk_data: dict | None,
) -> RoutedPrediction:
    has_symptoms  = bool(symptoms)
    has_milk_data = bool(milk_data)

    if not has_symptoms and not has_milk_data:
        raise ValueError("At least one of 'symptoms' or 'milk_data' must be provided.")

    result = RoutedPrediction()
    risk_levels: list[str] = []

    if has_symptoms:
        if not general_predictor.is_available():
            raise RuntimeError("General disease model is not available. Run train_general_model.py first.")
        result.general = general_predictor.predict(symptoms)
        result.models_used.append("general_cattle_disease")
        risk_levels.append(result.general.risk_level)

    if has_milk_data:
        if not mastitis_predictor.is_available():
            raise RuntimeError("Mastitis model is not available. Run train_mastitis_model.py first.")
        result.mastitis = mastitis_predictor.predict(milk_data)
        result.models_used.append("mastitis_specialist")
        risk_levels.append(result.mastitis.risk_level)

    result.combined_risk_level = _max_risk(*risk_levels)
    return result
