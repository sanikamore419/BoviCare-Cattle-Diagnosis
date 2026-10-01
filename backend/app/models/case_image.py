from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class CaseImage(Base):
    __tablename__ = "case_images"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("clinical_cases.id"), unique=True, index=True)
    cattle_id: Mapped[int | None] = mapped_column(ForeignKey("cattle.id"), nullable=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    stored_filename: Mapped[str] = mapped_column(String(120), unique=True)
    content_type: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
