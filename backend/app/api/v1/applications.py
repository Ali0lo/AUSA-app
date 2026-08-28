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

# -------------------------------------------------------------
# Demo / Fallback Tracker Fixtures
# -------------------------------------------------------------
DEMO_APPLICATIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "student_id": "std_demo",
        "program_id": 105,
        "university_name": "Technical University of Munich (TUM)",
        "program_name": "M.Sc. Informatics",
        "degree_level": "master",
        "country": "Germany",
        "deadline": "2026-07-15",
        "stage": "preparing_documents",
        "notes": "Blocked account required; motivation letter draft ready.",
    },
    {
        "id": 2,
        "student_id": "std_demo",
        "program_id": 101,
        "university_name": "ADA University",
        "program_name": "B.Sc. Computer Science",
        "degree_level": "bachelor",
        "country": "Azerbaijan",
        "deadline": "2026-06-01",
        "stage": "shortlisted",
        "notes": "DIM score requirement 600+ points.",
    },
    {
        "id": 3,
        "student_id": "std_demo",
        "program_id": 104,
        "university_name": "Baku Higher Oil School (BANM / BHOS)",
        "program_name": "B.Sc. Software Engineering",
        "degree_level": "bachelor",
        "country": "Azerbaijan",
        "deadline": "2026-06-15",
        "stage": "submitted",
        "notes": "Application submitted via state portal.",
    },
    {
        "id": 4,
        "student_id": "std_demo",
        "program_id": 106,
        "university_name": "RWTH Aachen University",
        "program_name": "M.Sc. Mechanical Engineering",
        "degree_level": "master",
        "country": "Germany",
        "deadline": "2026-03-01",
        "stage": "preparing_documents",
        "notes": "Studienkolleg certificate uploaded.",
    },
]


def calculate_days_remaining(deadline_val: Any) -> Tuple[int, bool]:
    """Calculate days remaining until deadline and return (days_remaining, is_urgent)."""
    if not deadline_val:
        return 90, False
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
        return 30, False


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
    days_remaining: int
    is_urgent: bool
    notes: Optional[str] = None


class CreateApplicationPayload(BaseModel):
    student_id: Optional[str] = Field("std_demo", description="Student ID")
    program_id: Optional[int] = Field(None, description="Target program ID")
    university_name: str = Field(..., description="University name")
    program_name: str = Field(..., description="Program name")
    degree_level: Optional[str] = Field("master", description="Degree level")
    country: Optional[str] = Field("International", description="Destination country")
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
    """
    days, is_urgent = calculate_days_remaining(payload.deadline)
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

        return ApplicationResponse(
            id=new_app.id,
            student_id=new_app.student_id,
            program_id=new_app.program_id,
            university_name=new_app.university_name,
            program_name=new_app.program_name,
            degree_level=new_app.degree_level,
            country=new_app.country,
            deadline=str(new_app.deadline) if new_app.deadline else None,
            stage=new_app.stage,
            days_remaining=days,
            is_urgent=is_urgent,
            notes=new_app.notes,
        )
    except SQLAlchemyError as exc:
        # Previously this appended to an in-memory demo list and reported success,
        # so the student believed the program was saved when nothing was written.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not save the application. Please try again shortly.",
        ) from exc


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
    """
    owner_id = _owner_key(current_student)

    try:
        stmt = select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.student_id == owner_id,
        )
        res = await db.execute(stmt)
        app = res.scalar_one_or_none()

        # 404 rather than 403 so the response does not reveal that an application
        # with this id exists under another account.
        if app is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found.",
            )

        app.stage = payload.stage
        if payload.notes is not None:
            app.notes = payload.notes
        await db.commit()
        await db.refresh(app)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not update the application. Please try again shortly.",
        ) from exc

    return _to_response(app)

