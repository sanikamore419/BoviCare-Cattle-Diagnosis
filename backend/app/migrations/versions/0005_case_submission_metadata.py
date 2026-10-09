"""Add farmer-submitted metadata to clinical_cases for doctor review."""

from alembic import op
import sqlalchemy as sa

revision = "0005_case_submission_metadata"
down_revision = "0004_notification_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("clinical_cases") as batch:
        batch.add_column(sa.Column("cattle_name", sa.String(length=120), nullable=True))
        batch.add_column(sa.Column("gender", sa.String(length=20), nullable=True))
        batch.add_column(sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("clinical_cases") as batch:
        batch.drop_column("notes")
        batch.drop_column("gender")
        batch.drop_column("cattle_name")
