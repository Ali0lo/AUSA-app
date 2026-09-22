"""FastAPI router for Statement of Purpose (SOP) & Academic CV rubric evaluation.

Endpoints:
- POST /api/v1/sop/analyze: Evaluates SOP essays against academic rubrics and State Programme criteria.
- POST /api/v1/sop/analyze-cv: Audits academic CVs for international graduate standards.
- GET  /api/v1/sop/templates: Returns curated exemplary SOP frameworks.
- GET  /api/v1/sop/cliches: Returns dictionary of common clichés with academic alternatives.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from app.domain.sop_analyzer import (
    CLICHE_PATTERNS,
    CURATED_SOP_TEMPLATES,
    CvAnalysisRequest,
    CvAnalysisResult,
    SopAnalysisRequest,
    SopAnalysisResult,
    SopTemplate,
    analyze_cv_text,
    analyze_sop_text,
)

router = APIRouter(prefix="/sop", tags=["sop-analyzer"])


@router.post(
    "/analyze",
    summary="Analyze Statement of Purpose / Motivation Letter",
    response_model=SopAnalysisResult,
)
async def analyze_sop(req: SopAnalysisRequest) -> SopAnalysisResult:
    """Evaluates an SOP or motivation letter across:

    - Length and paragraph cadence.
    - Cliché and formulaic phrase detection with academic rewrites.
    - Passive voice intensity and action verb density.
    - Core narrative section presence (Hook, Academic foundation, Why university, Career goals, State Programme contribution).
    - Flesch Reading Ease and lexical diversity.
    """
    try:
        return analyze_sop_text(req)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error evaluating SOP: {str(err)}",
        )


@router.post(
    "/analyze-cv",
    summary="Analyze Academic CV / Resume for international admissions standards",
    response_model=CvAnalysisResult,
)
async def analyze_cv(req: CvAnalysisRequest) -> CvAnalysisResult:
    """Audits an academic CV / Resume:

    - Section completeness (Education, Research, Experience, Skills, Honors).
    - Bullet discipline, action verb openers, and metric quantification.
    - Sensitive demographic data screening (marital status, date of birth) for US/UK compliance.
    """
    try:
        return analyze_cv_text(req)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error evaluating CV: {str(err)}",
        )


@router.get(
    "/templates",
    summary="Get curated exemplary SOP templates",
    response_model=List[SopTemplate],
)
async def get_sop_templates() -> List[SopTemplate]:
    """Returns curated, high-scoring Statement of Purpose frameworks for STEM, Data Science, and Bilateral Scholarships."""
    return CURATED_SOP_TEMPLATES


@router.get(
    "/cliches",
    summary="Get catalog of common admissions clichés and academic alternatives",
    response_model=List[Dict[str, Any]],
)
async def get_cliche_catalog() -> List[Dict[str, Any]]:
    """Returns common formulaic tropes flagged by admissions reviewers with recommendations for replacement."""
    return [
        {
            "id": idx,
            "title": title,
            "pattern": pattern,
            "recommendation": suggestion,
        }
        for idx, (pattern, title, suggestion) in enumerate(CLICHE_PATTERNS)
    ]
