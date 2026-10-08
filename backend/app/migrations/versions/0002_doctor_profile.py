"""Add doctor verification and availability fields.

Revision ID: 0002_doctor_profile
Revises: 0001_baseline
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_doctor_profile"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("registration_number", sa.String(100), nullable=True))
        batch.add_column(sa.Column("specialization", sa.String(160), nullable=True))
        batch.add_column(sa.Column("verification_status", sa.String(20), nullable=True))
        batch.add_column(sa.Column("verified_by", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("verified_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("availability", sa.String(20), nullable=True))
        batch.add_column(sa.Column("availability_updated_at", sa.DateTime(), nullable=True))
        batch.create_foreign_key("fk_users_verified_by_users", "users", ["verified_by"], ["id"])
        batch.create_check_constraint(
            "ck_users_verification_status_allowed",
            "verification_status IS NULL OR verification_status IN ('pending', 'approved', 'rejected')",
        )
        batch.create_check_constraint(
            "ck_users_availability_allowed",
            "availability IS NULL OR availability IN ('available', 'busy', 'offline')",
        )

    op.execute(sa.text("UPDATE users SET verification_status = 'approved', availability = 'offline' WHERE role = 'doctor'"))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("ck_users_availability_allowed", type_="check")
        batch.drop_constraint("ck_users_verification_status_allowed", type_="check")
        batch.drop_constraint("fk_users_verified_by_users", type_="foreignkey")
        batch.drop_column("availability_updated_at")
        batch.drop_column("availability")
        batch.drop_column("verified_at")
        batch.drop_column("verified_by")
        batch.drop_column("verification_status")
        batch.drop_column("specialization")
        batch.drop_column("registration_number")
