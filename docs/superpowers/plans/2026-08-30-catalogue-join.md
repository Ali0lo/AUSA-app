> **SUPERSEDED, 31 August 2026 — do not execute this plan.**
> Tasks 1 and 2 are **done and merged** (`program_cutoff_history`, its migration, and the
> idempotent CSV loader — commits `1821e4d..0647d20`). Tasks 3-6 were re-planned against the
> route-first spec, which made study level part of every key and turned "route matching" from
> a lookup into a two-hop engine. They now live in
> [`2026-08-31-dp-route-path.md`](2026-08-31-dp-route-path.md): old Task 3 and Task 4 became
> its Task 7, old Task 5 became its Tasks 8 and 9, old Task 6 became its Task 10.
> This plan's Ruling 6 — the deferred unique index on `program_cutoff_history` — is carried
> into that plan's Task 7, Steps 2 and 2b.
> Kept as the record of what was built and why; its rulings ledger is still authoritative for
> the decisions it made.

# Catalogue Join Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the 127,000 collected cutoff rows and the programme requirements join, so
the eligibility filter has something to filter on and the ML predictions have somewhere to
land.

**Architecture:** Four new tables and two pure services. `program_cutoff_history` holds the
collected CSVs. `student_qualifications` holds what a student actually has. `program_requirements`
holds what a programme accepts — several alternative entrance qualifications per programme
(ADR-0006), each row carrying its own provenance (ADR-0007 §5). `routes.py` matches the two
deterministically; `eligibility.py` returns both what passed and **why each exclusion
happened**, because a silent false exclusion is the unrecoverable failure (ADR-0007 §5).

No ML in this plan. No LLM in this plan. Every function here is deterministic and pure.

**Tech Stack:** SQLAlchemy 2.0 async, Alembic, Postgres (pgvector in prod), SQLite +
aiosqlite in tests, pytest + pytest-asyncio, pandas for the loader.

**Spec:** [`docs/adr/0007-three-number-model-and-honesty-tiers.md`](../../adr/0007-three-number-model-and-honesty-tiers.md),
with [`0006`](../../adr/0006-admission-routes.md) for the route matrix and
[`0004`](../../adr/0004-batch-serving-and-explainability.md) for provenance and batch serving.

## Global Constraints

- **No silent fallbacks.** ADR-0004 rule 2. Never `except Exception` → substitute a value →
  continue. If data is missing, the field is `None` and the caller is told; if a load fails,
  it raises. This pattern has been removed from this codebase three times.
- **Absent means `None`, never a default.** A programme with no stated IELTS minimum has
  `min_score = None`, which means *unknown* — not 0, not 6.0.
- **Provenance is one of exactly three strings:** `"seed"`, `"claude-extracted"`,
  `"human-verified"`. Only a human sets the third. An LLM confidence score never promotes a row.
- **Every requirement row carries `source_url`**, except `seed` rows, which carry `None`.
- Existing migration head is `ca962f4261fb`. Chain new migrations from it in order.
- Async SQLAlchemy throughout: `await db.execute(...)`, `async_sessionmaker`.
- Tests run from `backend/`: `cd backend && python -m pytest tests/ -q`
- `Base.metadata.create_all` cannot be called wholesale in SQLite tests — `university_documents`
  uses pgvector's `Vector`. Always pass `tables=[...]` explicitly. See `tests/test_auth.py`.

---

### Task 1: `program_cutoff_history` table

The table ADR-0004 assumed and nobody built. One row per (programme, intake year).

**Files:**
- Create: `backend/app/models/cutoff_history.py`
- Create: `backend/alembic/versions/2026_08_30_0001-a1b2c3d4e5f6_add_program_cutoff_history.py`
- Test: `backend/tests/test_cutoff_history_model.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `ProgramCutoffHistory` ORM class with columns `id, country, source_program_code,
  variant_index, intake_year, cutoff_value, cutoff_unit, lower_is_better, university_name,
  department_name, score_type, scholarship_type, is_undergraduate, source_url, verified_by`.
  Task 2 writes rows to it; the ML precompute reads them.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_cutoff_history_model.py
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.cutoff_history import ProgramCutoffHistory


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all, tables=[ProgramCutoffHistory.__table__]
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_cutoff_row_round_trips(session):
    session.add(
        ProgramCutoffHistory(
            country="AZ",
            source_program_code="komputer-elmleri--ada--g1",
            intake_year=2025,
            cutoff_value=692.6,
            cutoff_unit="dim_score_700",
            lower_is_better=False,
            university_name="ADA",
            department_name="Kompüter elmləri",
            source_url="https://sec.az/kecid-ballari",
        )
    )
    await session.commit()

    row = (await session.execute(select(ProgramCutoffHistory))).scalars().one()
    assert row.cutoff_value == 692.6
    assert row.lower_is_better is False
    assert row.verified_by is None, "verified_by must stay empty until a human checks it"


@pytest.mark.asyncio
async def test_variant_index_distinguishes_identical_programmes(session):
    """sec.az publishes rows identical but for their scores; merging corrupts lag features."""
    for idx, value in ((0, 400.0), (1, 355.0)):
        session.add(
            ProgramCutoffHistory(
                country="AZ",
                source_program_code="aqronomluq--adau--g3",
                variant_index=idx,
                intake_year=2025,
                cutoff_value=value,
                cutoff_unit="dim_score_700",
                lower_is_better=False,
                university_name="ADAU",
                department_name="Aqronomluq",
            )
        )
    await session.commit()

    rows = (await session.execute(select(ProgramCutoffHistory))).scalars().all()
    assert len(rows) == 2
    assert {r.cutoff_value for r in rows} == {400.0, 355.0}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_cutoff_history_model.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models.cutoff_history'`

- [ ] **Step 3: Write the model**

```python
# backend/app/models/cutoff_history.py
from sqlalchemy import Boolean, Column, Float, Index, Integer, String, Text
from app.core.database import Base


class ProgramCutoffHistory(Base):
    """One published admission cutoff, for one programme, for one intake year.

    This is collected source data, not a prediction. `cutoff_value` is the score of the
    last admitted applicant where the source publishes that (Azerbaijan's keçid balı,
    Turkey's final_score_012); the unit differs per country, so `cutoff_unit` and
    `lower_is_better` must be read before comparing any two rows.
    """

    __tablename__ = "program_cutoff_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    country = Column(String(2), nullable=False, index=True)
    source_program_code = Column(String(300), nullable=False, index=True)
    # sec.az publishes rows that are byte-identical except for their scores. They are
    # distinct competitions, so they are kept apart rather than merged -- merging would
    # interleave unrelated series and corrupt every lag feature built from them.
    variant_index = Column(Integer, nullable=True)
    variant_discriminator_known = Column(Boolean, nullable=True)

    intake_year = Column(Integer, nullable=False, index=True)
    cutoff_value = Column(Float, nullable=False)
    # e.g. "dim_score_700", "yks_score_012", "sat_total_1600". Units are NOT comparable
    # across countries; ADR-0002 keeps one model per country for this reason.
    cutoff_unit = Column(String(50), nullable=False)
    # True where the published figure is a rank (lower is better), False where it is a score.
    lower_is_better = Column(Boolean, nullable=False, default=False)

    university_name = Column(String(300), nullable=False)
    department_name = Column(String(300), nullable=True)
    score_type = Column(String(100), nullable=True)
    scholarship_type = Column(String(100), nullable=True)
    is_undergraduate = Column(Boolean, nullable=True)

    source_url = Column(Text, nullable=True)
    # Stays NULL until a person opens the source and confirms the row (ADR-0004 rule 2).
    verified_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index(
            "ix_cutoff_history_series",
            "country",
            "source_program_code",
            "variant_index",
            "intake_year",
        ),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_cutoff_history_model.py -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Write the Alembic migration**

```python
# backend/alembic/versions/2026_08_30_0001-a1b2c3d4e5f6_add_program_cutoff_history.py
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
```

- [ ] **Step 6: Verify the migration chain is valid**

Run: `cd backend && python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; s = ScriptDirectory.from_config(Config('alembic.ini')); print([r.revision for r in s.walk_revisions()])"`
Expected: prints `['a1b2c3d4e5f6', 'ca962f4261fb']` — exactly one head, chained correctly.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/cutoff_history.py backend/alembic/versions/ backend/tests/test_cutoff_history_model.py
git commit -m "Add program_cutoff_history table

The table ADR-0004 assumed and that was never built. 127k collected rows
lived only as CSVs, so cutoff history and programme requirements could not
join. variant_index keeps byte-identical sec.az rows apart: they are
distinct competitions, and merging them would corrupt every lag feature."
```

---

### Task 2: CSV loader for the three collected countries

**Files:**
- Create: `backend/scripts/load_cutoff_history.py`
- Test: `backend/tests/test_load_cutoff_history.py`

**Interfaces:**
- Consumes: `ProgramCutoffHistory` from Task 1.
- Produces: `REQUIRED_COLUMNS: set[str]`, `rows_from_csv(path: Path) -> list[dict]`, and
  `async load_csv(session: AsyncSession, path: Path) -> int` returning rows inserted.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_load_cutoff_history.py
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.cutoff_history import ProgramCutoffHistory

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))
from load_cutoff_history import load_csv, rows_from_csv  # noqa: E402

CSV = """country,source_program_code,variant_index,intake_year,cutoff_value,cutoff_unit,lower_is_better,university_name,department_name,source_url,verified_by
AZ,komputer-elmleri--ada--g1,,2025,692.6,dim_score_700,False,ADA,Kompüter elmləri,https://sec.az/kecid-ballari,
AZ,komputer-elmleri--ada--g1,,2024,688.0,dim_score_700,False,ADA,Kompüter elmləri,https://sec.az/kecid-ballari,
"""


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[ProgramCutoffHistory.__table__])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def test_missing_required_column_raises(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("country,intake_year\nAZ,2025\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        rows_from_csv(bad)


def test_blank_variant_index_becomes_none(tmp_path):
    path = tmp_path / "az.csv"
    path.write_text(CSV, encoding="utf-8")
    rows = rows_from_csv(path)
    assert rows[0]["variant_index"] is None, "blank must be None, not 0"


@pytest.mark.asyncio
async def test_load_is_idempotent(session, tmp_path):
    path = tmp_path / "az.csv"
    path.write_text(CSV, encoding="utf-8")

    assert await load_csv(session, path) == 2
    assert await load_csv(session, path) == 0, "re-running must not duplicate rows"

    total = (await session.execute(select(func.count()).select_from(ProgramCutoffHistory))).scalar()
    assert total == 2


@pytest.mark.asyncio
async def test_verified_by_is_never_populated_by_the_loader(session, tmp_path):
    path = tmp_path / "az.csv"
    path.write_text(CSV, encoding="utf-8")
    await load_csv(session, path)

    rows = (await session.execute(select(ProgramCutoffHistory))).scalars().all()
    assert all(r.verified_by is None for r in rows)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_load_cutoff_history.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'load_cutoff_history'`

- [ ] **Step 3: Write the loader**

```python
# backend/scripts/load_cutoff_history.py
"""Load collected cutoff-history CSVs into program_cutoff_history.

Idempotent: a row is identified by (country, source_program_code, variant_index,
intake_year), so re-running after a fresh collection inserts only what is new.

Nothing here fills a gap. A CSV missing a required column raises rather than
loading a partial table, and verified_by is never written -- only a person who
has opened the source may set it (ADR-0004 rule 2).
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.cutoff_history import ProgramCutoffHistory  # noqa: E402

REQUIRED_COLUMNS = {
    "country",
    "source_program_code",
    "intake_year",
    "cutoff_value",
    "cutoff_unit",
    "university_name",
}

OPTIONAL_COLUMNS = {
    "variant_index",
    "variant_discriminator_known",
    "lower_is_better",
    "department_name",
    "score_type",
    "scholarship_type",
    "is_undergraduate",
    "source_url",
}


def _clean(value: Any) -> Any:
    """NaN and empty string both mean 'the source did not say', which is None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def rows_from_csv(path: Path) -> list[dict]:
    """Parse one collected CSV into ORM kwargs. Raises if the schema does not match."""
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: {sorted(missing)}. "
            "Re-run the collector rather than loading a partial table."
        )

    rows: list[dict] = []
    for record in frame.to_dict(orient="records"):
        row = {key: _clean(record.get(key)) for key in REQUIRED_COLUMNS | OPTIONAL_COLUMNS}
        row["intake_year"] = int(row["intake_year"])
        row["cutoff_value"] = float(row["cutoff_value"])
        if row["variant_index"] is not None:
            row["variant_index"] = int(row["variant_index"])
        row["lower_is_better"] = bool(row["lower_is_better"]) if row["lower_is_better"] is not None else False
        rows.append(row)
    return rows


async def load_csv(session: AsyncSession, path: Path) -> int:
    """Insert rows not already present. Returns the number inserted."""
    rows = rows_from_csv(path)

    existing = set(
        (
            await session.execute(
                select(
                    ProgramCutoffHistory.country,
                    ProgramCutoffHistory.source_program_code,
                    ProgramCutoffHistory.variant_index,
                    ProgramCutoffHistory.intake_year,
                )
            )
        ).all()
    )

    inserted = 0
    for row in rows:
        key = (row["country"], row["source_program_code"], row["variant_index"], row["intake_year"])
        if key in existing:
            continue
        session.add(ProgramCutoffHistory(**row))
        existing.add(key)
        inserted += 1

    await session.commit()
    return inserted


async def _main(paths: list[Path]) -> None:
    async with AsyncSessionLocal() as session:
        for path in paths:
            count = await load_csv(session, path)
            print(f"{path.name}: {count} new rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="+", type=Path, help="collected CSVs from data/processed/")
    args = parser.parse_args()
    asyncio.run(_main(args.csv))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_load_cutoff_history.py -q`
Expected: PASS (4 passed)

If `AsyncSessionLocal` does not exist under that name in `app/core/database.py`, open that
file and use whatever the session factory is actually called. Do not create a second one.

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/load_cutoff_history.py backend/tests/test_load_cutoff_history.py
git commit -m "Add idempotent loader for collected cutoff-history CSVs

Keyed on (country, source_program_code, variant_index, intake_year) so a
re-collection loads only new rows. A CSV missing a required column raises
rather than loading a partial table, and verified_by is never written by
machine."
```

---

### Task 3: `student_qualifications` table

`students` has `gpa`, `ielts` and `toefl` and no entrance qualifications at all — so there
is nothing to compare against a cutoff. ADR-0006: a student holds several qualifications
and a programme accepts several alternatives.

**Files:**
- Create: `backend/app/models/qualification.py`
- Create: `backend/alembic/versions/2026_08_30_0002-b2c3d4e5f6a7_add_student_qualifications.py`
- Test: `backend/tests/test_qualification_model.py`

**Interfaces:**
- Consumes: `Student` from `app.models.student`.
- Produces: `StudentQualification` ORM class with `id, student_id, qualification_type,
  score, max_score, awarded_year, evidence_url`; and the module constants
  `ENTRANCE_QUALIFICATIONS: frozenset[str]` = `{"dim", "sat", "attestat", "abitur", "matura", "ucas_tariff"}`
  and `LANGUAGE_QUALIFICATIONS: frozenset[str]` = `{"ielts", "toefl", "duolingo", "testdaf", "dsh"}`.
  Task 5 imports both sets.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_qualification_model.py
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.qualification import (
    ENTRANCE_QUALIFICATIONS,
    LANGUAGE_QUALIFICATIONS,
    StudentQualification,
)
from app.models.student import Student


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[Student.__table__, StudentQualification.__table__],
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def test_yos_is_not_an_accepted_qualification():
    """YOS was dropped in ADR-0006; it must not reappear by accident."""
    assert "yos" not in ENTRANCE_QUALIFICATIONS


def test_entrance_and_language_sets_do_not_overlap():
    """Axis A is competitive, axis B is pass/fail. Confusing them breaks ranking."""
    assert not (ENTRANCE_QUALIFICATIONS & LANGUAGE_QUALIFICATIONS)


@pytest.mark.asyncio
async def test_student_can_hold_several_qualifications(session):
    student = Student(email="s@ausa.edu.az")
    session.add(student)
    await session.commit()
    await session.refresh(student)

    session.add_all([
        StudentQualification(
            student_id=student.id, qualification_type="dim", score=580.0,
            max_score=700.0, awarded_year=2026,
        ),
        StudentQualification(
            student_id=student.id, qualification_type="ielts", score=6.5, max_score=9.0,
        ),
    ])
    await session.commit()

    held = (
        await session.execute(
            select(StudentQualification).where(StudentQualification.student_id == student.id)
        )
    ).scalars().all()
    assert {q.qualification_type for q in held} == {"dim", "ielts"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_qualification_model.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models.qualification'`

- [ ] **Step 3: Write the model**

```python
# backend/app/models/qualification.py
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from app.core.database import Base

# Axis A (ADR-0006): competitive entrance qualifications. Each has a cutoff, and scoring
# higher makes an applicant more admissible. YOS is deliberately absent -- it was dropped.
ENTRANCE_QUALIFICATIONS = frozenset(
    {"dim", "sat", "attestat", "abitur", "matura", "ucas_tariff"}
)

# Axis B: language proficiency. Pass/fail thresholds, NOT competitive cutoffs -- scoring
# IELTS 8.0 against a 6.5 requirement does not make an applicant more admissible.
LANGUAGE_QUALIFICATIONS = frozenset({"ielts", "toefl", "duolingo", "testdaf", "dsh"})


class StudentQualification(Base):
    """One qualification a student actually holds.

    A row per qualification rather than columns on `students`, because a student may hold
    several and a programme may accept any one of them as an alternative route.
    """

    __tablename__ = "student_qualifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)

    qualification_type = Column(String(30), nullable=False, index=True)
    score = Column(Float, nullable=False)
    # The scale the score is on, so 580 is never read against a 1600-point requirement.
    max_score = Column(Float, nullable=True)
    awarded_year = Column(Integer, nullable=True)
    evidence_url = Column(Text, nullable=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_qualification_model.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Write the migration**

```python
# backend/alembic/versions/2026_08_30_0002-b2c3d4e5f6a7_add_student_qualifications.py
"""add student_qualifications

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-30
"""
import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_qualifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("qualification_type", sa.String(length=30), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("awarded_year", sa.Integer(), nullable=True),
        sa.Column("evidence_url", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_qualifications_id", "student_qualifications", ["id"])
    op.create_index("ix_student_qualifications_student_id", "student_qualifications", ["student_id"])
    op.create_index(
        "ix_student_qualifications_qualification_type",
        "student_qualifications",
        ["qualification_type"],
    )


def downgrade() -> None:
    op.drop_table("student_qualifications")
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/qualification.py backend/alembic/versions/ backend/tests/test_qualification_model.py
git commit -m "Add student_qualifications table

students held gpa/ielts/toefl and no entrance qualification at all, so
there was nothing to compare against a cutoff. One row per qualification,
because ADR-0006 says a student holds several and a programme accepts
several alternatives. Entrance (competitive) and language (pass/fail) are
kept as separate sets so ranking never treats IELTS 8.0 as more admissible
than 6.5 against a 6.5 requirement."
```

---

### Task 4: `program_requirements` with per-row provenance

One row per (programme, accepted qualification). This is where ADR-0007 §5's three
provenance states live.

**Files:**
- Create: `backend/app/models/requirement.py`
- Create: `backend/alembic/versions/2026_08_30_0003-c3d4e5f6a7b8_add_program_requirements.py`
- Test: `backend/tests/test_requirement_model.py`

**Interfaces:**
- Consumes: `Program` from `app.models.program`.
- Produces: `ProgramRequirement` ORM class with `id, program_id, qualification_type,
  min_score, max_score, is_mandatory, provenance, source_url, fetched_at, verified_by`;
  and `PROVENANCE_STATES: tuple[str, str, str] = ("seed", "claude-extracted", "human-verified")`.
  Task 5 and Task 6 both import `ProgramRequirement`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_requirement_model.py
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.program import Program
from app.models.requirement import PROVENANCE_STATES, ProgramRequirement


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[Program.__table__, ProgramRequirement.__table__],
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def test_exactly_three_provenance_states():
    assert PROVENANCE_STATES == ("seed", "claude-extracted", "human-verified")


@pytest.mark.asyncio
async def test_default_provenance_is_never_verified(session):
    program = Program(university_name="ADA", program_name="Computer Science")
    session.add(program)
    await session.commit()
    await session.refresh(program)

    session.add(ProgramRequirement(program_id=program.id, qualification_type="dim", min_score=600.0))
    await session.commit()

    row = (await session.execute(select(ProgramRequirement))).scalars().one()
    assert row.provenance == "claude-extracted"
    assert row.verified_by is None


@pytest.mark.asyncio
async def test_unknown_minimum_is_none_not_zero(session):
    """A page that does not state an IELTS minimum means unknown, not 'no minimum'."""
    program = Program(university_name="UCL", program_name="Computer Science")
    session.add(program)
    await session.commit()
    await session.refresh(program)

    session.add(
        ProgramRequirement(program_id=program.id, qualification_type="ielts", min_score=None)
    )
    await session.commit()

    row = (await session.execute(select(ProgramRequirement))).scalars().one()
    assert row.min_score is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_requirement_model.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.models.requirement'`

- [ ] **Step 3: Write the model**

```python
# backend/app/models/requirement.py
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from app.core.database import Base

# ADR-0007 section 5. Exactly three, and only a person may set the third.
PROVENANCE_STATES = ("seed", "claude-extracted", "human-verified")


class ProgramRequirement(Base):
    """One qualification a programme accepts, and the minimum it asks for.

    Several rows per programme: ADR-0006 established that programmes admit on alternative
    qualifications (SAT >= 1200 *or* an attestat conversion), each with its own threshold.

    `min_score = None` means the source did not state a minimum. That is 'unknown', not
    'no minimum' -- the eligibility filter must not read it as either 0 or a guess.
    """

    __tablename__ = "program_requirements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False, index=True)

    qualification_type = Column(String(30), nullable=False, index=True)
    min_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    # False for alternatives on axis A (any one accepted route suffices); True for a
    # language requirement that must be met alongside whichever entrance route is used.
    is_mandatory = Column(Boolean, nullable=False, default=False)

    provenance = Column(String(20), nullable=False, default="claude-extracted", index=True)
    source_url = Column(Text, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    # Set only by a person who has opened source_url and confirmed this row. An LLM
    # confidence score never writes here (ADR-0007 section 5).
    verified_by = Column(String(100), nullable=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_requirement_model.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Write the migration**

```python
# backend/alembic/versions/2026_08_30_0003-c3d4e5f6a7b8_add_program_requirements.py
"""add program_requirements

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-30
"""
import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "program_requirements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("program_id", sa.Integer(), nullable=False),
        sa.Column("qualification_type", sa.String(length=30), nullable=False),
        sa.Column("min_score", sa.Float(), nullable=True),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("provenance", sa.String(length=20), nullable=False, server_default="claude-extracted"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_program_requirements_id", "program_requirements", ["id"])
    op.create_index("ix_program_requirements_program_id", "program_requirements", ["program_id"])
    op.create_index(
        "ix_program_requirements_qualification_type", "program_requirements", ["qualification_type"]
    )
    op.create_index("ix_program_requirements_provenance", "program_requirements", ["provenance"])


def downgrade() -> None:
    op.drop_table("program_requirements")
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/requirement.py backend/alembic/versions/ backend/tests/test_requirement_model.py
git commit -m "Add program_requirements with three-state provenance

Several rows per programme, because ADR-0006 established programmes admit
on alternative qualifications. provenance is seed / claude-extracted /
human-verified per ADR-0007 section 5; only a person sets the third, and
min_score None means the source did not state a minimum -- unknown, not
zero and not a guess."
```

---

### Task 5: Route matching — which qualifications open which doors

Pure functions, no database, no I/O. This is the deterministic core ADR-0001 keeps out of
the model's hands.

**Files:**
- Create: `backend/app/services/matching/routes.py`
- Test: `backend/tests/test_routes.py`

**Interfaces:**
- Consumes: `ENTRANCE_QUALIFICATIONS`, `LANGUAGE_QUALIFICATIONS` from Task 3;
  `ProgramRequirement` from Task 4; `StudentQualification` from Task 3.
- Produces:
  - `@dataclass(frozen=True) RouteMatch` with fields `qualification_type: str`,
    `student_score: float`, `required_score: float | None`, `clears: bool`, `unknown: bool`.
  - `open_routes(held, requirements) -> list[RouteMatch]`
  - `language_gate(held, requirements) -> list[RouteMatch]`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_routes.py
from types import SimpleNamespace

from app.services.matching.routes import language_gate, open_routes


def q(qualification_type, score):
    return SimpleNamespace(qualification_type=qualification_type, score=score)


def r(qualification_type, min_score, is_mandatory=False):
    return SimpleNamespace(
        qualification_type=qualification_type, min_score=min_score, is_mandatory=is_mandatory
    )


def test_any_one_entrance_route_suffices():
    held = [q("sat", 1300)]
    reqs = [r("sat", 1200), r("attestat", 4.5)]
    matches = open_routes(held, reqs)
    assert [m.qualification_type for m in matches] == ["sat"]
    assert matches[0].clears is True


def test_route_below_threshold_is_returned_but_does_not_clear():
    """The gap matters in Mode B, so a failing route is reported rather than dropped."""
    matches = open_routes([q("dim", 580)], [r("dim", 650)])
    assert len(matches) == 1
    assert matches[0].clears is False
    assert matches[0].required_score == 650


def test_unknown_requirement_never_clears_and_never_excludes():
    """min_score None means the source did not say. Neither pass nor fail is honest."""
    matches = open_routes([q("dim", 580)], [r("dim", None)])
    assert matches[0].unknown is True
    assert matches[0].clears is False


def test_qualification_the_programme_does_not_accept_is_ignored():
    assert open_routes([q("dim", 690)], [r("sat", 1200)]) == []


def test_language_requirements_are_not_entrance_routes():
    """IELTS is a pass/fail gate on axis B; it must never appear as an entrance route."""
    held = [q("dim", 690), q("ielts", 7.0)]
    reqs = [r("dim", 650), r("ielts", 6.5, is_mandatory=True)]

    assert [m.qualification_type for m in open_routes(held, reqs)] == ["dim"]
    assert [m.qualification_type for m in language_gate(held, reqs)] == ["ielts"]


def test_language_gate_reports_a_missing_certificate_as_unknown():
    gate = language_gate([q("dim", 690)], [r("ielts", 6.5, is_mandatory=True)])
    assert len(gate) == 1
    assert gate[0].unknown is True
    assert gate[0].clears is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_routes.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.matching.routes'`

- [ ] **Step 3: Write the implementation**

```python
# backend/app/services/matching/routes.py
"""Match what a student holds against what a programme accepts.

Deterministic and pure. ADR-0001 keeps eligibility out of the model's hands entirely --
the model only ever predicts a cutoff, never decides who qualifies.

Two axes, from ADR-0006:
  A. Entrance qualifications are *alternatives* and *competitive*. Any one accepted route
     clearing its threshold opens the door, and a higher score is genuinely better.
  B. Language proficiency is a *pass/fail gate* applied alongside whichever route is used.
     IELTS 8.0 against a 6.5 requirement is not more admissible than 6.5.
"""

from dataclasses import dataclass

from app.models.qualification import ENTRANCE_QUALIFICATIONS, LANGUAGE_QUALIFICATIONS


@dataclass(frozen=True)
class RouteMatch:
    """One qualification the programme accepts, measured against what the student holds."""

    qualification_type: str
    student_score: float | None
    required_score: float | None
    clears: bool
    # True when the requirement exists but its threshold is unknown, or the student holds
    # no such qualification. Unknown is neither a pass nor a fail, and the caller must not
    # collapse it into one: see eligibility.py.
    unknown: bool


def _match(held_score: float | None, required: float | None, qualification_type: str) -> RouteMatch:
    unknown = held_score is None or required is None
    return RouteMatch(
        qualification_type=qualification_type,
        student_score=held_score,
        required_score=required,
        clears=(not unknown) and held_score >= required,
        unknown=unknown,
    )


def _scores_by_type(held) -> dict[str, float]:
    return {q.qualification_type: q.score for q in held}


def open_routes(held, requirements) -> list[RouteMatch]:
    """Entrance routes the programme accepts AND the student holds something for.

    A route below its threshold is returned with clears=False rather than dropped: Mode B
    needs the gap, and 'you are 68 points short' is the product's headline sentence.
    """
    scores = _scores_by_type(held)
    return [
        _match(scores[req.qualification_type], req.min_score, req.qualification_type)
        for req in requirements
        if req.qualification_type in ENTRANCE_QUALIFICATIONS
        and req.qualification_type in scores
    ]


def language_gate(held, requirements) -> list[RouteMatch]:
    """Language requirements, whether or not the student holds the certificate.

    A missing certificate is returned as unknown rather than omitted, so the UI can say
    'you still need IELTS' instead of silently dropping the programme.
    """
    scores = _scores_by_type(held)
    return [
        _match(scores.get(req.qualification_type), req.min_score, req.qualification_type)
        for req in requirements
        if req.qualification_type in LANGUAGE_QUALIFICATIONS
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_routes.py -q`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/matching/routes.py backend/tests/test_routes.py
git commit -m "Add deterministic route matching for qualifications

Entrance qualifications are alternatives and competitive; language
requirements are a pass/fail gate alongside them (ADR-0006). A route below
threshold is returned rather than dropped, because Mode B's headline is the
gap. Unknown is a third outcome and never collapses into pass or fail."
```

---

### Task 6: Eligibility filter that reports its exclusions

The rule from ADR-0007 §5: unverified requirements filter, **but never silently**.

**Files:**
- Create: `backend/app/services/matching/eligibility.py`
- Test: `backend/tests/test_eligibility.py`

**Interfaces:**
- Consumes: `open_routes`, `language_gate`, `RouteMatch` from Task 5.
- Produces:
  - `@dataclass(frozen=True) Exclusion` with `program_id: int`, `reason: str`,
    `qualification_type: str | None`, `provenance: str`, `source_url: str | None`.
  - `@dataclass(frozen=True) EligibilityResult` with `eligible: list[int]`,
    `filtered_out: list[Exclusion]`.
  - `evaluate(programs_with_requirements, held) -> EligibilityResult`, where the first
    argument is a list of `(program_id, [requirement, ...])` tuples.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_eligibility.py
from types import SimpleNamespace

from app.services.matching.eligibility import evaluate


def q(qualification_type, score):
    return SimpleNamespace(qualification_type=qualification_type, score=score)


def r(qualification_type, min_score, is_mandatory=False, provenance="claude-extracted",
      source_url="https://uni.edu/admissions"):
    return SimpleNamespace(
        qualification_type=qualification_type, min_score=min_score,
        is_mandatory=is_mandatory, provenance=provenance, source_url=source_url,
    )


def test_clearing_one_route_makes_the_programme_eligible():
    result = evaluate([(1, [r("dim", 650), r("ielts", 6.5, is_mandatory=True)])],
                      [q("dim", 690), q("ielts", 7.0)])
    assert result.eligible == [1]
    assert result.filtered_out == []


def test_every_exclusion_carries_a_reason_and_its_source():
    result = evaluate([(1, [r("dim", 650)])], [q("dim", 580)])
    assert result.eligible == []
    assert len(result.filtered_out) == 1

    excluded = result.filtered_out[0]
    assert excluded.program_id == 1
    assert excluded.qualification_type == "dim"
    # The reason is student-facing prose, so the qualification is upper-cased in it.
    assert "DIM" in excluded.reason
    assert "580" in excluded.reason and "650" in excluded.reason
    assert excluded.provenance == "claude-extracted"
    assert excluded.source_url == "https://uni.edu/admissions"


def test_language_gate_can_exclude_on_its_own():
    result = evaluate([(1, [r("dim", 650), r("ielts", 7.5, is_mandatory=True)])],
                      [q("dim", 690), q("ielts", 6.5)])
    assert result.eligible == []
    assert result.filtered_out[0].qualification_type == "ielts"


def test_unknown_requirement_does_not_exclude():
    """A source that never stated a minimum must not delete the programme."""
    result = evaluate([(1, [r("dim", None)])], [q("dim", 400)])
    assert result.eligible == [1]


def test_no_accepted_route_held_is_an_exclusion_with_its_own_reason():
    result = evaluate([(1, [r("sat", 1200)])], [q("dim", 690)])
    assert result.eligible == []
    assert "no accepted qualification" in result.filtered_out[0].reason


def test_a_programme_is_never_both_eligible_and_filtered_out():
    result = evaluate(
        [(1, [r("dim", 650)]), (2, [r("dim", 700)])], [q("dim", 690)]
    )
    assert result.eligible == [1]
    assert [e.program_id for e in result.filtered_out] == [2]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_eligibility.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.matching.eligibility'`

- [ ] **Step 3: Write the implementation**

```python
# backend/app/services/matching/eligibility.py
"""Decide which programmes a student is eligible for, and say why the rest were not.

ADR-0007 section 5: unverified requirements DO filter, but never silently. Every
exclusion carries its reason, the qualification involved, the provenance of the
requirement that caused it, and the source URL -- because the asymmetry is stark:

  A false inclusion is visible. The student sees the programme, checks it, finds we were
  wrong. Recoverable.

  A false exclusion is invisible. The programme never appears, the student never learns it
  existed, and a mis-extracted 'IELTS 7.0' that is really 6.0 quietly deletes their best
  option. Unrecoverable.

So exclusions are data the UI renders, not control flow the UI never sees.
"""

from dataclasses import dataclass

from app.services.matching.routes import language_gate, open_routes


@dataclass(frozen=True)
class Exclusion:
    program_id: int
    reason: str
    qualification_type: str | None
    provenance: str
    source_url: str | None


@dataclass(frozen=True)
class EligibilityResult:
    eligible: list[int]
    filtered_out: list[Exclusion]


def _requirement_for(requirements, qualification_type):
    return next(r for r in requirements if r.qualification_type == qualification_type)


def evaluate(programs_with_requirements, held) -> EligibilityResult:
    """Partition programmes into eligible and filtered-out-with-a-reason.

    Args:
        programs_with_requirements: list of (program_id, [ProgramRequirement, ...]).
        held: the student's StudentQualification rows.
    """
    eligible: list[int] = []
    filtered_out: list[Exclusion] = []

    for program_id, requirements in programs_with_requirements:
        routes = open_routes(held, requirements)

        if not routes:
            accepted = sorted(
                {r.qualification_type for r in requirements if not r.is_mandatory}
            )
            filtered_out.append(
                Exclusion(
                    program_id=program_id,
                    reason=(
                        "You hold no accepted qualification for this programme. "
                        f"It admits on: {', '.join(accepted) or 'no stated route'}."
                    ),
                    qualification_type=None,
                    provenance=requirements[0].provenance if requirements else "seed",
                    source_url=requirements[0].source_url if requirements else None,
                )
            )
            continue

        # Unknown thresholds must not exclude: the source never stated one, so we cannot
        # claim the student fails it. They also cannot count as clearing it.
        passing = [route for route in routes if route.clears or route.unknown]
        if not passing:
            worst = min(routes, key=lambda route: route.student_score - route.required_score)
            requirement = _requirement_for(requirements, worst.qualification_type)
            filtered_out.append(
                Exclusion(
                    program_id=program_id,
                    reason=(
                        f"{worst.qualification_type.upper()} {worst.student_score:g} is below "
                        f"the required {worst.required_score:g}."
                    ),
                    qualification_type=worst.qualification_type,
                    provenance=requirement.provenance,
                    source_url=requirement.source_url,
                )
            )
            continue

        failed_language = [
            gate for gate in language_gate(held, requirements)
            if not gate.clears and not gate.unknown
        ]
        if failed_language:
            gate = failed_language[0]
            requirement = _requirement_for(requirements, gate.qualification_type)
            filtered_out.append(
                Exclusion(
                    program_id=program_id,
                    reason=(
                        f"{gate.qualification_type.upper()} {gate.student_score:g} is below "
                        f"the required {gate.required_score:g}."
                    ),
                    qualification_type=gate.qualification_type,
                    provenance=requirement.provenance,
                    source_url=requirement.source_url,
                )
            )
            continue

        eligible.append(program_id)

    return EligibilityResult(eligible=eligible, filtered_out=filtered_out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_eligibility.py -q`
Expected: PASS (6 passed)

- [ ] **Step 5: Run the whole suite**

Run: `cd backend && python -m pytest tests/ -q`
Expected: PASS. Baseline before this plan was 48 passed; this plan adds 24, so expect 72.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/matching/eligibility.py backend/tests/test_eligibility.py
git commit -m "Add eligibility filter that reports every exclusion

ADR-0007 section 5: unverified requirements filter, but never silently.
Each exclusion carries its reason, the qualification involved, the
provenance of the requirement behind it, and the source URL, so the UI can
render a 'filtered out (N)' panel. A false exclusion is invisible to the
student and unrecoverable; a false inclusion is neither. An unknown
threshold never excludes."
```

---

## What this plan deliberately does not build

- **Any ML.** Predictions land on programme rows via a separate batch job (ADR-0004 §1,
  ADR-0007 §7). This plan builds the tables that job writes into and reads from.
- **Any LLM.** Requirement rows arrive from the extraction pipeline (ADR-0007 §11), which
  is Claude's track. This plan defines the shape they land in.
- **Score conversion.** Attestat → Abiturnote via the modified Bavarian formula is
  arithmetic (ADR-0006) and belongs with the route matrix, but it is a separate concern
  from the join and gets its own plan.
- **UI.** The `filtered_out` list is returned as data precisely so the "filtered out (N)"
  panel can be built against it without touching this layer.
