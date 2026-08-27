"""
API Endpoints for Exporting Application Dossiers and Motivation Letters to PDF.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Response, status
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
    student_dict = payload.student_data or {
        "email": "student@ausa.edu.az",
        "gpa": 3.65,
        "ielts": 7.0,
        "degree_level": "master",
        "field_of_study": "Computer Science",
    }

    program_dict = payload.program_data or {
        "university_name": "Technical University of Munich (TUM)",
        "program_name": "M.Sc. Informatics",
        "degree_level": "master",
        "country": "Germany",
        "tuition_fee": 0.0,
        "blocked_account_eur": 11208.0,
        "deadline": "2026-07-15",
    }

    # If student_id or program_id provided, query database for exact entity details
    if payload.student_id:
        try:
            stmt = select(StudentModel).where(StudentModel.id == payload.student_id)
            res = await db.execute(stmt)
            st = res.scalar_one_or_none()
            if st:
                student_dict = {
                    "email": st.email,
                    "gpa": st.gpa,
                    "ielts": st.ielts,
                    "toefl": st.toefl,
                    "degree_level": st.degree_level,
                    "field_of_study": st.field_of_study,
                }
        except Exception:
            pass

    if payload.program_id:
        try:
            stmt = select(ProgramModel).where(ProgramModel.id == payload.program_id)
            res = await db.execute(stmt)
            pr = res.scalar_one_or_none()
            if pr:
                program_dict = {
                    "university_name": pr.university_name,
                    "program_name": pr.program_name,
                    "degree_level": pr.degree_level,
                    "country": pr.country,
                    "tuition_fee": pr.tuition_fee,
                    "deadline": str(pr.deadline) if pr.deadline else "Upcoming",
                }
        except Exception:
            pass

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
