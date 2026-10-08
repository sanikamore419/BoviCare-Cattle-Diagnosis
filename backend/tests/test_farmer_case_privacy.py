import os
import tempfile
import unittest
import asyncio
import json
from urllib.parse import urlsplit
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token
from app.database import get_db
from app.database.session import Base
from app.main import app
from app.models import ClinicalCase, User


class FarmerCasePrivacyTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        path = Path(self.tempdir.name) / "farmer-case.db"
        self.engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

        def override_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        with self.Session.begin() as db:
            farmer = User(full_name="Test Farmer", email="privacy-farmer@example.test", password_hash="hash", role="farmer")
            db.add(farmer)
            db.flush()
            self.farmer_id = farmer.id
            case = ClinicalCase(
                owner_id=farmer.id, cattle_tag="PRIVACY-1", symptoms="[]", ai_prediction="Review",
                risk_level="low", status="completed", farmer_advice="Please contact your veterinarian.",
                clinical_notes="private clinical note sentinel", private_clinical_notes="private alias sentinel",
                veterinarian_notes="private legacy alias sentinel",
            )
            db.add(case)
            db.flush()
            self.case_id = case.id

    async def _request(self, path, headers):
        messages = []
        request_sent = False

        async def receive():
            nonlocal request_sent
            if request_sent:
                await asyncio.Event().wait()
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        parsed_path = urlsplit(path)
        raw_path = parsed_path.path.encode("ascii")
        scope = {
            "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1", "method": "GET", "scheme": "http",
            "path": parsed_path.path, "raw_path": raw_path, "query_string": parsed_path.query.encode("ascii"), "root_path": "",
            "headers": [(key.lower().encode("ascii"), value.encode("latin-1")) for key, value in headers.items()],
            "client": ("testclient", 50000), "server": ("testserver", 80),
            "extensions": {},
        }
        await app(scope, receive, send)
        status_code = next(message["status"] for message in messages if message["type"] == "http.response.start")
        body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
        return status_code, body

    def tearDown(self):
        app.dependency_overrides.pop(get_db, None)
        self.engine.dispose()
        self.tempdir.cleanup()

    def test_farmer_case_response_omits_all_private_note_fields(self):
        token = create_access_token(str(self.farmer_id))
        status_code, body = asyncio.run(self._request(
            f"/api/v1/cases/{self.case_id}", {"Authorization": f"Bearer {token}"},
        ))
        response_text = body.decode("utf-8")
        self.assertEqual(status_code, 200, response_text)
        payload = json.loads(response_text)
        self.assertEqual(payload["farmer_advice"], "Please contact your veterinarian.")
        self.assertNotIn("clinical_notes", payload)
        self.assertNotIn("private_clinical_notes", payload)
        self.assertNotIn("veterinarian_notes", payload)
        self.assertNotIn("private clinical note sentinel", response_text)
        self.assertNotIn("private alias sentinel", response_text)
        self.assertNotIn("private legacy alias sentinel", response_text)

    def test_farmer_report_download_is_pdf_and_hides_private_note_sentinels(self):
        token = create_access_token(str(self.farmer_id))
        status_code, body = asyncio.run(self._request(
            f"/api/v1/cases/{self.case_id}/report?language=en",
            {"Authorization": f"Bearer {token}"},
        ))
        self.assertEqual(status_code, 200)
        self.assertTrue(body.startswith(b"%PDF"), repr(body[:80]))
        self.assertNotIn(b"private clinical note sentinel", body)
        self.assertNotIn(b"private alias sentinel", body)


if __name__ == "__main__":
    unittest.main()
