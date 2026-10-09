import json
from io import BytesIO
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.time import as_utc, elapsed_hours_since, utcnow_naive
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
from app.services.urgency import calculate_urgency

router = APIRouter(prefix="/cases", tags=["clinical cases"])


def serialize(case: ClinicalCase, current_user: User | None = None) -> dict:
    data = {column.name: getattr(case, column.name) for column in case.__table__.columns}
    for name in ("created_at", "claimed_at", "completed_at"):
        data[name] = as_utc(data.get(name))
    data["symptoms"] = json.loads(data["symptoms"] or "[]")
    data["urgency_score"] = float(data.get("urgency_score") or 0.0)
    data["urgency_level"] = (data.get("urgency_level") or "LOW").upper()
    data["workflow_status"] = get_case_workflow_status(case)
    data["cattle_name"] = data.get("cattle_name") or getattr(case, "cattle_name", None)
    data["gender"] = data.get("gender") or getattr(case, "gender", None)
    data["notes"] = data.get("notes") or getattr(case, "notes", None)
    if current_user and current_user.role == "farmer":
        data.pop("clinical_notes", None)
        data.pop("private_clinical_notes", None)
        data.pop("veterinarian_notes", None)
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
    symptoms = json.loads(case.symptoms or "[]") if case.symptoms else []
    waiting_hours = elapsed_hours_since(case.created_at)

    rows = prediction_rows or []
    findings = [row.disease_label for row in rows]
    findings.extend(row.risk_level for row in rows)
    if not findings:
        findings.append(case.risk_level)
    scored = calculate_urgency(
        findings=findings,
        confidence_scores=[row.probability for row in rows],
        symptom_count=len(symptoms),
        waiting_hours=waiting_hours,
        animal_age_years=case.age_years,
    )
    case.urgency_score = scored["score"]
    case.urgency_level = scored["level"]
    case.urgency_breakdown = scored["breakdown"]
    return float(case.urgency_score)


def refresh_case_urgency(case: ClinicalCase, db: Session) -> None:
    prediction_rows = db.query(PredictionResult).filter(PredictionResult.case_id == case.id).all()
    calculate_case_urgency(case, prediction_rows)


def claim_case_for_veterinarian(case_id: int, veterinarian_id: int, db: Session) -> ClinicalCase:
    claimed_at = utcnow_naive()
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


def _create_triage_case(payload: CaseCreate, db: Session, current_user: User) -> ClinicalCase:
    cattle_id = None
    if payload.cattle_id is not None:
        cattle = db.get(Cattle, payload.cattle_id)
        if not cattle:
            raise HTTPException(status_code=404, detail="Cattle record not found.")
        if cattle.farmer_id != current_user.id:
            raise HTTPException(status_code=403, detail="That cattle record does not belong to you.")
        cattle_id = cattle.id
    elif payload.cattle_tag:
        cattle = db.query(Cattle).filter(Cattle.farmer_id == current_user.id, Cattle.tag_number == payload.cattle_tag).first()
        if cattle is None:
            cattle = Cattle(
                farmer_id=current_user.id,
                tag_number=payload.cattle_tag,
                name=payload.cattle_name,
                breed=payload.breed,
                sex=(payload.gender or "unknown").lower() if payload.gender else "unknown",
            )
            db.add(cattle)
            db.commit()
            db.refresh(cattle)
        cattle_id = cattle.id
    assessment = prediction_service.assess(payload.symptoms, payload.temperature_c) if payload.symptoms else None
    case = ClinicalCase(
        owner_id=current_user.id,
        cattle_id=cattle_id,
        cattle_tag=payload.cattle_tag,
        cattle_name=payload.cattle_name or (db.get(Cattle, cattle_id).name if cattle_id else None),
        breed=payload.breed,
        gender=(payload.gender or (db.get(Cattle, cattle_id).sex if cattle_id else None)),
        age_years=payload.age_years,
        temperature_c=payload.temperature_c,
        symptoms=json.dumps(payload.symptoms),
        notes=(payload.notes or None),
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
    return case


def create_triage(payload: CaseCreate, db: Session, current_user: User) -> ClinicalCase:
    return _create_triage_case(payload, db=db, current_user=current_user)


@router.post("/triage", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_triage_route(payload: CaseCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("farmer"))):
    case = _create_triage_case(payload, db=db, current_user=current_user)
    return serialize(case, current_user)


@router.get("")
def list_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(ClinicalCase)
    if current_user.role == "farmer":
        query = query.filter(ClinicalCase.owner_id == current_user.id)
    query = query.order_by(ClinicalCase.created_at.desc().nullslast(), ClinicalCase.id.desc())
    cases = query.all()
    for case in cases:
        refresh_case_urgency(case, db)
    if cases:
        db.commit()
    response = [serialize(case, current_user) for case in cases]
    if current_user.role == "doctor" and cases:
        case_ids = [case.id for case in cases]
        farmer_ids = {case.owner_id for case in cases}
        farmers = db.query(User).filter(User.id.in_(farmer_ids), User.role == "farmer").all()
        farmer_details = {farmer.id: {"name": farmer.full_name, "email": farmer.email} for farmer in farmers}
        image_case_ids = {
            case_id for (case_id,) in db.query(CaseImage.case_id).filter(CaseImage.case_id.in_(case_ids)).all()
        }
        prediction_rows = db.query(PredictionResult).filter(
            PredictionResult.case_id.in_(case_ids),
        ).order_by(
            PredictionResult.created_at.desc(), PredictionResult.id.desc(),
        ).all()
        latest_predictions: dict[int, list[dict]] = {case_id: [] for case_id in case_ids}
        seen_predictions: set[tuple[int, str, int | None]] = set()
        for prediction in prediction_rows:
            key = (prediction.case_id, prediction.model_name, prediction.rank)
            if key in seen_predictions:
                continue
            seen_predictions.add(key)
            latest_predictions[prediction.case_id].append({
                "model_name": prediction.model_name,
                "disease_label": prediction.disease_label,
                "probability": prediction.probability,
                "risk_level": prediction.risk_level,
            })
        for case, item in zip(cases, response):
            item["farmer"] = farmer_details.get(case.owner_id)
            item["has_image"] = case.id in image_case_ids
            item["prediction_results"] = latest_predictions[case.id]
    return response


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    refresh_case_urgency(case, db)
    db.commit()
    return serialize(case, current_user)


@router.get("/{case_id}/events")
def get_case_events(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at.asc()).all()
    timeline = []
    for event in events:
        payload = event.meta or {}
        if event.event == "case_submitted":
            title = "Case submitted"
            detail = "Farmer submitted the case for review."
        elif event.event == "ai_completed":
            title = "AI assessment completed"
            detail = "AI triage and prediction results were stored for the case."
        elif event.event == "status_changed":
            from_status = payload.get("from_status")
            to_status = payload.get("to_status")
            title = "Status changed"
            detail = f"{from_status or 'previous'} → {to_status or 'current'}"
        elif event.event == "veterinarian_reviewing_case":
            title = "Doctor accepted the case"
            detail = "The veterinarian began their review of the case."
        else:
            title = event.event.replace("_", " ").title()
            detail = json.dumps(payload, default=str) if payload else ""
        timeline.append({
            "id": event.id,
            "event": event.event,
            "title": title,
            "detail": detail,
            "meta": payload,
            "created_at": as_utc(event.created_at),
        })
    return timeline


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
    return [{"id": log.id, "case_id": log.case_id, "notification_type": log.notification_type, "target_role": log.target_role, "status": log.status, "created_at": as_utc(log.created_at)} for log in logs]


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
    case.claimed_at = case.claimed_at or utcnow_naive()
    if payload.review_status in {"completed", "reviewed"}:
        if not case.farmer_advice:
            raise HTTPException(status_code=400, detail="Farmer-facing advice is required before completing the case.")
        next_status = CaseStatus.COMPLETED.value
        case.completed_at = utcnow_naive()
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
