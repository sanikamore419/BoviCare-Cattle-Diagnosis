"""Create synthetic development data in backend/bovicare_demo.db only.

Run from backend/ with ENV=development plus ADMIN_EMAIL, ADMIN_PASSWORD, and
DEMO_USER_PASSWORD set. This script never uses DATABASE_URL from the caller.
"""
from __future__ import annotations

import os
import json
from datetime import datetime, timedelta
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEMO_DB = (BACKEND_DIR / "bovicare_demo.db").resolve()
LIVE_DB = (BACKEND_DIR / "bovicare.db").resolve()


def configure_demo_environment() -> None:
    if os.environ.get("ENV", "").lower() != "development":
        raise RuntimeError("Demo seeding is allowed only when ENV=development is explicitly set.")
    if DEMO_DB == LIVE_DB:
        raise RuntimeError("Refusing to seed because the demo database path matches the live database path.")
    if not os.environ.get("ADMIN_EMAIL") or not os.environ.get("ADMIN_PASSWORD"):
        raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD are required to seed the demo administrator.")
    if not os.environ.get("DEMO_USER_PASSWORD"):
        raise RuntimeError("DEMO_USER_PASSWORD is required for the synthetic demo accounts.")

    # Prevent Pydantic Settings from consulting a developer's .env file.
    from app.core.config import Settings

    Settings.model_config["env_file"] = None
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DATABASE_URL"] = f"sqlite:///{DEMO_DB.as_posix()}"


def main() -> None:
    configure_demo_environment()
    from alembic import command
    from alembic.config import Config

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "app" / "migrations"))
    command.upgrade(config, "head")

    from sqlalchemy import select
    from app.core.security import hash_password
    from app.database.session import SessionLocal
    from app.models import CaseEvent, Cattle, ClinicalCase, PredictionResult, User
    from app.services.urgency import calculate_urgency

    now = datetime.utcnow().replace(microsecond=0)
    with SessionLocal.begin() as db:
        admin_email = os.environ["ADMIN_EMAIL"].strip().lower()
        admin = db.scalar(select(User).where(User.role == "admin"))
        if admin is None:
            if db.scalar(select(User).where(User.email == admin_email)):
                raise RuntimeError("ADMIN_EMAIL belongs to a non-admin account in the demo database.")
            admin = User(full_name="BoviCare Demo Administrator", email=admin_email,
                         password_hash=hash_password(os.environ["ADMIN_PASSWORD"]), role="admin")
            db.add(admin)
            db.flush()

        doctor_specs = [
            ("Dr. Asha Rao", "demo.doctor1@bovicare.local", "REG-DEMO-001", "Large animal medicine", "approved", "available"),
            ("Dr. Imran Shaikh", "demo.doctor2@bovicare.local", "REG-DEMO-002", "Bovine health", "approved", "busy"),
            ("Dr. Neha Patil", "demo.doctor3@bovicare.local", "REG-DEMO-003", "Veterinary practice", "pending", "offline"),
        ]
        doctors: list[User] = []
        for name, email, registration, specialty, verification, availability in doctor_specs:
            doctor = db.scalar(select(User).where(User.email == email))
            if doctor is None:
                doctor = User(full_name=name, email=email, password_hash=hash_password(os.environ["DEMO_USER_PASSWORD"]),
                              role="doctor", registration_number=registration, specialization=specialty,
                              verification_status=verification, availability=availability,
                              availability_updated_at=now)
                db.add(doctor)
                db.flush()
            doctors.append(doctor)

        farmer_email = "demo.farmer@bovicare.local"
        farmer = db.scalar(select(User).where(User.email == farmer_email))
        if farmer is None:
            farmer = User(full_name="Demo Farmer", email=farmer_email,
                          password_hash=hash_password(os.environ["DEMO_USER_PASSWORD"]), role="farmer")
            db.add(farmer)
            db.flush()

        cattle_records = list(db.scalars(select(Cattle).where(Cattle.farmer_id == farmer.id).order_by(Cattle.id)))
        cattle_specs = [
            ("MH-001", "Gauri", "Gir", 5.0), ("MH-002", "Sona", "Sahiwal", 3.0),
            ("MH-003", "Moti", "Deoni", 7.0), ("MH-004", "Chandni", "Holstein Friesian", 2.0),
        ]
        for index, (tag, name, breed, age) in enumerate(cattle_specs):
            cattle = next((row for row in cattle_records if row.tag_number == tag), None)
            if cattle is None:
                cattle = Cattle(farmer_id=farmer.id, tag_number=tag, name=name, breed=breed,
                                date_of_birth=(now - timedelta(days=365 * age)).date().isoformat(),
                                sex="female", weight_kg=350 + index * 35, created_at=now, updated_at=now)
                db.add(cattle)
                db.flush()
                cattle_records.append(cattle)

        statuses = ["submitted", "ai_complete", "pending_review", "in_review", "completed"]
        levels = ["LOW", "MEDIUM", "HIGH"]
        existing_cases = list(db.scalars(select(ClinicalCase).where(ClinicalCase.owner_id == farmer.id)))
        for index in range(20):
            tag = cattle_specs[index % 4][0]
            cattle = next(row for row in cattle_records if row.tag_number == tag)
            created = now - timedelta(days=19 - index, hours=(index * 3) % 24)
            status = statuses[index % len(statuses)]
            level = levels[(index * 2) % len(levels)]
            confidence = {"LOW": 0.2, "MEDIUM": 0.6, "HIGH": 0.8}[level]
            symptom_values = {
                "LOW": [], "MEDIUM": ["skin changes", "reduced appetite"],
                "HIGH": ["fever", "reduced appetite", "skin changes", "weakness", "lameness"],
            }[level]
            disease_value = {"LOW": "Healthy appearance", "MEDIUM": "Ringworm", "HIGH": "FMD"}[level]
            image_value = {"LOW": "HEALTHY", "MEDIUM": "RINGWORM", "HIGH": "FMD"}[level]
            days_waiting = (now - created).total_seconds() / 3600
            predicted_values = [confidence, confidence - 0.05, confidence - 0.1, confidence - 0.15]
            urgency = calculate_urgency(
                findings=[level.lower(), disease_value, image_value], confidence_scores=predicted_values,
                symptom_count=len(symptom_values), waiting_hours=days_waiting,
                animal_age_years=float(cattle_specs[index % 4][3]),
            )
            if index < len(existing_cases):
                continue
            doctor = doctors[index % 2] if status in {"in_review", "completed"} else None
            case = ClinicalCase(
                owner_id=farmer.id, cattle_id=cattle.id, cattle_tag=cattle.tag_number, breed=cattle.breed,
                age_years=float(cattle_specs[index % 4][3]), temperature_c=38.5 + (index % 20) / 10,
                symptoms=json.dumps(symptom_values),
                ai_prediction=disease_value, risk_level=level.lower(), status=status,
                urgency_score=urgency["score"], urgency_level=urgency["level"],
                urgency_breakdown=urgency["breakdown"],
                claimed_by=doctor.id if doctor else None, veterinarian_id=doctor.id if doctor else None,
                claimed_at=created + timedelta(hours=1) if doctor else None,
                completed_at=created + timedelta(hours=5) if status == "completed" else None,
                farmer_advice="Demo advice: please arrange a veterinary assessment." if status == "completed" else None,
                clinical_notes="Synthetic demo note; not clinical guidance." if status == "completed" else None,
                created_at=created,
            )
            db.add(case)
            db.flush()
            actor_id = doctor.id if doctor else farmer.id
            event_names = ["case_submitted"]
            if status in {"ai_complete", "pending_review", "in_review", "completed"}:
                event_names.append("ai_complete")
            if status in {"pending_review", "in_review", "completed"}:
                event_names.append("pending_review")
            if status in {"in_review", "completed"}:
                event_names.append("in_review")
            if status == "completed":
                event_names.append("completed")
            for event_index, event_name in enumerate(event_names):
                db.add(CaseEvent(case_id=case.id, event=event_name,
                                 actor_id=farmer.id if event_name == "case_submitted" else actor_id,
                                 meta={"demo": True}, created_at=created + timedelta(minutes=event_index * 10)))
            # Keep the model outputs as independent rows. These are synthetic display data.
            model_results = (
                ("general_cattle_disease", disease_value),
                ("cattle_image_classifier", image_value),
                ("mastitis_specialist", "Mastitis" if level != "LOW" else "No Mastitis"),
                ("lumpy_skin_specialist", "Lumpy Skin" if level == "HIGH" else "Normal Skin"),
            )
            for model_index, (model_name, disease_label) in enumerate(model_results):
                db.add(PredictionResult(case_id=case.id, cattle_id=cattle.id, owner_id=farmer.id,
                                        model_name=model_name, model_version="demo-only", rank=1,
                                        disease_label=disease_label,
                                        probability=predicted_values[model_index],
                                        risk_level=level.lower(), created_at=created))

    print(f"Development demo data is ready in {DEMO_DB.name}.")
    print("Synthetic accounts: demo.doctor1@bovicare.local, demo.doctor2@bovicare.local, demo.doctor3@bovicare.local, demo.farmer@bovicare.local")
    print("Passwords were not printed. Use DEMO_USER_PASSWORD and the configured administrator environment values.")


if __name__ == "__main__":
    main()
