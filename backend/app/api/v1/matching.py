from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.scholarship import Scholarship as ScholarshipModel
from app.schemas.matching import MatchResult, ProgramRequirements, ScholarshipSchema, StudentProfile
from app.services.matching.engine import evaluate_match

router = APIRouter(prefix="/matching", tags=["Deterministic Matching Engine"])


class EvaluateMatchRequest(BaseModel):
    """Request payload combining student profile, program requirements, and optional scholarships."""
    student: StudentProfile = Field(..., description="Student academic parameters and preferences")
    program: ProgramRequirements = Field(..., description="Target university program requirements")
    available_scholarships: Optional[List[ScholarshipSchema]] = Field(
        default=None,
        description="Optional list of available scholarships to evaluate for net-cost calculation (ADR-0005)"
    )


@router.post(
    "/evaluate",
    response_model=MatchResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Program Match",
    description=(
        "Calculate a 100% deterministic, explainable match score between a student profile "
        "and university program requirements with Scholarship-First Net-Cost Evaluation (ADR-0005). "
        "Evaluates hard filters and soft ranking weights (Academics: 50%, Net Budget: 30%, Language: 20%)."
    )
)
async def evaluate_program_match(
    payload: EvaluateMatchRequest,
    db: AsyncSession = Depends(get_db)
) -> MatchResult:
    """
    Evaluate student profile eligibility, calculate net cost after eligible scholarships,
    and compute component factor score breakdowns.
    """
    try:
        scholarships = payload.available_scholarships
        if scholarships is None:
            try:
                stmt = select(ScholarshipModel)
                conditions = []
                if payload.program.country:
                    conditions.append(ScholarshipModel.country.ilike(f"%{payload.program.country}%"))
                if payload.program.degree_level:
                    conditions.append(ScholarshipModel.degree_level.ilike(f"%{payload.program.degree_level}%"))
                if conditions:
                    stmt = stmt.where(or_(*conditions))
                result = await db.execute(stmt)
                scholarships = list(result.scalars().all())
            except Exception:
                scholarships = []

        match_result = evaluate_match(
            student=payload.student,
            program=payload.program,
            available_scholarships=scholarships
        )
        return match_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating match: {str(e)}"
        )
