"""The route engine. The case that matters most is the attestat-only school-leaver:
Germany and the UK must come back BLOCKED, with both unlocks named."""

import pytest

from app.domain.route_definitions import ALL_ROUTES
from app.domain.routes import Route, RouteStatus, StudentRouteProfile
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

# Same as SCHOOL_LEAVER, plus a TestAS score -- the one field that turns the Studienkolleg
# hop fully OPEN instead of UNLOCKABLE, needed to exercise the all-hops-OPEN branch of a
# composed plan's status.
SCHOOL_LEAVER_WITH_TESTAS = StudentRouteProfile(
    level_sought="bachelor",
    qualification_held=QUALIFICATION_ATTESTAT,
    dim_score=520.0,
    ielts=7.0,
    test_as=1.0,
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
    """Composition answers a blockage. It must not propose a detour to a destination the
    student can already reach directly.

    ALL_ROUTES cannot exercise this guard: every producer route (az-prep-year,
    de-bachelor-studienkolleg, uk-bachelor-foundation) requires QUALIFICATION_ATTESTAT
    alone, and no consumer route accepts both an unlock-eligible original qualification and
    any of the three produced qualifications. So whenever a first hop is reachable, every
    already-open destination becomes BLOCKED again after the first hop's qualification is
    applied, and the (harmless, redundant) second-hop BLOCKED-skip guard hides whether the
    "already open" guard fired at all -- this is exactly how the original version of this
    test, built on real routes, passed 16/16 with the guard deleted outright.

    A synthetic route pair isolates it: an already-open destination that accepts BOTH the
    original qualification and the one the first hop produces, so it would still classify
    as reachable after the swap if the guard were gone.
    """
    unlock = Route(
        key="test-unlocker", country_code="ZZ", level="bachelor",
        mechanism="test fixture", requires_qualification=(QUALIFICATION_ATTESTAT,),
        produces_qualification="test-qualification-x", exams=(),
        time_cost_months=6, money_cost_azn=(100, 200), citation="test fixture",
    )
    already_open = Route(
        key="test-already-open", country_code="YY", level="bachelor",
        mechanism="test fixture",
        # Accepts the qualification the student already holds AND the one `unlock`
        # produces -- the one shape of route that can tell the "already open" guard apart
        # from the ordinary second-hop BLOCKED-skip guard.
        requires_qualification=(QUALIFICATION_ATTESTAT, "test-qualification-x"),
        produces_qualification=None, exams=(),
        time_cost_months=0, money_cost_azn=(0, 0), citation="test fixture",
    )
    profile = StudentRouteProfile(level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT)

    plans = compose_two_hop(profile, routes=(unlock, already_open))

    assert any(len(p.hops) == 1 and p.hops[0].key == "test-already-open" for p in plans), (
        "fixture bug: the destination is supposed to be reachable directly"
    )
    assert not any(p.hops[-1].key == "test-already-open" for p in plans if len(p.hops) == 2), (
        "a two-hop detour was proposed to a destination the student can already reach directly"
    )


def test_second_hop_never_composes_a_route_still_blocked_after_the_first():
    """Deleting the second-hop BLOCKED-skip produces a plan reporting OPEN while its own
    `missing` field still names an unmet qualification -- a plan that contradicts itself on
    its face, and precisely the ADR-0004 defect this branch exists to remove.

    de-bachelor-studienkolleg (fully OPEN, given a TestAS score) does not unlock
    uk-bachelor-direct: it produces QUALIFICATION_FESTSTELLUNGSPRUEFUNG, which
    uk-bachelor-direct does not accept, so that route stays BLOCKED after the swap.
    """
    plans = compose_two_hop(SCHOOL_LEAVER_WITH_TESTAS)
    assert not any(
        p.hops[0].key == "de-bachelor-studienkolleg" and p.hops[-1].key == "uk-bachelor-direct"
        for p in plans
    )


def test_no_composed_plan_reports_open_while_missing_a_requirement():
    """The general invariant the two guards above exist to hold: OPEN must mean OPEN. A
    plan can never claim full eligibility while its own `missing` field still names an
    unmet requirement, across every profile the engine is asked about."""
    profiles = [
        SCHOOL_LEAVER,
        SCHOOL_LEAVER_WITH_TESTAS,
        StudentRouteProfile(
            level_sought="bachelor",
            qualification_held=QUALIFICATION_ONE_YEAR_UNIVERSITY,
            ielts=7.0,
        ),
        StudentRouteProfile(
            level_sought="master",
            qualification_held=QUALIFICATION_BACHELOR_DEGREE,
            ielts=7.0,
        ),
    ]
    for profile in profiles:
        for plan in compose_two_hop(profile):
            if plan.status is RouteStatus.OPEN:
                assert plan.missing == (), (
                    f"{[h.key for h in plan.hops]} reports OPEN but missing={plan.missing}"
                )


def test_plan_status_reflects_the_weakest_hop():
    """OPEN only when every hop is OPEN; any UNLOCKABLE hop pulls the whole plan down.
    This is the branch _plan_from_hops's status computation depends on, and the default
    arm (UNLOCKABLE, not OPEN) that a route with no UNLOCKABLE hop should never reach by
    accident."""
    plans = compose_two_hop(SCHOOL_LEAVER)

    fully_open = next(
        p for p in plans
        if p.hops[0].key == "az-prep-year" and p.hops[-1].key == "de-bachelor-direct"
    )
    assert fully_open.status is RouteStatus.OPEN

    partially_unlockable = next(
        p for p in plans
        if p.hops[0].key == "de-bachelor-studienkolleg" and p.hops[-1].key == "de-bachelor-direct"
    )
    assert partially_unlockable.status is RouteStatus.UNLOCKABLE


def test_compose_two_hop_returns_nothing_for_an_attestat_at_master_level():
    """Level is part of the key, not a filter: an attestat cannot compose its way into a
    master's route, because none of the bachelor-level unlock routes are even considered
    once the level is master."""
    profile = StudentRouteProfile(
        level_sought="master",
        qualification_held=QUALIFICATION_ATTESTAT,
        ielts=7.0,
    )
    assert compose_two_hop(profile) == []


def test_a_mutually_blocked_cycle_produces_no_plan():
    """If route A requires what only route B produces and route B requires what only
    route A produces, and the student starts holding neither, composition must not
    manufacture a plan by treating a BLOCKED route as a usable first hop. There is no
    bootstrap into a closed two-node cycle, and the engine must say so by returning
    nothing -- not by hallucinating a hop out of a route it never should have started
    from."""
    route_a = Route(
        key="test-cycle-a", country_code="ZZ", level="bachelor", mechanism="test fixture",
        requires_qualification=("test-qualification-b",), produces_qualification="test-qualification-a",
        exams=(), time_cost_months=1, money_cost_azn=(0, 0), citation="test fixture",
    )
    route_b = Route(
        key="test-cycle-b", country_code="ZZ", level="bachelor", mechanism="test fixture",
        requires_qualification=("test-qualification-a",), produces_qualification="test-qualification-b",
        exams=(), time_cost_months=1, money_cost_azn=(0, 0), citation="test fixture",
    )
    profile = StudentRouteProfile(level_sought="bachelor", qualification_held="test-qualification-unrelated")

    assert compose_two_hop(profile, routes=(route_a, route_b)) == []


def test_the_german_visa_deposit_is_carried_separately_from_the_route_cost():
    """Germany's routes cost almost nothing and require the most cash up front of any of
    the six countries. Both facts are true and they are not the same field.

    Until `proof_of_funds` existed, `money_cost_azn=(0, 1200)` was the whole financial
    picture the product showed for Germany -- so the destination with the largest liquidity
    barrier read as the cheapest thing on the page. This pins that the deposit is present,
    that it is NOT added into the route cost (the money stays the student's own), and that
    it reaches every German route including the Studienkolleg year and the master's.
    """
    german = {r.key: r for r in ALL_ROUTES if r.country_code == "DE"}
    assert set(german) == {
        "de-bachelor-studienkolleg", "de-bachelor-direct", "de-master-direct",
    }

    for key, route in german.items():
        assert route.proof_of_funds is not None, f"{key} lost its deposit requirement"
        assert route.proof_of_funds.currency == "EUR"
        assert route.proof_of_funds.amount == 11904

    # Never folded into the cost. The deposit is EUR and the cost is AZN, so the two cannot
    # be compared at all without a conversion this project deliberately does not store --
    # which is the reason they are separate fields. What IS checkable is that adding the
    # deposit did not inflate the cost band: Germany's direct route is still tuition-free,
    # and the honest answer to "what does Germany cost" remains "almost nothing in fees, and
    # EUR 11,904 you must have in the bank first".
    assert german["de-bachelor-direct"].money_cost_azn == (0, 1200)
    assert german["de-master-direct"].money_cost_azn == (0, 1200)

    # And it is not silently applied to countries we have not collected it for. An absent
    # figure means "not recorded", which the UI must not render as "none required".
    turkey = [r for r in ALL_ROUTES if r.country_code == "TR"]
    assert turkey and all(r.proof_of_funds is None for r in turkey)
