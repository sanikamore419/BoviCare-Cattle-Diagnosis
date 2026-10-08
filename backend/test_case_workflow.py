import os
import queue
import threading
import tempfile
import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.database.session import Base
from app.models.case import ClinicalCase
from app.models.case_event import CaseEvent
from app.models.notification import NotificationLog
from app.models.user import User
from app.routers.cases import (
    calculate_case_urgency,
    claim_case_for_veterinarian,
    get_case_notifications,
    get_case_workflow_status,
)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False, "timeout": 30},
        )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _make_vet(self, email: str):
        user = User(full_name=f"Demo {email}", email=email, password_hash="x", role="doctor")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def test_urgency_score_is_in_range_and_high_for_high_risk(self):
        case = ClinicalCase(
            owner_id=1,
            cattle_tag="COW-1",
            symptoms='["difficulty breathing", "fever", "decreased appetite", "lethargy", "weight loss"]',
            ai_prediction="Urgent clinical review needed",
            risk_level="high",
            age_years=8,
            temperature_c=40.8,
            created_at=datetime.utcnow() - timedelta(hours=13),
        )
        score = calculate_case_urgency(case)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertEqual(get_case_workflow_status(case), "PENDING")
        self.assertEqual(case.urgency_level, "HIGH")

    def test_case_claim_sets_vet_and_status(self):
        vet = self._make_vet("vet@example.com")
        case = ClinicalCase(
            owner_id=1,
            cattle_tag="COW-2",
            symptoms='["coughing"]',
            ai_prediction="Veterinary assessment recommended",
            risk_level="medium",
            status="pending_review",
            created_at=datetime.utcnow() - timedelta(hours=12),
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)

        claimed = claim_case_for_veterinarian(case.id, vet.id, self.db)
        self.assertEqual(claimed.veterinarian_id, vet.id)
        self.assertEqual(claimed.status, "in_review")
        self.assertEqual(claimed.claimed_by, vet.id)
        self.assertIsNotNone(claimed.claimed_at)
        event = self.db.query(CaseEvent).filter(CaseEvent.case_id == case.id).one()
        self.assertEqual(event.event, "status_changed")
        self.assertEqual(event.meta, {"from_status": "pending_review", "to_status": "in_review"})

    def test_two_claim_attempts_do_not_both_succeed(self):
        vet_1 = self._make_vet("vet1@example.com")
        vet_2 = self._make_vet("vet2@example.com")
        case = ClinicalCase(
            owner_id=1,
            cattle_tag="COW-3",
            symptoms='["lameness"]',
            ai_prediction="Veterinary assessment recommended",
            risk_level="medium",
            status="pending_review",
            created_at=datetime.utcnow() - timedelta(hours=1),
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        self.db.commit()

        outcome = queue.Queue()
        start = threading.Barrier(3)
        Session = sessionmaker(bind=self.engine)

        def try_claim(vet_id):
            local_db = Session()
            try:
                start.wait(timeout=10)
                result = claim_case_for_veterinarian(case.id, vet_id, local_db)
                outcome.put((vet_id, "winner", result.veterinarian_id, result.status))
            except HTTPException as exc:
                outcome.put((vet_id, "conflict" if exc.status_code == 409 else "http_error", exc.status_code))
            except Exception as exc:  # Capture unexpected worker errors for an actionable assertion.
                outcome.put((vet_id, "error", repr(exc)))
            finally:
                local_db.close()

        threads = [threading.Thread(target=try_claim, args=(vet_1.id,)), threading.Thread(target=try_claim, args=(vet_2.id,))]
        for thread in threads:
            thread.start()
        start.wait(timeout=10)
        for thread in threads:
            thread.join(timeout=15)

        self.assertTrue(all(not thread.is_alive() for thread in threads), "claim workers did not finish")
        results = [outcome.get_nowait() for _ in threads]
        winners = [entry for entry in results if entry[1] == "winner"]
        conflicts = [entry for entry in results if entry[1] == "conflict"]
        self.assertEqual(len(winners), 1, msg=f"Expected one claim winner, got {results}")
        self.assertEqual(len(conflicts), 1, msg=f"Expected the losing doctor to receive 409, got {results}")
        self.assertIn(winners[0][0], (vet_1.id, vet_2.id))
        self.assertEqual(winners[0][2], winners[0][0])
        self.assertEqual(winners[0][3], "in_review")
        self.db.refresh(case)
        self.assertEqual(case.veterinarian_id, winners[0][0])

    def test_case_notification_list_excludes_legacy_rows_without_user_id(self):
        farmer = User(full_name="Farmer", email="farmer@example.com", password_hash="x", role="farmer")
        doctor = self._make_vet("notification-vet@example.com")
        self.db.add(farmer)
        self.db.commit()
        self.db.refresh(farmer)
        case = ClinicalCase(owner_id=farmer.id, cattle_tag="COW-N", symptoms="[]", ai_prediction="Review", risk_level="low", status="pending_review")
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        self.db.add_all([
            NotificationLog(case_id=case.id, notification_type="legacy_event", target_role="farmer", status="mock", event_payload="{}", user_id=None),
            NotificationLog(case_id=case.id, notification_type="farmer_event", target_role="farmer", status="mock", event_payload="{}", user_id=farmer.id),
            NotificationLog(case_id=case.id, notification_type="doctor_event", target_role="doctor", status="mock", event_payload="{}", user_id=doctor.id),
        ])
        self.db.commit()

        response = get_case_notifications(case.id, self.db, farmer)
        self.assertEqual([item["notification_type"] for item in response], ["farmer_event"])


if __name__ == "__main__":
    unittest.main()
