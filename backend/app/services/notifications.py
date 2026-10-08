import json
from dataclasses import dataclass

from app.core.config import get_settings
from app.models import ClinicalCase, NotificationLog


@dataclass
class NotificationEvent:
    case_id: int
    cattle_id: int | None
    risk_level: str
    disease: str
    model: str


def create_case_status_notification(case: ClinicalCase, db, notification_type: str, target_role: str = "doctor", payload: dict | None = None) -> NotificationLog | None:
    event_payload = payload or {"case_id": case.id, "cattle_id": case.cattle_id, "status": case.status, "workflow_status": get_case_workflow_status(case)}
    existing = db.query(NotificationLog).filter(NotificationLog.case_id == case.id, NotificationLog.notification_type == notification_type).first()
    if existing:
        return existing
    settings = get_settings()
    provider = settings.notification_provider.lower()
    has_credentials = bool(settings.notification_email_api_key or settings.notification_sms_api_key)
    delivery_status = "mock" if provider == "mock" else ("queued" if not has_credentials else "failed")
    log = NotificationLog(
        case_id=case.id,
        notification_type=notification_type,
        target_role=target_role,
        status=delivery_status,
        event_payload=json.dumps(event_payload),
    )
    db.add(log)
    return log


def create_high_risk_notification(case: ClinicalCase, db, disease: str | None = None, model: str = "clinical_triage") -> NotificationLog | None:
    if case.risk_level.lower() != "high":
        return None
    event = NotificationEvent(case.id, case.cattle_id, case.risk_level, disease or case.ai_prediction, model)
    existing = db.query(NotificationLog).filter(NotificationLog.case_id == case.id, NotificationLog.notification_type == "high_risk_case", NotificationLog.event_payload.contains(f'"model": "{model}"')).first()
    if existing:
        return existing
    settings = get_settings()
    provider = settings.notification_provider.lower()
    has_credentials = bool(settings.notification_email_api_key or settings.notification_sms_api_key)
    delivery_status = "mock" if provider == "mock" else ("queued" if not has_credentials else "failed")
    log = NotificationLog(
        case_id=case.id,
        notification_type="high_risk_case",
        target_role="doctor",
        status=delivery_status,
        event_payload=json.dumps({"case_id": event.case_id, "cattle_id": event.cattle_id, "risk_level": event.risk_level, "disease": event.disease, "model": event.model}),
    )
    db.add(log)
    return log


def get_case_workflow_status(case: ClinicalCase) -> str:
    status = (case.status or "").strip().lower()
    if status in {"pending", "pending_review", "new", "submitted", "ai_complete"}:
        return "PENDING"
    if status in {"in_progress", "in_review", "accepted", "claimed", "reviewing"}:
        return "IN_PROGRESS"
    if status in {"completed", "reviewed", "finished", "advice_received"}:
        return "COMPLETED"
    return "PENDING" if not status else status.upper()
