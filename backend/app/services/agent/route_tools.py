"""Agent tools over the route engine, the State Programme and the funding catalogue.

Until now the assistant's four tools could see documents and nothing else -- not a route,
not a scholarship gate, not the catalogue. It could not answer the question the product
exists to answer, while the answer sat one function call away, already structured and
already cited.

**Nothing here computes anything.** Every tool calls a service that already exists and
returns its result. That is deliberate and it is the safety property: an LLM narrating a
computed structure cannot invent a number, whereas an LLM asked to work one out will. The
division is spec §8's -- numbers come from ML or arithmetic, the model supplies framing.

Two rules these tools enforce on their own callers:

**The profile is the argument, never a lookup.** Like `/routes/assess`, every tool takes the
student's own answers as parameters. There is no `student_id` to resolve and therefore no
"row not found" branch to mishandle, and -- more to the point -- nothing for the model to
fill in from context. A field the student has not stated arrives as None and is answered as
unknown. This is the exact site where `extract_and_update_profile` used to invent GPA 3.8
and IELTS 7.5 and report success.

**`gates_unknown` never merges into `gates_missing`.** A missing gate is work the student
can do; an unknown gate is a fact they can tell us or a source we have to read. Neither ever
counts towards `open`. Merging them in prose is the same error as merging them in the API.

Not here yet: the universities a plan reaches. `services/university_requirements` needs a
database session, and these tools are deliberately sync and I/O-free. `/routes/assess`
already returns them, so a caller that needs universities should call the endpoint.
"""

from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from app.domain.route_definitions import ALL_ROUTES
from app.domain.routes import StudentRouteProfile
from app.domain.scholarship_definitions import ALL_SCHOLARSHIPS
from app.services.dp_eligibility import (
    application_window_note,
    assess_dp_eligibility,
    quota_note,
)
from app.services.route_engine import assess_routes, compose_two_hop
from app.services.scholarship_eligibility import (
    assess_scholarship,
    assess_scholarships,
    prep_year_scholarship_warning,
)

# Wording that must survive into whatever the model says. Clearing published gates is not an
# award: every instrument here is competitive and selection is a committee decision no
# dataset in this project models (spec §5.2).
POSSIBLY_ELIGIBLE_NOTE = (
    "Meeting these published requirements makes the student POSSIBLY ELIGIBLE to apply. "
    "It is never an award. Say 'you meet the published requirements', never 'you qualify "
    "for a scholarship' and never 'you will get it'."
)


def _profile(
    level_sought: str,
    qualification_held: str,
    dim_score: Optional[float] = None,
    dim_field_group: Optional[int] = None,
    ielts: Optional[float] = None,
    toefl: Optional[int] = None,
    sat: Optional[int] = None,
    act: Optional[int] = None,
    tr_yos: Optional[float] = None,
    test_as: Optional[float] = None,
    csca: Optional[float] = None,
    hsk: Optional[int] = None,
    language_certificate_level: Optional[str] = None,
    has_international_olympiad_medal: Optional[bool] = None,
    age: Optional[int] = None,
    work_experience_hours: Optional[int] = None,
    employer: Optional[str] = None,
    budget_azn_per_year: Optional[float] = None,
    gpa: Optional[float] = None,
    gpa_scale: Optional[str] = None,
) -> StudentRouteProfile:
    """Build the profile the services take. Every unstated field stays None."""
    return StudentRouteProfile(
        level_sought=level_sought.strip().lower(),
        qualification_held=qualification_held.strip().lower(),
        dim_score=dim_score,
        dim_field_group=dim_field_group,
        ielts=ielts,
        toefl=toefl,
        sat=sat,
        act=act,
        tr_yos=tr_yos,
        test_as=test_as,
        csca=csca,
        hsk=hsk,
        language_certificate_level=language_certificate_level,
        has_international_olympiad_medal=has_international_olympiad_medal,
        age=age,
        work_experience_hours=work_experience_hours,
        employer=employer,
        budget_azn_per_year=budget_azn_per_year,
        gpa=gpa,
        gpa_scale=gpa_scale,
    )


@tool
def assess_student_routes(
    level_sought: str,
    qualification_held: str,
    dim_score: Optional[float] = None,
    ielts: Optional[float] = None,
    toefl: Optional[int] = None,
    sat: Optional[int] = None,
    tr_yos: Optional[float] = None,
    test_as: Optional[float] = None,
    hsk: Optional[int] = None,
    language_certificate_level: Optional[str] = None,
    budget_azn_per_year: Optional[float] = None,
) -> Dict[str, Any]:
    """Find which study-abroad routes are open, unlockable or blocked for this student.

    Use this whenever the student asks where they can go, what they qualify for, or whether
    a country is possible. Pass ONLY what the student has actually told you; leave every
    other argument out. A score you were not given must not be guessed -- an omitted score
    is answered honestly as unknown, an invented one produces a confident wrong answer.

    Args:
        level_sought: 'bachelor' or 'master'. Required -- findings invert between the two.
        qualification_held: what they hold NOW. One of: attestat, one_year_university,
            bachelor_degree, a_level, ib, foundation_year, feststellungspruefung.
        dim_score: DİM score out of 700, if they sat it.
        ielts: IELTS overall band.
        toefl: TOEFL iBT total.
        sat: SAT total.
        tr_yos: TR-YÖS score.
        test_as: TestAS score.
        hsk: HSK level.
        language_certificate_level: CEFR level held, e.g. 'B2' or 'C1'.
        budget_azn_per_year: what they can spend per year, in AZN.

    Returns:
        `plans` -- each route or two-hop chain, with its status, what is missing, how many
        months it costs and its cost band in AZN. `blocked` -- routes closed on the
        qualification itself, each with the reason. `summary` counts them.
    """
    profile = _profile(
        level_sought=level_sought,
        qualification_held=qualification_held,
        dim_score=dim_score,
        ielts=ielts,
        toefl=toefl,
        sat=sat,
        tr_yos=tr_yos,
        test_as=test_as,
        hsk=hsk,
        language_certificate_level=language_certificate_level,
        budget_azn_per_year=budget_azn_per_year,
    )

    plans = [
        {
            "route_keys": [hop.key for hop in plan.hops],
            "destination_country": plan.hops[-1].country_code,
            "mechanism": " then ".join(hop.mechanism for hop in plan.hops),
            "status": plan.status.value,
            "missing": list(plan.missing),
            "total_months": plan.total_months,
            "cost_azn_low": plan.total_cost_azn[0],
            "cost_azn_high": plan.total_cost_azn[1],
            "citations": [hop.citation for hop in plan.hops],
            "proof_of_funds": [
                {
                    "amount": hop.proof_of_funds.amount,
                    "currency": hop.proof_of_funds.currency,
                    "period": hop.proof_of_funds.period,
                    "mechanism": hop.proof_of_funds.mechanism,
                }
                for hop in plan.hops
                if hop.proof_of_funds is not None
            ],
        }
        for plan in compose_two_hop(profile)
    ]

    blocked = [
        {
            "route_key": a.route.key,
            "country_code": a.route.country_code,
            "mechanism": a.route.mechanism,
            "reason": a.missing[0] if a.missing else "",
            "citation": a.route.citation,
        }
        for a in assess_routes(profile)
        if a.status.value == "blocked"
    ]

    return {
        "plans": plans,
        "blocked": blocked,
        "summary": {
            "open": sum(1 for p in plans if p["status"] == "open"),
            "unlockable": sum(1 for p in plans if p["status"] == "unlockable"),
            "blocked": len(blocked),
        },
        "note": (
            "A cost band is the route's own cost. It does NOT include tuition unless the "
            "route says so, and proof-of-funds is money the student must show for a visa, "
            "not money they spend. Do not add these numbers together."
        ),
    }


@tool
def describe_route_requirements(route_key: str) -> Dict[str, Any]:
    """Look up exactly what one route requires, with the source it was read from.

    Use this when the student asks why a route is closed to them, or what they would need
    for it. It takes no profile -- it reports the route's own published requirements, so it
    is the right tool for explaining a rule rather than judging a person.

    Args:
        route_key: e.g. 'de-bachelor-direct', 'az-prep-year', 'uk-bachelor-foundation'.
            Route keys come back from `assess_student_routes`.

    Returns:
        The qualifications that satisfy it, the exams and minimums, what completing it
        produces, its time and money cost, and the citation. `found: false` when the key is
        not one of ours -- in which case say so rather than describing a route from memory.
    """
    route = next((r for r in ALL_ROUTES if r.key == route_key.strip().lower()), None)
    if route is None:
        return {
            "found": False,
            "route_key": route_key,
            "known_route_keys": [r.key for r in ALL_ROUTES],
            "note": (
                "We hold no route by that key. Tell the student we do not have it rather "
                "than describing requirements from general knowledge."
            ),
        }

    return {
        "found": True,
        "route_key": route.key,
        "country_code": route.country_code,
        "level": route.level,
        "mechanism": route.mechanism,
        "accepts_any_one_of": list(route.requires_qualification),
        "exams_required": [
            {"name": e.name, "minimum": e.minimum} for e in route.exams
        ],
        "produces_qualification": route.produces_qualification,
        "time_cost_months": route.time_cost_months,
        "cost_azn_low": route.money_cost_azn[0],
        "cost_azn_high": route.money_cost_azn[1],
        "proof_of_funds": (
            {
                "amount": route.proof_of_funds.amount,
                "currency": route.proof_of_funds.currency,
                "period": route.proof_of_funds.period,
                "mechanism": route.proof_of_funds.mechanism,
                "citation": route.proof_of_funds.citation,
            }
            if route.proof_of_funds is not None
            else None
        ),
        "citation": route.citation,
        "provenance": route.provenance,
    }


@tool
def list_funding_options(
    level_sought: str,
    qualification_held: str,
    dim_score: Optional[float] = None,
    dim_field_group: Optional[int] = None,
    ielts: Optional[float] = None,
    toefl: Optional[int] = None,
    sat: Optional[int] = None,
    act: Optional[int] = None,
    language_certificate_level: Optional[str] = None,
    has_international_olympiad_medal: Optional[bool] = None,
    age: Optional[int] = None,
    work_experience_hours: Optional[int] = None,
    employer: Optional[str] = None,
) -> Dict[str, Any]:
    """Check every funding instrument's published gates against this student.

    Covers the Dövlət Proqramı and the other ten funders. Several gates have nothing to do
    with academic merit -- SOCAR's is employment, Türkiye Bursları' is being under 21,
    Chevening's is 2,800 documented hours -- so a student who looks strong academically can
    still be blocked, and that is worth telling them plainly.

    Pass only what the student has told you. Omitting `age` does not make the age gate pass;
    it makes it UNKNOWN, which is reported separately and never counts as eligible.

    Args:
        level_sought: 'bachelor' or 'master'. Seven of the ten funders are master's-only.
        qualification_held: what they hold now.
        dim_score: DİM out of 700 -- the DP's academic gate.
        dim_field_group: DİM ixtisas qrupu 1-4. The DP threshold is 400 for Group 1 and 550
            otherwise, so without this the answer can only be given at the extremes.
        ielts: IELTS overall band.
        toefl: TOEFL iBT total.
        sat: SAT total.
        act: ACT composite.
        language_certificate_level: CEFR level, e.g. 'C1'. The DP requires C1.
        has_international_olympiad_medal: an alternative to the DP's score gate.
        age: years. Decides Türkiye Bursları' under-21 bachelor limit and SOCAR's ceiling.
        work_experience_hours: documented professional hours, for Chevening.
        employer: only used to check employment-gated awards such as SOCAR's.

    Returns:
        `state_programme` with its band, gates met and missing, quota and window notes;
        `scholarships`, each with status and four SEPARATE gate lists; and
        `prep_year_warning` when the prep year would cost this student an award.
    """
    profile = _profile(
        level_sought=level_sought,
        qualification_held=qualification_held,
        dim_score=dim_score,
        dim_field_group=dim_field_group,
        ielts=ielts,
        toefl=toefl,
        sat=sat,
        act=act,
        language_certificate_level=language_certificate_level,
        has_international_olympiad_medal=has_international_olympiad_medal,
        age=age,
        work_experience_hours=work_experience_hours,
        employer=employer,
    )

    plans = compose_two_hop(profile)
    reachable = tuple({hop.country_code for plan in plans for hop in plan.hops})
    plan_route_keys = frozenset(hop.key for plan in plans for hop in plan.hops)

    dp = assess_dp_eligibility(profile)

    return {
        "state_programme": {
            "name": "Dövlət Proqramı",
            "status": dp.status.value,
            "band_checked": dp.band_checked,
            "gates_met": list(dp.gates_met),
            "gates_missing": list(dp.gates_missing),
            "quota_note": quota_note(profile.level_sought),
            "obligation_note": dp.obligation_note,
            "window_note": application_window_note(),
            # Deliberately not the funded programme list: that needs a database session.
            # Call POST /routes/assess for the programmes themselves.
        },
        "scholarships": [
            {
                "key": a.scholarship.key,
                "name": a.scholarship.name,
                "provider": a.scholarship.provider,
                "country_code": a.scholarship.country_code,
                "coverage": a.scholarship.coverage,
                "status": a.status,
                "gates_met": list(a.gates_met),
                "gates_missing": list(a.gates_missing),
                "gates_blocked": list(a.gates_blocked),
                "gates_unknown": list(a.gates_unknown),
                "window": a.scholarship.window,
                "obligation": a.scholarship.obligation,
                "citation": a.scholarship.citation,
                "provenance": a.scholarship.provenance,
            }
            for a in assess_scholarships(profile, reachable)
        ],
        "prep_year_warning": prep_year_scholarship_warning(profile, plan_route_keys),
        "countries_reachable": sorted(reachable),
        "note": POSSIBLY_ELIGIBLE_NOTE,
        "gate_note": (
            "gates_unknown means we could not check that gate, usually because the student "
            "has not told us something. It is NOT a pass and NOT a failure. Ask them for "
            "the missing fact rather than reporting the award as open or closed."
        ),
        "provenance_warning": (
            "Every figure in this catalogue is 'research-brief' provenance: taken from a "
            "research summary whose primary pages this project has not opened. Say the "
            "figure should be confirmed on the funder's own page before the student relies "
            "on it."
        ),
    }


@tool
def explain_funding_gate(
    scholarship_key: str,
    level_sought: str,
    qualification_held: str,
    age: Optional[int] = None,
    work_experience_hours: Optional[int] = None,
    employer: Optional[str] = None,
    ielts: Optional[float] = None,
    toefl: Optional[int] = None,
    language_certificate_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Explain why one specific award is or is not open to this student.

    Use it for "why can't I get Chevening?" -- it returns that award's gates one by one with
    the verdict on each, rather than a single yes or no.

    Args:
        scholarship_key: e.g. 'chevening', 'turkiye-burslari', 'socar-xarici-teqaud',
            'nawa-banach'. Keys come back from `list_funding_options`.
        level_sought: 'bachelor' or 'master'.
        qualification_held: what they hold now.
        age: years, if known.
        work_experience_hours: documented professional hours, if known.
        employer: if any.
        ielts: IELTS overall band.
        toefl: TOEFL iBT total.
        language_certificate_level: CEFR level held.

    Returns:
        The award's gates split four ways -- met, missing, blocked, unknown -- with its
        coverage, window, obligation and citation. `found: false` for an unknown key.
    """
    key = scholarship_key.strip().lower()
    scholarship = next((s for s in ALL_SCHOLARSHIPS if s.key == key), None)
    if scholarship is None:
        return {
            "found": False,
            "scholarship_key": scholarship_key,
            "known_keys": [s.key for s in ALL_SCHOLARSHIPS],
            "note": (
                "We do not model an award by that key. The Dövlət Proqramı is assessed "
                "separately -- use list_funding_options for it. Do not describe an award we "
                "do not hold from general knowledge."
            ),
        }

    profile = _profile(
        level_sought=level_sought,
        qualification_held=qualification_held,
        age=age,
        work_experience_hours=work_experience_hours,
        employer=employer,
        ielts=ielts,
        toefl=toefl,
        language_certificate_level=language_certificate_level,
    )
    # Assessed as though the destination is reachable, because this tool answers a question
    # about the AWARD, not about routing. `list_funding_options` is the one that applies the
    # reachability filter.
    assessment = assess_scholarship(
        scholarship, profile, (scholarship.country_code,) if scholarship.country_code else ()
    )

    return {
        "found": True,
        "key": scholarship.key,
        "name": scholarship.name,
        "provider": scholarship.provider,
        "coverage": scholarship.coverage,
        "status": assessment.status,
        "gates_met": list(assessment.gates_met),
        "gates_missing": list(assessment.gates_missing),
        "gates_blocked": list(assessment.gates_blocked),
        "gates_unknown": list(assessment.gates_unknown),
        "window": scholarship.window,
        "obligation": scholarship.obligation,
        "citation": scholarship.citation,
        "provenance": scholarship.provenance,
        "note": POSSIBLY_ELIGIBLE_NOTE,
    }


route_tools: List[Any] = [
    assess_student_routes,
    describe_route_requirements,
    list_funding_options,
    explain_funding_gate,
]
