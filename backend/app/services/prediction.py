from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from ml_model.predictor import CattleDiseasePredictor, PredictionResult


class PredictionService:
    def __init__(self) -> None:
        self.predictor = CattleDiseasePredictor()

    def assess(self, symptoms: list[str], temperature_c: float | None) -> PredictionResult:
        return self.predictor.predict(symptoms, temperature_c)


prediction_service = PredictionService()
