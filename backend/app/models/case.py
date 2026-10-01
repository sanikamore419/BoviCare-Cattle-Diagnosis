from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class ClinicalCase(Base):
    __tablename__ = "clinical_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    cattle_id: Mapped[int | None] = mapped_column(ForeignKey("cattle.id"), nullable=True, index=True)
    cattle_tag: Mapped[str] = mapped_column(String(80), index=True)
    breed: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    symptoms: Mapped[str] = mapped_column(Text)
    ai_prediction: Mapped[str] = mapped_column(String(255))
    risk_level: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="pending_review")
    veterinarian_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
