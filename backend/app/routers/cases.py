import json
from io import BytesIO
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user, require_roles
from app.models import CaseImage, Cattle, ClinicalCase, NotificationLog, User
from app.schemas.case import CaseCreate, CaseRead, CaseReview
from app.models import PredictionResult
from app.schemas.prediction import CasePredictionsResponse, CaseModelResult, CasePredictionRow
from app.services.prediction import prediction_service
from app.services.reports import build_case_report
from app.services.image_storage import image_path
from app.services.notifications import create_high_risk_notification

router = APIRouter(prefix="/cases", tags=["clinical cases"])


def serialize(case: ClinicalCase) -> dict:
    data = {column.name: getattr(case, column.name) for column in case.__table__.columns}
    data["symptoms"] = json.loads(data["symptoms"])
    return data


def get_case_or_404(case_id: int, db: Session) -> ClinicalCase:
    case = db.get(ClinicalCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return case


def ensure_case_access(case: ClinicalCase, user: User) -> None:
    if user.role == "farmer" and case.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to access this case.")


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
    case = ClinicalCase(owner_id=current_user.id, cattle_id=cattle_id, cattle_tag=payload.cattle_tag, breed=payload.breed, age_years=payload.age_years, temperature_c=payload.temperature_c, symptoms=json.dumps(payload.symptoms), ai_prediction=assessment.label if assessment else "No symptom triage submitted", risk_level=assessment.risk_level if assessment else "low")
    db.add(case)
    db.commit()
    db.refresh(case)
    if case.risk_level.lower() == "high":
        create_high_risk_notification(case, db)
        db.commit()
    return serialize(case)


@router.get("", response_model=list[CaseRead])
def list_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(ClinicalCase)
    if current_user.role == "farmer":
        query = query.filter(ClinicalCase.owner_id == current_user.id)
    return [serialize(case) for case in query.order_by(ClinicalCase.created_at.desc()).all()]


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    return serialize(case)


@router.get("/{case_id}/report")
def download_report(case_id: int, language: Literal["en", "mr"] = Query(default="en"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    pdf = build_case_report(case, db, farmer_view=current_user.role == "farmer", language=language)
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
    logs = db.query(NotificationLog).filter(NotificationLog.case_id == case_id).order_by(NotificationLog.created_at.desc()).all()
    return [{"id": log.id, "case_id": log.case_id, "notification_type": log.notification_type, "target_role": log.target_role, "status": log.status, "created_at": log.created_at} for log in logs]


@router.get("/{case_id}/predictions", response_model=CasePredictionsResponse)
def get_case_predictions(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = get_case_or_404(case_id, db)
    ensure_case_access(case, current_user)
    rows = db.query(PredictionResult).filter(PredictionResult.case_id == case_id).order_by(PredictionResult.model_name, PredictionResult.rank).all()
    # Group by model_name, keeping each model strictly separate
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
    case.veterinarian_notes = payload.veterinarian_notes
    case.status = "pending_review" if payload.review_status == "pending" else payload.review_status
    db.commit()
    db.refresh(case)
    return serialize(case)
