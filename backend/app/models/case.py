from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base
from app.models.status import CASE_STATUS_CHECK, CaseStatus


class ClinicalCase(Base):
    __tablename__ = "clinical_cases"
    __table_args__ = (
        CheckConstraint(CASE_STATUS_CHECK, name="ck_clinical_cases_status_allowed"),
        Index("ix_clinical_cases_status", "status"),
        Index("ix_clinical_cases_claimed_by", "claimed_by"),
        Index("ix_clinical_cases_urgency_level_score", "urgency_level", "urgency_score"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    cattle_id: Mapped[int | None] = mapped_column(ForeignKey("cattle.id"), nullable=True, index=True)
    cattle_tag: Mapped[str] = mapped_column(String(80), index=True)
    breed: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    symptoms: Mapped[str] = mapped_column(Text)
    ai_prediction: Mapped[str] = mapped_column(String(255))
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    status: Mapped[str] = mapped_column(String(30), default=CaseStatus.SUBMITTED.value, server_default=text("'submitted'"))
    urgency_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    urgency_level: Mapped[str | None] = mapped_column(String(20), nullable=True, default="LOW")
    urgency_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    claimed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    veterinarian_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    farmer_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    veterinarian_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
