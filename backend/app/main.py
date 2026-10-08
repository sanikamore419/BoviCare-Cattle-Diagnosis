from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import SessionLocal, engine
from app.models import CaseImage, Cattle, ClinicalCase, NotificationLog, PredictionResult, RefreshSession, User  # noqa: F401
from app.routers import auth, cases, cattle, health, predictions

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1")
app.include_router(cattle.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")


def ensure_admin_account() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(User).filter(User.role == "admin").first():
            return
        is_production = settings.environment.lower() in {"production", "prod"}
        if not settings.admin_email or not settings.admin_password:
            if is_production:
                raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD are required to seed the production administrator.")
            return
        email = settings.admin_email.lower().strip()
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise RuntimeError("The configured administrator email is already assigned to a non-admin account.")
        db.add(User(full_name="BoviCare Administrator", email=email, password_hash=hash_password(settings.admin_password), role="admin"))
        db.commit()
    finally:
        db.close()


def verify_schema_revision() -> None:
    backend_dir = Path(__file__).resolve().parent.parent
    migration_config = Config(str(backend_dir / "alembic.ini"))
    migration_config.set_main_option("script_location", str(backend_dir / "app" / "migrations"))
    head_revision = ScriptDirectory.from_config(migration_config).get_current_head()
    with engine.connect() as connection:
        current_revision = MigrationContext.configure(connection).get_current_revision()
    if current_revision != head_revision:
        raise RuntimeError("Database migrations are required before startup. Run 'python -m alembic upgrade head' from backend/.")


@app.on_event("startup")
def startup_checks() -> None:
    settings.validate_runtime_security()
    verify_schema_revision()
    ensure_admin_account()
