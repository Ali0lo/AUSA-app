"""Route assessment: a student's qualifications in, their open paths out.

The payload IS the student's profile -- there is no student_id lookup here, so there is no
"row not found" case to mishandle. `level_sought` and `qualification_held` are required
fields with no default; every exam score is `Optional[...] = None`. A request that omits a
score is answered with that field truly unset (None), never a fabricated value, and a
request that omits the two required fields is rejected by FastAPI's validation before this
function runs at all -- there is no profile to invent it from.
"""

from typing import Any, Dict, List, Optional
from typing import List, Optional, Literal
from dataclasses import replace
import json

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.routes import StudentRouteProfile
from app.services.agent.intake import intake_as_dict, parse_intake
from app.services.dp_eligibility import (
    any_funded_programmes_at_level,
    assess_dp_eligibility,
    describe_funded_programmes,
    funded_programmes,
)
from app.services.route_engine import assess_routes, compose_two_hop
from app.services.scholarship_eligibility import (
    assess_scholarships,
    prep_year_scholarship_warning,
)
from app.services.university_requirements import (
    any_requirements_curated,
    describe_universities,
    missing_requirement_note,
    qualification_delivered,
    universities_accepting,
)

router = APIRouter(prefix="/routes", tags=["Route Planning"])


class AssessRoutesPayload(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    level_sought: Literal["bachelor", "master"]
    qualification_held: Literal["attestat", "one_year_university", "bachelor_degree", "a_level", "ib", "foundation_year", "feststellungspruefung"]
    dim_score: Optional[float] = Field(None, ge=0, le=700)
    ielts: Optional[float] = Field(None, ge=0, le=9)
    toefl: Optional[int] = Field(None, ge=0, le=120)
    sat: Optional[int] = Field(None, ge=0, le=1600)
    act: Optional[int] = Field(None, ge=0, le=36)
    tr_yos: Optional[float] = Field(None, ge=0, le=500)
    test_as: Optional[float] = Field(None, ge=0)
    csca: Optional[float] = Field(None, ge=0)
    hsk: Optional[int] = Field(None, ge=0, le=9)
    language_certificate_level: Optional[str] = None
    has_international_olympiad_medal: Optional[bool] = None
    # 1-4. The Dövlət Proqramı's DİM threshold is 400 for Group 1 and 550 for every other
    # field, so this turns an indefinite answer into a definite one for any score between
    # them. Omitting it is allowed and is answered honestly rather than assumed.
    dim_field_group: Optional[int] = Field(
        default=None, ge=1, le=4,
        description="DİM ixtisas qrupu, 1-4. Group 1 is engineering and technology.",
    )
    # The three funding inputs. Every one is optional and an omission is answered as
    # "we could not check this gate", never as a pass -- see scholarship_eligibility.
    age: Optional[int] = Field(
        default=None, ge=14, le=80,
        description="Age in years. Decides Türkiye Bursları' under-21 bachelor limit and "
                    "SOCAR's upper limit; omitting it leaves those gates unchecked.",
    )
    work_experience_hours: Optional[int] = Field(
        default=None, ge=0,
        description="Documented professional hours. Chevening publishes 2,800 as its bar.",
    )
    employer: Optional[str] = Field(
        default=None, max_length=200,
        description="Your employer, if any. Only used to check employment-gated awards "
                    "such as SOCAR's, which is closed to everyone outside the group.",
    )
    budget_azn_per_year: Optional[float] = Field(None, ge=0)
    # The grade average of the qualification named in `qualification_held`: the attestat for
    # a school-leaver, the bachelor's degree for a master's applicant. Deliberately NOT
    # bounded to 0-4.0 the way `students.gpa` is -- that bound rejects an Azerbaijani
    # attestat average of 4.5 out of 5 as invalid input. The scale is what decides the
    # valid range, and `check_grade` reports an out-of-range value rather than a 422, so a
    # student who picks the wrong scale is told which scale their number cannot be on.
    gpa: Optional[float] = Field(default=None, ge=0.0)
    gpa_scale: Optional[str] = Field(
        default=None,
        description="One of: 5.0 (Azerbaijani attestat), 100, 4.0, german. "
                    "A grade sent without one is reported as not comparable, never assumed.",
    )


class ParseMessagePayload(BaseModel):
    message: str = Field(
        ..., min_length=1, max_length=4000,
        description="What the student wrote, in Azerbaijani or English, verbatim.",
    )


class HeardField(BaseModel):
    """One field read out of the message, and the words it was read from.

    The quote is the point. A student who is told "I understood your DİM score as 520"
    beside their own sentence can correct a misreading; one handed a filled-in form cannot
    see there was a reading at all.
    """
    field: str
    value: Any
    quote: str


class ParseMessageResponse(BaseModel):
    """A reading, not a decision.

    `fields` holds only what the message supports and is fed straight to `/routes/assess`
    once `ready_to_assess` is true. Everything else on this model exists so the caller can
    ask instead of assume: `conflicts` for a value stated twice, `still_needed` for the two
    fields the engine requires, `worth_asking` for gates that stay unknown without them, and
    `not_parsed` for fields no pattern here reads at all.
    """
    fields: Dict[str, Any]
    heard: List[HeardField]
    conflicts: List[str]
    # The subject the student named, carried through uninterpreted. It is not a DİM ixtisas
    # qrupu and must not be turned into one: the Dövlət Proqramı threshold is 400 for Group
    # 1 and 550 otherwise, so deriving the group from the word "robotics" would move a real
    # gate by 150 points on the strength of a guess.
    interest: Optional[str]
    ready_to_assess: bool
    still_needed: List[str]
    worth_asking: List[str]
    not_parsed: List[str]
    notes: List[str]
    instruction: str


class ProofOfFundsResponse(BaseModel):
    """Cash that must exist in an account before a visa, distinct from the route's cost."""
    amount: int
    currency: str
    period: str
    mechanism: str
    citation: str


class RouteHop(BaseModel):
    key: str
    country_code: str
    mechanism: str
    time_cost_months: int
    money_cost_azn_low: int
    money_cost_azn_high: int
    citation: str
    provenance: str
    # None means no requirement has been RECORDED for this hop, which is not the same as
    # this country having none (ADR-0004). The client must not render an absent gate as a
    # cleared one, so it says "not recorded" rather than showing nothing.
    proof_of_funds: Optional[ProofOfFundsResponse] = None


class UniversityResponse(BaseModel):
    """One university that documents accepting the qualification this plan produces.

    Every requirement field is Optional and stays Optional. `unknown_fields` names the ones
    that came back NULL and `not_stated` says it in a sentence, because a blank tuition
    rendered in a list reads as free and a blank language test reads as none required
    (ADR-0004: an unknown must never read as permission).
    """
    university_name: str
    program_name: str
    country_code: str
    intake_year: int
    entry_qualification_accepted: Optional[str]
    foundation_required: Optional[bool]
    foundation_providers: Optional[str]
    language_test: Optional[str]
    language_minimum_score: Optional[float]
    entrance_exam: Optional[str]
    entrance_exam_minimum: Optional[float]
    gpa_minimum: Optional[float]
    gpa_scale: Optional[str]
    tuition_per_year: Optional[float]
    currency: Optional[str]
    application_fee: Optional[float]
    application_deadline: Optional[str]
    application_portal: Optional[str]
    notes: Optional[str]
    unknown_fields: List[str]
    not_stated: Optional[str]
    # Advisory. `grade_exact` is False when the comparison crossed two scales and is a
    # proportional screening signal rather than an official conversion -- a client that
    # renders the verdict without that flag is overstating what was checked.
    grade_verdict: str
    grade_exact: bool
    grade_explanation: str
    provenance: str
    source_url: str
    last_checked: Optional[str]
    id: Optional[int] = None
    level: Optional[str] = None
    requirement_scope: str = "general"
    language_of_instruction: Optional[str] = None
    living_cost_estimate_per_year: Optional[float] = None
    evidence: List[dict] = Field(default_factory=list)
    checks: List[str] = Field(default_factory=list)
    application_status: str = "needs_review"
    verified_at: Optional[str] = None


class RoutePlanResponse(BaseModel):
    hops: List[RouteHop]
    total_months: int
    total_cost_azn_low: int
    total_cost_azn_high: int
    status: str
    missing: List[str]
    # Where this plan ends, and holding what. `qualification_delivered` is the join key into
    # the universities below: it is the qualification the student will actually be applying
    # with, which for a two-hop plan is what the FIRST hop produced, not what they hold today.
    destination_country: str
    qualification_delivered: str
    universities: List[UniversityResponse]
    # Never let an empty `universities` list stand unexplained: "we have not collected that
    # country" and "we collected it and none of them accept this qualification" are
    # different answers and only one of them is about the student.
    universities_status: str
    universities_explanation: str


class FundedProgrammeResponse(BaseModel):
    country_code: Optional[str]
    university_name: str
    program_name: str
    source_url: str
    intake_year: Optional[int] = None


class DPEligibilityResponse(BaseModel):
    status: str
    band_checked: str
    gates_met: List[str]
    gates_missing: List[str]
    # Deliberate wording. Clearing the published gates is not an award (spec §5.2).
    note: str = (
        "Meeting these published requirements makes you possibly eligible to apply. "
        "It is not an award: selection is competitive and is decided by a committee."
    )
    # Not gates -- the three things a student needs in order to decide whether they want
    # this funding at all, and which the product previously rendered nowhere: how many
    # places exist at their level, that the money carries a 5-year return-service contract,
    # and which academic year an application started today would actually be for.
    quota_note: str
    obligation_note: str
    window_note: str
    funded_programmes: List[FundedProgrammeResponse]
    # Distinguishes why the list above might be empty -- "listed", "no DP programmes exist
    # at this level at all", "programmes exist but not in a country you can reach", or "your
    # profile does not reach any country at this level" -- so an empty list is never read as
    # a blanket "DP funds nothing for you" (see dp_eligibility.describe_funded_programmes).
    funded_programmes_status: str
    funded_programmes_explanation: str


class ScholarshipResponse(BaseModel):
    """One funding instrument, with the gate that actually decides it.

    `gates_unknown` is separate from `gates_missing` on purpose, and a client must not merge
    them: a missing gate is work the student can do, an unknown gate is a fact they can tell
    us or a source we have to read. Neither ever counts towards `status: open`.
    """
    key: str
    name: str
    provider: str
    tier: int
    country_code: Optional[str]
    coverage: str
    status: str
    gates_met: List[str]
    gates_missing: List[str]
    gates_blocked: List[str]
    gates_unknown: List[str]
    obligation: Optional[str]
    window: Optional[str]
    citation: str
    provenance: str


class AssessRoutesResponse(BaseModel):
    blocked: List[str]
    plans: List[RoutePlanResponse]
    dp: DPEligibilityResponse
    # Every funder EXCEPT the Dövlət Proqramı, which is scored in `dp` above against its own
    # regulation. One award, one assessor: listing the DP in both would create a second
    # source of truth that diverges on the first correction.
    scholarships: List[ScholarshipResponse]
    scholarships_note: str = (
        "Meeting an award's published gates makes you possibly eligible to apply. It is "
        "never an award: every programme here is competitive and selection is a committee "
        "decision. Awards you cannot win are shown as blocked rather than hidden, with the "
        "gate that closed them."
    )
    # The trade-off between the prep year and Türkiye Bursları' age limit, when this profile
    # actually faces it. None when it does not arise (spec §11).
    prep_year_warning: Optional[str] = None


def _university_response(match) -> UniversityResponse:
    """Map one curated row to its response shape.

    Dates and timestamps go out as ISO strings rather than as `date`/`datetime`, so a
    consumer never has to guess a timezone from a bare date. A NULL stays None all the way
    to the wire; `unknown_fields` and `not_stated` are what turn that None into something a
    reader can see, rather than an empty cell they will fill in with an assumption.
    """
    row = match.requirement
    return UniversityResponse(
        university_name=row.university_name,
        program_name=row.program_name,
        country_code=row.country_code,
        intake_year=row.intake_year,
        entry_qualification_accepted=row.entry_qualification_accepted,
        foundation_required=row.foundation_required,
        foundation_providers=row.foundation_providers,
        language_test=row.language_test,
        language_minimum_score=row.language_minimum_score,
        entrance_exam=row.entrance_exam,
        entrance_exam_minimum=row.entrance_exam_minimum,
        gpa_minimum=row.gpa_minimum,
        gpa_scale=row.gpa_scale,
        tuition_per_year=row.tuition_per_year,
        currency=row.currency,
        application_fee=row.application_fee,
        application_deadline=(
            row.application_deadline.isoformat() if row.application_deadline else None
        ),
        application_portal=row.application_portal,
        notes="\n".join(v for v in (row.notes, row.documents_required) if v) or None,
        unknown_fields=list(match.unknown_fields),
        not_stated=missing_requirement_note(match.unknown_fields),
        grade_verdict=match.grade.verdict,
        grade_exact=match.grade.exact,
        grade_explanation=match.grade.explanation,
        provenance=row.provenance,
        source_url=row.source_url,
        last_checked=row.last_checked.isoformat() if row.last_checked else None,
        id=row.id,
        level=row.level,
        requirement_scope=row.requirement_scope or "general",
        language_of_instruction=row.language_of_instruction,
        living_cost_estimate_per_year=row.living_cost_estimate_per_year,
        evidence=json.loads(row.evidence) if row.evidence else [],
        checks=list(match.checks),
        application_status=match.application_status,
        verified_at=row.verified_at.isoformat() if row.verified_at else None,
    )


def _reachable_countries(plans: List[RoutePlanResponse]) -> tuple[str, ...]:
    """Every country code touched by any hop of any plan -- including a two-hop plan's
    destination, not just its intermediate first hop. This is the wiring the product's
    central finding depends on (the prep year unlocking a blocked country's funded
    programmes): a country reached only via a second hop must still contribute here, or
    its DP-funded programmes silently vanish from the response with no error and no test
    noticing (see the review report's mutation M3, and test_routes_reachable.py)."""
    return tuple({hop.country_code for plan in plans for hop in plan.hops})


@router.post(
    "/parse",
    response_model=ParseMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Read a student's own sentence into the fields /assess takes",
)
async def parse(payload: ParseMessagePayload) -> ParseMessageResponse:
    """Free text in, a partial `/assess` payload out.

    Deliberately a separate call rather than a `message` field on `/assess`: reading and
    assessing are two decisions and the student gets to see the first before we act on it.
    `fields` is partial by design -- when `ready_to_assess` is false it is missing something
    only the student can supply, and the caller must ask for `still_needed` rather than fill
    it in. No database, no session, no state.
    """
    return ParseMessageResponse(**intake_as_dict(parse_intake(payload.message)))


@router.post(
    "/assess",
    response_model=AssessRoutesResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess which routes are open, unlockable or blocked",
)
async def assess(
    payload: AssessRoutesPayload,
    db: AsyncSession = Depends(get_db),
) -> AssessRoutesResponse:
    profile = StudentRouteProfile(**payload.model_dump())

    blocked = [
        f"{a.route.country_code}: {a.route.mechanism} -- {a.missing[0]}"
        for a in assess_routes(profile)
        if a.status.value == "blocked"
    ]

    # One lookup per distinct (country, qualification) pair rather than one per plan.
    # Several plans routinely end in the same place -- the direct UK route and the prep-year
    # UK route both finish in GB -- and they would each issue the same two queries.
    seen_destinations: dict[tuple[str, str, str | None], tuple[list, str, str]] = {}
    plans: List[RoutePlanResponse] = []

    for plan in compose_two_hop(profile):
        destination = plan.hops[-1].country_code
        delivered = qualification_delivered(plan, profile)
        language = "Chinese" if any(h.key == "cn-bachelor-csc" for h in plan.hops) else None
        cache_key = (destination, delivered, language)

        if cache_key not in seen_destinations:
            matches = await universities_accepting(
                db,
                country_code=destination,
                level=profile.level_sought,
                qualification=delivered,
                student_gpa=profile.gpa,
                student_gpa_scale=profile.gpa_scale,
                profile=replace(profile, qualification_held=delivered),
                language=language,
            )
            # Only ask the existence question when it can change the answer.
            any_curated = (
                await any_requirements_curated(
                    db, country_code=destination, level=profile.level_sought
                )
                if not matches
                else False
            )
            uni_status, uni_explanation = describe_universities(
                matches,
                country_code=destination,
                qualification=delivered,
                any_curated=any_curated,
            )
            seen_destinations[cache_key] = (matches, uni_status, uni_explanation)

        matches, uni_status, uni_explanation = seen_destinations[cache_key]

        plans.append(
            RoutePlanResponse(
                hops=[
                    RouteHop(
                        key=hop.key,
                        country_code=hop.country_code,
                        mechanism=hop.mechanism,
                        time_cost_months=hop.time_cost_months,
                        money_cost_azn_low=hop.money_cost_azn[0],
                        money_cost_azn_high=hop.money_cost_azn[1],
                        citation=hop.citation,
                        provenance=hop.provenance,
                        proof_of_funds=(
                            ProofOfFundsResponse(
                                amount=hop.proof_of_funds.amount,
                                currency=hop.proof_of_funds.currency,
                                period=hop.proof_of_funds.period,
                                mechanism=hop.proof_of_funds.mechanism,
                                citation=hop.proof_of_funds.citation,
                            )
                            if hop.proof_of_funds is not None
                            else None
                        ),
                    )
                    for hop in plan.hops
                ],
                total_months=plan.total_months,
                total_cost_azn_low=plan.total_cost_azn[0],
                total_cost_azn_high=plan.total_cost_azn[1],
                status=plan.status.value,
                missing=list(plan.missing),
                destination_country=destination,
                qualification_delivered=delivered,
                universities=[_university_response(match) for match in matches],
                universities_status=uni_status,
                universities_explanation=uni_explanation,
            )
        )

    dp = assess_dp_eligibility(profile)
    # Only the countries this student's own plans actually reach -- never every country in
    # the catalogue. dp_catalogue rows for the 27 out-of-scope countries (country_code IS
    # NULL) are excluded by funded_programmes' own IN-filter (see its docstring); rows for
    # the 6 in-scope countries are excluded here too, whenever no plan reaches that country
    # for this student. Either way, the endpoint never claims a programme is or isn't
    # available in a country it has not actually checked for this profile.
    reachable = _reachable_countries(plans)
    funded = await funded_programmes(db, level=profile.level_sought, country_codes=reachable)

    # Only run the existence check when it can actually change the answer: not when
    # `funded` already has rows (case "listed"), and not when `reachable` is empty (case
    # (c) is already decided without needing it). Keeps this a cheap LIMIT-1 query, not an
    # unconditional extra fetch.
    any_at_level = (
        await any_funded_programmes_at_level(db, level=profile.level_sought)
        if not funded and reachable
        else False
    )
    funded_status, funded_explanation = describe_funded_programmes(funded, reachable, any_at_level)
    if not funded and reachable and not any_at_level:
        funded_status = "catalogue_unavailable"
        funded_explanation = "The DP catalogue for this level has not been loaded. Funding coverage is unavailable; an empty store does not mean that the programme funds nothing."

    # The other nine funders. Given the same `reachable` set the DP catalogue query uses, so
    # an award is never offered for a country this profile has no way to enter -- and so
    # that limitation is reported as a fact about routes rather than as a failed gate.
    scholarships = assess_scholarships(profile, reachable)
    plan_route_keys = frozenset(hop.key for plan in plans for hop in plan.hops)

    return AssessRoutesResponse(
        blocked=blocked,
        plans=plans,
        scholarships=[
            ScholarshipResponse(
                key=a.scholarship.key,
                name=a.scholarship.name,
                provider=a.scholarship.provider,
                tier=a.scholarship.tier,
                country_code=a.scholarship.country_code,
                coverage=a.scholarship.coverage,
                status=a.status,
                gates_met=list(a.gates_met),
                gates_missing=list(a.gates_missing),
                gates_blocked=list(a.gates_blocked),
                gates_unknown=list(a.gates_unknown),
                obligation=a.scholarship.obligation,
                window=a.scholarship.window,
                citation=a.scholarship.citation,
                provenance=a.scholarship.provenance,
            )
            for a in scholarships
        ],
        prep_year_warning=prep_year_scholarship_warning(profile, plan_route_keys),
        dp=DPEligibilityResponse(
            status=dp.status.value,
            band_checked=dp.band_checked,
            gates_met=list(dp.gates_met),
            gates_missing=list(dp.gates_missing),
            quota_note=dp.quota_note,
            obligation_note=dp.obligation_note,
            window_note=dp.window_note,
            funded_programmes=[
                FundedProgrammeResponse(
                    country_code=row.country_code,
                    university_name=row.university_name,
                    program_name=row.program_name,
                    source_url=row.source_url,
                    intake_year=row.intake_year,
                )
                for row in funded
            ],
            funded_programmes_status=funded_status,
            funded_programmes_explanation=funded_explanation,
        ),
    )
