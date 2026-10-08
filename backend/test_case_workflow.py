import os
import threading
import tempfile
import unittest
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.case import ClinicalCase
from app.models.user import User
from app.routers.cases import (
    calculate_case_urgency,
    claim_case_for_veterinarian,
    get_case_workflow_status,
)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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
            symptoms='["difficulty breathing", "fever", "decreased appetite"]',
            ai_prediction="Urgent clinical review needed",
            risk_level="high",
            age_years=7,
            temperature_c=40.8,
            created_at=datetime.utcnow() - timedelta(hours=2),
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
        self.assertEqual(claimed.status, "in_progress")
        self.assertIsNotNone(claimed.claimed_at)

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

        outcome = []
        Session = sessionmaker(bind=self.engine)

        def try_claim(vet_id):
            local_db = Session()
            try:
                result = claim_case_for_veterinarian(case.id, vet_id, local_db)
                outcome.append((vet_id, result.veterinarian_id, result.status))
            except Exception as exc:  # pragma: no cover - concurrency guard test path
                outcome.append((vet_id, "error", str(exc)))
            finally:
                local_db.close()

        threads = [threading.Thread(target=try_claim, args=(vet_1.id,)), threading.Thread(target=try_claim, args=(vet_2.id,))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assigned = [entry for entry in outcome if entry[1] not in ("error",)]
        self.assertEqual(len(assigned), 1)
        self.assertIn(assigned[0][0], (vet_1.id, vet_2.id))
        self.db.refresh(case)
        self.assertEqual(case.veterinarian_id, assigned[0][0])


if __name__ == "__main__":
    unittest.main()
