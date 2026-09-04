"""The join from a route plan to the named universities it reaches.

The tests that matter here are not "does the query filter correctly". They are the two
places this code can be confidently wrong: delivering the wrong qualification for a two-hop
plan (which would list the universities a student CANNOT apply to and hide the ones they
can), and rendering a NULL requirement as an absent one.
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.domain.grades import check_grade
from app.domain.routes import StudentRouteProfile
from app.domain.route_definitions import (
    AZ_PREP_YEAR,
    DE_BACHELOR_STUDIENKOLLEG,
    TR_BACHELOR_DIRECT,
    UK_BACHELOR_DIRECT,
    UK_BACHELOR_FOUNDATION,
)
from app.models.qualifications import (
    QUALIFICATION_ATTESTAT,
    QUALIFICATION_FESTSTELLUNGSPRUEFUNG,
    QUALIFICATION_FOUNDATION_YEAR,
    QUALIFICATION_ONE_YEAR_UNIVERSITY,
    ProgramRequirement,
)
from app.services.route_engine import RoutePlan, compose_two_hop
from app.services.university_requirements import (
    UNIS_STATUS_LISTED,
    UNIS_STATUS_NONE_ACCEPT_QUALIFICATION,
    UNIS_STATUS_NONE_CURATED_FOR_COUNTRY,
    UniversityMatch,
    any_requirements_curated,
    describe_universities,
    missing_requirement_note,
    qualification_delivered,
    universities_accepting,
)

SCHOOL_LEAVER = StudentRouteProfile(
    level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT
)

NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)


def make_row(**overrides) -> ProgramRequirement:
    defaults = dict(
        university_name="Test University",
        program_name="International undergraduate admission",
        level="bachelor",
        intake_year=2026,
        country_code="GB",
        entry_qualification_accepted=QUALIFICATION_ONE_YEAR_UNIVERSITY,
        provenance="claude-extracted",
        source_url="https://example.edu/admissions",
        retrieved_at=NOW,
        last_checked=NOW,
    )
    defaults.update(overrides)
    return ProgramRequirement(**defaults)


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[ProgramRequirement.__table__])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def plan_of(*hops) -> RoutePlan:
    """A RoutePlan carrying only what `qualification_delivered` reads."""
    return RoutePlan(hops=tuple(hops), total_months=0, total_cost_azn=(0, 0),
                     status=None, missing=())


# -------------------------------------------------------------
# The fold: what qualification does a plan actually deliver?
# -------------------------------------------------------------
def test_a_direct_plan_delivers_what_the_student_already_holds():
    """Turkey admits on the attestat itself, so the attestat is what the university sees."""
    assert qualification_delivered(plan_of(TR_BACHELOR_DIRECT), SCHOOL_LEAVER) == (
        QUALIFICATION_ATTESTAT
    )


def test_a_producing_hop_replaces_what_the_student_held():
    """The Studienkolleg turns an attestat into a Feststellungsprüfung; TUM's row is keyed
    on the latter, not on what the student walked in with."""
    assert qualification_delivered(plan_of(DE_BACHELOR_STUDIENKOLLEG), SCHOOL_LEAVER) == (
        QUALIFICATION_FESTSTELLUNGSPRUEFUNG
    )
    assert qualification_delivered(plan_of(UK_BACHELOR_FOUNDATION), SCHOOL_LEAVER) == (
        QUALIFICATION_FOUNDATION_YEAR
    )


def test_a_two_hop_plan_delivers_what_the_first_hop_produced():
    """THE CENTRAL CASE, and the one a naive implementation gets wrong.

    The plan is: a year at an Azerbaijani university, then direct entry to the UK. Reading
    `profile.qualification_held` would answer 'attestat' -- the qualification the student
    holds TODAY and the one the UK has already refused -- and would then list the UK
    foundation-year universities while hiding Manchester and Cambridge, which are the two
    that actually accept this plan's output. The whole point of the two-hop plan is that
    the student is no longer the person who walked in.
    """
    assert qualification_delivered(
        plan_of(AZ_PREP_YEAR, UK_BACHELOR_DIRECT), SCHOOL_LEAVER
    ) == QUALIFICATION_ONE_YEAR_UNIVERSITY


def test_two_plans_to_the_same_country_deliver_different_qualifications():
    """Guards the fold against becoming hypothetical, and pins the discrimination it exists
    for.

    A school-leaver reaches UK direct entry by TWO different two-hop plans, because two
    routes unlock it: a UK foundation year (producing `foundation_year`) and a year at an
    Azerbaijani university (producing `one_year_university`). Both plans end at the same
    hop in the same country, so anything keyed on the destination alone cannot tell them
    apart -- and they reach different universities, because a university's row names one
    qualification, not a country. Cambridge accepts the completed year; it does not appear
    for the foundation plan. This is the case that makes the fold necessary rather than
    decorative.
    """
    plans = compose_two_hop(SCHOOL_LEAVER)
    delivered = {
        p.hops[0].key: qualification_delivered(p, SCHOOL_LEAVER)
        for p in plans
        if len(p.hops) == 2 and p.hops[-1].key == "uk-bachelor-direct"
    }
    assert delivered["az-prep-year"] == QUALIFICATION_ONE_YEAR_UNIVERSITY
    assert delivered["uk-bachelor-foundation"] == QUALIFICATION_FOUNDATION_YEAR


# -------------------------------------------------------------
# The query
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_only_universities_accepting_that_qualification_are_listed(session):
    session.add_all([
        make_row(university_name="Accepts Transfers",
                 entry_qualification_accepted=QUALIFICATION_ONE_YEAR_UNIVERSITY),
        make_row(university_name="Foundation Only",
                 entry_qualification_accepted=QUALIFICATION_FOUNDATION_YEAR),
    ])
    await session.commit()

    matches = await universities_accepting(
        session, country_code="GB", level="bachelor",
        qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    )
    assert [m.requirement.university_name for m in matches] == ["Accepts Transfers"]


@pytest.mark.asyncio
async def test_a_university_in_another_country_is_not_listed(session):
    session.add(make_row(university_name="Elsewhere", country_code="PL"))
    await session.commit()

    matches = await universities_accepting(
        session, country_code="GB", level="bachelor",
        qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    )
    assert matches == []


@pytest.mark.asyncio
async def test_only_the_most_recent_intake_year_is_returned(session):
    """A stale fee shown beside a current one, separated only by a small integer, is how a
    student acts on last year's number."""
    session.add_all([
        make_row(intake_year=2025, tuition_per_year=18000.0),
        make_row(intake_year=2026, tuition_per_year=21000.0),
    ])
    await session.commit()

    matches = await universities_accepting(
        session, country_code="GB", level="bachelor",
        qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    )
    assert len(matches) == 1
    assert matches[0].requirement.intake_year == 2026
    assert matches[0].requirement.tuition_per_year == 21000.0


# -------------------------------------------------------------
# Unknowns must stay visible
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_a_null_requirement_is_named_rather_than_left_blank(session):
    """ADR-0004 at the point of rendering. A blank tuition in a list of universities reads
    as free and a blank language test reads as none required; both are wrong in the
    direction that costs a student an application."""
    session.add(make_row(language_test=None, tuition_per_year=None))
    await session.commit()

    matches = await universities_accepting(
        session, country_code="GB", level="bachelor",
        qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    )
    assert "language_test" in matches[0].unknown_fields
    assert "tuition_per_year" in matches[0].unknown_fields

    note = missing_requirement_note(matches[0].unknown_fields)
    assert "language test" in note
    assert "never that it is not required" in note


@pytest.mark.asyncio
async def test_a_stated_zero_is_a_known_value_not_an_unknown(session):
    """Free tuition is a real answer at several German universities, and 0.0 is falsy.
    `_unknown_fields` must test `is None`, never truthiness, or every free programme
    would be reported as 'tuition not stated'."""
    session.add(make_row(tuition_per_year=0.0, entrance_exam_minimum=0.0))
    await session.commit()

    matches = await universities_accepting(
        session, country_code="GB", level="bachelor",
        qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    )
    assert "tuition_per_year" not in matches[0].unknown_fields
    assert "entrance_exam_minimum" not in matches[0].unknown_fields


def test_a_row_with_everything_stated_gets_no_note():
    assert missing_requirement_note(()) is None


# -------------------------------------------------------------
# An empty list must say WHY it is empty
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_a_country_we_never_collected_is_reported_as_our_gap(session):
    assert not await any_requirements_curated(session, country_code="PL", level="bachelor")

    status, text = describe_universities(
        [], country_code="PL", qualification=QUALIFICATION_ATTESTAT, any_curated=False
    )
    assert status == UNIS_STATUS_NONE_CURATED_FOR_COUNTRY
    assert "gap in our data" in text
    assert "route itself is still open" in text


@pytest.mark.asyncio
async def test_a_collected_country_with_no_match_is_reported_as_a_finding(session):
    """Germany is the live example: three German universities collected, all documenting
    the Studienkolleg path, none documenting direct entry on a completed year. Telling a
    student that as 'we have no data' would hide a real finding; telling them 'no German
    university accepts you' would overstate three universities as a country."""
    session.add(make_row(country_code="DE",
                         entry_qualification_accepted=QUALIFICATION_FESTSTELLUNGSPRUEFUNG))
    await session.commit()

    assert await any_requirements_curated(session, country_code="DE", level="bachelor")
    matches = await universities_accepting(
        session, country_code="DE", level="bachelor",
        qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    )
    assert matches == []

    status, text = describe_universities(
        matches, country_code="DE",
        qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY, any_curated=True,
    )
    assert status == UNIS_STATUS_NONE_ACCEPT_QUALIFICATION
    assert "real finding rather than a gap" in text
    assert "others may accept it" in text


def test_a_non_empty_result_needs_no_explanation():
    status, text = describe_universities(
        [UniversityMatch(
            requirement=make_row(),
            unknown_fields=(),
            # This test is about the empty-list explanation, not about grades. The grade
            # check is filled with the shape a university publishing no minimum actually
            # produces, so the fixture cannot assert a state the service never emits.
            grade=check_grade(None, None, None, None),
        )],
        country_code="GB", qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
        any_curated=True,
    )
    assert status == UNIS_STATUS_LISTED
    assert text == ""


# -------------------------------------------------------------
# The real curated file, joined for real
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_the_prep_year_plan_reaches_the_uk_universities_that_document_it(session):
    """End to end on the real data: load the curated rows, compose the real plan, and
    confirm the universities surfaced are the ones whose own pages name this route."""
    from scripts.load_program_requirements import DEFAULT_FILE, load_program_requirements

    await load_program_requirements(session, DEFAULT_FILE)

    plans = compose_two_hop(SCHOOL_LEAVER)
    uk_two_hop = next(
        p for p in plans
        if len(p.hops) == 2
        and p.hops[0].key == "az-prep-year"
        and p.hops[-1].key == "uk-bachelor-direct"
    )
    matches = await universities_accepting(
        session,
        country_code="GB",
        level="bachelor",
        qualification=qualification_delivered(uk_two_hop, SCHOOL_LEAVER),
    )
    names = {m.requirement.university_name for m in matches}
    assert "University of Manchester" in names
    assert "University of Cambridge" in names
    # The foundation-year universities must NOT appear here: this plan does not deliver a
    # foundation year, and listing them would send the student down a route they have
    # already bypassed by spending a year at an Azerbaijani university.
    assert "UCL" not in names


@pytest.mark.asyncio
async def test_an_attestat_average_is_checked_against_ucls_real_stated_minimum(session):
    """The grade path, end to end on the curated file rather than on a fixture.

    UCL is the one row in the real data whose scale matches an Azerbaijani attestat, so
    this is the comparison that must come back EXACT. Everything else is proportional, and
    a change that quietly turned this one proportional too would be invisible without it.
    """
    from scripts.load_program_requirements import DEFAULT_FILE, load_program_requirements

    await load_program_requirements(session, DEFAULT_FILE)

    foundation = await universities_accepting(
        session, country_code="GB", level="bachelor",
        qualification=QUALIFICATION_FOUNDATION_YEAR,
        student_gpa=4.8, student_gpa_scale="5",
    )
    ucl = next(m for m in foundation if m.requirement.university_name == "UCL")
    assert ucl.grade.verdict == "meets"
    assert ucl.grade.exact is True

    below = await universities_accepting(
        session, country_code="GB", level="bachelor",
        qualification=QUALIFICATION_FOUNDATION_YEAR,
        student_gpa=4.0, student_gpa_scale="5",
    )
    assert next(
        m for m in below if m.requirement.university_name == "UCL"
    ).grade.verdict == "below"


@pytest.mark.asyncio
async def test_a_student_who_gives_no_grade_gets_no_grade_verdict_not_a_pass(session):
    """A profile with no GPA must not have every university silently report 'meets'."""
    session.add(make_row(gpa_minimum=4.5, gpa_scale="5.0"))
    await session.commit()

    matches = await universities_accepting(
        session, country_code="GB", level="bachelor",
        qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    )
    assert matches[0].grade.verdict == "no_grade_given"
