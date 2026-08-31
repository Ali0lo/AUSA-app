"""The two tables the route engine reads. Level is part of the key in both."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.dp_catalogue import DPCatalogueEntry
from app.models.qualifications import (
    QUALIFICATION_ATTESTAT,
    ProgramRequirement,
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
            tables=[
                Student.__table__,
                StudentQualification.__table__,
                ProgramRequirement.__table__,
                DPCatalogueEntry.__table__,
            ],
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_one_student_can_hold_a_profile_per_level(session):
    """Bachelor and master are different questions with different answers."""
    student = Student(email="two_levels@ausa.edu.az")
    session.add(student)
    await session.commit()
    await session.refresh(student)

    session.add_all([
        StudentQualification(
            student_id=student.id,
            level_sought="bachelor",
            qualification_held=QUALIFICATION_ATTESTAT,
            dim_score=520.0,
        ),
        StudentQualification(
            student_id=student.id,
            level_sought="master",
            qualification_held="bachelor_degree",
            ielts=7.0,
        ),
    ])
    await session.commit()

    rows = (await session.execute(select(StudentQualification))).scalars().all()
    assert {r.level_sought for r in rows} == {"bachelor", "master"}


@pytest.mark.asyncio
async def test_a_second_profile_for_the_same_level_is_rejected(session):
    student = Student(email="duplicate@ausa.edu.az")
    session.add(student)
    await session.commit()
    await session.refresh(student)

    session.add(StudentQualification(
        student_id=student.id, level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
    ))
    await session.commit()

    session.add(StudentQualification(
        student_id=student.id, level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
    ))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
async def test_unset_scores_stay_null(session):
    """'Did not sit the exam' and 'scored zero' are different facts."""
    student = Student(email="no_scores@ausa.edu.az")
    session.add(student)
    await session.commit()
    await session.refresh(student)

    session.add(StudentQualification(
        student_id=student.id, level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
    ))
    await session.commit()

    row = (await session.execute(select(StudentQualification))).scalars().one()
    assert row.dim_score is None
    assert row.ielts is None
    assert row.sat is None


@pytest.mark.asyncio
async def test_the_same_programme_carries_different_requirements_per_level(session):
    """One university, one subject, two levels, two sets of requirements and fees."""
    now = datetime.now(timezone.utc)
    session.add_all([
        ProgramRequirement(
            university_name="Technical University of Munich",
            program_name="Informatics", level="bachelor", intake_year=2026,
            country_code="DE", entry_qualification_accepted="one_year_university",
            tuition_per_year=0.0, currency="EUR",
            source_url="https://www.tum.de/en/studies", retrieved_at=now,
        ),
        ProgramRequirement(
            university_name="Technical University of Munich",
            program_name="Informatics", level="master", intake_year=2026,
            country_code="DE", entry_qualification_accepted="bachelor_degree",
            language_test="IELTS", language_minimum_score=6.5,
            tuition_per_year=0.0, currency="EUR",
            source_url="https://www.tum.de/en/studies", retrieved_at=now,
        ),
    ])
    await session.commit()

    rows = (await session.execute(select(ProgramRequirement))).scalars().all()
    by_level = {r.level: r for r in rows}
    assert by_level["bachelor"].entry_qualification_accepted == "one_year_university"
    assert by_level["master"].entry_qualification_accepted == "bachelor_degree"


@pytest.mark.asyncio
async def test_a_requirement_row_must_carry_its_source(session):
    """source_url is NOT NULL: a requirement nobody can trace is not a requirement."""
    session.add(ProgramRequirement(
        university_name="Nowhere University", program_name="Something",
        level="bachelor", intake_year=2026, country_code="TR",
        retrieved_at=datetime.now(timezone.utc),
    ))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
