"""Tests for target institution catalog and gap analysis endpoints."""
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.models.qualifications import ProgramRequirement


@pytest.mark.asyncio
async def test_target_catalog_returns_items():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/routes/catalog")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "university_name" in first
    assert "country_code" in first
    assert "level" in first


@pytest.mark.asyncio
async def test_target_gap_blocked_germany_attestat():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/routes/target-gap",
            json={
                "university_name": "Technical University of Munich",
                "level": "bachelor",
                "qualification_held": "attestat",
                "gpa": 4.5,
                "gpa_scale": "5.0",
                "ielts": 6.5,
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is True
    assert data["country_code"] == "DE"
    assert data["route_status"] == "BLOCKED"
    assert "Studienkolleg" in " ".join(data["unlock_steps"])
    assert data["unlock_time_months"] == 12
    # Checklist verification
    checklist = {item["name"]: item for item in data["checklist"]}
    assert "Entry Qualification" in checklist
    assert checklist["Entry Qualification"]["status"] == "GAP"


@pytest.mark.asyncio
async def test_target_gap_turkey_attestat_open():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/routes/target-gap",
            json={
                "university_name": "Bogazici University",
                "level": "bachelor",
                "qualification_held": "attestat",
                "gpa": 4.8,
                "gpa_scale": "5.0",
                "ielts": 7.0,
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is True
    assert data["country_code"] == "TR"
    assert data["route_status"] == "OPEN"


@pytest.mark.asyncio
async def test_target_gap_uncurated_university_returns_honest_gap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/routes/target-gap",
            json={
                "university_name": "Nonexistent University Of Mars",
                "level": "bachelor",
                "qualification_held": "attestat",
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is False
    assert "catalogue gap" in data["route_gap_statement"].lower()
    assert len(data["alternatives"]) > 0


# The curated catalogue lives in two files: program_requirements_2026.csv (bachelor) and
# program_requirements_track_a.csv (Track A, which is where every master row and all US
# and Polish coverage landed). bootstrap_catalogue loads both; the endpoint's offline
# fallback read only the first, so a student whose plan depends on Track A was told we
# hold nothing -- a claim the data does not support.


@pytest.mark.asyncio
async def test_catalog_serves_master_programmes_and_not_only_bachelor():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/routes/catalog", params={"level": "master"})
    assert res.status_code == 200
    data = res.json()
    assert data, "master's returned nothing while 30 curated master rows are on disk"
    assert all(item["level"] == "master" for item in data)


@pytest.mark.asyncio
async def test_catalog_reaches_the_countries_track_a_curated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/routes/catalog", params={"country": "US"})
    assert res.status_code == 200
    names = {item["university_name"] for item in res.json()}
    assert "Carnegie Mellon University" in names


@pytest.mark.asyncio
async def test_target_gap_finds_a_curated_master_programme():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/routes/target-gap",
            json={
                "university_name": "Technical University of Munich",
                "level": "master",
                "qualification_held": "bachelor_degree",
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is True, (
        "a curated master programme reported as a catalogue gap; "
        "'we have not collected this' is a claim about our data, and here it is false"
    )
    assert data["country_code"] == "DE"


# The two endpoints above read the database first and fall back to the curated CSVs.
# Every other test in this file exercises only the fallback, because the suite's sqlite
# database has no schema -- so the database branch stayed unproven even after the missing
# `select` import was restored. This fixture gives it a real table to answer from.


@pytest_asyncio.fixture
async def catalogue_db():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all, tables=[ProgramRequirement.__table__]
        )
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        async def database():
            yield session

        app.dependency_overrides[get_db] = database
        try:
            yield session
        finally:
            app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_catalog_answers_from_the_database_when_one_is_available(catalogue_db):
    # A name that appears in neither CSV, so seeing it back proves the row came from the
    # database rather than from the fallback that would mask a broken query.
    catalogue_db.add(
        ProgramRequirement(
            university_name="Database Only University",
            program_name="Proof of Wiring",
            level="master",
            intake_year=2026,
            country_code="GB",
            source_url="https://example.edu/admissions",
            retrieved_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        )
    )
    await catalogue_db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/routes/catalog", params={"level": "master"})

    assert res.status_code == 200
    names = {item["university_name"] for item in res.json()}
    assert "Database Only University" in names, (
        "the database branch did not answer; the CSV fallback masked it"
    )
