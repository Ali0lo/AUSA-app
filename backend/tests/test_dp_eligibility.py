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
from app.models.qualifications import (
    QUALIFICATION_ATTESTAT,
    QUALIFICATION_BACHELOR_DEGREE,
    ProgramRequirement,
)
from app.services.dp_eligibility import (
    FUNDED_STATUS_LISTED,
    FUNDED_STATUS_NONE_AT_LEVEL,
    FUNDED_STATUS_NO_ROUTES_REACHABLE,
    FUNDED_STATUS_UNREACHABLE,
    any_funded_programmes_at_level,
    assess_dp_eligibility,
    describe_funded_programmes,
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
        # `program_requirements` is created but left EMPTY on purpose. The endpoint now
        # reads it as well, and this test's subject is the DP funded-programmes answer --
        # so the empty table also pins that an uncollected country degrades to a named
        # "we have not collected this" rather than to a 500 or a silent empty list.
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[DPCatalogueEntry.__table__, ProgramRequirement.__table__],
        )
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


def test_a_score_above_both_thresholds_is_decided_without_the_field_group():
    """560 clears the harder of the two thresholds, so the student's ixtisas qrupu cannot
    change the answer. Withholding a verdict here would be false caution: the check really
    was conclusive."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.OPEN
    assert any("does not change the answer" in gate for gate in result.gates_met)


def test_a_score_below_both_thresholds_is_decided_without_the_field_group():
    """The mirror image, and the one that must not be softened: 380 clears neither 400 nor
    550, so no field group rescues it. A 'we cannot say' here would read as hope."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=380.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("below both thresholds" in gate for gate in result.gates_missing)


def test_a_score_between_the_thresholds_withholds_the_verdict_and_asks_for_the_group():
    """470 clears Group 1's 400 and fails everyone else's 550. This is the ONLY case the
    field group decides, and picking a side would be a coin flip presented as a check."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=470.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("ixtisas qrupu" in gate for gate in result.gates_missing)
    assert any("400" in gate and "550" in gate for gate in result.gates_missing)


def test_the_same_score_passes_for_group_1_and_fails_for_the_others():
    """The correction the research forced, stated as one test. 470 is not 'partly
    qualifying' -- it is a pass for engineering and a fail for everything else, and the old
    code could express neither."""
    engineering = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=470.0, dim_field_group=1, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(engineering)
    assert result.status is RouteStatus.OPEN
    assert any("clears the 400" in gate for gate in result.gates_met)

    humanities = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=470.0, dim_field_group=3, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(humanities)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("below the 550" in gate for gate in result.gates_missing)


def test_a_missing_language_certificate_is_named_as_a_gate():
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0,
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("C1" in gate for gate in result.gates_missing)


def test_a_toefl_score_surfaces_the_unresolved_language_conflict_without_resolving_it():
    """Our two sources disagree: C1 in the spec, TOEFL 80 in the research brief. The
    stricter reading stands, so a TOEFL-85 student is still UNLOCKABLE and never told they
    clear a bar nobody verified -- but they are told the disagreement exists, because
    silently failing them on a contested rule is its own kind of dishonesty."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0, toefl=85,
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("disagree" in gate for gate in result.gates_missing)
    assert any("85" in gate for gate in result.gates_missing)


def test_an_olympiad_medal_is_an_alternative_to_the_dim_route():
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        language_certificate_level="C1", has_international_olympiad_medal=True,
    )
    assert assess_dp_eligibility(profile).status is RouteStatus.OPEN


def test_master_applicants_are_not_asked_for_a_bachelor_only_dim_score():
    """The DİM threshold is a bachelor gate and the regulation excludes it above that
    level. A master's applicant -- degree in hand, C1, correctly no DİM score, since DİM is
    a school-leaving exam -- must never be told they are missing it."""
    profile = StudentRouteProfile(
        level_sought="master", qualification_held=QUALIFICATION_BACHELOR_DEGREE,
        language_certificate_level="C1", gpa=3.6, gpa_scale="4.0",
    )
    result = assess_dp_eligibility(profile)
    assert not any("DİM" in gate for gate in result.gates_missing)
    assert not any("SAT" in gate for gate in result.gates_missing)


def test_the_master_gate_is_gpa_and_an_offer_not_an_unknown():
    """This module used to report the master's gate as UNKNOWN and record the spec's
    self-contradiction as an open question. The research settles it: CGPA plus an
    unconditional offer. The GPA is read and reported, and -- because no numeric minimum is
    published anywhere -- it is never compared against a threshold."""
    profile = StudentRouteProfile(
        level_sought="master", qualification_held=QUALIFICATION_BACHELOR_DEGREE,
        language_certificate_level="C1", gpa=3.6, gpa_scale="4.0",
    )
    result = assess_dp_eligibility(profile)
    assert "CGPA" in result.band_checked
    assert "550" not in result.band_checked
    assert any("3.6" in gate for gate in result.gates_met)
    assert any("no published minimum" in gate.lower() for gate in result.gates_met)
    # The offer is a document, not a score, so it can never be cleared from a profile.
    assert any("unconditional offer" in gate.lower() for gate in result.gates_missing)
    assert result.status is RouteStatus.UNLOCKABLE


def test_a_master_applicant_without_a_gpa_is_asked_for_it():
    profile = StudentRouteProfile(
        level_sought="master", qualification_held=QUALIFICATION_BACHELOR_DEGREE,
        language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert any("grade average" in gate for gate in result.gates_missing)


def test_a_sat_score_never_opens_the_dp_because_no_sat_route_exists():
    """The regulation exempts exactly one group from the DİM requirement: international
    subject-olympiad medallists. The 75th-percentile SAT/ACT alternative in spec §2.2 does
    not exist, and this pins that a SAT can never satisfy the academic gate -- the property
    the old fail-closed code happened to have, now the property the rule actually states."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        sat=1550, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert not any("SAT" in gate for gate in result.gates_met)
    assert any("no SAT or ACT route" in gate for gate in result.gates_missing)


def test_a_low_sat_score_is_treated_exactly_like_a_high_one():
    """SAT 200 and SAT 1550 must produce the same outcome, because the score is never
    compared to anything -- there is no bar to compare it to."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        sat=200, dim_score=300.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert result.gates_missing


def test_a_sat_does_not_bypass_the_dim_evaluation():
    """The academic-gate chain was once a single elif, so a SAT value skipped the DİM
    checks entirely. A student offering both must have both considered."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=470.0, sat=1550, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("ixtisas qrupu" in gate for gate in result.gates_missing)
    assert any("SAT" in gate for gate in result.gates_missing)


def test_an_act_score_is_read_and_reported_not_ignored():
    """Asserting the offered score itself (35) appears in the explanation proves the value
    was actually read, not that a fixed string happened to contain the letters."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        act=35, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("35" in gate for gate in result.gates_missing)
    assert not any("ACT" in gate for gate in result.gates_met)


def test_the_quota_note_names_the_places_at_the_students_own_level():
    """125 bachelor against 353 master's out of 500. A student choosing a level is choosing
    a queue, and the size of that queue was previously rendered nowhere."""
    bachelor = assess_dp_eligibility(StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
    ))
    assert "125" in bachelor.quota_note and "500" in bachelor.quota_note

    master = assess_dp_eligibility(StudentRouteProfile(
        level_sought="master", qualification_held=QUALIFICATION_BACHELOR_DEGREE,
    ))
    assert "353" in master.quota_note
    # And the note must never be read as odds of winning one of them.
    assert "not your odds" in master.quota_note


def test_the_five_year_return_obligation_is_always_stated():
    """Accepting the funding is a contract with a repayment clause. It is not conditional
    on clearing any gate, so it is reported for every profile -- including one that clears
    nothing, because that student is still deciding whether to aim for this at all."""
    result = assess_dp_eligibility(StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
    ))
    assert "5 years" in result.obligation_note
    assert "repaying" in result.obligation_note


def test_the_window_note_says_which_academic_year_an_application_would_be_for():
    """After June the current cycle has closed, so an application is for the year after --
    the difference between a plan a student can act on now and one they cannot."""
    from datetime import date as _date

    from app.services.dp_eligibility import application_window_note

    september = application_window_note(_date(2026, 9, 4))
    assert "2026/2027" in september and "closed" in september
    assert "2027/2028" in september

    february = application_window_note(_date(2026, 2, 4))
    assert "closed" not in february
    # No invented precision: the sources give months, so the note gives months.
    assert "dp.edu.az" in february


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
    """The USA has zero DP bachelor programmes. That is an answer, not a gap to fill --
    but an 'always return []' implementation would also pass an empty-only check. So this
    test also proves, against the SAME seeded data, that the query returns real rows when
    they exist: a US *master's* row and a TR *bachelor's* row are both seeded alongside
    the empty case, and both must come back. A broken query that always returns [] fails
    here; one that always returns everything fails the empty assertion above.
    """
    assert await funded_programmes(session, level="bachelor", country_codes=("US",)) == []

    master_us = await funded_programmes(session, level="master", country_codes=("US",))
    assert {r.university_name for r in master_us} == {"Some US University"}

    bachelor_tr = await funded_programmes(session, level="bachelor", country_codes=("TR",))
    assert {r.university_name for r in bachelor_tr} == {"Bogazici University"}


@pytest.mark.asyncio
async def test_any_funded_programmes_at_level_true_when_rows_exist(session):
    assert await any_funded_programmes_at_level(session, level="bachelor") is True
    assert await any_funded_programmes_at_level(session, level="master") is True


@pytest.mark.asyncio
async def test_any_funded_programmes_at_level_false_when_none_exist(session):
    """No row in the fixture is at any level but 'bachelor'/'master' -- this proves the
    existence check discriminates rather than always returning True."""
    assert await any_funded_programmes_at_level(session, level="doctorate") is False


def test_describe_funded_programmes_when_the_list_has_rows():
    status, explanation = describe_funded_programmes(
        programmes=["placeholder"], reachable=("TR", "DE"), any_at_level=True,
    )
    assert status == FUNDED_STATUS_LISTED
    assert explanation == ""


def test_describe_funded_programmes_when_no_route_reaches_any_country():
    """Case (c): the profile's routes reach nothing at this level, so no country was
    queried -- must not be conflated with 'the DP funds nothing at this level'."""
    status, explanation = describe_funded_programmes(
        programmes=[], reachable=(), any_at_level=False,
    )
    assert status == FUNDED_STATUS_NO_ROUTES_REACHABLE
    assert "does not currently reach any country" in explanation
    assert "not a statement that the Dövlət Proqramı funds nothing" in explanation


def test_describe_funded_programmes_when_the_level_funds_nothing_at_all():
    """Case (a): a real answer, e.g. the USA's zero DP bachelor places."""
    status, explanation = describe_funded_programmes(
        programmes=[], reachable=("US",), any_at_level=False,
    )
    assert status == FUNDED_STATUS_NONE_AT_LEVEL
    assert "zero programmes at this level" in explanation


def test_describe_funded_programmes_when_programmes_exist_but_not_reachable():
    """Case (b): the DP funds this level somewhere, just not anywhere this profile's
    routes reach today -- must not read as 'you are ineligible for the programme'."""
    status, explanation = describe_funded_programmes(
        programmes=[], reachable=("PL",), any_at_level=True,
    )
    assert status == FUNDED_STATUS_UNREACHABLE
    assert "not in a country your current profile can reach" in explanation
    assert "not a statement that you are ineligible" in explanation


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

    # The funded list itself: this profile reaches both TR (direct, OPEN) and DE (via the
    # prep-year unlock and/or the UNLOCKABLE Studienkolleg hop), and the fixture seeds a
    # bachelor row in each -- both must actually appear, not just be permitted to.
    assert {p["university_name"] for p in body["dp"]["funded_programmes"]} == {
        "Bogazici University", "Technical University of Munich",
    }
    assert body["dp"]["funded_programmes_status"] == FUNDED_STATUS_LISTED


@pytest.mark.asyncio
async def test_a_profile_blocked_everywhere_gets_an_honest_reason_not_a_bare_empty_list(session):
    """A master's applicant holding only an attestat: every master route requires a
    completed bachelor's degree, so `compose_two_hop` reaches zero plans (no bachelor-level
    route produces a qualification that unlocks a master route either). `reachable` is
    empty, so `funded_programmes` is `[]` -- but the fixture has a real US master's row,
    so an unexplained `[]` here would misread as 'the DP funds nothing at master level',
    which is false. The response must say which of the three empty-list reasons applies.
    """
    async def _get_test_db():
        yield session

    app.dependency_overrides[get_db] = _get_test_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            res = await c.post(
                "/api/v1/routes/assess",
                json={"level_sought": "master", "qualification_held": "attestat"},
            )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()
    assert body["dp"]["funded_programmes"] == []
    assert body["dp"]["funded_programmes_status"] == FUNDED_STATUS_NO_ROUTES_REACHABLE
    assert "does not currently reach any country" in body["dp"]["funded_programmes_explanation"]
    assert "not a statement" in body["dp"]["funded_programmes_explanation"]
