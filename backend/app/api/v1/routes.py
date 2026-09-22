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

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.qualifications import ProgramRequirement
from app.domain.process_definitions import PROCESS_BY_ROUTE_KEY
from app.domain.route_definitions import ALL_ROUTES
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

logger = logging.getLogger(__name__)

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


class TargetCatalogItem(BaseModel):
    university_name: str
    program_name: str
    level: str
    country_code: str
    source_type: str
    source_url: str


@router.get(
    "/catalog",
    response_model=List[TargetCatalogItem],
    status_code=status.HTTP_200_OK,
    summary="List target institutions and programs available for analysis",
)
async def list_target_catalog(
    level: Optional[str] = None,
    country: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[TargetCatalogItem]:
    """Returns curated target institutions with offline database resilience."""
    items: List[TargetCatalogItem] = []
    try:
        stmt = select(ProgramRequirement)
        if level:
            stmt = stmt.where(ProgramRequirement.level == level)
        if country:
            stmt = stmt.where(ProgramRequirement.country_code == country)
        result = await db.execute(stmt)
        rows = result.scalars().all()
        for r in rows:
            items.append(
                TargetCatalogItem(
                    university_name=r.university_name,
                    program_name=r.program_name,
                    level=r.level,
                    country_code=r.country_code,
                    source_type="curated",
                    source_url=r.source_url or "",
                )
            )
    except Exception:
        # The fallback below reads the same cited CSVs the database is loaded from, so
        # serving them substitutes nothing and is worth more to a student than a 500.
        # What was wrong here was the silence: `except Exception: pass` hid a NameError
        # on `select` for as long as this endpoint has existed, so the database branch
        # never once ran and nobody could see that. Catch broadly, record loudly.
        logger.exception("catalogue database unavailable; serving the curated CSVs")

    if not items:
        # Offline fallback to the curated CSVs -- every file in the catalogue, not just
        # the first. Track A holds all 30 master rows and the only US and Polish rows.
        import csv
        from scripts.load_program_requirements import CATALOGUE_FILES

        for csv_path in CATALOGUE_FILES:
            if not csv_path.exists():
                continue
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if level and row.get("level") != level:
                        continue
                    if country and row.get("country_code") != country:
                        continue
                    items.append(
                        TargetCatalogItem(
                            university_name=row.get("university_name", ""),
                            program_name=row.get("program_name", ""),
                            level=row.get("level", ""),
                            country_code=row.get("country_code", ""),
                            source_type="curated",
                            source_url=row.get("source_url", ""),
                        )
                    )
    return items


class ChecklistItem(BaseModel):
    name: str
    requirement: str
    student_value: Optional[str] = None
    status: str  # "MET", "GAP", "UNKNOWN"
    explanation: str


class TargetGapPayload(BaseModel):
    university_name: str
    program_name: Optional[str] = None
    level: str = "bachelor"
    qualification_held: str = "attestat"
    gpa: Optional[float] = None
    gpa_scale: Optional[str] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    dim_score: Optional[float] = None
    sat: Optional[int] = None
    tr_yos: Optional[float] = None
    test_as: Optional[float] = None


class TargetGapResponse(BaseModel):
    found: bool
    university_name: str
    program_name: str
    level: str
    country_code: str
    route_status: str  # "OPEN", "UNLOCKABLE", "BLOCKED", "UNKNOWN"
    route_gap_statement: str
    unlock_steps: List[str]
    unlock_time_months: int
    unlock_cost_azn_low: int
    unlock_cost_azn_high: int
    checklist: List[ChecklistItem]
    application_portal: Optional[str] = None
    application_deadline: Optional[str] = None
    application_fee: Optional[float] = None
    currency: Optional[str] = None
    documents_required: Optional[str] = None
    alternatives: List[dict] = []
    provenance: str = "claude-extracted"
    source_url: str = ""
    last_checked: Optional[str] = None
    notes: Optional[str] = None


@router.post(
    "/target-gap",
    response_model=TargetGapResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed gap analysis for a specific target university",
)
async def assess_target_gap(
    payload: TargetGapPayload,
    db: AsyncSession = Depends(get_db),
) -> TargetGapResponse:
    """Evaluates a student's profile against an explicit target university with gap analysis."""
    from app.domain.grades import check_grade
    from app.domain.routes import StudentRouteProfile

    # Search in database first
    row = None
    try:
        stmt = select(ProgramRequirement).where(
            ProgramRequirement.university_name.ilike(f"%{payload.university_name}%"),
            ProgramRequirement.level == payload.level,
        )
        if payload.program_name:
            stmt = stmt.where(ProgramRequirement.program_name.ilike(f"%{payload.program_name}%"))
        res = await db.execute(stmt)
        row = res.scalars().first()
    except Exception:
        # The fallback below reads the same cited CSVs the database is loaded from, so
        # serving them substitutes nothing and is worth more to a student than a 500.
        # What was wrong here was the silence: `except Exception: pass` hid a NameError
        # on `select` for as long as this endpoint has existed, so the database branch
        # never once ran and nobody could see that. Catch broadly, record loudly.
        logger.exception("catalogue database unavailable; serving the curated CSVs")

    # Offline fallback to CSV if row not in DB
    if not row:
        import csv
        from scripts.load_program_requirements import CATALOGUE_FILES

        for csv_path in CATALOGUE_FILES:
            if row or not csv_path.exists():
                continue
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                for r in csv.DictReader(f):
                    if (
                        payload.university_name.lower() in r.get("university_name", "").lower()
                        and r.get("level", "") == payload.level
                    ):
                        class CsvRequirement:
                            pass
                        req = CsvRequirement()
                        for k, v in r.items():
                            setattr(req, k, v if v != "" else None)
                        req.gpa_minimum = float(r["gpa_minimum"]) if r.get("gpa_minimum") else None
                        req.language_minimum_score = float(r["language_minimum_score"]) if r.get("language_minimum_score") else None
                        req.entrance_exam_minimum = float(r["entrance_exam_minimum"]) if r.get("entrance_exam_minimum") else None
                        req.tuition_per_year = float(r["tuition_per_year"]) if r.get("tuition_per_year") else None
                        req.application_fee = float(r["application_fee"]) if r.get("application_fee") else None
                        row = req
                        break

    # If university is not held in our catalogue
    if not row:
        return TargetGapResponse(
            found=False,
            university_name=payload.university_name,
            program_name=payload.program_name or "General Admissions",
            level=payload.level,
            country_code="UNKNOWN",
            route_status="UNKNOWN",
            route_gap_statement=(
                f"We have not collected admission requirements for {payload.university_name} yet. "
                "This is a catalogue gap in our data, not a statement that the institution will reject you. "
                "Please check the institution's official international admissions page directly."
            ),
            unlock_steps=[],
            unlock_time_months=0,
            unlock_cost_azn_low=0,
            unlock_cost_azn_high=0,
            checklist=[],
            alternatives=[
                {"university_name": "Bogazici University", "country_code": "TR", "reason": "Direct attestat accepted"},
                {"university_name": "Istanbul Technical University", "country_code": "TR", "reason": "Direct attestat accepted"},
                {"university_name": "University of Warsaw", "country_code": "PL", "reason": "Direct entry with apostille"},
            ],
            provenance="not_collected",
            source_url="",
        )

    # University is held. Evaluate Route Gap
    c_code = getattr(row, "country_code", "UNKNOWN")
    accepted_qual = getattr(row, "entry_qualification_accepted", None)
    held_qual = payload.qualification_held

    route_status = "OPEN"
    gap_statement = f"Direct route to {row.university_name} is accessible with your qualification ({held_qual})."
    unlock_steps: List[str] = []
    unlock_months = 0
    cost_low = 0
    cost_high = 0

    if c_code == "DE" and held_qual == "attestat" and payload.level == "bachelor":
        route_status = "BLOCKED"
        gap_statement = (
            f"{row.university_name} does not accept a 11-year school certificate (attestat) for direct entry. "
            "Under anabin regulations, direct entry requires one completed university year or a Studienkolleg."
        )
        unlock_steps = [
            "Attend Studienkolleg in Germany and pass Feststellungsprüfung (12 months, TestAS required, ~6,000–14,000 AZN)",
            "Complete 1 year at an accredited Azerbaijani university (~1,000–4,000 AZN) to unlock subject-restricted direct entry"
        ]
        unlock_months = 12
        cost_low = 1000
        cost_high = 14000
    elif c_code == "GB" and held_qual == "attestat" and payload.level == "bachelor":
        route_status = "BLOCKED"
        gap_statement = (
            f"{row.university_name} does not accept an Azerbaijani attestat alone for direct bachelor entry. "
            "Entry requires an international foundation year or one completed year of university."
        )
        unlock_steps = [
            "Enroll in an accredited International Foundation Programme (12 months, ~25,000–45,000 AZN)",
            "Complete 1 year at an accredited Azerbaijani university (~1,000–4,000 AZN) for direct UCAS admission"
        ]
        unlock_months = 12
        cost_low = 1000
        cost_high = 45000
    elif accepted_qual and accepted_qual != held_qual:
        route_status = "UNLOCKABLE"
        gap_statement = f"This programme requires {accepted_qual.replace('_', ' ')}. You currently hold {held_qual.replace('_', ' ')}."
        unlock_steps = [f"Attain {accepted_qual.replace('_', ' ')} credential before enrollment."]

    # Requirement Checklist
    checklist: List[ChecklistItem] = []

    # 1. Entry Qualification
    checklist.append(
        ChecklistItem(
            name="Entry Qualification",
            requirement=f"Accepts: {(accepted_qual or 'Varies').replace('_', ' ')}",
            student_value=held_qual.replace('_', ' '),
            status="MET" if (accepted_qual == held_qual or route_status == "OPEN") else "GAP",
            explanation="Your current schooling status vs published entry qualification.",
        )
    )

    # 2. GPA Requirement
    gpa_min = getattr(row, "gpa_minimum", None)
    gpa_scale = getattr(row, "gpa_scale", None)
    if gpa_min is not None:
        if payload.gpa is not None:
            grade_check = check_grade(
                student_gpa=payload.gpa,
                student_scale=payload.gpa_scale,
                min_gpa=gpa_min,
                min_scale=gpa_scale,
            )
            checklist.append(
                ChecklistItem(
                    name="Academic Grade Average",
                    requirement=f"{gpa_min} out of {gpa_scale or 'stated scale'}",
                    student_value=f"{payload.gpa} out of {payload.gpa_scale or 'unknown scale'}",
                    status="MET" if grade_check.verdict == "meets" else "GAP",
                    explanation=grade_check.explanation,
                )
            )
        else:
            checklist.append(
                ChecklistItem(
                    name="Academic Grade Average",
                    requirement=f"{gpa_min} out of {gpa_scale or 'stated scale'}",
                    student_value=None,
                    status="UNKNOWN",
                    explanation="You have not entered a grade average. Check if your grade clears this bar.",
                )
            )
    else:
        checklist.append(
            ChecklistItem(
                name="Academic Grade Average",
                requirement="No minimum grade stated",
                student_value=f"{payload.gpa}" if payload.gpa else None,
                status="UNKNOWN",
                explanation="The university admissions page did not publish a cutoff grade.",
            )
        )

    # 3. Language Requirement
    lang_test = getattr(row, "language_test", None)
    lang_min = getattr(row, "language_minimum_score", None)
    if lang_test:
        student_score = None
        st_val = "Not entered"
        status_lang = "UNKNOWN"
        if lang_test.upper() == "IELTS" and payload.ielts is not None:
            student_score = payload.ielts
            st_val = f"IELTS {payload.ielts}"
            status_lang = "MET" if (lang_min is None or payload.ielts >= lang_min) else "GAP"
        elif lang_test.upper() == "TOEFL" and payload.toefl is not None:
            student_score = payload.toefl
            st_val = f"TOEFL {payload.toefl}"
            status_lang = "MET" if (lang_min is None or payload.toefl >= lang_min) else "GAP"

        checklist.append(
            ChecklistItem(
                name="Language Proficiency",
                requirement=f"{lang_test} {lang_min if lang_min else '(score not stated)'}",
                student_value=st_val if student_score is not None else None,
                status=status_lang,
                explanation=f"Tested against {lang_test} benchmark." if student_score else "No matching test score entered.",
            )
        )
    else:
        checklist.append(
            ChecklistItem(
                name="Language Proficiency",
                requirement="Not stated on the source page",
                student_value=f"IELTS {payload.ielts}" if payload.ielts else None,
                status="UNKNOWN",
                explanation="The official admissions page did not state a language minimum. Not 'none required'.",
            )
        )

    # 4. Entrance Exam
    exam_name = getattr(row, "entrance_exam", None)
    exam_min = getattr(row, "entrance_exam_minimum", None)
    if exam_name:
        status_exam = "UNKNOWN"
        student_ex_val = None
        if "SAT" in exam_name.upper() and payload.sat:
            student_ex_val = f"SAT {payload.sat}"
            status_exam = "MET" if (not exam_min or payload.sat >= exam_min) else "GAP"
        elif "YÖS" in exam_name.upper() and payload.tr_yos:
            student_ex_val = f"TR-YÖS {payload.tr_yos}"
            status_exam = "MET" if (not exam_min or payload.tr_yos >= exam_min) else "GAP"
        elif "TESTAS" in exam_name.upper() and payload.test_as:
            student_ex_val = f"TestAS {payload.test_as}"
            status_exam = "MET" if (not exam_min or payload.test_as >= exam_min) else "GAP"

        checklist.append(
            ChecklistItem(
                name="Entrance Examination",
                requirement=f"{exam_name} {exam_min if exam_min else ''}".strip(),
                student_value=student_ex_val,
                status=status_exam,
                explanation=f"{exam_name} benchmark evaluation.",
            )
        )

    # 5. Foundation Requirement
    found_req = getattr(row, "foundation_required", None)
    if found_req is not None:
        checklist.append(
            ChecklistItem(
                name="Preparatory / Foundation Year",
                requirement="Mandatory before degree" if found_req else "Direct entry possible",
                student_value="Completed foundation" if held_qual == "foundation_year" else "Attestat / School-leaver",
                status="MET" if (not found_req or held_qual in ("foundation_year", "one_year_university")) else "GAP",
                explanation=getattr(row, "foundation_providers", None) or "Check recognized preparatory course providers.",
            )
        )

    # Alternatives along open routes
    alternatives = [
        {"university_name": "Bogazici University", "country_code": "TR", "reason": "Direct attestat accepted, Turkey #1 destination"},
        {"university_name": "Istanbul Technical University", "country_code": "TR", "reason": "Direct attestat accepted, low tuition"},
        {"university_name": "University of Warsaw", "country_code": "PL", "reason": "Direct attestat accepted with apostille"},
    ]

    return TargetGapResponse(
        found=True,
        university_name=getattr(row, "university_name", payload.university_name),
        program_name=getattr(row, "program_name", "Degree Programme"),
        level=getattr(row, "level", payload.level),
        country_code=c_code,
        route_status=route_status,
        route_gap_statement=gap_statement,
        unlock_steps=unlock_steps,
        unlock_time_months=unlock_months,
        unlock_cost_azn_low=cost_low,
        unlock_cost_azn_high=cost_high,
        checklist=checklist,
        application_portal=getattr(row, "application_portal", None),
        application_deadline=str(getattr(row, "application_deadline", "")) or None,
        application_fee=getattr(row, "application_fee", None),
        currency=getattr(row, "currency", None),
        documents_required=getattr(row, "documents_required", None),
        alternatives=alternatives,
        provenance=getattr(row, "provenance", "claude-extracted"),
        source_url=getattr(row, "source_url", ""),
        last_checked=str(getattr(row, "last_checked", "")) or None,
        notes=getattr(row, "notes", None),
    )

class ProcessStepResponse(BaseModel):
    """One act the student performs on a document, with the page that requires it."""
    key: str
    title: str
    detail: str
    # 'before_applying' | 'after_offer' | 'after_graduation'. Not a date: the deadline
    # belongs to the programme row, and a step's position is stable while a deadline is not.
    when: str
    authority: str
    citation: str
    provenance: str
    last_checked: str


class RouteProcessResponse(BaseModel):
    """The paperwork for one route, or a statement that nobody has collected it.

    `status` is the field the client must branch on. `not_collected` with an empty `steps`
    means our catalogue has a gap, NEVER that the route needs no documents -- rendering the
    two the same way is the blank-means-permission error (ADR-0004).
    """
    route_key: str
    country_code: str
    level: str
    status: str
    steps: List[ProcessStepResponse]
    # Procedures we believe exist but could not verify. Show them; never state one as a
    # requirement. Kept apart from `steps` so the distinction survives to the screen.
    known_gaps: List[str]
    note: str


@router.get(
    "/{route_key}/process",
    response_model=RouteProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="The document legalisation and recognition steps for one route",
)
async def route_process(route_key: str) -> RouteProcessResponse:
    """What a student must do to their Azerbaijani documents to use them on this route.

    Curated data, so it answers with no language model and no API key -- the same reason
    `/parse` exists. It deliberately does not restate the visa deposit (on the route), the
    portal and deadline (on the programme row) or a funder's window (on the scholarship):
    each already has one home, and a second copy drifts from it.

    404 means we hold no such route. A route we hold but have not curated answers 200 with
    `status: not_collected`, because "nobody checked" and "no such route" are different
    facts and only one of them is about the student.
    """
    key = route_key.strip().lower()
    route = next((r for r in ALL_ROUTES if r.key == key), None)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"We hold no route with key '{route_key}'.",
        )

    process = PROCESS_BY_ROUTE_KEY[route.key]
    return RouteProcessResponse(
        route_key=route.key,
        country_code=route.country_code,
        level=route.level,
        status=process.status,
        steps=[ProcessStepResponse(**vars(step)) for step in process.steps],
        known_gaps=list(process.known_gaps),
        note=process.note,
    )
