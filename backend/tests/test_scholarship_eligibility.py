"""The funding layer: nine instruments, each with the gate that actually decides it.

Pure logic, no database. The subject of most of these tests is a single question -- does an
unmet or uncheckable gate ever read as permission? -- because that is the failure this
layer exists to prevent. A scholarship reported OPEN when its age limit was never checked
sends a student to spend January on an application they cannot win.
"""

from app.domain.routes import RouteStatus, StudentRouteProfile
from app.domain.scholarship_definitions import (
    ALL_SCHOLARSHIPS,
    CHEVENING,
    CHEVENING_MINIMUM_WORK_HOURS,
    ERASMUS_MUNDUS,
    NAWA_BANACH,
    PREZIDENT_TEQAUDU,
    SOCAR_XARICI_TEQAUD,
    TURKIYE_BURSLARI,
    TURKIYE_BURSLARI_BACHELOR_MAX_AGE,
)
from app.domain.scholarships import LevelGate
from app.models.qualifications import (
    QUALIFICATION_ATTESTAT,
    QUALIFICATION_BACHELOR_DEGREE,
)
from app.services.scholarship_eligibility import (
    assess_scholarship,
    assess_scholarships,
    prep_year_scholarship_warning,
)

EVERYWHERE = ("TR", "DE", "GB", "US", "PL", "CN", "AZ")


def school_leaver(**kwargs) -> StudentRouteProfile:
    return StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT, **kwargs
    )


def graduate(**kwargs) -> StudentRouteProfile:
    return StudentRouteProfile(
        level_sought="master", qualification_held=QUALIFICATION_BACHELOR_DEGREE, **kwargs
    )


# --- The rule the whole layer turns on -----------------------------------------------------


def test_an_unchecked_age_gate_never_makes_an_award_open():
    """The failure this layer exists to prevent.

    A 22-year-old is ineligible for Türkiye Bursları at bachelor level. If the student does
    not tell us their age, the honest answer is "we could not check this", and that answer
    must not be OPEN -- because OPEN is read as "you meet the published requirements".
    """
    assessed = assess_scholarship(TURKIYE_BURSLARI, school_leaver(), EVERYWHERE)

    assert assessed.status == RouteStatus.UNLOCKABLE.value
    assert assessed.gates_unknown, "the unchecked age gate must be reported, not dropped"
    assert any("age" in text.lower() for text in assessed.gates_unknown)
    # And it must not have been quietly filed as something the student cleared.
    assert not any("age" in text.lower() for text in assessed.gates_met)


def test_unknown_gates_are_reported_apart_from_missing_ones():
    """They ask different things of the student and must not be merged.

    A missing gate is work to do -- sit the test, accrue the hours. An unknown gate is a
    fact to tell us or a source we have to read. A client that concatenates the two tells a
    student to go and do something about a question we simply never asked them.
    """
    assessed = assess_scholarship(
        CHEVENING, graduate(work_experience_hours=1000), EVERYWHERE
    )

    assert assessed.gates_missing, "1,000 hours is short of the bar and that is actionable"
    assert any("post-degree" in text for text in assessed.gates_unknown)
    assert all("short of" not in text for text in assessed.gates_unknown)


# --- Level: the gate that decides six of the nine ------------------------------------------


def test_seven_of_the_ten_instruments_are_masters_only():
    """Not a gap in the catalogue -- the finding (spec §2.3).

    At bachelor level scholarships barely exist, and the lever is affordability instead. A
    product that padded the bachelor list to look generous would be lying about the single
    fact that most changes a school-leaver's plan. Only two instruments here reach bachelor
    at all, which is why the honest answer to a school-leaver is short.
    """
    masters_only = [
        s
        for s in ALL_SCHOLARSHIPS
        for gate in s.gates
        if isinstance(gate, LevelGate) and gate.levels == ("master",)
    ]
    reaches_bachelor = [
        s
        for s in ALL_SCHOLARSHIPS
        for gate in s.gates
        if isinstance(gate, LevelGate) and "bachelor" in gate.levels
    ]

    assert len(ALL_SCHOLARSHIPS) == 10
    assert len(masters_only) == 7
    assert {s.key for s in reaches_bachelor} == {"turkiye-burslari", "csc-china"}


def test_a_school_leaver_is_told_a_masters_only_award_is_closed_not_competitive():
    assessed = assess_scholarship(CHEVENING, school_leaver(), EVERYWHERE)

    assert assessed.status == RouteStatus.BLOCKED.value
    assert any("master's study only" in text for text in assessed.gates_blocked)
    # The distinction the wording has to carry: closed, not a long shot.
    assert any("not competitive, closed" in text for text in assessed.gates_blocked)


# --- Gates that are not about merit --------------------------------------------------------


def test_an_employment_gate_blocks_a_perfect_academic_record():
    """SOCAR's award is closed to everyone outside the group. No grade opens it."""
    outsider = graduate(
        employer="Ministry of Education",
        gpa=4.9,
        gpa_scale="5.0",
        language_certificate_level="C2",
        age=25,
    )

    assessed = assess_scholarship(SOCAR_XARICI_TEQAUD, outsider, EVERYWHERE)

    assert assessed.status == RouteStatus.BLOCKED.value
    assert any("employment, not merit" in text for text in assessed.gates_blocked)


def test_the_employment_gate_is_unknown_rather_than_failed_when_no_employer_is_given():
    assessed = assess_scholarship(SOCAR_XARICI_TEQAUD, graduate(age=25), EVERYWHERE)

    assert assessed.status == RouteStatus.UNLOCKABLE.value
    assert any("SOCAR" in text for text in assessed.gates_unknown)
    assert not assessed.gates_blocked


def test_a_socar_employee_clears_the_employment_gate():
    insider = graduate(
        employer="SOCAR Downstream Management", age=30, language_certificate_level="C1"
    )

    assessed = assess_scholarship(SOCAR_XARICI_TEQAUD, insider, EVERYWHERE)

    assert assessed.status == RouteStatus.UNLOCKABLE.value
    assert any("SOCAR" in text for text in assessed.gates_met)
    assert any("current official" in text for text in assessed.gates_unknown)


def test_an_age_limit_blocks_and_says_it_cannot_be_worked_towards():
    over = school_leaver(age=TURKIYE_BURSLARI_BACHELOR_MAX_AGE + 1)

    assessed = assess_scholarship(TURKIYE_BURSLARI, over, EVERYWHERE)

    assert assessed.status == RouteStatus.BLOCKED.value
    assert any("not something you can work towards" in t for t in assessed.gates_blocked)


def test_hours_short_of_chevening_is_missing_not_blocked_because_hours_accrue():
    """A 23-year-old short of the bar is being told WHEN to apply, not that they cannot."""
    short = graduate(work_experience_hours=CHEVENING_MINIMUM_WORK_HOURS - 800)

    assessed = assess_scholarship(CHEVENING, short, EVERYWHERE)

    assert assessed.status == RouteStatus.UNLOCKABLE.value
    assert not assessed.gates_blocked
    assert any("800 short" in text for text in assessed.gates_missing)


def test_chevening_states_its_bar_in_hours_and_its_return_obligation():
    """Two years is the marketing phrasing; 2,800 documented hours is the requirement."""
    assessed = assess_scholarship(
        CHEVENING, graduate(work_experience_hours=CHEVENING_MINIMUM_WORK_HOURS), EVERYWHERE
    )

    assert assessed.status == RouteStatus.UNLOCKABLE.value
    assert any("post-degree" in text for text in assessed.gates_unknown)
    assert "2,800" in assessed.scholarship.gates[1].description
    assert assessed.scholarship.obligation is not None
    assert "two years" in assessed.scholarship.obligation


# --- Sources that contradict each other ----------------------------------------------------


def test_the_banach_primary_call_replaces_the_conflicting_field_lists():
    """The 2026 primary call resolves the field conflict; other criteria remain unmodelled."""
    assessed = assess_scholarship(NAWA_BANACH, graduate(), ("PL",))

    assert assessed.status == RouteStatus.UNLOCKABLE.value
    conflict = " ".join(assessed.gates_unknown)
    assert "participating universities" in conflict
    assert "neither earlier exclusive field list applies" in conflict
    assert "2026---Call-for-applications-EN.pdf" in NAWA_BANACH.citation


def test_an_award_with_an_unresolved_gate_can_never_be_open():
    for scholarship in ALL_SCHOLARSHIPS:
        assessed = assess_scholarship(scholarship, graduate(age=25), EVERYWHERE)
        if assessed.gates_unknown:
            assert assessed.status != RouteStatus.OPEN.value, scholarship.key


# --- Awards that are not study-abroad awards -----------------------------------------------


def test_the_presidential_scholarship_is_listed_precisely_so_it_can_be_refused():
    """Students ask about it. An empty list is not an answer to a question they asked."""
    assessed = assess_scholarship(PREZIDENT_TEQAUDU, graduate(), EVERYWHERE)

    assert assessed.status == RouteStatus.BLOCKED.value
    assert any("study inside Azerbaijan only" in t for t in assessed.gates_blocked)
    assert any("about what the award is, not about you" in t for t in assessed.gates_blocked)


# --- Reachability: an award is worth nothing in a country you cannot enter ------------------


def test_an_unreachable_country_blocks_the_award_but_blames_the_route_not_the_student():
    """A student who cannot enter the UK has not failed Chevening's criteria."""
    qualified = graduate(work_experience_hours=CHEVENING_MINIMUM_WORK_HOURS)

    assessed = assess_scholarship(CHEVENING, qualified, ("TR", "PL"))

    assert assessed.status == RouteStatus.BLOCKED.value
    blocked = " ".join(assessed.gates_blocked)
    assert "not about your eligibility for Chevening" in blocked
    assert "statement about your entry routes" in blocked


def test_a_multi_country_award_is_not_destination_checked():
    """An Erasmus Mundus consortium spans several countries; there is no single one to check."""
    assessed = assess_scholarship(ERASMUS_MUNDUS, graduate(), ())

    assert ERASMUS_MUNDUS.country_code is None
    assert not assessed.gates_blocked


# --- Ordering and completeness -------------------------------------------------------------


def test_blocked_awards_are_returned_rather_than_hidden():
    """A 22-year-old needs to be told Türkiye Bursları is closed, or they will still apply."""
    assessed = assess_scholarships(school_leaver(age=22), EVERYWHERE)

    assert len(assessed) == len(ALL_SCHOLARSHIPS)
    turkish = next(a for a in assessed if a.scholarship.key == TURKIYE_BURSLARI.key)
    assert turkish.status == RouteStatus.BLOCKED.value


def test_the_most_available_awards_come_first():
    assessed = assess_scholarships(
        graduate(age=25, work_experience_hours=CHEVENING_MINIMUM_WORK_HOURS), EVERYWHERE
    )
    order = {"open": 0, "unlockable": 1, "blocked": 2}
    ranks = [order[a.status] for a in assessed]

    assert ranks == sorted(ranks)


def test_every_instrument_carries_a_citation_and_stays_unverified():
    """`research-brief` is a rung below `claude-extracted`. Loading a row never verifies it."""
    for scholarship in ALL_SCHOLARSHIPS:
        assert scholarship.citation, scholarship.key
        assert scholarship.provenance in {"research-brief", "claude-extracted"}, scholarship.key


def test_the_dp_is_not_in_this_catalogue_because_it_has_its_own_assessor():
    """One award, one assessor. Two would diverge on the first correction."""
    keys = {s.key for s in ALL_SCHOLARSHIPS}

    assert not any("dovlet" in key or "dp" == key for key in keys)


# --- The trade-off between two things the engine already models ----------------------------


def test_the_prep_year_can_cost_a_student_turkiye_burslari_and_says_so():
    """Spec §11's open question, answerable now that the profile carries an age.

    The prep year is the product's central finding -- it is what opens Germany and the UK to
    a school-leaver. It also costs twelve months, and Türkiye Bursları' bachelor award is
    under-21 only. No agency surfaces this, because both halves have to be modelled at once.
    """
    warning = prep_year_scholarship_warning(
        school_leaver(age=20), frozenset({"az-prep-year", "de-bachelor-direct"})
    )

    assert warning is not None
    assert "21" in warning
    assert "opens Germany and the UK" in warning


def test_a_student_already_over_the_limit_is_not_told_the_prep_year_costs_them_it():
    """It is already closed to them. Its own gate says so, and says why.

    Claiming the prep year would close it as well would be false, and would make the year
    look more expensive than it is for exactly the student it cannot cost anything.
    """
    over = school_leaver(age=TURKIYE_BURSLARI_BACHELOR_MAX_AGE + 1)

    assert prep_year_scholarship_warning(over, frozenset({"az-prep-year"})) is None
    # And the award still tells them plainly why it is shut.
    assessed = assess_scholarship(TURKIYE_BURSLARI, over, EVERYWHERE)
    assert assessed.status == RouteStatus.BLOCKED.value


def test_a_younger_student_faces_no_such_trade_off():
    assert (
        prep_year_scholarship_warning(
            school_leaver(age=17), frozenset({"az-prep-year", "de-bachelor-direct"})
        )
        is None
    )


def test_the_trade_off_is_not_raised_when_no_plan_uses_the_prep_year():
    assert (
        prep_year_scholarship_warning(school_leaver(age=20), frozenset({"tr-bachelor-direct"}))
        is None
    )


def test_without_an_age_the_trade_off_is_named_as_a_question_rather_than_dropped():
    warning = prep_year_scholarship_warning(
        school_leaver(), frozenset({"az-prep-year", "uk-bachelor-direct"})
    )

    assert warning is not None
    assert "Tell us your age" in warning


def test_a_masters_applicant_is_not_shown_a_bachelor_age_limit():
    assert (
        prep_year_scholarship_warning(graduate(age=20), frozenset({"az-prep-year"})) is None
    )
