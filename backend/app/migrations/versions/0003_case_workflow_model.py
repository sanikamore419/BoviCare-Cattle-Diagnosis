"""Add constrained workflow fields and legacy migration events.

Revision ID: 0003_case_workflow_model
Revises: 0002_doctor_profile
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_case_workflow_model"
down_revision = "0002_doctor_profile"
branch_labels = None
depends_on = None

STATUS_MAP = {
    "pending": "pending_review",
    "pending_review": "pending_review",
    "new": "pending_review",
    "submitted": "submitted",
    "ai_complete": "ai_complete",
    "in_progress": "in_review",
    "in_review": "in_review",
    "accepted": "in_review",
    "claimed": "in_review",
    "reviewing": "in_review",
    "reviewed": "completed",
    "completed": "completed",
    "finished": "completed",
    "advice_received": "completed",
}
ALLOWED_STATUSES = ("submitted", "ai_complete", "pending_review", "in_review", "completed")


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    existing = _columns("clinical_cases")
    with op.batch_alter_table("clinical_cases") as batch:
        if "claimed_at" not in existing:
            batch.add_column(sa.Column("claimed_at", sa.DateTime(), nullable=True))
        if "completed_at" not in existing:
            batch.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))
        if "urgency_breakdown" not in existing:
            batch.add_column(sa.Column("urgency_breakdown", sa.JSON(), nullable=True))
        if "claimed_by" not in existing:
            batch.add_column(sa.Column("claimed_by", sa.Integer(), nullable=True))
            batch.create_foreign_key("fk_clinical_cases_claimed_by_users", "users", ["claimed_by"], ["id"])
        if "clinical_notes" not in existing:
            batch.add_column(sa.Column("clinical_notes", sa.Text(), nullable=True))
        batch.alter_column("status", existing_type=sa.String(30), type_=sa.String(30), server_default=sa.text("'submitted'"), nullable=False)

    inspector = sa.inspect(op.get_bind())
    if "case_events" not in inspector.get_table_names():
        op.create_table(
            "case_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("case_id", sa.Integer(), sa.ForeignKey("clinical_cases.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event", sa.String(60), nullable=False),
            sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
    else:
        required_event_columns = {"id", "case_id", "event", "actor_id", "meta", "created_at"}
        existing_event_columns = {column["name"] for column in inspector.get_columns("case_events")}
        if not required_event_columns.issubset(existing_event_columns):
            raise RuntimeError("Existing case_events table does not match the migration schema; inspect it before migrating.")
    existing_event_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("case_events")}
    if "ix_case_events_case_id" not in existing_event_indexes:
        op.create_index("ix_case_events_case_id", "case_events", ["case_id"])
    conn = op.get_bind()
    cases = sa.table(
        "clinical_cases",
        sa.column("id", sa.Integer()),
        sa.column("status", sa.String(30)),
        sa.column("created_at", sa.DateTime()),
        sa.column("veterinarian_id", sa.Integer()),
        sa.column("private_clinical_notes", sa.Text()),
    )
    case_events = sa.table(
        "case_events",
        sa.column("case_id", sa.Integer()),
        sa.column("event", sa.String(60)),
        sa.column("actor_id", sa.Integer()),
        sa.column("meta", sa.JSON()),
        sa.column("created_at", sa.DateTime()),
    )
    rows = conn.execute(sa.select(cases).order_by(cases.c.id)).mappings().all()
    for row in rows:
        old_status = (row["status"] or "").strip().lower()
        if old_status not in STATUS_MAP:
            raise RuntimeError(f"Cannot migrate case {row['id']}: unsupported legacy status {old_status!r}.")
        new_status = STATUS_MAP[old_status]
        conn.execute(
            sa.text("UPDATE clinical_cases SET status = :status, claimed_by = COALESCE(claimed_by, veterinarian_id), clinical_notes = COALESCE(clinical_notes, private_clinical_notes) WHERE id = :id"),
            {"status": new_status, "id": row["id"]},
        )
        created_at = row["created_at"]
        conn.execute(
            sa.text("UPDATE clinical_cases SET claimed_at = (SELECT MIN(created_at) FROM notification_logs WHERE notification_logs.case_id = clinical_cases.id AND notification_logs.notification_type = 'veterinarian_reviewing_case') WHERE id = :id AND claimed_at IS NULL"),
            {"id": row["id"]},
        )
        conn.execute(
            sa.text("UPDATE clinical_cases SET completed_at = (SELECT MAX(created_at) FROM notification_logs WHERE notification_logs.case_id = clinical_cases.id AND notification_logs.notification_type = 'veterinary_advice_received') WHERE id = :id AND completed_at IS NULL"),
            {"id": row["id"]},
        )
        conn.execute(case_events.insert().values(
            case_id=row["id"], event="legacy_migrated", actor_id=None,
            meta={"from_status": old_status, "to_status": new_status}, created_at=created_at,
        ))

    with op.batch_alter_table("clinical_cases") as batch:
        batch.create_check_constraint("ck_clinical_cases_status_allowed", "status IN ('submitted', 'ai_complete', 'pending_review', 'in_review', 'completed')")
    op.create_index("ix_clinical_cases_status", "clinical_cases", ["status"])
    op.create_index("ix_clinical_cases_claimed_by", "clinical_cases", ["claimed_by"])
    op.create_index("ix_clinical_cases_urgency_level_score", "clinical_cases", ["urgency_level", "urgency_score"])


def downgrade() -> None:
    op.drop_index("ix_clinical_cases_urgency_level_score", table_name="clinical_cases")
    op.drop_index("ix_clinical_cases_claimed_by", table_name="clinical_cases")
    op.drop_index("ix_clinical_cases_status", table_name="clinical_cases")
    op.drop_index("ix_case_events_case_id", table_name="case_events")
    op.drop_table("case_events")
    with op.batch_alter_table("clinical_cases") as batch:
        batch.drop_constraint("ck_clinical_cases_status_allowed", type_="check")
        batch.alter_column("status", existing_type=sa.String(30), server_default=None, nullable=False)
        batch.drop_constraint("fk_clinical_cases_claimed_by_users", type_="foreignkey")
        batch.drop_column("clinical_notes")
        batch.drop_column("urgency_breakdown")
        batch.drop_column("claimed_by")
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE clinical_cases SET status = CASE status WHEN 'in_review' THEN 'in_progress' WHEN 'completed' THEN 'reviewed' WHEN 'submitted' THEN 'pending_review' WHEN 'ai_complete' THEN 'pending_review' ELSE status END"))
