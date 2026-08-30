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
