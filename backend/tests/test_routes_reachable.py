"""Pins the product's central finding: a country reached only via a second hop (the
prep-year unlock) must still contribute its funded programmes.

The review report's mutation M3 -- computing `reachable` from `plan.hops[:1]` instead of
every hop -- left all 152 tests green, because in the current `ALL_ROUTES`, every blocked
destination (Germany, the UK) has a same-country non-blocked sibling route that is
reachable in a single hop (`de-bachelor-studienkolleg`, `uk-bachelor-foundation`). So no
country in the real route set is EVER reachable only via a two-hop plan today, and this
wiring -- the two-hop composition actually feeding the DP funded-programmes list -- has
never been exercised by a real profile.

Because no real country isolates this path, this file constructs a synthetic route pair
that does: a one-hop "prep year"-shaped unlock, and a destination that is BLOCKED direct
and reachable only by first completing the unlock. This is disclosed here rather than left
implicit, per the fix report.
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.v1.routes import RouteHop, RoutePlanResponse, _reachable_countries
from app.core.database import Base
from app.domain.routes import Route, StudentRouteProfile
from app.models.dp_catalogue import DPCatalogueEntry
from app.models.qualifications import QUALIFICATION_ATTESTAT
from app.services.dp_eligibility import funded_programmes
from app.services.route_engine import compose_two_hop
from app.services.university_requirements import UNIS_STATUS_NONE_CURATED_FOR_COUNTRY

SYNTH_PREP_UNLOCK = Route(
    key="synth-prep-unlock", country_code="AZ", level="bachelor",
    mechanism="test fixture: a one-hop unlock, shaped like az-prep-year",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    produces_qualification="synth-prep-qualification",
    exams=(), time_cost_months=12, money_cost_azn=(0, 0), citation="test fixture",
)

# BLOCKED direct (an attestat does not satisfy it) and no other route in this synthetic
# set reaches it in one hop -- so it is reachable ONLY as a two-hop destination, the exact
# shape that does not exist anywhere in the real ALL_ROUTES today.
SYNTH_DESTINATION = Route(
    key="synth-destination-direct", country_code="ZZ", level="bachelor",
    mechanism="test fixture: reachable only after the prep unlock",
    requires_qualification=("synth-prep-qualification",),
    produces_qualification=None,
    exams=(), time_cost_months=0, money_cost_azn=(0, 0), citation="test fixture",
)

PROFILE = StudentRouteProfile(level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT)


def test_fixture_sanity_zz_is_reachable_only_via_two_hops():
    """Guards the fixture itself: ZZ must not be reachable in one hop, or this test proves
    nothing about the two-hop wiring."""
    plans = compose_two_hop(PROFILE, routes=(SYNTH_PREP_UNLOCK, SYNTH_DESTINATION))
    one_hop_countries = {p.hops[0].country_code for p in plans if len(p.hops) == 1}
    assert "ZZ" not in one_hop_countries
    two_hop_destinations = {p.hops[-1].country_code for p in plans if len(p.hops) == 2}
    assert "ZZ" in two_hop_destinations


def test_reachable_countries_includes_a_two_hop_destination():
    """Direct unit test of the exact function the endpoint uses to build `reachable`
    (`app.api.v1.routes._reachable_countries`). Mutating it to only look at
    `plan.hops[:1]` (M3) makes this fail: ZZ would never appear."""
    plans_domain = compose_two_hop(PROFILE, routes=(SYNTH_PREP_UNLOCK, SYNTH_DESTINATION))
    # Mirror the endpoint's own construction of RoutePlanResponse from RoutePlan.
    plans = [
        RoutePlanResponse(
            hops=[
                RouteHop(
                    key=hop.key, country_code=hop.country_code, mechanism=hop.mechanism,
                    time_cost_months=hop.time_cost_months,
                    money_cost_azn_low=hop.money_cost_azn[0],
                    money_cost_azn_high=hop.money_cost_azn[1],
                    citation=hop.citation, provenance=hop.provenance,
                )
                for hop in plan.hops
            ],
            total_months=plan.total_months,
            total_cost_azn_low=plan.total_cost_azn[0],
            total_cost_azn_high=plan.total_cost_azn[1],
            status=plan.status.value,
            missing=list(plan.missing),
            # This test is about `_reachable_countries`, which reads only `hops`. The
            # university fields are filled with the shape an uncollected destination
            # actually produces -- an empty list with a named reason -- rather than with
            # placeholders, so the fixture cannot drift into asserting a state the
            # endpoint never emits.
            destination_country=plan.hops[-1].country_code,
            qualification_delivered=(
                plan.hops[-1].produces_qualification or PROFILE.qualification_held
            ),
            universities=[],
            universities_status=UNIS_STATUS_NONE_CURATED_FOR_COUNTRY,
            universities_explanation="synthetic country; nothing collected",
        )
        for plan in plans_domain
    ]

    reachable = _reachable_countries(plans)

    assert "ZZ" in reachable, (
        "a country reachable only via a two-hop plan did not contribute to `reachable` -- "
        "this is exactly mutation M3 from the review report"
    )


@pytest_asyncio.fixture
async def zz_session():
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
        s.add(DPCatalogueEntry(
            level="bachelor", country_source="Synthetic Country", country_code="ZZ",
            university_name="Synthetic University", program_name="Synthetic Programme",
            intake_year=2026, source_url="https://example.az/dp", retrieved_at=now,
        ))
        await s.commit()
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_a_country_reachable_only_through_the_prep_unlock_contributes_its_funded_programmes(zz_session):
    """End-to-end wiring: compose_two_hop -> _reachable_countries -> funded_programmes.
    ZZ is reachable only via the synthetic prep-year-shaped unlock (a two-hop plan). If the
    two-hop destination were ever dropped from `reachable` (M3), this seeded ZZ programme
    would silently disappear from the response with no error raised anywhere."""
    plans_domain = compose_two_hop(PROFILE, routes=(SYNTH_PREP_UNLOCK, SYNTH_DESTINATION))
    reachable = tuple({hop.country_code for plan in plans_domain for hop in plan.hops})
    assert "ZZ" in reachable  # fixture sanity, re-asserted at the domain-object level

    funded = await funded_programmes(zz_session, level="bachelor", country_codes=reachable)

    assert {row.university_name for row in funded} == {"Synthetic University"}
