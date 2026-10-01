from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("clinical_cases.id"), index=True)
    notification_type: Mapped[str] = mapped_column(String(40))
    target_role: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))
    event_payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
