"""Safely migrate backend/bovicare.db after verifying the deployed baseline.

Run from backend/: python scripts/migrate_active_database.py
The script never reads .env and never targets the repository-root database.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
DATABASE_PATH = (BACKEND_DIR / "bovicare.db").resolve()
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
EXPECTED_COUNTS = {
    "users": 5,
    "clinical_cases": 2,
    "prediction_results": 12,
    "notification_logs": 4,
    "refresh_sessions": 2,
    "case_images": 1,
    "cattle": 0,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def signature(engine: Engine) -> dict:
    inspector = inspect(engine)
    result = {}
    for table in sorted(name for name in inspector.get_table_names() if name != "alembic_version"):
        columns = tuple(
            (column["name"], str(column["type"]).upper(), column["nullable"], column["primary_key"])
            for column in inspector.get_columns(table)
        )
        indexes = tuple(sorted(
            (index["name"], tuple(index["column_names"]), index["unique"])
            for index in inspector.get_indexes(table)
        ))
        foreign_keys = tuple(sorted(
            (tuple(fk["constrained_columns"]), fk["referred_table"], tuple(fk["referred_columns"]))
            for fk in inspector.get_foreign_keys(table)
        ))
        result[table] = (columns, indexes, foreign_keys)
    return result


def assert_integrity(connection) -> None:
    integrity = connection.exec_driver_sql("PRAGMA integrity_check").fetchall()
    if integrity != [("ok",)]:
        raise RuntimeError(f"SQLite integrity_check failed: {integrity!r}")
    foreign_keys = connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
    if foreign_keys:
        raise RuntimeError(f"SQLite foreign_key_check failed: {foreign_keys!r}")


def migration_config(database_url: str):
    # Disable Pydantic's .env loader before Alembic imports application models.
    from app.core.config import Settings

    Settings.model_config["env_file"] = None
    from alembic.config import Config

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(BACKEND_DIR / "app" / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def verify_expected_rows(connection) -> dict[str, int]:
    counts = {
        table: connection.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar_one()
        for table in EXPECTED_COUNTS
    }
    if counts != EXPECTED_COUNTS:
        raise RuntimeError(f"Unexpected row counts: {counts!r}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH, help="SQLite database to migrate; defaults to backend/bovicare.db")
    args = parser.parse_args()
    database_path = args.database.resolve()
    root_database = (BACKEND_DIR.parent / "bovicare.db").resolve()
    if database_path == root_database:
        raise RuntimeError("Refusing to migrate the repository-root bovicare.db.")
    if not database_path.is_file():
        raise RuntimeError(f"Database does not exist: {database_path}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = database_path.with_name(f"{database_path.name}.bak-{timestamp}")
    if backup_path.exists():
        raise RuntimeError(f"Refusing to overwrite existing backup: {backup_path}")
    shutil.copy2(database_path, backup_path)
    backup_size = backup_path.stat().st_size
    backup_hash = sha256(backup_path)
    print(f"backup={backup_path}")
    print(f"backup_size_bytes={backup_size}")
    print(f"backup_sha256={backup_hash}")

    # Avoid loading .env. Alembic receives the exact active file URL below.
    database_url = f"sqlite:///{database_path.as_posix()}"
    os.environ["DATABASE_URL"] = database_url

    from alembic import command

    config = migration_config(database_url)
    target_engine = create_engine(database_url, connect_args={"check_same_thread": False})
    baseline_engine = create_engine("sqlite://")
    target_connection = target_engine.connect()
    baseline_connection = baseline_engine.connect()
    changed = False
    try:
        # Generate the expected baseline using the checked-in 0001 migration.
        config.attributes["connection"] = baseline_connection
        command.upgrade(config, "0001_baseline")

        config.attributes["connection"] = target_connection
        # Alembic batch mode rebuilds users; SQLite blocks dropping a referenced
        # parent table while enforcement is on. Validate all references before
        # commit with foreign_key_check instead.
        target_connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        assert_integrity(target_connection)

        tables = inspect(target_connection).get_table_names()
        if "case_events" not in tables:
            raise RuntimeError("Expected the startup-created case_events table; refusing to continue.")
        event_rows = target_connection.execute(text("SELECT COUNT(*) FROM case_events")).scalar_one()
        if event_rows != 0:
            raise RuntimeError(f"case_events contains {event_rows} rows; refusing to drop it.")

        # Start an explicit SQLite write transaction before any DDL.
        target_connection.exec_driver_sql("BEGIN IMMEDIATE")
        target_connection.exec_driver_sql("DROP TABLE case_events")
        changed = True

        if signature(target_connection) != signature(baseline_connection):
            raise RuntimeError("Active schema does not match migration 0001_baseline; refusing to stamp.")

        config.attributes["connection"] = target_connection
        command.stamp(config, "0001_baseline")
        command.upgrade(config, "head")

        revision = target_connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        if revision != "0004_notification_fields":
            raise RuntimeError(f"Unexpected migration state: {revision}")

        counts = verify_expected_rows(target_connection)
        events = target_connection.execute(text("SELECT COUNT(*) FROM case_events WHERE event='legacy_migrated'")).scalar_one()
        if events != EXPECTED_COUNTS["clinical_cases"]:
            raise RuntimeError(f"Expected one legacy event per case, found {events}.")
        doctor_states = target_connection.execute(text("SELECT DISTINCT verification_status FROM users WHERE role='doctor'")).scalars().all()
        if not doctor_states or any(state != "approved" for state in doctor_states):
            raise RuntimeError(f"Existing doctors are not all approved: {doctor_states!r}")
        assert_integrity(target_connection)

        target_connection.commit()
        print(f"migration_state={revision}")
        print(f"row_counts={counts}")
        print(f"legacy_migrated_events={events}")
        print(f"existing_doctor_verification_statuses={doctor_states}")
        print("integrity_check=ok")
        print("foreign_key_check=ok")
    except Exception:
        if target_connection.in_transaction():
            target_connection.rollback()
        target_connection.close()
        target_engine.dispose()
        baseline_connection.close()
        baseline_engine.dispose()
        if changed:
            shutil.copy2(backup_path, database_path)
            print("migration_failed; active database restored from timestamped backup", file=sys.stderr)
        raise
    finally:
        if not target_connection.closed:
            target_connection.close()
        target_engine.dispose()
        if not baseline_connection.closed:
            baseline_connection.close()
        baseline_engine.dispose()


if __name__ == "__main__":
    main()
