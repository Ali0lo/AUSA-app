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
    _parse_lower_is_better,
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


# --- Ruling 1: lower_is_better must be parsed explicitly, never via bool() -----------


class TestParseLowerIsBetter:
    def test_none_becomes_false(self):
        assert _parse_lower_is_better(None) is False

    def test_python_bool_passthrough(self):
        assert _parse_lower_is_better(True) is True
        assert _parse_lower_is_better(False) is False

    def test_string_false_is_false_not_bool_of_string(self):
        # This is the exact bug bool() would introduce: bool("False") is True.
        assert _parse_lower_is_better("False") is False
        assert _parse_lower_is_better("false") is False
        assert _parse_lower_is_better("FALSE") is False

    def test_string_true_variants(self):
        assert _parse_lower_is_better("True") is True
        assert _parse_lower_is_better("true") is True
        assert _parse_lower_is_better("TRUE") is True

    def test_string_digit_variants(self):
        assert _parse_lower_is_better("1") is True
        assert _parse_lower_is_better("0") is False

    def test_numeric_variants(self):
        assert _parse_lower_is_better(1) is True
        assert _parse_lower_is_better(0) is False

    def test_numpy_bool(self):
        import numpy as np

        assert _parse_lower_is_better(np.bool_(True)) is True
        assert _parse_lower_is_better(np.bool_(False)) is False

    def test_unparseable_string_raises_naming_the_value(self):
        with pytest.raises(ValueError, match="maybe"):
            _parse_lower_is_better("maybe")

    def test_unparseable_number_raises(self):
        with pytest.raises(ValueError, match="7"):
            _parse_lower_is_better(7)


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
