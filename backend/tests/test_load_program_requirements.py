"""The writer program_requirements never had.

The table has existed with a migration and its own tests since Task 7, and nothing in the
application ever wrote a row into it or read one out. These tests cover the loader that
closes that gap, and they are mostly about what an EMPTY CSV CELL must become.

That is the whole risk here. A curated requirements file is mostly blanks -- nobody has
read every field off every page -- and the difference between "unknown" and "not required"
is the difference between a route that correctly reads BLOCKED and one that tells a student
to apply somewhere that will reject them. `int("")` raises, but `bool("")` is False, and a
False in foundation_required is a claim that no foundation year is needed.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.qualifications import ProgramRequirement
from scripts.load_program_requirements import (
    CuratedRowError,
    load_program_requirements,
    parse_row,
)

HEADER = (
    "university_name,program_name,level,intake_year,country_code,"
    "entry_qualification_accepted,foundation_required,foundation_providers,"
    "language_test,language_minimum_score,language_of_instruction,"
    "entrance_exam,entrance_exam_minimum,gpa_minimum,gpa_scale,"
    "tuition_per_year,currency,living_cost_estimate_per_year,application_fee,"
    "application_deadline,application_portal,documents_required,"
    "provenance,source_url,retrieved_at,last_checked,verified_by"
)

FULL_ROW = (
    "Technical University of Munich,International undergraduate admission,bachelor,2026,DE,"
    "feststellungspruefung,true,Studienkolleg,"
    "IELTS,6.5,German,"
    "Feststellungspruefung,50.0,3.2,4.0,"
    "0,EUR,11904,75,"
    "2026-07-15,TUMonline,VPD required,"
    "claude-extracted,https://www.tum.de/en/studies/application,"
    "2026-09-02T00:00:00Z,2026-09-02T00:00:00Z,"
)

# The realistic shape: identifiers and provenance present, most requirement fields blank.
SPARSE_ROW = (
    "Istanbul Technical University,International undergraduate admission,bachelor,2026,TR,"
    "attestat,,,"
    ",,,"
    ",,,,"
    ",,,,"
    ",,,"
    "claude-extracted,https://www.sis.itu.edu.tr/EN/student/intenational-students/application.php,"
    "2026-09-02T00:00:00Z,,"
)


def write_csv(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "curated.csv"
    path.write_text("\n".join((HEADER, *rows)) + "\n", encoding="utf-8")
    return path


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all, tables=[ProgramRequirement.__table__]
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


# -------------------------------------------------------------
# Blank cells
# -------------------------------------------------------------
def test_a_blank_boolean_is_unknown_not_false():
    """The one that matters most.

    foundation_required=False is a claim: "this university needs no foundation year."
    An empty cell says nobody checked. bool("") is False, so the obvious parse turns
    every unchecked university into one that accepts direct entry -- which is exactly
    the advice that sends a student to an application they cannot make.
    """
    row = parse_row(dict(zip(HEADER.split(","), SPARSE_ROW.split(","))))
    assert row["foundation_required"] is None


def test_blank_numbers_are_none_not_zero():
    row = parse_row(dict(zip(HEADER.split(","), SPARSE_ROW.split(","))))
    for field in (
        "language_minimum_score",
        "entrance_exam_minimum",
        "gpa_minimum",
        "tuition_per_year",
        "living_cost_estimate_per_year",
        "application_fee",
    ):
        assert row[field] is None, f"{field} became {row[field]!r}, not None"


def test_a_blank_tuition_is_not_free_tuition():
    """tuition_per_year=0.0 means "this programme is free", which several German
    universities genuinely are. A blank must never render as that number."""
    row = parse_row(dict(zip(HEADER.split(","), SPARSE_ROW.split(","))))
    assert row["tuition_per_year"] is None
    assert row["tuition_per_year"] is not False


def test_zero_tuition_is_preserved_when_actually_stated():
    """The mirror of the test above: a real 0 must survive, or free tuition reads as unknown."""
    row = parse_row(dict(zip(HEADER.split(","), FULL_ROW.split(","))))
    assert row["tuition_per_year"] == 0.0


def test_blank_strings_are_none_not_empty_string():
    row = parse_row(dict(zip(HEADER.split(","), SPARSE_ROW.split(","))))
    assert row["language_test"] is None
    assert row["foundation_providers"] is None


def test_blank_dates_are_none():
    row = parse_row(dict(zip(HEADER.split(","), SPARSE_ROW.split(","))))
    assert row["application_deadline"] is None
    assert row["last_checked"] is None


def test_full_row_parses_every_field():
    row = parse_row(dict(zip(HEADER.split(","), FULL_ROW.split(","))))
    assert row["foundation_required"] is True
    assert row["language_minimum_score"] == 6.5
    assert row["gpa_minimum"] == 3.2
    assert row["application_fee"] == 75.0
    assert row["application_deadline"].isoformat() == "2026-07-15"
    assert row["intake_year"] == 2026


# -------------------------------------------------------------
# Provenance
# -------------------------------------------------------------
def test_verified_by_from_the_csv_is_refused():
    """A CSV cannot name the human who checked a row.

    verified_by is the record that a person opened the source page. Letting a file set it
    means anyone editing the file can claim a verification that never happened -- the same
    reason the client-suppliable verified_by was dropped when PR #4 was merged.
    """
    # FULL_ROW already ends with the trailing comma for an empty verified_by.
    bad = FULL_ROW + "curator@ausa.edu.az"
    with pytest.raises(CuratedRowError, match="verified_by"):
        parse_row(dict(zip(HEADER.split(","), bad.split(","))))


def test_a_row_without_a_source_url_is_refused():
    no_source = FULL_ROW.replace("https://www.tum.de/en/studies/application", "")
    with pytest.raises(CuratedRowError, match="source_url"):
        parse_row(dict(zip(HEADER.split(","), no_source.split(","))))


def test_provenance_must_be_a_known_state():
    bad = FULL_ROW.replace("claude-extracted", "verified")
    with pytest.raises(CuratedRowError, match="provenance"):
        parse_row(dict(zip(HEADER.split(","), bad.split(","))))


def test_human_verified_provenance_without_a_verifier_is_refused():
    """human-verified is a claim about a person, so a person has to be named.

    The CSV cannot name them (see above), so this state can only be reached through the
    admin review queue. A file asserting it is asserting a verification nobody performed.
    """
    bad = FULL_ROW.replace("claude-extracted", "human-verified")
    with pytest.raises(CuratedRowError, match="human-verified"):
        parse_row(dict(zip(HEADER.split(","), bad.split(","))))


# -------------------------------------------------------------
# Loading
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_loads_rows_and_leaves_them_unverified(session, tmp_path):
    path = write_csv(tmp_path, FULL_ROW, SPARSE_ROW)
    summary = await load_program_requirements(session, path)

    rows = (await session.execute(select(ProgramRequirement))).scalars().all()
    assert summary["inserted"] == 2
    assert len(rows) == 2
    assert all(r.verified_by is None for r in rows)
    assert all(r.provenance == "claude-extracted" for r in rows)


@pytest.mark.asyncio
async def test_loading_twice_updates_rather_than_duplicates(session, tmp_path):
    path = write_csv(tmp_path, FULL_ROW)
    await load_program_requirements(session, path)
    summary = await load_program_requirements(session, path)

    rows = (await session.execute(select(ProgramRequirement))).scalars().all()
    assert len(rows) == 1
    assert summary["inserted"] == 0
    assert summary["updated"] == 1


@pytest.mark.asyncio
async def test_a_changed_value_is_written_on_reload(session, tmp_path):
    await load_program_requirements(session, write_csv(tmp_path, FULL_ROW))
    changed = FULL_ROW.replace(",IELTS,6.5,", ",IELTS,7.0,")
    await load_program_requirements(session, write_csv(tmp_path, changed))

    row = (await session.execute(select(ProgramRequirement))).scalars().one()
    assert row.language_minimum_score == 7.0


@pytest.mark.asyncio
async def test_reloading_does_not_resurrect_a_value_the_curator_cleared(session, tmp_path):
    """Clearing a cell means "we no longer believe this", and must clear the column.

    An update that skips blanks would leave the old value in place forever, so a figure
    found to be wrong could never be withdrawn -- only overwritten with another figure.
    """
    await load_program_requirements(session, write_csv(tmp_path, FULL_ROW))
    cleared = FULL_ROW.replace(",IELTS,6.5,", ",,,")
    await load_program_requirements(session, write_csv(tmp_path, cleared))

    row = (await session.execute(select(ProgramRequirement))).scalars().one()
    assert row.language_test is None
    assert row.language_minimum_score is None


@pytest.mark.asyncio
async def test_a_bad_row_aborts_the_load_without_writing_anything(session, tmp_path):
    """Partial loads are worse than failed ones: half a file is not a state anyone chose."""
    bad = FULL_ROW.replace("claude-extracted", "verified")
    path = write_csv(tmp_path, SPARSE_ROW, bad)

    with pytest.raises(CuratedRowError):
        await load_program_requirements(session, path)

    rows = (await session.execute(select(ProgramRequirement))).scalars().all()
    assert rows == []


@pytest.mark.asyncio
async def test_the_real_curated_file_loads(session):
    """The file people actually edit must parse. Catches a broken hand edit in CI."""
    real = Path(__file__).resolve().parents[2] / "data" / "curation" / "program_requirements_2026.csv"
    if not real.exists():
        pytest.skip("curated file not present")

    summary = await load_program_requirements(session, real)
    assert summary["inserted"] > 0

    rows = (await session.execute(select(ProgramRequirement))).scalars().all()
    assert all(r.verified_by is None for r in rows), (
        "A curated row claims a human verifier. Only the admin review queue may set that."
    )
    assert all(r.source_url for r in rows)
