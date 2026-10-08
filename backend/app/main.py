from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import Base, SessionLocal, engine
from app.models import CaseImage, Cattle, ClinicalCase, NotificationLog, PredictionResult, User  # noqa: F401
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


def ensure_demo_veterinarians() -> None:
    db: Session = SessionLocal()
    try:
        current = db.query(User).filter(User.role == "doctor").count()
        if current > 0:
            return
        demo_users = [
            ("Demo Veterinarian 1", "demo_vet_1@example.com", "DemoVet123"),
            ("Demo Veterinarian 2", "demo_vet_2@example.com", "DemoVet123"),
        ]
        for name, email, password in demo_users:
            if not db.query(User).filter(User.email == email.lower()).first():
                db.add(User(full_name=name, email=email.lower(), password_hash=hash_password(password), role="doctor"))
        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def create_tables() -> None:
    settings.validate_runtime_security()
    Base.metadata.create_all(bind=engine)
    ensure_demo_veterinarians()
    # Add cattle_id column to clinical_cases if it doesn't exist yet (SQLite migration)
    if settings.database_url.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(clinical_cases)"))]
            if "cattle_id" not in cols:
                conn.execute(text("ALTER TABLE clinical_cases ADD COLUMN cattle_id INTEGER REFERENCES cattle(id)"))
                conn.commit()
            for column_name in ["urgency_score", "urgency_level", "veterinarian_id", "claimed_at", "completed_at", "farmer_advice", "private_clinical_notes"]:
                if column_name not in cols:
                    if column_name in {"urgency_score"}:
                        conn.execute(text(f"ALTER TABLE clinical_cases ADD COLUMN {column_name} FLOAT DEFAULT 0.0"))
                    elif column_name in {"claimed_at", "completed_at"}:
                        conn.execute(text(f"ALTER TABLE clinical_cases ADD COLUMN {column_name} DATETIME"))
                    elif column_name in {"farmer_advice", "private_clinical_notes"}:
                        conn.execute(text(f"ALTER TABLE clinical_cases ADD COLUMN {column_name} TEXT"))
                    else:
                        conn.execute(text(f"ALTER TABLE clinical_cases ADD COLUMN {column_name} VARCHAR(20)"))
            conn.commit()
