"""
API Endpoints for Exporting Application Dossiers and Motivation Letters to PDF.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.program import Program as ProgramModel
from app.models.student import Student as StudentModel
from app.services.pdf_export import generate_application_dossier_pdf

router = APIRouter(prefix="/export", tags=["Export Services"])


class ExportMotivationLetterPayload(BaseModel):
    """Payload for generating application dossier PDF."""
    student_id: Optional[int] = Field(None, description="Optional student account ID")
    program_id: Optional[int] = Field(None, description="Optional target program ID")
    motivation_letter_text: str = Field(..., description="Full text content of motivation letter / SOP")
    student_data: Optional[Dict[str, Any]] = Field(None, description="Override student profile dictionary")
    program_data: Optional[Dict[str, Any]] = Field(None, description="Override program data dictionary")


@router.post(
    "/motivation-letter/pdf",
    response_class=Response,
    status_code=status.HTTP_200_OK,
    summary="Export Motivation Letter & Application Dossier PDF",
    description="Renders a binary PDF dossier containing student profile metrics, target program checklist, and formatted motivation letter."
)
async def export_motivation_letter_pdf(
    payload: ExportMotivationLetterPayload,
    db: AsyncSession = Depends(get_db)
) -> Response:
    """Generate and return binary PDF application dossier."""
    student_dict: Optional[Dict[str, Any]] = payload.student_data
    program_dict: Optional[Dict[str, Any]] = payload.program_data

    if payload.student_id:
        try:
            stmt = select(StudentModel).where(StudentModel.id == payload.student_id)
            res = await db.execute(stmt)
            st = res.scalar_one_or_none()
        except Exception as exc:
            # A profile we could not read is not a profile we may invent.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot reach the student store; no dossier was generated.",
            ) from exc
        if st is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No student with id {payload.student_id}.",
            )
        student_dict = {
            "email": st.email,
            "gpa": st.gpa,
            "ielts": st.ielts,
            "toefl": st.toefl,
            "degree_level": st.degree_level,
            "field_of_study": st.field_of_study,
        }

    if payload.program_id:
        try:
            stmt = select(ProgramModel).where(ProgramModel.id == payload.program_id)
            res = await db.execute(stmt)
            pr = res.scalar_one_or_none()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot reach the programs store; no dossier was generated.",
            ) from exc
        if pr is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No programme with id {payload.program_id}.",
            )
        program_dict = {
            "university_name": pr.university_name,
            "program_name": pr.program_name,
            "degree_level": pr.degree_level,
            "country": pr.country,
            "tuition_fee": pr.tuition_fee,
            "deadline": str(pr.deadline) if pr.deadline else None,
        }

    # A dossier is a document the student submits under their own name. Filling either half
    # of it with a plausible default -- gpa 3.65, a TU Munich programme, an 11208 EUR
    # blocked account -- is the fabrication ADR-0004 forbids, and it is worse here than in
    # the pipeline because the output leaves the building.
    #
    # We do not require every field: a student legitimately has no TOEFL score, and a gate
    # that rejects every honest partial profile would be as unusable as one that fabricates
    # data. Missing fields render "Not stated" instead. But the dossier is *about* a specific
    # programme, so the programme half must at least name that programme.
    has_named_program = bool(
        program_dict
        and str(program_dict.get("university_name") or "").strip()
        and str(program_dict.get("program_name") or "").strip()
    )
    if not student_dict or not has_named_program:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "A dossier needs both a student and a named programme. Supply student_data "
                "or a resolvable student_id, and program_data with university_name and "
                "program_name (or a resolvable program_id)."
            ),
        )

    pdf_bytes = generate_application_dossier_pdf(
        student_data=student_dict,
        program_data=program_dict,
        motivation_letter=payload.motivation_letter_text,
    )

    filename = "AUSA_Application_Dossier.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )

