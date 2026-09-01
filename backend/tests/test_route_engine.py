"""The route engine. The case that matters most is the attestat-only school-leaver:
Germany and the UK must come back BLOCKED, with both unlocks named."""

import pytest

from app.domain.route_definitions import ALL_ROUTES
from app.domain.routes import RouteStatus, StudentRouteProfile
from app.models.qualifications import (
    QUALIFICATION_ATTESTAT,
    QUALIFICATION_BACHELOR_DEGREE,
    QUALIFICATION_ONE_YEAR_UNIVERSITY,
)
from app.services.route_engine import assess_routes, classify_route, compose_two_hop

SCHOOL_LEAVER = StudentRouteProfile(
    level_sought="bachelor",
    qualification_held=QUALIFICATION_ATTESTAT,
    dim_score=520.0,
    ielts=7.0,
)


def _by_key(assessments):
    return {a.route.key: a for a in assessments}


def test_every_route_carries_a_citation_and_seed_provenance():
    """A route without a source is not a route. Loading one does not verify it."""
    for route in ALL_ROUTES:
        assert route.citation, f"{route.key} has no citation"
        assert route.provenance in ("seed", "human-verified")


def test_germany_and_the_uk_are_blocked_to_a_school_leaver():
    """The finding the whole design rests on: an attestat opens the Studienkolleg, not
    a German degree, and the UK does not accept it for direct undergraduate entry."""
    assessed = _by_key(assess_routes(SCHOOL_LEAVER))
    assert assessed["de-bachelor-direct"].status is RouteStatus.BLOCKED
    assert assessed["uk-bachelor-direct"].status is RouteStatus.BLOCKED


def test_turkey_and_poland_are_open_to_the_same_student():
    assessed = _by_key(assess_routes(SCHOOL_LEAVER))
    assert assessed["tr-bachelor-direct"].status is RouteStatus.OPEN
    assert assessed["pl-bachelor-direct"].status is RouteStatus.OPEN


def test_the_unlocks_are_offered_not_merely_the_blockage():
    """Studienkolleg and the prep year both accept an attestat, so both are actionable."""
    assessed = _by_key(assess_routes(SCHOOL_LEAVER))
    assert assessed["de-bachelor-studienkolleg"].status is not RouteStatus.BLOCKED
    assert assessed["az-prep-year"].status is not RouteStatus.BLOCKED


def test_a_missing_exam_is_unlockable_not_blocked():
    """A score you have not got yet is a gap you can close. A qualification you do not
    hold is not -- that distinction is the entire point of the two statuses."""
    no_english = StudentRouteProfile(
        level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
        ielts=None,
    )
    assessed = _by_key(assess_routes(no_english))
    poland = assessed["pl-bachelor-direct"]
    assert poland.status is RouteStatus.UNLOCKABLE
    assert any("IELTS" in m for m in poland.missing)


def test_a_score_below_the_bar_names_the_bar():
    low_english = StudentRouteProfile(
        level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
        ielts=5.0,
    )
    poland = _by_key(assess_routes(low_english))["pl-bachelor-direct"]
    assert poland.status is RouteStatus.UNLOCKABLE
    assert any("6.0" in m for m in poland.missing)


def test_the_prep_year_opens_germany_directly():
    """After a year at an Azerbaijani university the same person is no longer blocked."""
    after_prep = StudentRouteProfile(
        level_sought="bachelor",
        qualification_held=QUALIFICATION_ONE_YEAR_UNIVERSITY,
        ielts=7.0,
    )
    assessed = _by_key(assess_routes(after_prep))
    assert assessed["de-bachelor-direct"].status is RouteStatus.OPEN
    assert assessed["uk-bachelor-direct"].status is RouteStatus.OPEN


def test_a_bachelor_holder_sees_only_master_routes():
    """Level is a key, not a filter: the bachelor routes are not applicable at all."""
    graduate = StudentRouteProfile(
        level_sought="master",
        qualification_held=QUALIFICATION_BACHELOR_DEGREE,
        ielts=7.0,
    )
    assessed = assess_routes(graduate)
    assert {a.route.level for a in assessed} == {"master"}
    assert _by_key(assessed)["de-master-direct"].status is RouteStatus.OPEN


def test_germany_inverts_between_the_two_levels():
    """Blocked to a school-leaver, open to a bachelor holder. A level-agnostic engine
    would give a confident wrong answer to one of these two students."""
    school_leaver = _by_key(assess_routes(SCHOOL_LEAVER))["de-bachelor-direct"]
    graduate = _by_key(assess_routes(StudentRouteProfile(
        level_sought="master",
        qualification_held=QUALIFICATION_BACHELOR_DEGREE,
        ielts=7.0,
    )))["de-master-direct"]
    assert school_leaver.status is RouteStatus.BLOCKED
    assert graduate.status is RouteStatus.OPEN


def test_classify_route_names_what_is_missing_and_why():
    from app.domain.route_definitions import DE_BACHELOR_DIRECT

    assessment = classify_route(DE_BACHELOR_DIRECT, SCHOOL_LEAVER)
    assert assessment.status is RouteStatus.BLOCKED
    assert assessment.missing
    assert any(QUALIFICATION_ATTESTAT in m or "qualification" in m.lower()
               for m in assessment.missing)


def test_composition_produces_the_prep_year_path_to_germany():
    """The sentence the product exists to say: Germany is blocked, and one year at an
    Azerbaijani university opens it."""
    plans = compose_two_hop(SCHOOL_LEAVER)
    german = [p for p in plans if p.hops[-1].country_code == "DE"]
    assert german, "no two-hop plan reaches Germany"

    via_prep = [p for p in german if p.hops[0].key == "az-prep-year"]
    assert via_prep, "the prep-year unlock was not found"
    assert via_prep[0].hops[-1].key == "de-bachelor-direct"
    assert via_prep[0].total_months == 12


def test_both_german_unlocks_are_offered():
    """Studienkolleg and the prep year are different trades -- 12 months either way, but
    one costs 6,000-14,000 AZN and the other keeps Turkey and Poland open."""
    plans = compose_two_hop(SCHOOL_LEAVER)
    first_hops = {p.hops[0].key for p in plans if p.hops[-1].country_code == "DE"}
    assert {"az-prep-year", "de-bachelor-studienkolleg"} <= first_hops


def test_the_prep_year_also_opens_the_uk():
    """One unlock, two countries. This is why it is the mechanic the design is built on."""
    plans = compose_two_hop(SCHOOL_LEAVER)
    uk_via_prep = [
        p for p in plans
        if p.hops[-1].country_code == "GB" and p.hops[0].key == "az-prep-year"
    ]
    assert uk_via_prep


def test_composition_costs_are_the_sum_of_both_hops():
    plans = compose_two_hop(SCHOOL_LEAVER)
    plan = next(p for p in plans if p.hops[0].key == "az-prep-year"
                and p.hops[-1].key == "de-bachelor-direct")
    assert plan.total_months == plan.hops[0].time_cost_months + plan.hops[1].time_cost_months
    assert plan.total_cost_azn[0] == plan.hops[0].money_cost_azn[0] + plan.hops[1].money_cost_azn[0]


def test_no_plan_is_longer_than_two_hops():
    """Deeper chains exist but do not help a 17-year-old, and uncapped graph search turns
    a product into a research project."""
    assert all(len(p.hops) <= 2 for p in compose_two_hop(SCHOOL_LEAVER))


def test_a_student_who_is_already_open_gets_no_detour():
    """Composition answers a blockage. It must not propose a prep year to someone who can
    already go directly."""
    after_prep = StudentRouteProfile(
        level_sought="bachelor",
        qualification_held=QUALIFICATION_ONE_YEAR_UNIVERSITY,
        ielts=7.0,
    )
    plans = compose_two_hop(after_prep)
    assert all(p.hops[-1].country_code != "DE" for p in plans if len(p.hops) == 2)
