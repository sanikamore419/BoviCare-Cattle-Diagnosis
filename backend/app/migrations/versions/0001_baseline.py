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


def upgrade() -> None:
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
