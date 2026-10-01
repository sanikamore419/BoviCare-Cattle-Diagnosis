from pydantic import BaseModel, Field, model_validator
from typing import Optional


class MilkData(BaseModel):
    Milk_Temperature: float = Field(ge=30.0, le=45.0)
    Milk_pH: float = Field(ge=5.0, le=9.0)
    Milk_Conductivity: float = Field(ge=0.0)
    Somatic_Cell_Count: float = Field(ge=0.0)
    Milk_Yield: float = Field(ge=0.0)
    Clotting: int = Field(ge=0, le=1)


class PredictionRequest(BaseModel):
    cattle_id: Optional[int] = None
    case_id: Optional[int] = None
    symptoms: Optional[list[str]] = None
    milk_data: Optional[MilkData] = None

    @model_validator(mode="after")
    def at_least_one_input(self):
        if not self.symptoms and not self.milk_data:
            raise ValueError("Provide at least one of 'symptoms' or 'milk_data'.")
        return self


class DiseasePredictionOut(BaseModel):
    rank: int
    disease: str
    probability: float


class GeneralResultOut(BaseModel):
    model: str
    model_version: str
    predictions: list[DiseasePredictionOut]
    risk_level: str


class MastitisResultOut(BaseModel):
    model: str
    model_version: str
    condition: str
    probability: float
    risk_level: str


class PredictionResponse(BaseModel):
    cattle_id: Optional[int]
    models_used: list[str]
    combined_risk_level: str
    general: Optional[GeneralResultOut] = None
    mastitis: Optional[MastitisResultOut] = None
    disclaimer: str = (
        "AI-assisted decision support only. "
        "Model confidence does not equal clinical disease probability. "
        "Consult a qualified veterinarian before treatment."
    )


class ImagePredictionOut(BaseModel):
    rank: int
    label: str
    probability: float


class ImagePredictionResponse(BaseModel):
    cattle_id: Optional[int]
    model: str
    model_version: str
    top_label: str
    top_probability: float
    risk_level: str
    predictions: list[ImagePredictionOut]
    disclaimer: str = (
        "AI image analysis is provided for decision support only. "
        "A qualified veterinarian should confirm the condition."
    )


# ── Case predictions endpoint schemas ────────────────────────────────────────

class CasePredictionRow(BaseModel):
    rank: Optional[int]
    disease_label: str
    probability: float


class CaseModelResult(BaseModel):
    model_name: str
    model_version: str
    risk_level: str
    predictions: list[CasePredictionRow]


class CasePredictionsResponse(BaseModel):
    case_id: int
    models: list[CaseModelResult]
