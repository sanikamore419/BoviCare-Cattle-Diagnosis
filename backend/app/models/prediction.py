from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class PredictionResult(Base):
    __tablename__ = "prediction_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("clinical_cases.id"), nullable=True, index=True)
    cattle_id: Mapped[int | None] = mapped_column(ForeignKey("cattle.id"), nullable=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(60))
    model_version: Mapped[str] = mapped_column(String(40))
    # For general model: rank 1-5; for mastitis: rank=1
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disease_label: Mapped[str] = mapped_column(String(120))
    probability: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
