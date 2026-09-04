"""add gpa and gpa_scale to student_qualifications

The route engine could compare a student's exam scores to a route's bars but had no grade
at all, so `program_requirements.gpa_minimum` was displayed and never checked. These two
columns are the student's half of that comparison.

They are added as a PAIR, and that is the point. `program_requirements` has stored
gpa_minimum beside gpa_scale since it was created, on the rule that a grade without its
scale is not a number; storing a student's grade without one would break the same rule on
the other side. An Azerbaijani attestat average of 4.5 is excellent on its five-point
scale and impossible on a four-point one, and nothing but the scale distinguishes them.

Both are nullable. A student who has not given us a grade has no grade, and a NULL here
means unknown -- never zero, and never "no grade requirement applies" (ADR-0004).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-04
"""
import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("student_qualifications", sa.Column("gpa", sa.Float(), nullable=True))
    op.add_column(
        "student_qualifications", sa.Column("gpa_scale", sa.String(length=10), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("student_qualifications", "gpa_scale")
    op.drop_column("student_qualifications", "gpa")
