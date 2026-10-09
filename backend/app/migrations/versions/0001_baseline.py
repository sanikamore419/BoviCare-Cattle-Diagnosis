"""Baseline for the deployed BoviCare backend schema.

Revision ID: 0001_baseline
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def _adopt_existing_schema() -> bool:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    required_columns = {
        "users": {"id", "full_name", "email", "password_hash", "role", "created_at"},
        "cattle": {"id", "farmer_id", "tag_number", "name", "breed", "date_of_birth", "sex", "weight_kg", "created_at", "updated_at"},
        "clinical_cases": {"id", "owner_id", "cattle_id", "cattle_tag", "breed", "age_years", "temperature_c", "symptoms", "ai_prediction", "risk_level", "status", "urgency_score", "urgency_level", "veterinarian_id", "claimed_at", "completed_at", "farmer_advice", "veterinarian_notes", "private_clinical_notes", "created_at"},
        "case_images": {"id", "case_id", "cattle_id", "owner_id", "stored_filename", "content_type", "created_at"},
        "prediction_results": {"id", "case_id", "cattle_id", "owner_id", "model_name", "model_version", "rank", "disease_label", "probability", "risk_level", "created_at"},
        "notification_logs": {"id", "case_id", "notification_type", "target_role", "status", "event_payload", "created_at"},
    }
    if not inspector.has_table("users"):
        return False

    for table_name, expected in required_columns.items():
        if not inspector.has_table(table_name):
            raise RuntimeError(
                f"Cannot adopt the existing database: required table {table_name!r} is missing."
            )
        actual = {column["name"] for column in inspector.get_columns(table_name)}
        if not expected.issubset(actual):
            missing = sorted(expected - actual)
            raise RuntimeError(
                f"Cannot adopt the existing database: table {table_name!r} is missing columns {missing}."
            )

    if not inspector.has_table("refresh_sessions"):
        op.create_table(
            "refresh_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("revoked_at", sa.DateTime()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    else:
        actual = {column["name"] for column in inspector.get_columns("refresh_sessions")}
        expected = {"id", "user_id", "token_hash", "expires_at", "revoked_at", "created_at"}
        if not expected.issubset(actual):
            missing = sorted(expected - actual)
            raise RuntimeError(
                f"Cannot adopt the existing database: table 'refresh_sessions' is missing columns {missing}."
            )

    indexes = {
        "users": [("ix_users_email", ["email"], True)],
        "cattle": [("ix_cattle_farmer_id", ["farmer_id"], False), ("ix_cattle_tag_number", ["tag_number"], False)],
        "clinical_cases": [
            ("ix_clinical_cases_cattle_tag", ["cattle_tag"], False),
            ("ix_clinical_cases_cattle_id", ["cattle_id"], False),
            ("ix_clinical_cases_veterinarian_id", ["veterinarian_id"], False),
            ("ix_clinical_cases_owner_id", ["owner_id"], False),
        ],
        "case_images": [
            ("ix_case_images_case_id", ["case_id"], True),
            ("ix_case_images_cattle_id", ["cattle_id"], False),
            ("ix_case_images_owner_id", ["owner_id"], False),
        ],
        "prediction_results": [
            ("ix_prediction_results_case_id", ["case_id"], False),
            ("ix_prediction_results_cattle_id", ["cattle_id"], False),
            ("ix_prediction_results_owner_id", ["owner_id"], False),
        ],
        "notification_logs": [("ix_notification_logs_case_id", ["case_id"], False)],
        "refresh_sessions": [
            ("ix_refresh_sessions_user_id", ["user_id"], False),
            ("ix_refresh_sessions_token_hash", ["token_hash"], True),
            ("ix_refresh_sessions_expires_at", ["expires_at"], False),
        ],
    }
    for table_name, table_indexes in indexes.items():
        existing = {index["name"] for index in sa.inspect(connection).get_indexes(table_name)}
        for name, columns, unique in table_indexes:
            if name not in existing:
                op.create_index(name, table_name, columns, unique=unique)
    return True


def upgrade() -> None:
    if _adopt_existing_schema():
        return

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "cattle",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tag_number", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120)),
        sa.Column("breed", sa.String(100)),
        sa.Column("date_of_birth", sa.String(20)),
        sa.Column("sex", sa.String(10), nullable=False),
        sa.Column("weight_kg", sa.Float()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_cattle_farmer_id", "cattle", ["farmer_id"])
    op.create_index("ix_cattle_tag_number", "cattle", ["tag_number"])

    op.create_table(
        "clinical_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("cattle_id", sa.Integer(), sa.ForeignKey("cattle.id")),
        sa.Column("cattle_tag", sa.String(80), nullable=False),
        sa.Column("breed", sa.String(100)),
        sa.Column("age_years", sa.Float()),
        sa.Column("temperature_c", sa.Float()),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("ai_prediction", sa.String(255), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("urgency_score", sa.Float()),
        sa.Column("urgency_level", sa.String(20)),
        sa.Column("veterinarian_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("claimed_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("farmer_advice", sa.Text()),
        sa.Column("veterinarian_notes", sa.Text()),
        sa.Column("private_clinical_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name, column in [
        ("ix_clinical_cases_cattle_tag", "cattle_tag"),
        ("ix_clinical_cases_cattle_id", "cattle_id"),
        ("ix_clinical_cases_veterinarian_id", "veterinarian_id"),
        ("ix_clinical_cases_owner_id", "owner_id"),
    ]:
        op.create_index(name, "clinical_cases", [column])

    op.create_table(
        "case_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("clinical_cases.id"), nullable=False),
        sa.Column("cattle_id", sa.Integer(), sa.ForeignKey("cattle.id")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("stored_filename", sa.String(120), nullable=False, unique=True),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_case_images_case_id", "case_images", ["case_id"], unique=True)
    op.create_index("ix_case_images_cattle_id", "case_images", ["cattle_id"])
    op.create_index("ix_case_images_owner_id", "case_images", ["owner_id"])

    op.create_table(
        "prediction_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("clinical_cases.id")),
        sa.Column("cattle_id", sa.Integer(), sa.ForeignKey("cattle.id")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("model_name", sa.String(60), nullable=False),
        sa.Column("model_version", sa.String(40), nullable=False),
        sa.Column("rank", sa.Integer()),
        sa.Column("disease_label", sa.String(120), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for name, column in [
        ("ix_prediction_results_case_id", "case_id"),
        ("ix_prediction_results_cattle_id", "cattle_id"),
        ("ix_prediction_results_owner_id", "owner_id"),
    ]:
        op.create_index(name, "prediction_results", [column])

    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("clinical_cases.id"), nullable=False),
        sa.Column("notification_type", sa.String(40), nullable=False),
        sa.Column("target_role", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("event_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notification_logs_case_id", "notification_logs", ["case_id"])

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])
    op.create_index("ix_refresh_sessions_token_hash", "refresh_sessions", ["token_hash"], unique=True)
    op.create_index("ix_refresh_sessions_expires_at", "refresh_sessions", ["expires_at"])


def downgrade() -> None:
    op.drop_table("refresh_sessions")
    op.drop_table("notification_logs")
    op.drop_table("prediction_results")
    op.drop_table("case_images")
    op.drop_table("clinical_cases")
    op.drop_table("cattle")
    op.drop_table("users")
