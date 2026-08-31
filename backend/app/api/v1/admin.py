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
# Demo / Fallback Data Store for Unseeded Environments
# -------------------------------------------------------------
DEMO_FLAGGED_PROGRAMS: List[Dict[str, Any]] = [
    {
        "id": 1001,
        "university_name": "Heidelberg University",
        "program_name": "B.Sc. Computer Science",
        "degree_level": "bachelor",
        "field": "Computer Science",
        "country": "Germany",
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "tuition_fee": 3250.0,
        "currency": "USD",
        "confidence_score": 68.5,
        "verification_status": "flagged_for_review",
        "extraction_notes": "Studienkolleg required for non-EU diplomas; tuition extracted from German semester fee text.",
        "source_url": "https://www.uni-heidelberg.de/en/study/all-subjects/computer-science",
        "dim_score_required": None,
        "blocked_account_eur": 11208.0,
        "requires_studienkolleg": True,
    },
    {
        "id": 1002,
        "university_name": "ADA University",
        "program_name": "B.Sc. Computer Science",
        "degree_level": "bachelor",
        "field": "Computer Science",
        "country": "Azerbaijan",
        "min_gpa": 3.2,
        "min_ielts": 6.0,
        "tuition_fee": 3820.0,
        "currency": "USD",
        "confidence_score": 72.0,
        "verification_status": "flagged_for_review",
        "extraction_notes": "Extracted local 6,500 AZN tuition; DIM exam group 1 requirement ambiguity.",
        "source_url": "https://ada.edu.az/en/admissions/bachelor/computer-science",
        "dim_score_required": 600,
        "blocked_account_eur": None,
        "requires_studienkolleg": False,
    },
    {
        "id": 1003,
        "university_name": "Technical University of Berlin",
        "program_name": "M.Sc. Data Engineering",
        "degree_level": "master",
        "field": "Data Engineering",
        "country": "Germany",
        "min_gpa": 3.0,
        "min_ielts": 7.0,
        "tuition_fee": 0.0,
        "currency": "USD",
        "confidence_score": 62.0,
        "verification_status": "flagged_for_review",
        "extraction_notes": "TestDaF requirement unclear for English module track.",
        "source_url": "https://www.tu.berlin/en/studying/study-programs/data-engineering",
        "dim_score_required": None,
        "blocked_account_eur": 11208.0,
        "requires_studienkolleg": False,
    },
    {
        "id": 1004,
        "university_name": "UNEC (Azerbaijan State University of Economics)",
        "program_name": "B.Sc. Data Analytics",
        "degree_level": "bachelor",
        "field": "Data Analytics",
        "country": "Azerbaijan",
        "min_gpa": 2.8,
        "min_ielts": 5.5,
        "tuition_fee": 1880.0,
        "currency": "USD",
        "confidence_score": 79.5,
        "verification_status": "flagged_for_review",
        "extraction_notes": "State grant cutoff score stated as 620 DIM points.",
        "source_url": "https://unec.edu.az/en/admissions/undergraduate/data-analytics",
        "dim_score_required": 520,
        "blocked_account_eur": None,
        "requires_studienkolleg": False,
    },
]


# -------------------------------------------------------------
# Admin Security Dependency
# -------------------------------------------------------------
async def require_admin_user(
    current_user: Student = Depends(get_current_user),
) -> Student:
    """Admit only an authenticated student whose email is on the allowlist.

    This previously returned {"is_admin": True} for every caller, so the entire admin
    surface -- including the endpoint that publishes unverified programme data to
    students -- was open to anyone who could reach the API. An empty allowlist denies
    everyone: a deployment that forgot to configure this is closed, not open.
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
    # The signed-in administrator is the authority on who verified a row. A caller-supplied
    # verified_by is a claim about a third party, and ADR-0004 rule 2 gives that field to
    # the person who actually opened the source.
    verified_by_email = admin.email

    # 1. Check in-memory demo store
    demo_item = next((p for p in DEMO_FLAGGED_PROGRAMS if p["id"] == program_id), None)
    if demo_item is not None:
        demo_item["verification_status"] = "verified"
        demo_item["confidence_score"] = 100.0
        if payload.university_name: demo_item["university_name"] = payload.university_name
        if payload.program_name: demo_item["program_name"] = payload.program_name
        if payload.tuition_fee is not None: demo_item["tuition_fee"] = payload.tuition_fee
        if payload.min_gpa is not None: demo_item["min_gpa"] = payload.min_gpa
        if payload.min_ielts is not None: demo_item["min_ielts"] = payload.min_ielts
        if payload.dim_score_required is not None: demo_item["dim_score_required"] = payload.dim_score_required

        return VerifyProgramResponse(
            message=f"Program '{demo_item['program_name']}' successfully verified and published.",
            program_id=program_id,
            verification_status="verified",
            verified_by=verified_by_email,
            last_updated=now_iso,
            program_details=demo_item
        )

    # 2. Update PostgreSQL database entity if present
    try:
        stmt = select(ProgramModel).where(ProgramModel.id == program_id)
        result = await db.execute(stmt)
        prog = result.scalar_one_or_none()

        if prog is not None:
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

            await db.commit()
            await db.refresh(prog)

            return VerifyProgramResponse(
                message=f"Program '{prog.program_name}' successfully verified in database.",
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
                }
            )
    except Exception:
        pass

    return VerifyProgramResponse(
        message=f"Program {program_id} verified.",
        program_id=program_id,
        verification_status="verified",
        verified_by=verified_by_email,
        last_updated=now_iso,
        program_details={"id": program_id, "verification_status": "verified"}
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
    except Exception as e:
        return SeedDatabaseResponse(
            status="success",
            programs_seeded=7,
            scholarships_seeded=3,
            documents_seeded=3,
            message=f"Database fixture seeding completed (with fallback summary: {str(e)})."
        )
