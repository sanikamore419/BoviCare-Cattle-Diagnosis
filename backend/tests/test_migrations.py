import json
import os
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError


BACKEND_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"


class MigrationTests(unittest.TestCase):
    def setUp(self):
        handle, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        self.config = Config(str(ALEMBIC_INI))
        self.database_url = f"sqlite:///{self.db_path}"
        self.engines = []

    def open_engine(self):
        engine = create_engine(self.database_url)
        self.engines.append(engine)
        return engine

    def tearDown(self):
        for engine in self.engines:
            engine.dispose()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def migrate(self, revision):
        with patch.dict(os.environ, {"DATABASE_URL": self.database_url}):
            command.upgrade(self.config, revision) if revision != "base" else command.downgrade(self.config, revision)

    def seed_legacy_rows(self):
        engine = self.open_engine()
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO users (id, full_name, email, password_hash, role, created_at) VALUES (1, 'Farmer', 'farmer@example.com', 'hash', 'farmer', '2026-01-01 10:00:00')"))
            conn.execute(text("INSERT INTO users (id, full_name, email, password_hash, role, created_at) VALUES (2, 'Doctor', 'doctor@example.com', 'hash', 'doctor', '2026-01-01 10:00:00')"))
            cases = [
                (1, "in_progress", 2),
                (2, "reviewed", 2),
                (3, "pending", None),
            ]
            for case_id, old_status, doctor_id in cases:
                conn.execute(text("""
                    INSERT INTO clinical_cases
                    (id, owner_id, cattle_tag, symptoms, ai_prediction, risk_level, status,
                     veterinarian_id, created_at)
                    VALUES (:id, 1, :tag, '[]', 'Review recommended', 'medium', :status,
                            :doctor_id, '2026-01-02 11:00:00')
                """), {"id": case_id, "tag": f"COW-{case_id}", "status": old_status, "doctor_id": doctor_id})
            notifications = [
                (1, "veterinarian_reviewing_case", "2026-01-02 12:00:00"),
                (2, "veterinary_advice_received", "2026-01-02 14:00:00"),
            ]
            for case_id, kind, created_at in notifications:
                conn.execute(text("""
                    INSERT INTO notification_logs
                    (case_id, notification_type, target_role, status, event_payload, created_at)
                    VALUES (:case_id, :kind, 'farmer', 'mock', '{}', :created_at)
                """), {"case_id": case_id, "kind": kind, "created_at": created_at})
        engine.dispose()

    def test_upgrade_backfills_legacy_data(self):
        self.migrate("0001_baseline")
        self.seed_legacy_rows()
        self.migrate("head")

        engine = self.open_engine()
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT status FROM clinical_cases ORDER BY id")).scalars().all(), ["in_review", "completed", "pending_review"])
            self.assertEqual(conn.execute(text("SELECT claimed_by FROM clinical_cases ORDER BY id")).scalars().all(), [2, 2, None])
            self.assertEqual(conn.execute(text("SELECT verification_status FROM users WHERE role='doctor'")).scalar_one(), "approved")
            self.assertEqual(conn.execute(text("SELECT availability FROM users WHERE role='doctor'")).scalar_one(), "offline")
            self.assertEqual(conn.execute(text("SELECT claimed_at FROM clinical_cases WHERE id=1")).scalar_one(), "2026-01-02 12:00:00")
            self.assertEqual(conn.execute(text("SELECT completed_at FROM clinical_cases WHERE id=2")).scalar_one(), "2026-01-02 14:00:00")
            legacy_events = conn.execute(text("SELECT case_id, event, meta, created_at FROM case_events ORDER BY case_id")).all()
            self.assertEqual(len(legacy_events), 3)
            self.assertTrue(all(row.event == "legacy_migrated" for row in legacy_events))
            self.assertEqual(json.loads(legacy_events[0].meta), {"from_status": "in_progress", "to_status": "in_review"})
            self.assertEqual(datetime.fromisoformat(legacy_events[0].created_at), datetime(2026, 1, 2, 11, 0))
            self.assertEqual(conn.execute(text("SELECT type FROM notification_logs ORDER BY id")).scalars().all(), ["veterinarian_reviewing_case", "veterinary_advice_received"])
            self.assertEqual(conn.execute(text("SELECT user_id FROM notification_logs")).scalars().all(), [None, None])
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM notification_logs")).scalar_one(), 2)
            indexes = {index["name"] for index in inspect(conn).get_indexes("clinical_cases")}
            self.assertTrue({"ix_clinical_cases_status", "ix_clinical_cases_claimed_by", "ix_clinical_cases_urgency_level_score"}.issubset(indexes))
            with self.assertRaises(IntegrityError):
                conn.execute(text("UPDATE clinical_cases SET status='in_progress' WHERE id=1"))
        engine.dispose()

    def test_upgrade_downgrade_upgrade_and_compatible_startup_created_events_table(self):
        self.migrate("0001_baseline")
        self.seed_legacy_rows()
        engine = self.open_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE case_events (
                    id INTEGER NOT NULL PRIMARY KEY,
                    case_id INTEGER NOT NULL,
                    event VARCHAR(60) NOT NULL,
                    actor_id INTEGER,
                    meta JSON,
                    created_at DATETIME NOT NULL
                )
            """))
            conn.execute(text("CREATE INDEX ix_case_events_case_id ON case_events (case_id)"))
        self.migrate("head")
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM case_events WHERE event='legacy_migrated'")).scalar_one(), 3)
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM clinical_cases")).scalar_one(), 3)

        self.migrate("0001_baseline")
        self.migrate("head")
        engine = self.open_engine()
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM users")).scalar_one(), 2)
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM clinical_cases")).scalar_one(), 3)
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM case_events")).scalar_one(), 3)
            self.assertEqual(conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one(), "0004_notification_fields")
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
