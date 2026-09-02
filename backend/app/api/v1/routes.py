"""Route assessment: a student's qualifications in, their open paths out.

The payload IS the student's profile -- there is no student_id lookup here, so there is no
"row not found" case to mishandle. `level_sought` and `qualification_held` are required
fields with no default; every exam score is `Optional[...] = None`. A request that omits a
score is answered with that field truly unset (None), never a fabricated value, and a
request that omits the two required fields is rejected by FastAPI's validation before this
function runs at all -- there is no profile to invent it from.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.routes import StudentRouteProfile
from app.services.dp_eligibility import (
    any_funded_programmes_at_level,
    assess_dp_eligibility,
    describe_funded_programmes,
    funded_programmes,
)
from app.services.route_engine import assess_routes, compose_two_hop
from app.services.university_requirements import (
    any_requirements_curated,
    describe_universities,
    missing_requirement_note,
    qualification_delivered,
    universities_accepting,
)

router = APIRouter(prefix="/routes", tags=["Route Planning"])


class AssessRoutesPayload(BaseModel):
    level_sought: str = Field(..., description="'bachelor' or 'master'")
    qualification_held: str = Field(..., description="attestat, one_year_university, bachelor_degree, a_level, ib")
    dim_score: Optional[float] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    sat: Optional[int] = None
    act: Optional[int] = None
    tr_yos: Optional[float] = None
    test_as: Optional[float] = None
    csca: Optional[float] = None
    hsk: Optional[int] = None
    language_certificate_level: Optional[str] = None
    has_international_olympiad_medal: Optional[bool] = None
    budget_azn_per_year: Optional[float] = None


class RouteHop(BaseModel):
    key: str
    country_code: str
    mechanism: str
    time_cost_months: int
    money_cost_azn_low: int
    money_cost_azn_high: int
    citation: str
    provenance: str


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
    provenance: str
    source_url: str
    last_checked: Optional[str]


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
    funded_programmes: List[FundedProgrammeResponse]
    # Distinguishes why the list above might be empty -- "listed", "no DP programmes exist
    # at this level at all", "programmes exist but not in a country you can reach", or "your
    # profile does not reach any country at this level" -- so an empty list is never read as
    # a blanket "DP funds nothing for you" (see dp_eligibility.describe_funded_programmes).
    funded_programmes_status: str
    funded_programmes_explanation: str


class AssessRoutesResponse(BaseModel):
    blocked: List[str]
    plans: List[RoutePlanResponse]
    dp: DPEligibilityResponse


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
        notes=row.documents_required,
        unknown_fields=list(match.unknown_fields),
        not_stated=missing_requirement_note(match.unknown_fields),
        provenance=row.provenance,
        source_url=row.source_url,
        last_checked=row.last_checked.isoformat() if row.last_checked else None,
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
    seen_destinations: dict[tuple[str, str], tuple[list, str, str]] = {}
    plans: List[RoutePlanResponse] = []

    for plan in compose_two_hop(profile):
        destination = plan.hops[-1].country_code
        delivered = qualification_delivered(plan, profile)
        cache_key = (destination, delivered)

        if cache_key not in seen_destinations:
            matches = await universities_accepting(
                db,
                country_code=destination,
                level=profile.level_sought,
                qualification=delivered,
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

    return AssessRoutesResponse(
        blocked=blocked,
        plans=plans,
        dp=DPEligibilityResponse(
            status=dp.status.value,
            band_checked=dp.band_checked,
            gates_met=list(dp.gates_met),
            gates_missing=list(dp.gates_missing),
            funded_programmes=[
                FundedProgrammeResponse(
                    country_code=row.country_code,
                    university_name=row.university_name,
                    program_name=row.program_name,
                    source_url=row.source_url,
                )
                for row in funded
            ],
            funded_programmes_status=funded_status,
            funded_programmes_explanation=funded_explanation,
        ),
    )
