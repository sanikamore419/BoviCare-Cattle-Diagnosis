from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.core.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse, UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["authentication"])


def user_read(user: User) -> UserRead:
    return UserRead(id=user.id, name=user.full_name, email=user.email, role=user.role)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if payload.role == "doctor" and get_settings().environment.lower() not in {"development", "dev", "test"}:
        raise HTTPException(status_code=403, detail="Doctor accounts must be provisioned by an administrator.")
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(full_name=payload.name, email=payload.email.lower(), password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_read(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user_read(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return user_read(current_user)
