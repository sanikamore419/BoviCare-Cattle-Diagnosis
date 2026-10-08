from datetime import datetime

from app.models import CaseEvent, ClinicalCase


def record_status_transition(
    db,
    case: ClinicalCase,
    to_status: str,
    actor_id: int | None,
    *,
    event: str = "status_changed",
    created_at: datetime | None = None,
) -> bool:
    from_status = case.status
    if from_status == to_status:
        return False
    case.status = to_status
    db.add(CaseEvent(
        case_id=case.id,
        event=event,
        actor_id=actor_id,
        meta={"from_status": from_status, "to_status": to_status},
        created_at=created_at or datetime.utcnow(),
    ))
    return True


def record_case_submitted(db, case: ClinicalCase, actor_id: int) -> None:
    db.add(CaseEvent(
        case_id=case.id,
        event="case_submitted",
        actor_id=actor_id,
        meta={"from_status": None, "to_status": case.status},
        created_at=case.created_at or datetime.utcnow(),
    ))
