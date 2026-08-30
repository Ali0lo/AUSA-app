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
from load_cutoff_history import (  # noqa: E402
    _clean,
    _parse_bool_or_none,
    load_csv,
    rows_from_csv,
)

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


# --- Round-2 fix: a numeric source_program_code (as Turkey's real CSV has) must not --
# --- defeat the dedupe. pandas infers int64 for an unquoted numeric column, but the --
# --- model column is String(300); the CSV-side key and the DB-side key must be built -
# --- by the same function so they cannot silently drift into different types. -------

NUMERIC_CODE_CSV = """country,source_program_code,variant_index,intake_year,cutoff_value,cutoff_unit,lower_is_better,university_name,department_name,source_url,verified_by
TR,12345,,2024,600.0,dim_score_700,False,Uni,Dept,,
"""


@pytest.mark.asyncio
async def test_numeric_source_program_code_is_idempotent(session, tmp_path):
    path = tmp_path / "numeric_code.csv"
    path.write_text(NUMERIC_CODE_CSV, encoding="utf-8")

    assert await load_csv(session, path) == 1
    assert await load_csv(session, path) == 0, (
        "a numeric source_program_code (int64 from pandas) must not defeat the "
        "dedupe against the DB-stored str value"
    )

    total = (await session.execute(select(func.count()).select_from(ProgramCutoffHistory))).scalar()
    assert total == 1


@pytest.mark.asyncio
async def test_source_program_code_is_stored_as_str(session, tmp_path):
    path = tmp_path / "numeric_code.csv"
    path.write_text(NUMERIC_CODE_CSV, encoding="utf-8")
    await load_csv(session, path)

    row = (await session.execute(select(ProgramCutoffHistory))).scalars().one()
    assert isinstance(row.source_program_code, str)
    assert row.source_program_code == "12345"


# --- Ruling 1 (generalized in the round-1 fix): all three Boolean columns must be ----
# --- parsed explicitly via _parse_bool_or_none, never via bool(). --------------------


class TestParseBoolOrNone:
    def test_none_becomes_none_not_false(self):
        # The parser itself never decides the nullable-vs-default question -- that is
        # the call site's job (see rows_from_csv). None in, None out.
        assert _parse_bool_or_none(None) is None

    def test_python_bool_passthrough(self):
        assert _parse_bool_or_none(True) is True
        assert _parse_bool_or_none(False) is False

    def test_string_false_is_false_not_bool_of_string(self):
        # This is the exact bug bool() would introduce: bool("False") is True.
        assert _parse_bool_or_none("False") is False
        assert _parse_bool_or_none("false") is False
        assert _parse_bool_or_none("FALSE") is False

    def test_string_true_variants(self):
        assert _parse_bool_or_none("True") is True
        assert _parse_bool_or_none("true") is True
        assert _parse_bool_or_none("TRUE") is True

    def test_string_digit_variants(self):
        assert _parse_bool_or_none("1") is True
        assert _parse_bool_or_none("0") is False

    def test_numeric_variants(self):
        assert _parse_bool_or_none(1) is True
        assert _parse_bool_or_none(0) is False

    def test_numpy_bool(self):
        import numpy as np

        assert _parse_bool_or_none(np.bool_(True)) is True
        assert _parse_bool_or_none(np.bool_(False)) is False

    def test_blank_string_becomes_none(self):
        assert _parse_bool_or_none("") is None
        assert _parse_bool_or_none("   ") is None

    def test_unparseable_string_raises_naming_the_value(self):
        with pytest.raises(ValueError, match="maybe"):
            _parse_bool_or_none("maybe")

    def test_unparseable_number_raises(self):
        with pytest.raises(ValueError, match="7"):
            _parse_bool_or_none(7)


# --- Round-1 fix gap: variant_discriminator_known and is_undergraduate were never ----
# --- run through any boolean parser, only through _clean (which does not interpret ---
# --- "True"/"False" strings). Both are nullable=True, so a blank there must stay ----
# --- None -- it must NOT collapse to False the way lower_is_better's blank does. -----

BOOL_COLUMNS_CSV = (
    "country,source_program_code,variant_index,intake_year,cutoff_value,cutoff_unit,"
    "lower_is_better,university_name,department_name,source_url,verified_by,"
    "variant_discriminator_known,is_undergraduate\n"
    "AZ,x--case1,,2024,600.0,dim_score_700,,ADA,Dept,,,True,False\n"
    "AZ,x--case2,,2024,610.0,dim_score_700,False,ADA,Dept,,,,\n"
)


def test_string_true_false_parsed_for_the_two_nullable_boolean_columns(tmp_path):
    path = tmp_path / "bools.csv"
    path.write_text(BOOL_COLUMNS_CSV, encoding="utf-8")
    rows = rows_from_csv(path)

    # Row 0: "True"/"False" strings for the two nullable columns must parse, not
    # pass through as truthy strings.
    assert rows[0]["variant_discriminator_known"] is True
    assert rows[0]["is_undergraduate"] is False


def test_blank_nullable_boolean_columns_stay_none_while_lower_is_better_defaults_false(tmp_path):
    path = tmp_path / "bools.csv"
    path.write_text(BOOL_COLUMNS_CSV, encoding="utf-8")
    rows = rows_from_csv(path)

    # Row 0: lower_is_better is blank -> False (NOT NULL column, False default).
    assert rows[0]["lower_is_better"] is False

    # Row 1: both nullable boolean columns are blank -> None, NOT False. "The source
    # did not say" is not the same as "no", and must not be collapsed away.
    assert rows[1]["variant_discriminator_known"] is None
    assert rows[1]["is_undergraduate"] is None
    # Row 1's lower_is_better is explicitly "False" in the CSV -> False either way.
    assert rows[1]["lower_is_better"] is False


# --- Ruling 2: _clean must coerce numpy scalars to Python natives --------------------


class TestCleanCoercesNumpyScalars:
    def test_numpy_bool_becomes_python_bool(self):
        import numpy as np

        result = _clean(np.bool_(True))
        assert result is True
        assert type(result) is bool

    def test_numpy_int64_becomes_python_int(self):
        import numpy as np

        result = _clean(np.int64(2025))
        assert result == 2025
        assert type(result) is int

    def test_numpy_float64_becomes_python_float(self):
        import numpy as np

        result = _clean(np.float64(692.6))
        assert result == 692.6
        assert type(result) is float

    def test_numpy_nan_still_becomes_none(self):
        import numpy as np

        assert _clean(np.float64("nan")) is None

    def test_plain_none_stays_none(self):
        assert _clean(None) is None

    def test_blank_string_becomes_none(self):
        assert _clean("   ") is None
