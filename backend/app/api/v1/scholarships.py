"""API Router for Global Scholarship Engine & Qualification Assessment.

Provides endpoints for exploring, searching, and evaluating international and bilateral
scholarship programs (Chevening, Fulbright, Türkiye Bursları, Stipendium Hungaricum,
Italian DSU, DAAD, Eiffel France, NAWA Poland, CSC China, Erasmus Mundus, GREAT, etc.).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.domain.global_scholarships import (
    ALL_GLOBAL_SCHOLARSHIPS,
    FundingTier,
    FundingType,
    GlobalScholarship,
    GlobalScholarshipEvaluation,
    ScholarshipStatus,
    StudentScholarshipProfile,
    evaluate_all_scholarships,
    evaluate_scholarship,
)

router = APIRouter(prefix="/scholarships", tags=["Global Scholarships"])


# ==============================================================================
# SCHEMAS
# ==============================================================================

class ScholarshipBrief(BaseModel):
    key: str
    name: str
    native_name: str
    provider: str
    tier: str
    country_code: Optional[str]
    country_name: str
    degree_levels: List[str]
    funding_type: str
    coverage_summary: str
    stipend_monthly_local: Optional[str]
    stipend_monthly_azn_approx: Optional[float]
    tuition_coverage_pct: float
    travel_covered: bool
    housing_covered: bool
    health_insurance_covered: bool
    return_service_obligation: Optional[str]
    min_gpa: Optional[float]
    min_ielts: Optional[float]
    min_toefl: Optional[int]
    age_limit_bachelor: Optional[int]
    age_limit_master: Optional[int]
    work_experience_hours: Optional[int]
    financial_need_based: bool
    application_window_start: str
    application_window_end: str
    official_portal_url: str
    azerbaijan_quota_or_seats: Optional[str]


class ScholarshipDetail(ScholarshipBrief):
    official_guidelines_url: Optional[str]
    min_gpa_scale: Optional[str]
    max_household_income_eur: Optional[float]
    eligibility_criteria: List[str]
    required_documents: List[str]
    selection_stages: List[str]
    citation: str
    provenance: str


class ScholarshipListResponse(BaseModel):
    total_count: int
    items: List[ScholarshipBrief]
    available_countries: List[str]
    available_degree_levels: List[str]
    available_funding_types: List[str]


class ScholarshipEvaluationRequest(BaseModel):
    level_sought: str = Field("master", description="bachelor, master, or phd")
    age: Optional[int] = Field(None, ge=14, le=75, description="Candidate current age in years")
    gpa: Optional[float] = Field(None, ge=0.0, le=100.0, description="Cumulative grade average")
    gpa_scale: str = Field("4.0", description="4.0, 5.0, or 100")
    ielts: Optional[float] = Field(None, ge=0.0, le=9.0, description="IELTS Academic overall band")
    toefl: Optional[int] = Field(None, ge=0, le=120, description="TOEFL iBT total score")
    dim_score: Optional[float] = Field(None, ge=0.0, le=700.0, description="DİM national entrance score (0-700)")
    work_experience_hours: Optional[int] = Field(None, ge=0, le=50000, description="Documented professional hours")
    employer: Optional[str] = Field(None, description="Current employer organization name")
    is_azerbaijani_citizen: bool = Field(True, description="Citizen of the Republic of Azerbaijan")
    family_household_income_azn: Optional[float] = Field(None, ge=0.0, description="Annual household income in AZN (for DSU need check)")
    target_country_codes: List[str] = Field(default_factory=list, description="Target destination country codes (e.g. ['GB', 'DE'])")


class EvaluationItemResponse(BaseModel):
    scholarship: ScholarshipBrief
    status: ScholarshipStatus
    gates_met: List[str]
    gates_missing: List[str]
    gates_blocked: List[str]
    gates_unknown: List[str]
    summary_verdict: str


class ScholarshipEvaluationResponse(BaseModel):
    profile_summary: Dict[str, Any]
    total_evaluated: int
    open_count: int
    unlockable_count: int
    blocked_count: int
    results: List[EvaluationItemResponse]


# Helper to convert domain GlobalScholarship into Pydantic schema
def _to_brief(s: GlobalScholarship) -> ScholarshipBrief:
    return ScholarshipBrief(
        key=s.key,
        name=s.name,
        native_name=s.native_name,
        provider=s.provider,
        tier=s.tier.value,
        country_code=s.country_code,
        country_name=s.country_name,
        degree_levels=list(s.degree_levels),
        funding_type=s.funding_type.value,
        coverage_summary=s.coverage_summary,
        stipend_monthly_local=s.stipend_monthly_local,
        stipend_monthly_azn_approx=s.stipend_monthly_azn_approx,
        tuition_coverage_pct=s.tuition_coverage_pct,
        travel_covered=s.travel_covered,
        housing_covered=s.housing_covered,
        health_insurance_covered=s.health_insurance_covered,
        return_service_obligation=s.return_service_obligation,
        min_gpa=s.min_gpa,
        min_ielts=s.min_ielts,
        min_toefl=s.min_toefl,
        age_limit_bachelor=s.age_limit_bachelor,
        age_limit_master=s.age_limit_master,
        work_experience_hours=s.work_experience_hours,
        financial_need_based=s.financial_need_based,
        application_window_start=s.application_window_start,
        application_window_end=s.application_window_end,
        official_portal_url=s.official_portal_url,
        azerbaijan_quota_or_seats=s.azerbaijan_quota_or_seats,
    )


def _to_detail(s: GlobalScholarship) -> ScholarshipDetail:
    brief = _to_brief(s)
    return ScholarshipDetail(
        **brief.model_dump(),
        official_guidelines_url=s.official_guidelines_url,
        min_gpa_scale=s.min_gpa_scale,
        max_household_income_eur=s.max_household_income_eur,
        eligibility_criteria=list(s.eligibility_criteria),
        required_documents=list(s.required_documents),
        selection_stages=list(s.selection_stages),
        citation=s.citation,
        provenance=s.provenance,
    )


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@router.get("", response_model=ScholarshipListResponse)
async def list_scholarships(
    country: Optional[str] = Query(None, description="Filter by country code (e.g. GB, DE, US, TR, HU, IT, FR, PL, CN, AZ)"),
    degree_level: Optional[str] = Query(None, description="bachelor, master, or phd"),
    funding_type: Optional[str] = Query(None, description="fully_funded, tuition_reduction, etc."),
    tier: Optional[str] = Query(None, description="azerbaijani_state, destination_government, etc."),
    search: Optional[str] = Query(None, description="Search query string"),
):
    """Lists and filters global and bilateral scholarships accessible to Azerbaijani students."""
    filtered: List[GlobalScholarship] = list(ALL_GLOBAL_SCHOLARSHIPS)

    if country:
        country_cf = country.casefold()
        filtered = [s for s in filtered if (s.country_code and s.country_code.casefold() == country_cf) or (country_cf in s.country_name.casefold())]

    if degree_level:
        lvl_cf = degree_level.casefold()
        filtered = [s for s in filtered if lvl_cf in s.degree_levels]

    if funding_type:
        ft_cf = funding_type.casefold()
        filtered = [s for s in filtered if s.funding_type.value.casefold() == ft_cf]

    if tier:
        tier_cf = tier.casefold()
        filtered = [s for s in filtered if s.tier.value.casefold() == tier_cf]

    if search:
        q = search.casefold()
        filtered = [
            s for s in filtered
            if q in s.name.casefold()
            or q in s.native_name.casefold()
            or q in s.provider.casefold()
            or q in s.country_name.casefold()
            or q in s.coverage_summary.casefold()
        ]

    countries = sorted(list({s.country_name for s in ALL_GLOBAL_SCHOLARSHIPS}))
    degrees = ["bachelor", "master", "phd"]
    funding_types = [ft.value for ft in FundingType]

    return ScholarshipListResponse(
        total_count=len(filtered),
        items=[_to_brief(s) for s in filtered],
        available_countries=countries,
        available_degree_levels=degrees,
        available_funding_types=funding_types,
    )


@router.get("/{key_or_id}", response_model=ScholarshipDetail)
async def get_scholarship_detail(key_or_id: str):
    """Retrieves full specification, selection stages, and criteria for a specific scholarship."""
    target_key = key_or_id.strip().lower()
    for s in ALL_GLOBAL_SCHOLARSHIPS:
        if s.key.lower() == target_key or str(s.key).lower() == target_key:
            return _to_detail(s)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Scholarship with key '{key_or_id}' was not found in the global catalogue.",
    )


@router.post("/evaluate", response_model=ScholarshipEvaluationResponse)
async def evaluate_student_scholarships(payload: ScholarshipEvaluationRequest):
    """Evaluates student qualifications against discrete statutory gates for all scholarships.

    Returns discrete verdicts (OPEN / UNLOCKABLE / BLOCKED) with honest diagnostics.
    """
    profile = StudentScholarshipProfile(
        level_sought=payload.level_sought,
        age=payload.age,
        gpa=payload.gpa,
        gpa_scale=payload.gpa_scale,
        ielts=payload.ielts,
        toefl=payload.toefl,
        dim_score=payload.dim_score,
        work_experience_hours=payload.work_experience_hours,
        employer=payload.employer,
        is_azerbaijani_citizen=payload.is_azerbaijani_citizen,
        family_household_income_azn=payload.family_household_income_azn,
        target_country_codes=tuple(payload.target_country_codes),
    )

    evaluations = evaluate_all_scholarships(profile)

    results: List[EvaluationItemResponse] = []
    open_count = 0
    unlockable_count = 0
    blocked_count = 0

    for ev in evaluations:
        if ev.status == ScholarshipStatus.OPEN:
            open_count += 1
        elif ev.status == ScholarshipStatus.UNLOCKABLE:
            unlockable_count += 1
        else:
            blocked_count += 1

        results.append(
            EvaluationItemResponse(
                scholarship=_to_brief(ev.scholarship),
                status=ev.status,
                gates_met=list(ev.gates_met),
                gates_missing=list(ev.gates_missing),
                gates_blocked=list(ev.gates_blocked),
                gates_unknown=list(ev.gates_unknown),
                summary_verdict=ev.summary_verdict,
            )
        )

    profile_summary = {
        "level_sought": payload.level_sought,
        "age": payload.age,
        "gpa": f"{payload.gpa} ({payload.gpa_scale})" if payload.gpa else None,
        "ielts": payload.ielts,
        "toefl": payload.toefl,
        "dim_score": payload.dim_score,
        "work_experience_hours": payload.work_experience_hours,
        "employer": payload.employer,
    }

    return ScholarshipEvaluationResponse(
        profile_summary=profile_summary,
        total_evaluated=len(results),
        open_count=open_count,
        unlockable_count=unlockable_count,
        blocked_count=blocked_count,
        results=results,
    )
