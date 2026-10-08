from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main
from app.database.session import Base
from app.models import User


class AdminSeedTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "admin-seed.db"
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.tempdir.cleanup()

    def run_seed(self, environment="test", email=None, password=None):
        settings = SimpleNamespace(environment=environment, admin_email=email, admin_password=password)
        with patch.object(main, "settings", settings), patch.object(main, "SessionLocal", self.session_factory):
            main.ensure_admin_account()

    def test_seeds_admin_from_environment_values(self):
        self.run_seed(email="admin@example.com", password="seed-test-password-123")
        with self.session_factory() as db:
            admin = db.query(User).filter(User.role == "admin").one()
            self.assertEqual(admin.email, "admin@example.com")
            self.assertNotEqual(admin.password_hash, "seed-test-password-123")

    def test_production_requires_admin_environment_when_no_admin_exists(self):
        with self.assertRaisesRegex(RuntimeError, "ADMIN_EMAIL and ADMIN_PASSWORD are required"):
            self.run_seed(environment="production")

    def test_existing_admin_skips_environment_seed(self):
        with self.session_factory.begin() as db:
            db.add(User(full_name="Existing admin", email="existing-admin@example.com", password_hash="hash", role="admin"))
        self.run_seed(environment="production")
        with self.session_factory() as db:
            self.assertEqual(db.query(User).filter(User.role == "admin").count(), 1)


if __name__ == "__main__":
    unittest.main()
