from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    __table_args__ = (Index("ix_notification_logs_user_read", "user_id", "read"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("clinical_cases.id"), index=True)
    notification_type: Mapped[str] = mapped_column(String(40))
    target_role: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))
    event_payload: Mapped[str] = mapped_column(Text)
    message_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
