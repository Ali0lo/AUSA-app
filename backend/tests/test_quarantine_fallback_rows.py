"""The deleted extraction fallback left rows behind. This finds them.

Marker values, all from the removed code path: a university named "Extracted University",
a programme named "Extracted Program", and the note "Extracted via fallback parser."
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.program import Program as ProgramModel
from scripts.quarantine_fallback_rows import find_suspect_programs, quarantine


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[ProgramModel.__table__])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_finds_only_the_fallback_rows(session):
    session.add_all([
        ProgramModel(university_name="Extracted University", program_name="B.Sc. Something"),
        ProgramModel(university_name="TU Munich", program_name="Extracted Program"),
        ProgramModel(
            university_name="Real University",
            program_name="B.Sc. Real",
            requirements_text="Extracted via fallback parser.",
        ),
        ProgramModel(university_name="Honest University", program_name="B.Sc. Honest"),
    ])
    await session.commit()

    suspects = await find_suspect_programs(session)
    assert {p.university_name for p in suspects} == {
        "Extracted University", "TU Munich", "Real University",
    }


@pytest.mark.asyncio
async def test_quarantine_deactivates_without_deleting(session):
    """Deactivated, not deleted. A human still needs to look at what the fallback wrote."""
    session.add(ProgramModel(university_name="Extracted University", program_name="B.Sc. X"))
    await session.commit()

    count = await quarantine(session, await find_suspect_programs(session))
    assert count == 1

    row = (await session.execute(select(ProgramModel))).scalars().one()
    assert row.is_active is False
    assert row.verification_status == "quarantined_fallback_extraction"
    assert row.confidence_score is None


@pytest.mark.asyncio
async def test_a_clean_database_yields_nothing(session):
    session.add(ProgramModel(university_name="Honest University", program_name="B.Sc. Honest"))
    await session.commit()
    assert await find_suspect_programs(session) == []
