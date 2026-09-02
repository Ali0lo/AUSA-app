import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.cutoff_history import ProgramCutoffHistory


def test_model_is_registered_in_the_models_package():
    """alembic/env.py builds target_metadata from `import app.models`.

    A model absent from that package is invisible to autogenerate, which then
    emits a migration dropping its table.
    """
    import app.models

    assert "program_cutoff_history" in Base.metadata.tables
    assert hasattr(app.models, "ProgramCutoffHistory")


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

# The variant/natural-key invariant (that two byte-identical sec.az rows never collide
# on (country, source_program_code, intake_year)) moved to test_collect_azerbaijan.py:
# a model-level test here could pass "because the rows happen to differ" without ever
# exercising the collector code that is actually responsible for making them differ
# (Ruling 14).
