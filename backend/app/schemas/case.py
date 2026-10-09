from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    cattle_tag: str = Field(min_length=1, max_length=80)
    cattle_id: int | None = None
    cattle_name: str | None = Field(default=None, max_length=120)
    breed: str | None = None
    gender: str | None = Field(default=None, max_length=20)
    age_years: float | None = Field(default=None, ge=0, le=40)
    temperature_c: float | None = Field(default=None, ge=30, le=45)
    symptoms: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=5000)


class CaseRead(BaseModel):
    id: int
    cattle_id: int | None
    cattle_tag: str
    cattle_name: str | None = None
    breed: str | None
    gender: str | None = None
    age_years: float | None
    temperature_c: float | None
    symptoms: list[str]
    notes: str | None = None
    ai_prediction: str
    risk_level: str
    status: str
    workflow_status: str | None = None
    urgency_score: float | None = None
    urgency_level: str | None = None
    veterinarian_id: int | None = None
    veterinarian_notes: str | None = None
    farmer_advice: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class CaseReview(BaseModel):
    veterinarian_notes: str | None = Field(default=None, max_length=3000)
    private_clinical_notes: str | None = Field(default=None, max_length=3000)
    farmer_advice: str | None = Field(default=None, min_length=1, max_length=3000)
    review_status: Literal["submitted", "ai_complete", "pending_review", "in_review", "completed", "pending", "reviewed", "in_progress"] = "completed"
