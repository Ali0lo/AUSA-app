"""Loader tests for the Dövlət Proqramı catalogue.

The fixture CSV reproduces the real file's two traps: a utf-8 BOM, and university and
programme values wrapped in literal double-quote characters inside the field.
"""

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.dp_catalogue import DPCatalogueEntry
from scripts.load_dp_catalogue import load_csv, rows_from_csv

SOURCE_URL = "https://admin.opendata.az/dataset/example/resource/example/download/dp-test.csv"

CSV_BODY = (
    "﻿Nömrə,Təhsil səviyyəsi,Ölkə,Universitet,Təhsil proqramı\n"
    '1,bakalavriat,Almaniya Federativ Respublikası,"""Technical University of Munich""","""Architecture"""\n'
    '2,bakalavriat,Türkiyə Respublikası,"""Bogazici University""","""Computer Engineering"""\n'
    '3,bakalavriat,Malayziya,"""Universiti Malaya""","""Chemistry"""\n'
)


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "dp-bakalavr-2026.csv"
    path.write_text(CSV_BODY, encoding="utf-8")
    return path


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[DPCatalogueEntry.__table__])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def test_quotes_are_stripped_from_names(csv_path):
    """Every university value in the real file is wrapped in literal double quotes.

    Storing them keeps the quote characters in the name, and no join to any other source
    will ever match.
    """
    rows = rows_from_csv(csv_path, SOURCE_URL)
    assert rows[0]["university_name"] == "Technical University of Munich"
    assert rows[0]["program_name"] == "Architecture"


def test_level_and_country_are_mapped(csv_path):
    rows = rows_from_csv(csv_path, SOURCE_URL)
    assert rows[0]["level"] == "bachelor"
    assert rows[0]["country_code"] == "DE"
    assert rows[1]["country_code"] == "TR"


def test_a_country_outside_scope_gets_no_code_rather_than_a_guess(csv_path):
    """27 of the 33 countries are out of scope. NULL is the honest answer for them."""
    rows = rows_from_csv(csv_path, SOURCE_URL)
    malaysia = next(r for r in rows if r["country_source"] == "Malayziya")
    assert malaysia["country_code"] is None
    assert malaysia["university_name"] == "Universiti Malaya"


def test_an_unknown_level_raises_rather_than_loading(tmp_path):
    """A level we cannot map is a changed source file, not a row to guess at."""
    path = tmp_path / "dp-broken-2026.csv"
    path.write_text(
        "﻿Nömrə,Təhsil səviyyəsi,Ölkə,Universitet,Təhsil proqramı\n"
        '1,doktorantura,Malayziya,"""X University""","""Y"""\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="doktorantura"):
        rows_from_csv(path, SOURCE_URL)


def test_a_missing_column_raises_rather_than_loading_a_partial_table(tmp_path):
    path = tmp_path / "dp-missing-2026.csv"
    path.write_text("﻿Nömrə,Ölkə\n1,Malayziya\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        rows_from_csv(path, SOURCE_URL)


@pytest.mark.asyncio
async def test_loading_twice_inserts_nothing_the_second_time(session, csv_path):
    assert await load_csv(session, csv_path, SOURCE_URL) == 3
    assert await load_csv(session, csv_path, SOURCE_URL) == 0
    total = (await session.execute(select(func.count()).select_from(DPCatalogueEntry))).scalar()
    assert total == 3


@pytest.mark.asyncio
async def test_every_row_carries_its_source(session, csv_path):
    """ADR-0004: a row that cannot be traced back to where it came from is not evidence."""
    await load_csv(session, csv_path, SOURCE_URL)
    rows = (await session.execute(select(DPCatalogueEntry))).scalars().all()
    assert all(r.source_url == SOURCE_URL for r in rows)
    assert all(r.retrieved_at is not None for r in rows)
    assert all(r.verified_by is None for r in rows)
