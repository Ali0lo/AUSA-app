from datetime import datetime, timezone
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure backend root is in sys.path
backend_dir = str(Path(__file__).parent.parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.program import Program as ProgramModel
from app.models.student import Student

router = APIRouter(prefix="/admin", tags=["Admin Curation & Data Verification"])


# -------------------------------------------------------------
# Admin Security Dependency
# -------------------------------------------------------------
async def require_admin_user(
    current_user: Student = Depends(get_current_user),
) -> Student:
    """Admit only an authenticated student whose email is on the allowlist.

    Authentication is delegated to get_current_user (raises 401 on a bad or unknown
    token). Authorisation is an explicit allowlist in settings.ADMIN_EMAILS.

    This previously returned {"is_admin": True} for every caller, so the entire admin
    surface -- including the endpoint that publishes unverified programme data to
    students -- was open to anyone who could reach the API. Fail-closed: an empty or
    misconfigured allowlist denies everyone rather than opening the curation endpoints
    -- which mark scraped programs as human-verified, the guardrail data-sourcing.md
    requires before data reaches a student -- to the world.
    """
    allowed = {email.strip().lower() for email in settings.ADMIN_EMAILS if email.strip()}
    if not current_user.email or current_user.email.strip().lower() not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required for this endpoint.",
        )
    return current_user


# -------------------------------------------------------------
# Request & Response Schemas
# -------------------------------------------------------------
class FlaggedProgramResponse(BaseModel):
    """Schema representing a flagged program record requiring human curation."""
    id: int
    university_name: str
    program_name: str
    degree_level: Optional[str] = None
    field: Optional[str] = None
    country: Optional[str] = None
    min_gpa: Optional[float] = None
    min_ielts: Optional[float] = None
    tuition_fee: Optional[float] = None
    currency: str = "USD"
    # Nullable: a record nobody scored has no confidence. The reviewer must be able to tell
    # "not scored" from a low score, so this stays None rather than collapsing to a number.
    confidence_score: Optional[float] = None
    verification_status: str
    extraction_notes: Optional[str] = None
    source_url: Optional[str] = None
    dim_score_required: Optional[int] = None
    blocked_account_eur: Optional[float] = None
    requires_studienkolleg: Optional[bool] = None


class VerifyProgramPayload(BaseModel):
    """Payload submitted by admin to correct and verify a flagged program."""
    university_name: Optional[str] = Field(None, description="Corrected university name")
    program_name: Optional[str] = Field(None, description="Corrected program name")
    degree_level: Optional[str] = Field(None, description="Corrected degree level")
    field: Optional[str] = Field(None, description="Corrected field of study")
    country: Optional[str] = Field(None, description="Corrected country")
    min_gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Corrected minimum GPA")
    min_ielts: Optional[float] = Field(None, ge=0.0, le=9.0, description="Corrected minimum IELTS score")
    tuition_fee: Optional[float] = Field(None, ge=0.0, description="Corrected annual tuition fee")
    currency: Optional[str] = Field("USD", description="Tuition currency")
    dim_score_required: Optional[int] = Field(None, ge=0, le=700, description="Corrected DIM score requirement")
    blocked_account_eur: Optional[float] = Field(None, ge=0.0, description="Corrected German blocked account requirement")
    requires_studienkolleg: Optional[bool] = Field(None, description="Corrected Studienkolleg requirement")


class VerifyProgramResponse(BaseModel):
    """Response confirming successful verification and publishing of program."""
    message: str
    program_id: int
    verification_status: str
    verified_by: str
    last_updated: str
    program_details: Dict[str, Any]


class SeedDatabaseResponse(BaseModel):
    """Response schema summarizing database seeding output."""
    status: str
    programs_seeded: int
    scholarships_seeded: int
    documents_seeded: int
    message: str


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@router.get(
    "/programs/flagged",
    response_model=List[FlaggedProgramResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Flagged Programs for Review",
    description="Retrieve all university program records with confidence_score < 85% flagged for human curation."
)
async def get_flagged_programs(
    admin: Student = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db)
) -> List[FlaggedProgramResponse]:
    """Query and return all programs flagged for human review."""
    try:
        stmt = select(ProgramModel).where(ProgramModel.verification_status == "flagged_for_review")
        result = await db.execute(stmt)
        db_programs = list(result.scalars().all())

        if db_programs:
            return [
                FlaggedProgramResponse(
                    id=p.id,
                    university_name=p.university_name,
                    program_name=p.program_name,
                    degree_level=p.degree_level,
                    field=p.field,
                    country=p.country,
                    min_gpa=p.min_gpa,
                    min_ielts=p.min_ielts,
                    tuition_fee=p.tuition_fee,
                    currency=p.currency or "USD",
                    # Not `or 70.0`: that invented a score for unscored rows, and because
                    # 0.0 is falsy it also rewrote a genuine zero-confidence record as 70.
                    confidence_score=p.confidence_score,
                    verification_status=p.verification_status or "flagged_for_review",
                    extraction_notes=p.requirements_text,
                    source_url=p.source_url,
                )
                for p in db_programs
            ]

        # An empty queue is a real answer and is returned as one. This used to fall through
        # to DEMO_FLAGGED_PROGRAMS, so a reviewer with an empty database was shown four
        # invented programmes -- Heidelberg, TUM and the rest -- as though they were records
        # awaiting their approval. The human-in-the-loop safeguard cannot itself be a source
        # of fabricated data.
        return []

    except Exception as exc:
        # And a database that cannot be read is an outage, not an empty queue. Serving demo
        # rows here hid the outage behind plausible content.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot read the review queue; the programs store is unavailable.",
        ) from exc


@router.put(
    "/programs/{program_id}/verify",
    response_model=VerifyProgramResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve & Publish Corrected Program",
    description="Update corrected program attributes and change verification_status to 'verified'."
)
async def verify_and_approve_program(
    program_id: int,
    payload: VerifyProgramPayload,
    admin: Student = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db)
) -> VerifyProgramResponse:
    """Correct and verify a program record, changing status to 'verified'."""
    now_iso = datetime.now(timezone.utc).isoformat()
    # The signed-in administrator is the authority on who verified a row.
    verified_by_email = admin.email

    try:
        stmt = select(ProgramModel).where(ProgramModel.id == program_id)
        result = await db.execute(stmt)
        prog = result.scalar_one_or_none()
    except Exception as exc:
        # A write that could not be attempted is not a verification. This used to be
        # `except Exception: pass` followed by an unconditional success response.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot reach the programs store; nothing was verified.",
        ) from exc

    if prog is None:
        # A programme we do not hold cannot be verified. The endpoint previously answered
        # "successfully verified and published" here -- for ids 1001-1004 from an in-memory
        # demo list, and for every other unknown id from a trailing success response.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No programme with id {program_id}.",
        )

    if payload.university_name: prog.university_name = payload.university_name
    if payload.program_name: prog.program_name = payload.program_name
    if payload.degree_level: prog.degree_level = payload.degree_level
    if payload.field: prog.field = payload.field
    if payload.country: prog.country = payload.country
    if payload.min_gpa is not None: prog.min_gpa = payload.min_gpa
    if payload.min_ielts is not None: prog.min_ielts = payload.min_ielts
    if payload.tuition_fee is not None: prog.tuition_fee = payload.tuition_fee
    if payload.currency: prog.currency = payload.currency

    prog.verification_status = "verified"
    prog.confidence_score = 100.0
    prog.verified_by = verified_by_email

    try:
        await db.commit()
    except Exception as exc:
        # Only a commit that did not happen is a failed write. Guarding refresh() here
        # too would let a post-commit error (the write already persisted) come back as
        # the same 503 as a genuine failed write -- a false failure, the mirror image
        # of the false success this endpoint used to report.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The verification could not be saved.",
        ) from exc

    await db.refresh(prog)

    return VerifyProgramResponse(
        message=f"Program '{prog.program_name}' verified in the database.",
        program_id=program_id,
        verification_status="verified",
        verified_by=verified_by_email,
        last_updated=now_iso,
        program_details={
            "id": prog.id,
            "university_name": prog.university_name,
            "program_name": prog.program_name,
            "tuition_fee": prog.tuition_fee,
            "min_gpa": prog.min_gpa,
            "min_ielts": prog.min_ielts,
        },
    )


@router.post(
    "/seed",
    response_model=SeedDatabaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Populate Database Fixtures",
    description="Seed baseline universities, programs, scholarships, and RAG document vector chunks."
)
async def seed_database_endpoint(
    admin: Student = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db)
) -> SeedDatabaseResponse:
    """Trigger background seeding routine for baseline universities, programs, and scholarships."""
    try:
        from scripts.seed_db import seed_database
        summary = await seed_database(db)
        return SeedDatabaseResponse(**summary)
    except Exception as exc:
        # A seed that failed did not seed anything. This used to return status="success"
        # with counts of 7/3/3 that nobody had written, so a broken seeder looked healthy.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database seeding failed: {exc}",
        ) from exc
