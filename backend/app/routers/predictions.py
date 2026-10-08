from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.security import get_current_user
from app.database import get_db
from app.models import CaseImage, Cattle, ClinicalCase, PredictionResult, User
from app.models.status import CaseStatus
from app.services.case_events import record_status_transition
from app.schemas.prediction import (
    ImagePredictionResponse, PredictionRequest, PredictionResponse
)
from ml.services.prediction_router import route_prediction
from ml.services.image_predictor import cattle_image_predictor, lumpy_skin_predictor
from app.services.image_storage import read_valid_image, save_image, image_path
from app.services.notifications import create_high_risk_notification

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("", response_model=PredictionResponse, status_code=status.HTTP_200_OK)
def run_prediction(
    payload: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # -- Cattle ownership check ------------------------------------------------
    cattle_id = None
    if payload.cattle_id is not None:
        cattle = db.get(Cattle, payload.cattle_id)
        if not cattle:
            raise HTTPException(status_code=404, detail="Cattle record not found.")
        if current_user.role == "farmer" and cattle.farmer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="That cattle record does not belong to you.",
            )
        cattle_id = cattle.id

    # -- Case ownership check --------------------------------------------------
    case_id = None
    if payload.case_id is not None:
        case = db.get(ClinicalCase, payload.case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")
        if current_user.role == "farmer" and case.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="That case does not belong to you.")
        if cattle_id is not None and case.cattle_id not in (None, cattle_id):
            raise HTTPException(status_code=422, detail="The cattle record does not match this case.")
        if cattle_id is None:
            cattle_id = case.cattle_id
        case_id = case.id

    if payload.image_only:
        if case_id is None:
            raise HTTPException(status_code=422, detail="Image-only prediction lookup requires a case_id.")
        image_rows = db.query(PredictionResult).filter(
            PredictionResult.case_id == case_id,
            PredictionResult.model_name.in_(["cattle_image_classifier", "lumpy_skin_specialist"]),
        ).all()
        if not image_rows:
            raise HTTPException(status_code=422, detail="Run image prediction for this case before requesting its results.")
        case = db.get(ClinicalCase, case_id)
        return PredictionResponse(
            cattle_id=cattle_id,
            models_used=sorted({row.model_name for row in image_rows}),
            combined_risk_level=(case.risk_level if case else "low").lower(),
            general=None,
            mastitis=None,
        )

    # -- Route to appropriate model(s) ----------------------------------------
    try:
        milk_dict = payload.milk_data.model_dump() if payload.milk_data else None
        routed = route_prediction(
            symptoms=payload.symptoms,
            milk_data=milk_dict,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # -- Persist prediction results -------------------------------------------
    if routed.general:
        for pred in routed.general.predictions:
            db.add(PredictionResult(
                case_id=case_id,
                cattle_id=cattle_id,
                owner_id=current_user.id,
                model_name=routed.general.model,
                model_version=routed.general.model_version,
                rank=pred.rank,
                disease_label=pred.disease,
                probability=pred.probability,
                risk_level=routed.general.risk_level,
            ))

    if routed.mastitis:
        db.add(PredictionResult(
            case_id=case_id,
            cattle_id=cattle_id,
            owner_id=current_user.id,
            model_name=routed.mastitis.model,
            model_version=routed.mastitis.model_version,
            rank=1,
            disease_label=routed.mastitis.condition,
            probability=routed.mastitis.probability,
            risk_level=routed.mastitis.risk_level,
        ))

    db.commit()
    if case_id is not None:
        case = db.get(ClinicalCase, case_id)
        if case is not None:
            from app.routers.cases import calculate_case_urgency
            prediction_rows = db.query(PredictionResult).filter(PredictionResult.case_id == case_id).all()
            calculate_case_urgency(case, prediction_rows)
        if case and case.status == CaseStatus.SUBMITTED.value:
            record_status_transition(db, case, CaseStatus.AI_COMPLETE.value, current_user.id, event="ai_completed")
        if case and case.status == CaseStatus.AI_COMPLETE.value:
            record_status_transition(db, case, CaseStatus.PENDING_REVIEW.value, current_user.id)
        db.commit()
    if case_id is not None and routed.combined_risk_level.lower() == "high":
        case = db.get(ClinicalCase, case_id)
        case.risk_level = "high"
        create_high_risk_notification(case, db, disease=(routed.general.predictions[0].disease if routed.general else routed.mastitis.condition if routed.mastitis else None), model=(routed.models_used[0] if routed.models_used else "prediction"))
        db.commit()

    # -- Build response --------------------------------------------------------
    general_out = None
    if routed.general:
        general_out = {
            "model": routed.general.model,
            "model_version": routed.general.model_version,
            "risk_level": routed.general.risk_level,
            "predictions": [
                {"rank": p.rank, "disease": p.disease, "probability": p.probability}
                for p in routed.general.predictions
            ],
        }

    mastitis_out = None
    if routed.mastitis:
        mastitis_out = {
            "model": routed.mastitis.model,
            "model_version": routed.mastitis.model_version,
            "condition": routed.mastitis.condition,
            "probability": routed.mastitis.probability,
            "risk_level": routed.mastitis.risk_level,
        }

    return PredictionResponse(
        cattle_id=cattle_id,
        models_used=routed.models_used,
        combined_risk_level=routed.combined_risk_level,
        general=general_out,
        mastitis=mastitis_out,
    )


def _resolve_cattle(cattle_id: Optional[int], db: Session, current_user: User) -> Optional[int]:
    if cattle_id is None:
        return None
    cattle = db.get(Cattle, cattle_id)
    if not cattle:
        raise HTTPException(status_code=404, detail="Cattle record not found.")
    if current_user.role == "farmer" and cattle.farmer_id != current_user.id:
        raise HTTPException(status_code=403, detail="That cattle record does not belong to you.")
    return cattle.id


@router.post("/image", response_model=ImagePredictionResponse, status_code=status.HTTP_200_OK)
async def run_image_prediction(
    file: UploadFile = File(...),
    cattle_id: Optional[int] = Form(default=None),
    case_id: Optional[int] = Form(default=None),
    model: str = Form(default="cattle"),  # "cattle" or "lumpy"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # -- Cattle ownership ------------------------------------------------------
    resolved_cattle_id = _resolve_cattle(cattle_id, db, current_user)
    resolved_case_id = None
    if case_id is not None:
        case = db.get(ClinicalCase, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")
        if current_user.role == "farmer" and case.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="That case does not belong to you.")
        if resolved_cattle_id is not None and case.cattle_id not in (None, resolved_cattle_id):
            raise HTTPException(status_code=422, detail="The cattle record does not match this case.")
        if resolved_cattle_id is None:
            resolved_cattle_id = case.cattle_id
        resolved_case_id = case.id

    # -- File validation -------------------------------------------------------
    image_bytes, content_type = await read_valid_image(file)

    # -- Select model ----------------------------------------------------------
    if model == "lumpy":
        predictor = lumpy_skin_predictor
        model_label = "lumpy_skin_specialist"
    else:
        predictor = cattle_image_predictor
        model_label = "cattle_image_classifier"

    if not predictor.is_available():
        raise HTTPException(status_code=503, detail=f"Image model '{model_label}' is not available.")

    # -- Run inference ---------------------------------------------------------
    try:
        result = predictor.predict(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # -- Persist prediction rows and the private case image -------------------
    stored_filename = None
    if resolved_case_id is not None:
        case = db.get(ClinicalCase, resolved_case_id)
        stored_filename = save_image(image_bytes, content_type)
        previous_image = db.query(CaseImage).filter(CaseImage.case_id == resolved_case_id).one_or_none()
        if previous_image:
            old_path = image_path(previous_image.stored_filename)
            if old_path.exists():
                old_path.unlink()
            previous_image.stored_filename = stored_filename
            previous_image.content_type = content_type
            previous_image.cattle_id = resolved_cattle_id
        else:
            db.add(CaseImage(case_id=resolved_case_id, cattle_id=resolved_cattle_id, owner_id=current_user.id, stored_filename=stored_filename, content_type=content_type))
    for pred in result.predictions:
        db.add(PredictionResult(
            case_id=resolved_case_id,
            cattle_id=resolved_cattle_id,
            owner_id=current_user.id,
            model_name=result.model,
            model_version=result.model_version,
            rank=pred.rank,
            disease_label=pred.label,
            probability=pred.probability,
            risk_level=result.risk_level,
        ))
    try:
        db.commit()
    except Exception:
        if stored_filename:
            path = image_path(stored_filename)
            if path.exists():
                path.unlink()
        db.rollback()
        raise
    if resolved_case_id is not None:
        case = db.get(ClinicalCase, resolved_case_id)
        if case is not None:
            from app.routers.cases import calculate_case_urgency
            prediction_rows = db.query(PredictionResult).filter(PredictionResult.case_id == resolved_case_id).all()
            calculate_case_urgency(case, prediction_rows)
        if case and case.status == CaseStatus.SUBMITTED.value:
            record_status_transition(db, case, CaseStatus.AI_COMPLETE.value, current_user.id, event="ai_completed")
        if case and case.status == CaseStatus.AI_COMPLETE.value:
            record_status_transition(db, case, CaseStatus.PENDING_REVIEW.value, current_user.id)
        db.commit()
    if resolved_case_id is not None and result.risk_level.lower() == "high":
        case = db.get(ClinicalCase, resolved_case_id)
        case.risk_level = "high"
        create_high_risk_notification(case, db, disease=result.top_label, model=result.model)
        db.commit()

    return ImagePredictionResponse(
        cattle_id=resolved_cattle_id,
        model=result.model,
        model_version=result.model_version,
        top_label=result.top_label,
        top_probability=result.top_probability,
        risk_level=result.risk_level,
        predictions=[{"rank": p.rank, "label": p.label, "probability": p.probability} for p in result.predictions],
        disclaimer="AI image analysis is provided for decision support only. A qualified veterinarian should confirm the condition.",
    )
