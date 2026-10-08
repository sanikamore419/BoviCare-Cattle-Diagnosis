import json
from datetime import datetime
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user, require_roles
from app.models import CaseEvent, CaseImage, Cattle, ClinicalCase, NotificationLog, PredictionResult, User
from app.models.status import CaseStatus
from app.services.case_events import record_case_submitted, record_status_transition
from app.schemas.case import CaseCreate, CaseRead, CaseReview
from app.schemas.prediction import CaseModelResult, CasePredictionRow, CasePredictionsResponse
from app.services.prediction import prediction_service
from app.services.reports import build_case_report
from app.services.image_storage import image_path
from app.services.notifications import create_case_status_notification, create_high_risk_notification, get_case_workflow_status

router = APIRouter(prefix="/cases", tags=["clinical cases"])


def serialize(case: ClinicalCase, current_user: User | None = None) -> dict:
    data = {column.name: getattr(case, column.name) for column in case.__table__.columns}
    data["symptoms"] = json.loads(data["symptoms"] or "[]")
    data["urgency_score"] = float(data.get("urgency_score") or 0.0)
    data["urgency_level"] = (data.get("urgency_level") or "LOW").upper()
    data["workflow_status"] = get_case_workflow_status(case)
    if current_user and current_user.role == "farmer":
        data["private_clinical_notes"] = None
        data.pop("clinical_notes", None)
    data["farmer_advice"] = data.get("farmer_advice") or data.get("veterinarian_notes")
    return data


def get_case_or_404(case_id: int, db: Session) -> ClinicalCase:
    case = db.get(ClinicalCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


def ensure_case_access(case: ClinicalCase, user: User) -> None:
    if user.role == "farmer" and case.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to access this case.")
    if user.role == "doctor" and case.veterinarian_id is not None and case.veterinarian_id != user.id:
        if user.id != case.owner_id:
            # Doctors can view all cases for review if they are the assigned veterinarian.
            pass


def calculate_case_urgency(case: ClinicalCase, prediction_rows: list | None = None) -> float:
    """Urgency formula: disease severity 30 + AI confidence 25 + symptom count 20 + waiting time 15 + age risk 10 = 100.
    The disease severity value is mapped from the existing risk_level semantics already used by the app:
    high => 30, medium => 15, low => 5. When a model prediction is present, confidence contributes up to 25 points.
    If no model result exists, the score falls back to zero for confidence rather than inventing a value.
    """
    symptoms = json.loads(case.symptoms or "[]") if case.symptoms else []
    disease_severity = {"high": 30, "medium": 15, "low": 5, "urgent": 30}.get((case.risk_level or "").lower(), 0)
    if disease_severity == 0:
        ai_text = (case.ai_prediction or "").lower()
        if any(token in ai_text for token in ["urgent", "critical", "emergency"]):
            disease_severity = 30
        elif any(token in ai_text for token in ["moderate", "recommended"]):
            disease_severity = 15

    highest_confidence = 0.0
    if prediction_rows:
        highest_confidence = max((float(row.probability) for row in prediction_rows if row.probability is not None), default=0.0)
    elif case.risk_level:
        highest_confidence = {"high": 0.85, "medium": 0.65, "low": 0.35}.get(case.risk_level.lower(), 0.0)

    ai_confidence_points = min(25.0, highest_confidence * 25.0)
    symptom_points = min(20, len(symptoms) * 4)

    waiting_hours = 0.0
    if case.created_at is not None:
        waiting_hours = max((datetime.utcnow() - case.created_at).total_seconds() / 3600, 0.0)
    waiting_time_points = min(15.0, (waiting_hours / 24.0) * 15.0)

    animal_age = case.age_years
    age_risk_points = 0.0
    if animal_age is not None:
        if animal_age >= 8:
            age_risk_points = 10.0
        elif animal_age >= 5:
            age_risk_points = 6.0
        elif animal_age >= 3:
            age_risk_points = 3.0

    score = min(100.0, disease_severity + ai_confidence_points + symptom_points + waiting_time_points + age_risk_points)
    case.urgency_score = round(score, 2)
    case.urgency_level = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
    return float(case.urgency_score)


def refresh_case_urgency(case: ClinicalCase, db: Session) -> None:
    prediction_rows = db.query(PredictionResult).filter(PredictionResult.case_id == case.id).all()
    calculate_case_urgency(case, prediction_rows)


def claim_case_for_veterinarian(case_id: int, veterinarian_id: int, db: Session) -> ClinicalCase:
    claimed_at = datetime.utcnow()
    updated = db.execute(
        text("UPDATE clinical_cases SET veterinarian_id = :veterinarian_id, claimed_by = :veterinarian_id, status = 'in_review', claimed_at = :claimed_at WHERE id = :case_id AND claimed_by IS NULL AND status = 'pending_review'"),
        {"veterinarian_id": veterinarian_id, "claimed_at": claimed_at, "case_id": case_id},
    )
    if updated.rowcount == 1:
        db.add(CaseEvent(case_id=case_id, event="status_changed", actor_id=veterinarian_id, meta={"from_status": CaseStatus.PENDING_REVIEW.value, "to_status": CaseStatus.IN_REVIEW.value}, created_at=claimed_at))
        db.commit()
        claimed_case = db.get(ClinicalCase, case_id)
        if claimed_case is None:
            raise HTTPException(status_code=404, detail="Case not found.")
        return claimed_case

    # The conditional UPDATE is the claim operation. Only after it loses do we
    # read the row to distinguish a duplicate owner's retry from a conflict.
    db.rollback()
    case = db.get(ClinicalCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if case.claimed_by == veterinarian_id and case.status == CaseStatus.IN_REVIEW.value:
        return case
    if case.status == CaseStatus.COMPLETED.value:
        raise HTTPException(status_code=409, detail="This case has already been completed.")
    if case.veterinarian_id is not None:
        raise HTTPException(status_code=409, detail="This case has already been claimed by another veterinarian.")
    raise HTTPException(status_code=409, detail="This case is no longer available for acceptance.")


@router.post("/triage", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_triage(payload: CaseCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("farmer"))):
    cattle_id = None
    if payload.cattle_id is not None:
        cattle = db.get(Cattle, payload.cattle_id)
        if not cattle:
            raise HTTPException(status_code=404, detail="Cattle record not found.")
        if cattle.farmer_id != current_user.id:
            raise HTTPException(status_code=403, detail="That cattle record does not belong to you.")
        cattle_id = cattle.id
    assessment = prediction_service.assess(payload.symptoms, payload.temperature_c) if payload.symptoms else None
    case = ClinicalCase(
        owner_id=current_user.id,
        cattle_id=cattle_id,
        cattle_tag=payload.cattle_tag,
        breed=payload.breed,
        age_years=payload.age_years,
        temperature_c=payload.temperature_c,
        symptoms=json.dumps(payload.symptoms),
        ai_prediction=assessment.label if assessment else "No symptom triage submitted",
        risk_level=assessment.risk_level if assessment else "low",
        status=CaseStatus.SUBMITTED.value,
    )
    case.urgency_score = calculate_case_urgency(case)
    case.urgency_level = case.urgency_level or "LOW"
    db.add(case)
    db.commit()
    db.refresh(case)
    record_case_submitted(db, case, current_user.id)
    create_case_status_notification(case, db, "case_submitted", "doctor", {"case_id": case.id, "status": case.status, "risk_level": case.risk_level, "urgency_level": case.urgency_level})
    if case.risk_level.lower() == "high":
        create_high_risk_notification(case, db)
    db.commit()
    return serialize(case, current_user)


@router.get("", response_model=list[CaseRead])
def list_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(ClinicalCase)
    if current_user.role == "farmer":
        query = query.filter(ClinicalCase.owner_id == current_user.id)
    cases = query.all()
    for case in cases:
        refresh_case_urgency(case, db)
    if cases:
        db.commit()
    if current_user.role == "doctor":
        priority = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        cases.sort(key=lambda item: (priority.get((item.urgency_level or "LOW").upper(), 99), item.created_at))
    else:
        cases.sort(key=lambda item: item.created_at, reverse=True)
    return [serialize(case, current_user) for case in cases]


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    refresh_case_urgency(case, db)
    db.commit()
    return serialize(case, current_user)


@router.post("/{case_id}/accept", response_model=CaseRead)
def accept_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("doctor"))):
    case = claim_case_for_veterinarian(case_id, current_user.id, db)
    create_case_status_notification(case, db, "veterinarian_reviewing_case", "doctor", {"case_id": case.id, "status": case.status, "veterinarian_id": case.veterinarian_id})
    db.commit()
    return serialize(case, current_user)


@router.post("/{case_id}/accept-review")
def accept_case_review(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("doctor"))):
    return accept_case(case_id, db=db, current_user=current_user)


@router.get("/{case_id}/report")
def download_report(case_id: int, language: Literal["en", "mr"] = Query(default="en"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    pdf = build_case_report(case, db, farmer_view=current_user.role == "farmer", language=language, user_id=current_user.id)
    return StreamingResponse(BytesIO(pdf), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="bovicare-case-{case_id}.pdf"'})


@router.get("/{case_id}/image")
def get_case_image(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    image = db.query(CaseImage).filter(CaseImage.case_id == case_id).one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="No image is stored for this case.")
    path = image_path(image.stored_filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Case image file is missing.")
    return FileResponse(path, media_type=image.content_type, filename=f"case-{case_id}{path.suffix}")


@router.get("/{case_id}/notifications")
def get_case_notifications(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    logs = db.query(NotificationLog).filter(NotificationLog.case_id == case_id, NotificationLog.user_id == current_user.id).order_by(NotificationLog.created_at.desc()).all()
    return [{"id": log.id, "case_id": log.case_id, "notification_type": log.notification_type, "target_role": log.target_role, "status": log.status, "created_at": log.created_at} for log in logs]


@router.get("/{case_id}/predictions", response_model=CasePredictionsResponse)
def get_case_predictions(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    rows = db.query(PredictionResult).filter(PredictionResult.case_id == case_id).order_by(PredictionResult.model_name, PredictionResult.rank).all()
    groups: dict = {}
    for row in rows:
        if row.model_name not in groups:
            groups[row.model_name] = {"model_version": row.model_version, "risk_level": row.risk_level, "predictions": []}
        groups[row.model_name]["predictions"].append(CasePredictionRow(rank=row.rank, disease_label=row.disease_label, probability=row.probability))
    models = [CaseModelResult(model_name=name, model_version=g["model_version"], risk_level=g["risk_level"], predictions=g["predictions"]) for name, g in groups.items()]
    return CasePredictionsResponse(case_id=case_id, models=models)


@router.put("/{case_id}/review", response_model=CaseRead)
def review_case(case_id: int, payload: CaseReview, db: Session = Depends(get_db), current_user: User = Depends(require_roles("doctor"))):
    case = get_case_or_404(case_id, db)
    if case.veterinarian_id is not None and case.veterinarian_id != current_user.id:
        raise HTTPException(status_code=403, detail="This case is assigned to another veterinarian.")
    if payload.farmer_advice is None and payload.veterinarian_notes is None and payload.private_clinical_notes is None:
        raise HTTPException(status_code=400, detail="Please provide farmer-facing advice or clinical notes before submitting.")

    if payload.farmer_advice is not None:
        case.farmer_advice = payload.farmer_advice.strip()
    elif case.farmer_advice is None and payload.veterinarian_notes is not None:
        case.farmer_advice = payload.veterinarian_notes.strip()

    private_notes = payload.private_clinical_notes or payload.veterinarian_notes
    if private_notes is not None:
        case.private_clinical_notes = private_notes.strip()
        case.clinical_notes = private_notes.strip()
    case.veterinarian_notes = private_notes.strip() if private_notes else case.veterinarian_notes

    case.veterinarian_id = case.veterinarian_id or current_user.id
    case.claimed_by = case.claimed_by or current_user.id
    case.claimed_at = case.claimed_at or datetime.utcnow()
    if payload.review_status in {"completed", "reviewed"}:
        if not case.farmer_advice:
            raise HTTPException(status_code=400, detail="Farmer-facing advice is required before completing the case.")
        next_status = CaseStatus.COMPLETED.value
        case.completed_at = datetime.utcnow()
    elif payload.review_status in {"in_progress", "in_review"}:
        next_status = CaseStatus.IN_REVIEW.value
        case.completed_at = None
    else:
        next_status = CaseStatus.PENDING_REVIEW.value
        case.completed_at = None
    record_status_transition(db, case, next_status, current_user.id)

    if case.farmer_advice:
        case.urgency_score = calculate_case_urgency(case)
        case.urgency_level = case.urgency_level or "LOW"

    db.commit()
    db.refresh(case)

    if case.status == CaseStatus.COMPLETED.value:
        create_case_status_notification(case, db, "veterinary_advice_received", "farmer", {"case_id": case.id, "status": case.status, "farmer_advice": case.farmer_advice[:200]})
    db.commit()
    return serialize(case, current_user)
