import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.time import as_utc, elapsed_hours_since, utcnow_naive
from app.database.session import Base
from app.models import CaseEvent, ClinicalCase, User
from app.routers.cases import serialize
from app.services.case_events import record_case_submitted


class TimestampHandlingTests(unittest.TestCase):
    def test_known_utc_instant_is_explicitly_utc_when_serialized(self):
        instant = datetime(2026, 10, 9, 5, 45, tzinfo=timezone.utc)
        normalized = as_utc(instant)
        self.assertEqual(normalized.isoformat(), "2026-10-09T05:45:00+00:00")
        self.assertEqual(
            normalized.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST"),
            "09 Oct 2026, 11:15 AM IST",
        )

    def test_legacy_naive_timestamp_is_utc_without_changing_its_wall_time(self):
        legacy_value = datetime(2026, 10, 9, 5, 45)
        normalized = as_utc(legacy_value)
        self.assertEqual(normalized.replace(tzinfo=None), legacy_value)
        self.assertEqual(normalized.utcoffset(), timedelta(0))

    def test_waiting_time_uses_utc_instants_and_clamps_future_values(self):
        created_at = datetime(2026, 10, 9, 5, 45)
        now = datetime(2026, 10, 9, 7, 15, tzinfo=timezone.utc)
        self.assertEqual(elapsed_hours_since(created_at, now=now), 1.5)
        self.assertEqual(elapsed_hours_since(now + timedelta(hours=1), now=now), 0)
        self.assertEqual(elapsed_hours_since(None, now=now), 0)

    def test_new_case_and_submission_timeline_share_persisted_utc_timestamp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        try:
            with Session(engine) as db:
                farmer = User(
                    full_name="Timestamp Test Farmer",
                    email="timestamp-test@example.test",
                    password_hash="hash",
                    role="farmer",
                    created_at=utcnow_naive(),
                )
                db.add(farmer)
                db.flush()
                case = ClinicalCase(
                    owner_id=farmer.id,
                    cattle_tag="TIME-1",
                    symptoms="[]",
                    ai_prediction="Review",
                    risk_level="low",
                    status="submitted",
                )
                db.add(case)
                db.flush()
                saved_submission_time = case.created_at
                self.assertIsNone(saved_submission_time.tzinfo)
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                self.assertLess(abs((now_utc - saved_submission_time).total_seconds()), 5)

                record_case_submitted(db, case, farmer.id)
                db.flush()
                event = db.query(CaseEvent).filter_by(case_id=case.id, event="case_submitted").one()
                serialized_case = serialize(case)
                case_payload = jsonable_encoder(serialized_case)
                timeline_timestamp = jsonable_encoder(as_utc(event.created_at))

                self.assertEqual(event.created_at, saved_submission_time)
                self.assertEqual(serialized_case["created_at"], as_utc(saved_submission_time))
                self.assertEqual(as_utc(event.created_at), serialized_case["created_at"])
                self.assertTrue(case_payload["created_at"].endswith("+00:00"))
                self.assertEqual(case_payload["created_at"], timeline_timestamp)
        finally:
            Base.metadata.drop_all(engine)
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
