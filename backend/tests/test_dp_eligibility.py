"""The DP funding gate.

The wording rule matters as much as the logic here: clearing the published gates is
"possibly eligible", never a promise of an award. The DP funds roughly 400 places against
a much larger pool, and the selection that follows the gates is a committee decision no
dataset in this project models (spec §5.2).
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.domain.routes import RouteStatus, StudentRouteProfile
from app.models.dp_catalogue import DPCatalogueEntry
from app.models.qualifications import QUALIFICATION_ATTESTAT
from app.services.dp_eligibility import (
    assess_dp_eligibility,
    funded_programmes,
)

from datetime import datetime, timezone


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
        now = datetime.now(timezone.utc)
        s.add_all([
            DPCatalogueEntry(
                level="bachelor", country_source="Türkiyə Respublikası", country_code="TR",
                university_name="Bogazici University", program_name="Computer Engineering",
                intake_year=2026, source_url="https://example.az/dp", retrieved_at=now,
            ),
            DPCatalogueEntry(
                level="bachelor", country_source="Almaniya Federativ Respublikası",
                country_code="DE", university_name="Technical University of Munich",
                program_name="Architecture", intake_year=2026,
                source_url="https://example.az/dp", retrieved_at=now,
            ),
            DPCatalogueEntry(
                level="master", country_source="Amerika Birləşmiş Ştatları", country_code="US",
                university_name="Some US University", program_name="Data Science",
                intake_year=2026, source_url="https://example.az/dp", retrieved_at=now,
            ),
        ])
        await s.commit()
        yield s
    await engine.dispose()


def test_a_clear_dim_score_and_c1_is_possibly_eligible():
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.OPEN
    assert "550" in result.band_checked


def test_a_score_inside_the_band_says_so_rather_than_inventing_a_threshold():
    """400-550 'depending on field', and the per-field table is not verified. The band is
    reported; a single number would be invented."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=470.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert "400" in result.band_checked and "550" in result.band_checked
    assert any("field" in gate.lower() for gate in result.gates_missing)


def test_a_missing_language_certificate_is_named_as_a_gate():
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0,
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("C1" in gate for gate in result.gates_missing)


def test_an_olympiad_medal_is_an_alternative_to_the_dim_route():
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        language_certificate_level="C1", has_international_olympiad_medal=True,
    )
    assert assess_dp_eligibility(profile).status is RouteStatus.OPEN


def test_the_gate_never_promises_an_award():
    """Prohibited output, in generated text and UI labels alike (spec §5.2)."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    rendered = " ".join((result.band_checked, *result.gates_met, *result.gates_missing)).lower()
    for promise in ("you will receive", "guaranteed", "you qualify for a full scholarship"):
        assert promise not in rendered


@pytest.mark.asyncio
async def test_funded_programmes_are_filtered_by_level_and_country(session):
    rows = await funded_programmes(session, level="bachelor", country_codes=("TR", "DE"))
    assert {r.university_name for r in rows} == {
        "Bogazici University", "Technical University of Munich",
    }


@pytest.mark.asyncio
async def test_a_level_with_no_funded_programmes_returns_empty_not_a_substitute(session):
    """The USA has zero DP bachelor programmes. That is an answer, not a gap to fill."""
    assert await funded_programmes(session, level="bachelor", country_codes=("US",)) == []


from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app


@pytest.mark.asyncio
async def test_the_endpoint_answers_the_walkthrough_profile(session):
    """Spec §6's walkthrough: attestat, DİM 520, IELTS 7.0, bachelor.

    Germany and the UK blocked, both unlocks offered, the DP band shown, and the funded
    programme list filtered to what is reachable.
    """
    async def _get_test_db():
        yield session

    app.dependency_overrides[get_db] = _get_test_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            res = await c.post(
                "/api/v1/routes/assess",
                json={
                    "level_sought": "bachelor",
                    "qualification_held": "attestat",
                    "dim_score": 520.0,
                    "ielts": 7.0,
                    "language_certificate_level": "C1",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()

    assert any("DE" in entry for entry in body["blocked"])
    assert any("GB" in entry for entry in body["blocked"])

    prep_plans = [
        p for p in body["plans"]
        if len(p["hops"]) == 2 and p["hops"][0]["key"] == "az-prep-year"
    ]
    assert prep_plans, "the prep-year unlock was not offered"
    assert all(hop["citation"] for plan in body["plans"] for hop in plan["hops"])

    assert "400" in body["dp"]["band_checked"]
    assert "not an award" in body["dp"]["note"].lower()
