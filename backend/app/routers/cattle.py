from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user, require_roles
from app.models import Cattle, User
from app.schemas.cattle import CattleCreate, CattleRead, CattleUpdate

router = APIRouter(prefix="/cattle", tags=["cattle"])


def get_cattle_or_404(cattle_id: int, db: Session) -> Cattle:
    cattle = db.get(Cattle, cattle_id)
    if not cattle:
        raise HTTPException(status_code=404, detail="Cattle record not found.")
    return cattle


def ensure_owner(cattle: Cattle, user: User) -> None:
    if cattle.farmer_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to access this cattle record.")


@router.get("", response_model=list[CattleRead])
def list_cattle(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "farmer":
        return db.query(Cattle).filter(Cattle.farmer_id == current_user.id).order_by(Cattle.created_at.desc()).all()
    # doctors can list all cattle (read-only, for case context)
    return db.query(Cattle).order_by(Cattle.created_at.desc()).all()


@router.post("", response_model=CattleRead, status_code=status.HTTP_201_CREATED)
def create_cattle(payload: CattleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("farmer"))):
    cattle = Cattle(farmer_id=current_user.id, **payload.model_dump())
    db.add(cattle)
    db.commit()
    db.refresh(cattle)
    return cattle


@router.get("/{cattle_id}", response_model=CattleRead)
def get_cattle(cattle_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cattle = get_cattle_or_404(cattle_id, db)
    if current_user.role == "farmer":
        ensure_owner(cattle, current_user)
    return cattle


@router.put("/{cattle_id}", response_model=CattleRead)
def update_cattle(cattle_id: int, payload: CattleUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles("farmer"))):
    cattle = get_cattle_or_404(cattle_id, db)
    ensure_owner(cattle, current_user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cattle, field, value)
    db.commit()
    db.refresh(cattle)
    return cattle


@router.delete("/{cattle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cattle(cattle_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles("farmer"))):
    cattle = get_cattle_or_404(cattle_id, db)
    ensure_owner(cattle, current_user)
    db.delete(cattle)
    db.commit()
