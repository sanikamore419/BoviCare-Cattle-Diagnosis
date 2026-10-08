from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("verification_status IS NULL OR verification_status IN ('pending', 'approved', 'rejected')", name="ck_users_verification_status_allowed"),
        CheckConstraint("availability IS NULL OR availability IN ('available', 'busy', 'offline')", name="ck_users_availability_allowed"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="farmer")
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(160), nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    verified_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    availability: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    availability_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
