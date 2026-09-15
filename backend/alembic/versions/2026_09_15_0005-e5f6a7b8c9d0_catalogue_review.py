"""Retain alternative entry qualifications and record scoped catalogue evidence.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""
from alembic import op
import sqlalchemy as sa

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uq_program_requirement_entry", "program_requirements", type_="unique")
    op.create_index("uq_program_requirement_entry", "program_requirements", [
        "country_code", "university_name", "program_name", "level", "intake_year",
        sa.text("coalesce(entry_qualification_accepted, '')"),
    ], unique=True)
    op.add_column("program_requirements", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("program_requirements", sa.Column("evidence", sa.Text(), nullable=True))
    op.add_column("program_requirements", sa.Column("requirement_scope", sa.String(20), nullable=False, server_default="general"))
    op.add_column("program_requirements", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True))
    # The old launcher created this existing Track C model via create_all in the LLM
    # seeder. Preserve that capability when deterministic startup uses migrations.
    op.execute("""CREATE TABLE IF NOT EXISTS student_applications (
        id SERIAL PRIMARY KEY, student_id VARCHAR(100) NOT NULL,
        program_id INTEGER, university_name VARCHAR(200) NOT NULL,
        program_name VARCHAR(300) NOT NULL, degree_level VARCHAR(20),
        country VARCHAR(50), deadline DATE, stage VARCHAR(50) NOT NULL,
        notes TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    )""")
    op.execute("CREATE INDEX IF NOT EXISTS ix_student_applications_id ON student_applications (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_student_applications_student_id ON student_applications (student_id)")


def downgrade():
    # Never remove student_applications: it may predate this migration and contain
    # another teammate's application records.
    # Returning to the old key would discard legitimate alternative routes. Refuse a
    # destructive downgrade unless the operator has explicitly resolved those records.
    duplicate = op.get_bind().execute(sa.text(
        "SELECT 1 FROM program_requirements GROUP BY university_name, program_name, "
        "level, intake_year HAVING count(*) > 1 LIMIT 1"
    )).first()
    if duplicate:
        raise RuntimeError("Resolve alternative qualification rows before downgrading; no data was removed.")
    op.drop_index("uq_program_requirement_entry", table_name="program_requirements")
    op.create_unique_constraint("uq_program_requirement_entry", "program_requirements", [
        "university_name", "program_name", "level", "intake_year",
    ])
    for name in ("verified_at", "requirement_scope", "evidence", "notes"):
        op.drop_column("program_requirements", name)
