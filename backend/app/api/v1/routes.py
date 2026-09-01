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


class RoutePlanResponse(BaseModel):
    hops: List[RouteHop]
    total_months: int
    total_cost_azn_low: int
    total_cost_azn_high: int
    status: str
    missing: List[str]


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

    plans = [
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
        )
        for plan in compose_two_hop(profile)
    ]

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
