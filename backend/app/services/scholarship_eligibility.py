"""Check a profile against every funding instrument's published gates.

The one rule that shapes this whole module: **an unknown gate never contributes to OPEN.**
A gate we could not check -- because the student did not give us their age, or because our
two sources contradict each other -- is reported in `gates_unknown` and forces the award to
UNLOCKABLE. That is ADR-0004 applied to money: the failure mode this prevents is a student
reading "you meet the published requirements" for an award that has an age limit we never
checked.

Wording rule, inherited from spec §5.2 and from `dp_eligibility`: clearing the published
gates makes a student *possibly eligible to apply*. It is never an award. Every instrument
here is competitive and the selection that follows is a committee decision no dataset in
this project models.
"""

from typing import Optional

from app.domain.route_definitions import AZ_PREP_YEAR
from app.domain.routes import RouteStatus, StudentRouteProfile
from app.domain.scholarship_definitions import (
    ALL_SCHOLARSHIPS,
    TURKIYE_BURSLARI,
    TURKIYE_BURSLARI_BACHELOR_MAX_AGE,
)
from app.domain.scholarships import (
    AgeGate,
    EmploymentGate,
    GATE_BLOCKED,
    GATE_MET,
    GATE_MISSING,
    GATE_UNKNOWN,
    Gate,
    GateResult,
    LanguageGate,
    LevelGate,
    Scholarship,
    ScholarshipAssessment,
    UnresolvedGate,
    WorkExperienceGate,
)

# The Dövlət Proqramı is assessed by `dp_eligibility`, not here. Stated in code so a reader
# of this module does not go looking for the biggest funder in a list that omits it.
DP_ASSESSED_BY = "app.services.dp_eligibility.assess_dp_eligibility"

# Ordered weakest to strongest. A certificate at or above the required rung satisfies a
# LanguageGate; anything else, including an unrecognised string, does not.
CEFR_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")


def _cefr_at_least(held: Optional[str], required: str) -> bool:
    """Is `held` at or above `required` on the CEFR ladder?

    An unrecognised or absent level is False, never a pass. A student who typed something we
    do not understand has not shown us a certificate.
    """
    if held is None or held not in CEFR_LEVELS or required not in CEFR_LEVELS:
        return False
    return CEFR_LEVELS.index(held) >= CEFR_LEVELS.index(required)


def _check_level(gate: LevelGate, profile: StudentRouteProfile) -> GateResult:
    named = " or ".join(f"{level}'s" for level in gate.levels)
    if profile.level_sought in gate.levels:
        return GateResult(GATE_MET, f"This award funds {named} study, which is your level")
    return GateResult(
        GATE_BLOCKED,
        f"This award funds {named} study only. You are applying at {profile.level_sought} "
        "level, so it is closed to you this cycle -- not competitive, closed",
    )


def _check_age(gate: AgeGate, profile: StudentRouteProfile) -> GateResult:
    if profile.level_sought not in gate.applies_to_levels:
        return GateResult(GATE_UNKNOWN, gate.unverified_at_other_levels)
    if profile.age is None:
        return GateResult(
            GATE_UNKNOWN,
            f"This award requires you to be under {gate.maximum_age} at {profile.level_sought} "
            "level. Tell us your age and this becomes a definite answer either way",
        )
    if profile.age < gate.maximum_age:
        return GateResult(
            GATE_MET,
            f"You are {profile.age}, under the age limit of {gate.maximum_age}",
        )
    return GateResult(
        GATE_BLOCKED,
        f"You are {profile.age} and this award requires you to be under {gate.maximum_age} "
        f"at {profile.level_sought} level. An age limit is not something you can work "
        "towards -- this one is closed",
    )


def _check_employment(gate: EmploymentGate, profile: StudentRouteProfile) -> GateResult:
    if profile.employer is None:
        return GateResult(
            GATE_UNKNOWN,
            f"This award is open only to {gate.employer} group employees. Tell us your "
            "employer and we can say whether it applies to you",
        )
    if gate.employer.casefold() in profile.employer.casefold():
        return GateResult(
            GATE_MET,
            f"You have told us you work at {profile.employer}, which is what this award "
            f"requires. {gate.employer} verifies employment itself during the application",
        )
    return GateResult(
        GATE_BLOCKED,
        f"This award is open only to {gate.employer} group employees, and you have told us "
        f"you work at {profile.employer}. No academic record opens it -- the gate is "
        "employment, not merit",
    )


def _check_work_experience(
    gate: WorkExperienceGate, profile: StudentRouteProfile
) -> GateResult:
    if profile.work_experience_hours is None:
        return GateResult(
            GATE_UNKNOWN,
            f"This award requires {gate.description}. Tell us your documented hours and we "
            "can check it",
        )
    if profile.work_experience_hours >= gate.minimum_hours:
        return GateResult(
            GATE_MET,
            f"{profile.work_experience_hours:,} documented hours clears the "
            f"{gate.minimum_hours:,} required",
        )
    shortfall = gate.minimum_hours - profile.work_experience_hours
    return GateResult(
        # Missing, not blocked: hours accrue. This tells a student when to apply rather than
        # that they never can.
        GATE_MISSING,
        f"{profile.work_experience_hours:,} documented hours is {shortfall:,} short of the "
        f"{gate.minimum_hours:,} required. Hours accrue, so this is a question of when you "
        "apply rather than whether you can",
    )


def _check_language(gate: LanguageGate, profile: StudentRouteProfile) -> GateResult:
    bar = (
        f"{gate.minimum_certificate_level}, IELTS {gate.ielts:g}, or TOEFL {gate.toefl}"
    )
    if _cefr_at_least(profile.language_certificate_level, gate.minimum_certificate_level):
        return GateResult(
            GATE_MET, f"Your {profile.language_certificate_level} certificate clears {bar}"
        )
    if profile.ielts is not None and profile.ielts >= gate.ielts:
        return GateResult(GATE_MET, f"IELTS {profile.ielts:g} clears {bar}")
    if profile.toefl is not None and profile.toefl >= gate.toefl:
        return GateResult(GATE_MET, f"TOEFL {profile.toefl} clears {bar}")
    return GateResult(
        GATE_MISSING, f"A language qualification at {bar} is required and none of yours reaches it"
    )


def _check_gate(gate: Gate, profile: StudentRouteProfile) -> GateResult:
    if isinstance(gate, LevelGate):
        return _check_level(gate, profile)
    if isinstance(gate, AgeGate):
        return _check_age(gate, profile)
    if isinstance(gate, EmploymentGate):
        return _check_employment(gate, profile)
    if isinstance(gate, WorkExperienceGate):
        return _check_work_experience(gate, profile)
    if isinstance(gate, LanguageGate):
        return _check_language(gate, profile)
    if isinstance(gate, UnresolvedGate):
        # Always unknown, by construction. A requirement we cannot state is not a
        # requirement the student has cleared.
        return GateResult(GATE_UNKNOWN, gate.summary)
    raise TypeError(f"No checker for gate type {type(gate).__name__}")


def _destination_result(
    scholarship: Scholarship, reachable: tuple[str, ...]
) -> Optional[GateResult]:
    """Can the student actually reach the country this money spends in?

    Not a gate the award publishes -- it is a fact about the student's own routes, and the
    text says so. An award is worth nothing if no route reaches the country, but that is a
    statement about entry, not about eligibility, and conflating the two would tell a
    student they failed Chevening's criteria when what they lack is a way into the UK.

    Returns None for a multi-country award (`country_code is None`), where there is no
    single destination to check.
    """
    if scholarship.country_code is None:
        return None
    if scholarship.country_code in reachable:
        return GateResult(
            GATE_MET,
            f"Your routes reach {scholarship.country_code}, so this award has somewhere to "
            "spend",
        )
    return GateResult(
        GATE_BLOCKED,
        f"No route in your profile currently reaches {scholarship.country_code}, so this "
        "award has nothing to fund. That is a statement about your entry routes, not about "
        f"your eligibility for {scholarship.name} -- open a route there and re-check",
    )


def assess_scholarship(
    scholarship: Scholarship,
    profile: StudentRouteProfile,
    reachable: tuple[str, ...],
) -> ScholarshipAssessment:
    """One instrument against one profile.

    Status is decided by the strongest outcome present: any blocked gate blocks the award;
    otherwise any missing OR unknown gate makes it unlockable; only an award whose every
    gate came back met is OPEN. The `unknown` half of that rule is the important half.
    """
    if not scholarship.funds_study_abroad:
        # Settled before eligibility is even a question. Listed rather than hidden, because
        # a student who asks about this award deserves an answer.
        return ScholarshipAssessment(
            scholarship=scholarship,
            status=RouteStatus.BLOCKED.value,
            gates_blocked=(
                f"{scholarship.name} funds study inside Azerbaijan only. It is not a "
                "study-abroad award, so no eligibility check applies -- this is about what "
                "the award is, not about you",
            ),
        )

    results = [_check_gate(gate, profile) for gate in scholarship.gates]
    destination = _destination_result(scholarship, reachable)
    if destination is not None:
        results.append(destination)

    met = tuple(r.text for r in results if r.outcome == GATE_MET)
    missing = tuple(r.text for r in results if r.outcome == GATE_MISSING)
    blocked = tuple(r.text for r in results if r.outcome == GATE_BLOCKED)
    unknown = tuple(r.text for r in results if r.outcome == GATE_UNKNOWN)

    if blocked:
        status = RouteStatus.BLOCKED
    elif missing or unknown:
        status = RouteStatus.UNLOCKABLE
    else:
        status = RouteStatus.OPEN

    return ScholarshipAssessment(
        scholarship=scholarship,
        status=status.value,
        gates_met=met,
        gates_missing=missing,
        gates_blocked=blocked,
        gates_unknown=unknown,
    )


def assess_scholarships(
    profile: StudentRouteProfile, reachable: tuple[str, ...]
) -> list[ScholarshipAssessment]:
    """Every instrument in the catalogue, assessed and ordered most-available first.

    Blocked awards are returned, never filtered out. A student who is 22 needs to be told
    that Türkiye Bursları is closed to them and why, or they will spend January applying;
    and a student asking about Prezident Təqaüdü needs the answer, not an empty list.
    """
    assessments = [assess_scholarship(s, profile, reachable) for s in ALL_SCHOLARSHIPS]
    order = {
        RouteStatus.OPEN.value: 0,
        RouteStatus.UNLOCKABLE.value: 1,
        RouteStatus.BLOCKED.value: 2,
    }
    return sorted(assessments, key=lambda a: (order[a.status], a.scholarship.tier))


def prep_year_scholarship_warning(
    profile: StudentRouteProfile, plan_route_keys: frozenset[str]
) -> Optional[str]:
    """The trade-off between two things this engine already models, and nothing else says.

    The prep year at an Azerbaijani university is the product's central finding: it is what
    opens Germany and the UK to a school-leaver. It also costs twelve months, and Türkiye
    Bursları' bachelor award requires you to be under 21. A student who takes the prep year
    to open Germany can age out of a fully funded Turkish place in the process.

    Spec §11 records this interaction as a known trade-off the engine "should surface;
    whether it can is untested". It can now, because the profile carries an age.

    Returns None when there is nothing to say -- no prep-year plan, the wrong level, or a
    student who is not actually facing the trade-off. That last case includes anyone ALREADY
    over the limit: the award is closed to them whatever they do next, its own gate says so
    plainly, and telling them the prep year would "close" it as well would be false.
    """
    if profile.level_sought != "bachelor":
        return None
    if AZ_PREP_YEAR.key not in plan_route_keys:
        return None

    limit = TURKIYE_BURSLARI_BACHELOR_MAX_AGE
    if profile.age is None:
        return (
            f"One of your plans uses the {AZ_PREP_YEAR.time_cost_months}-month year at an "
            f"Azerbaijani university. That year is what opens Germany and the UK to you, and "
            f"it also puts you a year closer to {TURKIYE_BURSLARI.name}' under-{limit} "
            "bachelor limit. Tell us your age and we can tell you whether the prep year "
            "would cost you a fully funded Turkish place"
        )
    # Both halves matter. `age < limit` is what makes this a trade-off at all -- the award
    # has to be open today for the prep year to be able to cost it. `age + 1 >= limit` is
    # what makes the year decisive.
    if profile.age < limit and profile.age + 1 >= limit:
        return (
            f"Taking the {AZ_PREP_YEAR.time_cost_months}-month prep year would make you "
            f"{profile.age + 1} at the next {TURKIYE_BURSLARI.name} window, which is at or "
            f"over its under-{limit} bachelor limit. That year opens Germany and the UK to "
            "you and closes a fully funded Turkish place in the same move. Both are real; "
            "which one is worth more is your decision, not ours"
        )
    return None
