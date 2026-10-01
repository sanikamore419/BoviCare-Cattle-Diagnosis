"""A replaceable model interface; no trained-model performance is implied."""

from dataclasses import dataclass


@dataclass
class PredictionResult:
    label: str
    risk_level: str
    confidence: float | None
    note: str


class CattleDiseasePredictor:
    def predict(self, symptoms: list[str], temperature_c: float | None = None) -> PredictionResult:
        """Return preliminary, rule-based triage until a validated model is integrated."""
        urgent = {"difficulty breathing", "cannot stand", "seizure", "severe bleeding"}
        normalized = {symptom.lower().strip() for symptom in symptoms}
        if urgent & normalized or (temperature_c is not None and temperature_c >= 40.5):
            return PredictionResult("Urgent clinical review needed", "high", None, "Preliminary triage only; contact a veterinarian promptly.")
        return PredictionResult("Veterinary assessment recommended", "medium", None, "No trained ML model is connected yet.")
