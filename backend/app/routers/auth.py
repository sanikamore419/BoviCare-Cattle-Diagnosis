from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.config import get_settings
from app.database import get_db
from app.models import RefreshSession, User
from app.schemas.auth import LoginRequest, TokenResponse, UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["authentication"])


def user_read(user: User) -> UserRead:
    return UserRead(id=user.id, name=user.full_name, email=user.email, role=user.role)


def issue_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
    )


def clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
    )


def persist_refresh_session(user_id: int, db: Session) -> str:
    settings = get_settings()
    raw_token = create_refresh_token()
    db.add(RefreshSession(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
    ))
    return raw_token


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if payload.role == "doctor" and get_settings().environment.lower() not in {"development", "dev", "test"}:
        raise HTTPException(status_code=403, detail="Doctor accounts must be provisioned by an administrator.")
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(
        full_name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        registration_number=payload.registration_number if payload.role == "doctor" else None,
        specialization=payload.specialization if payload.role == "doctor" else None,
        verification_status="pending" if payload.role == "doctor" else None,
        availability="offline" if payload.role == "doctor" else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_read(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    refresh_token = persist_refresh_session(user.id, db)
    db.commit()
    issue_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=create_access_token(str(user.id)), expires_in=get_settings().access_token_expire_minutes * 60, user=user_read(user))


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    settings = get_settings()
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if not raw_token:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh session is missing or expired.")

    digest = hash_refresh_token(raw_token)
    current = db.query(RefreshSession).filter(RefreshSession.token_hash == digest).one_or_none()
    now = datetime.utcnow()
    if current is None or current.revoked_at is not None or current.expires_at <= now:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh session is missing or expired.")

    claimed = db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.id == current.id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now,
        )
        .values(revoked_at=now)
    )
    if claimed.rowcount != 1:
        db.rollback()
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="Refresh session was already rotated.")

    user = db.get(User, current.user_id)
    if user is None:
        db.rollback()
        clear_refresh_cookie(response)
        raise HTTPException(status_code=401, detail="User account no longer exists.")

    replacement = persist_refresh_session(user.id, db)
    db.commit()
    issue_refresh_cookie(response, replacement)
    return TokenResponse(access_token=create_access_token(str(user.id)), expires_in=settings.access_token_expire_minutes * 60, user=user_read(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_token = request.cookies.get(get_settings().refresh_cookie_name)
    if raw_token:
        db.query(RefreshSession).filter(
            RefreshSession.token_hash == hash_refresh_token(raw_token),
            RefreshSession.revoked_at.is_(None),
        ).update({RefreshSession.revoked_at: datetime.utcnow()}, synchronize_session=False)
        db.commit()
    clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return user_read(current_user)
