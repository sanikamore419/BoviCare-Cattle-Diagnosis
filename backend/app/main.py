from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.database.session import Base, engine
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


@app.on_event("startup")
def create_tables() -> None:
    settings.validate_runtime_security()
    Base.metadata.create_all(bind=engine)
    # Add cattle_id column to clinical_cases if it doesn't exist yet (SQLite migration)
    if settings.database_url.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(clinical_cases)"))]
            if "cattle_id" not in cols:
                conn.execute(text("ALTER TABLE clinical_cases ADD COLUMN cattle_id INTEGER REFERENCES cattle(id)"))
                conn.commit()
