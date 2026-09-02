"""
API Router for Student Application Lifecycle Tracker and Deadline Calculations.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.application import StudentApplication as ApplicationModel
from app.models.student import Student

router = APIRouter(prefix="/applications", tags=["Application Tracker & Deadlines"])


def calculate_days_remaining(deadline_val: Any) -> Tuple[Optional[int], Optional[bool]]:
    """Calculate days remaining until deadline and return (days_remaining, is_urgent).

    Returns (None, None) when the deadline is unknown or unparseable. This previously
    returned (90, False) for an unknown deadline and (30, False) for an unparseable one --
    a made-up countdown *and* a claim of "not urgent" for a deadline nobody has verified,
    on the exact field spec 5.4 calls the most damaging one to get wrong (ADR-0004).
    """
    if not deadline_val:
        return None, None
    try:
        if isinstance(deadline_val, date):
            dl_date = deadline_val
        else:
            dl_date = datetime.strptime(str(deadline_val)[:10], "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()
        delta = (dl_date - today).days
        days = max(delta, 0)
        is_urgent = days <= 14
        return days, is_urgent
    except Exception:
        # An unparseable value is unknown, not "30 days away and not urgent".
        return None, None


# -------------------------------------------------------------
# Schemas
# -------------------------------------------------------------
class ApplicationResponse(BaseModel):
    id: int
    student_id: str
    program_id: Optional[int] = None
    university_name: str
    program_name: str
    degree_level: Optional[str] = None
    country: Optional[str] = None
    deadline: Optional[str] = None
    stage: str
    # Null when the deadline is unknown -- never a guessed countdown (see
    # calculate_days_remaining).
    days_remaining: Optional[int] = None
    is_urgent: Optional[bool] = None
    notes: Optional[str] = None


class CreateApplicationPayload(BaseModel):
    student_id: Optional[str] = Field("std_demo", description="Student ID")
    program_id: Optional[int] = Field(None, description="Target program ID")
    university_name: str = Field(..., description="University name")
    program_name: str = Field(..., description="Program name")
    # None, not a plausible value. These are persisted onto the student's own tracker
    # entry, so a default here is indistinguishable from something they typed -- the same
    # defect fixed in RegisterRequest, and "International" is the literal removed from
    # pdf_export.py for inventing a country nobody stated (ADR-0004). `stage` below keeps
    # its default because a starting stage is a workflow fact we do decide, not a claim
    # about the student.
    degree_level: Optional[str] = Field(None, description="Degree level")
    country: Optional[str] = Field(None, description="Destination country")
    deadline: Optional[str] = Field(None, description="Application deadline YYYY-MM-DD")
    stage: Optional[str] = Field("shortlisted", description="Initial stage")
    notes: Optional[str] = Field(None, description="Personal application notes")


class UpdateStagePayload(BaseModel):
    stage: str = Field(..., description="New stage: shortlisted, preparing_documents, submitted, accepted, rejected")
    notes: Optional[str] = Field(None, description="Updated notes")


# -------------------------------------------------------------
# Ownership helpers
# -------------------------------------------------------------
def _owner_key(student: Student) -> str:
    """The tracker's owner key for an authenticated student.

    StudentApplication.student_id is a string column, so the numeric account id
    is stringified. This is the ONLY source of ownership -- never a request
    parameter, or one student can read and mutate another's records.
    """
    return str(student.id)


def _to_response(app: ApplicationModel) -> "ApplicationResponse":
    """Serialize a tracker row, computing its deadline countdown."""
    days, is_urgent = calculate_days_remaining(app.deadline)
    return ApplicationResponse(
        id=app.id,
        student_id=app.student_id,
        program_id=app.program_id,
        university_name=app.university_name,
        program_name=app.program_name,
        degree_level=app.degree_level,
        country=app.country,
        deadline=str(app.deadline) if app.deadline else None,
        stage=app.stage,
        days_remaining=days,
        is_urgent=is_urgent,
        notes=app.notes,
    )


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@router.get(
    "/my-applications",
    response_model=List[ApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Student Applications & Deadline Countdowns"
)
async def get_my_applications(
    current_student: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ApplicationResponse]:
    """Retrieve the authenticated student's applications with deadline countdowns.

    The owner is taken from the bearer token. It was previously a `student_id`
    query parameter with a default, so any caller could read any student's
    applications by passing their id.

    An empty result is a real answer -- a student who has tracked nothing gets an
    empty list, never four applications that are not theirs. This previously fell
    through to DEMO_APPLICATIONS (TUM, ADA, BHOS, RWTH Aachen) whenever the query
    returned zero rows, which is indistinguishable from "the database is fine and
    you have no applications". A database that cannot be read is reported as an
    outage (503), not silently answered with the same invented rows.
    """
    owner_id = _owner_key(current_student)

    try:
        stmt = select(ApplicationModel).where(ApplicationModel.student_id == owner_id)
        res = await db.execute(stmt)
        db_apps = list(res.scalars().all())
    except SQLAlchemyError as exc:
        # Do not fall back to demo records -- that silently showed one student
        # another student's data and hid a broken schema. See docs/adr/0004.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The application tracker is temporarily unavailable.",
        ) from exc

    return [_to_response(app) for app in db_apps]


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Program to Application Tracker"
)
async def create_application(
    payload: CreateApplicationPayload,
    current_student: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApplicationResponse:
    """Add a new target program to the authenticated student's tracker.

    `payload.student_id` is deliberately ignored: the owner comes from the token,
    so a caller cannot create records under another student's account.

    A write that did not happen is not a 201. This previously caught any exception
    from the insert, invented an id from `len(DEMO_APPLICATIONS) + 101`, appended to
    an in-memory list nothing else ever reads back from the database, defaulted a
    missing deadline to "2026-07-01", and returned 201 Created for a row that was
    never persisted.
    """
    sid = _owner_key(current_student)

    try:
        new_app = ApplicationModel(
            student_id=sid,
            program_id=payload.program_id,
            university_name=payload.university_name,
            program_name=payload.program_name,
            degree_level=payload.degree_level,
            country=payload.country,
            stage=payload.stage or "shortlisted",
            notes=payload.notes,
        )
        if payload.deadline:
            new_app.deadline = datetime.strptime(payload.deadline[:10], "%Y-%m-%d").date()

        db.add(new_app)
        await db.commit()
        await db.refresh(new_app)
    except SQLAlchemyError as exc:
        # Previously this appended to an in-memory demo list and reported success,
        # so the student believed the program was saved when nothing was written.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The application could not be saved.",
        ) from exc

    return _to_response(new_app)


@router.patch(
    "/{application_id}/stage",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Application Stage"
)
async def update_application_stage(
    application_id: int,
    payload: UpdateStagePayload,
    current_student: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ApplicationResponse:
    """Update the stage and notes of one of the authenticated student's applications.

    The record is looked up by id **and** owner. Looking up by primary key alone
    let any caller mutate any student's application.

    An application we do not hold cannot be updated. This previously answered an
    unknown id with HTTP 200 and the literals "Target Institution" / "Degree Program"
    -- the same fabricated strings Ruling 6 removed from pdf_export.py, one file over.
    """
    owner_id = _owner_key(current_student)

    try:
        stmt = select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.student_id == owner_id,
        )
        res = await db.execute(stmt)
        app = res.scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot reach the applications store; nothing was updated.",
        ) from exc

    if app is None:
        # 404 rather than 403 so the response does not reveal that an application
        # with this id exists under another account.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No application with id {application_id}.",
        )

    app.stage = payload.stage
    if payload.notes is not None:
        app.notes = payload.notes

    try:
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The stage update could not be saved.",
        ) from exc

    await db.refresh(app)
    return _to_response(app)
