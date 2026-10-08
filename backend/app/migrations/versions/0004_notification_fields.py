"""Extend notification_logs in place without replacing legacy records.

Revision ID: 0004_notification_fields
Revises: 0003_case_workflow_model
"""
import json

from alembic import op
import sqlalchemy as sa

revision = "0004_notification_fields"
down_revision = "0003_case_workflow_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notification_logs") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("type", sa.String(40), nullable=True))
        batch.add_column(sa.Column("message_key", sa.String(100), nullable=True))
        batch.add_column(sa.Column("params", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_foreign_key("fk_notification_logs_user_id_users", "users", ["user_id"], ["id"])

    conn = op.get_bind()
    notifications = sa.table(
        "notification_logs",
        sa.column("id", sa.Integer()),
        sa.column("notification_type", sa.String(40)),
        sa.column("event_payload", sa.Text()),
    )
    new_fields = sa.table(
        "notification_logs",
        sa.column("id", sa.Integer()),
        sa.column("type", sa.String(40)),
        sa.column("message_key", sa.String(100)),
        sa.column("params", sa.JSON()),
    )
    rows = conn.execute(sa.select(notifications)).mappings().all()
    for row in rows:
        payload = row["event_payload"]
        try:
            params = json.loads(payload) if payload else {}
        except (TypeError, ValueError):
            params = {"legacy_payload": payload}
        conn.execute(new_fields.update().where(new_fields.c.id == row["id"]).values(
            type=row["notification_type"], message_key=row["notification_type"], params=params,
        ))

    op.create_index("ix_notification_logs_user_read", "notification_logs", ["user_id", "read"])


def downgrade() -> None:
    op.drop_index("ix_notification_logs_user_read", table_name="notification_logs")
    with op.batch_alter_table("notification_logs") as batch:
        batch.drop_constraint("fk_notification_logs_user_id_users", type_="foreignkey")
        batch.drop_column("read")
        batch.drop_column("params")
        batch.drop_column("message_key")
        batch.drop_column("type")
        batch.drop_column("user_id")
