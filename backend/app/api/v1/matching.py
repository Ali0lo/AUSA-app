from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.schemas.matching import MatchResult, ProgramRequirements, StudentProfile
from app.services.matching.engine import evaluate_match

router = APIRouter(prefix="/matching", tags=["Deterministic Matching Engine"])


class EvaluateMatchRequest(BaseModel):
    """Request payload combining student profile and target program requirements."""
    student: StudentProfile = Field(..., description="Student academic parameters and preferences")
    program: ProgramRequirements = Field(..., description="Target university program requirements")


@router.post(
    "/evaluate",
    response_model=MatchResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Program Match",
    description=(
        "Calculate a 100% deterministic, explainable match score between a student profile "
        "and university program requirements. Evaluates hard filters (degree level mismatch) "
        "and soft ranking weights (Academics: 50%, Budget: 30%, Language: 20%)."
    )
)
async def evaluate_program_match(payload: EvaluateMatchRequest) -> MatchResult:
    """
    Evaluate student profile eligibility and compute factor score breakdowns.
    """
    try:
        match_result = evaluate_match(student=payload.student, program=payload.program)
        return match_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating match: {str(e)}"
        )
