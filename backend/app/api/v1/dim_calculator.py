"""FastAPI router for DİM 700-point score simulation and specialty recommendation.

Endpoints:
- GET  /api/v1/dim/groups: Statutory structure of Groups I, II, III, IV, V and sub-groups.
- GET  /api/v1/dim/default-inputs: Default subject question templates for given group/sub-group.
- POST /api/v1/dim/calculate: Evaluates question counts or direct scores into 700-point breakdown.
- POST /api/v1/dim/recommend: Cross-references candidate score against 2,578 historical DİM cutoffs.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.dim_calculator import (
    BlokInput,
    BuraxilisInput,
    ChanceLevel,
    DimCalculationRequest,
    DimGroup,
    DimRecommendationResponse,
    DimScoreBreakdown,
    SubGroup,
    calculate_total_dim_score,
    get_all_dim_group_metadata,
    get_default_blok_input,
    get_specialty_recommendations,
    load_cutoff_history_records,
)
from app.models.cutoff_history import ProgramCutoffHistory

router = APIRouter(prefix="/dim", tags=["dim-calculator"])


class RecommendRequest(BaseModel):
    """Payload for finding matching specialties."""
    group: DimGroup = Field(default=DimGroup.GROUP_1, description="DİM group")
    subgroup: SubGroup = Field(default=SubGroup.RI, description="Sub-group code")
    candidate_score: Optional[float] = Field(default=None, ge=0.0, le=700.0, description="Total score out of 700")
    calculation_request: Optional[DimCalculationRequest] = Field(
        default=None, description="Optional raw calculation request if score not yet calculated"
    )
    university_filter: Optional[str] = Field(default=None, description="Filter by university name (e.g. ADA, BANM)")
    chance_filter: Optional[ChanceLevel] = Field(default=None, description="Filter by SAFE, REALISTIC, TARGET")
    search_query: Optional[str] = Field(default=None, description="Search specialty or faculty title")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum number of recommendations to return")


@router.get(
    "/groups",
    summary="Get statutory DİM group metadata",
    response_model=List[Dict[str, Any]],
)
async def get_dim_groups() -> List[Dict[str, Any]]:
    """Returns statutory specifications for all 5 DİM admission groups, including sub-groups,

    maximum weights, and scoring rules.
    """
    return get_all_dim_group_metadata()


@router.get(
    "/default-inputs",
    summary="Get default subject question template for group and subgroup",
    response_model=Dict[str, Any],
)
async def get_default_inputs(
    group: DimGroup = Query(default=DimGroup.GROUP_1, description="DİM Group"),
    subgroup: SubGroup = Query(default=SubGroup.RI, description="Sub-group specialization"),
) -> Dict[str, Any]:
    """Returns the default Buraxılış and Blok subject structures for frontend state initialization."""
    buraxilis = BuraxilisInput()
    blok = get_default_blok_input(group, subgroup)
    return {
        "group": group.value,
        "subgroup": subgroup.value,
        "buraxilis": buraxilis.model_dump(),
        "blok": blok.model_dump(),
    }


@router.post(
    "/calculate",
    summary="Calculate 700-point DİM score from question counts or direct scores",
    response_model=DimScoreBreakdown,
)
async def calculate_score(req: DimCalculationRequest) -> DimScoreBreakdown:
    """Calculates official DİM score out of 700:

    - Buraxılış exam scaled to 300 points (Ana Dili 100, Riyaziyyat 100, Xarici Dil 100).
    - Blok exam scaled to 400 points with group-specific subject weights (150, 150, 100).
    - 4-wrong-penalty rule applied to closed questions.
    - Flags BHOS 650+ full scholarship benchmark clearance.
    """
    try:
        return calculate_total_dim_score(req)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error calculating DİM score: {str(err)}",
        )


@router.post(
    "/recommend",
    summary="Match candidate score against historical DİM admission cutoffs",
    response_model=DimRecommendationResponse,
)
async def recommend_specialties(
    req: RecommendRequest,
    db: AsyncSession = Depends(get_db),
) -> DimRecommendationResponse:
    """Cross-references candidate score against the 2,578 historical DİM cutoff records in database.

    Organizes opportunities into SAFE, REALISTIC, TARGET, and ASPIRATIONAL tiers,
    highlighting 3-year historical trends and the Baku Higher Oil School 650+ benchmark.
    """
    # 1. Determine candidate score breakdown
    if req.calculation_request is not None:
        score_breakdown = calculate_total_dim_score(req.calculation_request)
    elif req.candidate_score is not None:
        calc_req = DimCalculationRequest(group=req.group, subgroup=req.subgroup)
        # Approximate 40/60 split between Buraxılış and Blok for breakdown visualization
        buraxilis_pts = min(300.0, req.candidate_score * (300.0 / 700.0))
        blok_pts = min(400.0, req.candidate_score - buraxilis_pts)
        calc_req.buraxilis.direct_total_score = buraxilis_pts
        calc_req.blok = get_default_blok_input(req.group, req.subgroup)
        calc_req.blok.direct_total_score = blok_pts
        score_breakdown = calculate_total_dim_score(calc_req)
        # Force exact score
        score_breakdown.total_score = round(req.candidate_score, 1)
        score_breakdown.clears_bhos_benchmark = req.candidate_score >= 650.0
        score_breakdown.passed_competition_minimum = req.candidate_score >= 150.0
    else:
        # Default zero score
        calc_req = DimCalculationRequest(group=req.group, subgroup=req.subgroup)
        score_breakdown = calculate_total_dim_score(calc_req)

    # 2. Query cutoff records: try DB first, fallback to cached CSV
    records: Optional[List[Dict[str, Any]]] = None
    try:
        stmt = (
            select(ProgramCutoffHistory)
            .where(ProgramCutoffHistory.country == "AZ")
            .where(ProgramCutoffHistory.score_type == req.group.value)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()
        if rows:
            records = [
                {
                    "program_code": r.source_program_code,
                    "university_name": r.university_name,
                    "department_name": r.department_name or "",
                    "score_type": r.score_type or "",
                    "scholarship_type": r.scholarship_type or "dövlət sifarişli",
                    "intake_year": r.intake_year,
                    "cutoff_value": r.cutoff_value,
                }
                for r in rows
            ]
    except Exception:
        records = None

    if not records:
        records = load_cutoff_history_records()

    return get_specialty_recommendations(
        score_breakdown=score_breakdown,
        records=records,
        university_filter=req.university_filter,
        chance_filter=req.chance_filter,
        search_query=req.search_query,
        limit=req.limit,
    )
