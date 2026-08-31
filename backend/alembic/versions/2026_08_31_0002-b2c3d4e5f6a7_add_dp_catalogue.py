"""add dp_catalogue

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-31
"""
import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dp_catalogue",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("country_source", sa.String(length=120), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("university_name", sa.String(length=300), nullable=False),
        sa.Column("program_name", sa.String(length=500), nullable=False),
        sa.Column("intake_year", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "level", "country_source", "university_name", "program_name", "intake_year",
            name="uq_dp_catalogue_entry",
        ),
    )
    op.create_index("ix_dp_catalogue_id", "dp_catalogue", ["id"])
    op.create_index("ix_dp_catalogue_level", "dp_catalogue", ["level"])
    op.create_index("ix_dp_catalogue_country_code", "dp_catalogue", ["country_code"])
    op.create_index("ix_dp_catalogue_university_name", "dp_catalogue", ["university_name"])
    op.create_index("ix_dp_catalogue_intake_year", "dp_catalogue", ["intake_year"])


def downgrade() -> None:
    op.drop_table("dp_catalogue")
