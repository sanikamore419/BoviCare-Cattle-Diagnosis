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
