"""give students.gpa the scale it is on

`students.gpa` has been stored since the first migration with no scale beside it, and
`/auth/register` bounded it `le=4.0`. That bound is not a validation, it is an assumption
about which country the student went to school in -- and it is wrong for ours. An
Azerbaijani attestat average is out of **5**, so a real 4.5 was rejected as invalid input
at the point of registration, while a 3.9 out of 5 (a weak result) was accepted and then
read downstream as a strong US-style GPA.

`student_qualifications` already stores the pair (migration c3d4e5f6a7b8) and
`program_requirements` has stored `gpa_minimum` beside `gpa_scale` since it was created,
both on the same rule: a grade without its scale is not a number. This closes the last
place in the schema that broke it.

Nullable, and no backfill. Existing rows have a grade whose scale nobody recorded, and
inventing '4.0' for them would assert the very thing this migration exists to stop
assuming. They read as "scale unknown", which `check_grade` already reports as
`scales_not_comparable` rather than as a pass or a failure.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-05
"""
import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("students", sa.Column("gpa_scale", sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column("students", "gpa_scale")
