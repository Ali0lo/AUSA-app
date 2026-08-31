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

    op.create_table(
        "student_qualifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("level_sought", sa.String(length=20), nullable=False),
        sa.Column("qualification_held", sa.String(length=50), nullable=False),
        sa.Column("dim_score", sa.Float(), nullable=True),
        sa.Column("ielts", sa.Float(), nullable=True),
        sa.Column("toefl", sa.Integer(), nullable=True),
        sa.Column("sat", sa.Integer(), nullable=True),
        sa.Column("act", sa.Integer(), nullable=True),
        sa.Column("tr_yos", sa.Float(), nullable=True),
        sa.Column("test_as", sa.Float(), nullable=True),
        sa.Column("csca", sa.Float(), nullable=True),
        sa.Column("hsk", sa.Integer(), nullable=True),
        sa.Column("language_certificate_level", sa.String(length=10), nullable=True),
        sa.Column("has_international_olympiad_medal", sa.Boolean(), nullable=True),
        sa.Column("budget_azn_per_year", sa.Float(), nullable=True),
        sa.Column("field_of_interest", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "level_sought", name="uq_student_qualification_level"),
    )
    op.create_index("ix_student_qualifications_id", "student_qualifications", ["id"])
    op.create_index("ix_student_qualifications_student_id", "student_qualifications", ["student_id"])

    op.create_table(
        "program_requirements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("university_name", sa.String(length=300), nullable=False),
        sa.Column("program_name", sa.String(length=500), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("intake_year", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("entry_qualification_accepted", sa.String(length=50), nullable=True),
        sa.Column("foundation_required", sa.Boolean(), nullable=True),
        sa.Column("foundation_providers", sa.Text(), nullable=True),
        sa.Column("language_test", sa.String(length=30), nullable=True),
        sa.Column("language_minimum_score", sa.Float(), nullable=True),
        sa.Column("language_of_instruction", sa.String(length=50), nullable=True),
        sa.Column("entrance_exam", sa.String(length=30), nullable=True),
        sa.Column("entrance_exam_minimum", sa.Float(), nullable=True),
        sa.Column("gpa_minimum", sa.Float(), nullable=True),
        sa.Column("gpa_scale", sa.String(length=10), nullable=True),
        sa.Column("tuition_per_year", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("living_cost_estimate_per_year", sa.Float(), nullable=True),
        sa.Column("application_fee", sa.Float(), nullable=True),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("application_portal", sa.String(length=60), nullable=True),
        sa.Column("documents_required", sa.Text(), nullable=True),
        sa.Column("provenance", sa.String(length=30), nullable=False, server_default="claude-extracted"),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_text_hash", sa.String(length=64), nullable=True),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "university_name", "program_name", "level", "intake_year",
            name="uq_program_requirement_entry",
        ),
    )
    op.create_index("ix_program_requirements_id", "program_requirements", ["id"])
    op.create_index("ix_program_requirements_university_name", "program_requirements", ["university_name"])
    op.create_index("ix_program_requirements_level", "program_requirements", ["level"])
    op.create_index("ix_program_requirements_country_code", "program_requirements", ["country_code"])
    op.create_index("ix_program_requirements_intake_year", "program_requirements", ["intake_year"])


def downgrade() -> None:
    op.drop_table("program_requirements")
    op.drop_table("student_qualifications")
    op.drop_table("dp_catalogue")
