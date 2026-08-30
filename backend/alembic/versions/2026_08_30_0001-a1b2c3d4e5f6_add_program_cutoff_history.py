"""add program_cutoff_history

Revision ID: a1b2c3d4e5f6
Revises: ca962f4261fb
Create Date: 2026-08-30
"""
import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "ca962f4261fb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "program_cutoff_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("source_program_code", sa.String(length=300), nullable=False),
        sa.Column("variant_index", sa.Integer(), nullable=True),
        sa.Column("variant_discriminator_known", sa.Boolean(), nullable=True),
        sa.Column("intake_year", sa.Integer(), nullable=False),
        sa.Column("cutoff_value", sa.Float(), nullable=False),
        sa.Column("cutoff_unit", sa.String(length=50), nullable=False),
        sa.Column("lower_is_better", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("university_name", sa.String(length=300), nullable=False),
        sa.Column("department_name", sa.String(length=300), nullable=True),
        sa.Column("score_type", sa.String(length=100), nullable=True),
        sa.Column("scholarship_type", sa.String(length=100), nullable=True),
        sa.Column("is_undergraduate", sa.Boolean(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_program_cutoff_history_id", "program_cutoff_history", ["id"])
    op.create_index("ix_program_cutoff_history_country", "program_cutoff_history", ["country"])
    op.create_index(
        "ix_program_cutoff_history_source_program_code",
        "program_cutoff_history",
        ["source_program_code"],
    )
    op.create_index(
        "ix_program_cutoff_history_intake_year", "program_cutoff_history", ["intake_year"]
    )
    op.create_index(
        "ix_cutoff_history_series",
        "program_cutoff_history",
        ["country", "source_program_code", "variant_index", "intake_year"],
    )


def downgrade() -> None:
    op.drop_table("program_cutoff_history")
