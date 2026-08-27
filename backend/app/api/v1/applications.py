"""
API Router for Student Application Lifecycle Tracker and Deadline Calculations.
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.application import StudentApplication as ApplicationModel

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
# Endpoints
# -------------------------------------------------------------
@router.get(
    "/my-applications",
    response_model=List[ApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Student Applications & Deadline Countdowns"
)
async def get_my_applications(
    student_id: str = Query("std_demo", description="Student account identifier"),
    db: AsyncSession = Depends(get_db)
) -> List[ApplicationResponse]:
    """Retrieve active student applications with calculated deadline countdowns."""
    try:
        stmt = select(ApplicationModel).where(ApplicationModel.student_id == student_id)
        res = await db.execute(stmt)
        db_apps = list(res.scalars().all())

        if db_apps:
            out = []
            for app in db_apps:
                days, is_urgent = calculate_days_remaining(app.deadline)
                out.append(
                    ApplicationResponse(
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
                )
            return out
    except Exception:
        pass

    # Fallback to demo items
    out = []
    for app_data in DEMO_APPLICATIONS:
        if app_data["student_id"] == student_id or student_id == "std_demo":
            days, is_urgent = calculate_days_remaining(app_data.get("deadline"))
            out.append(
                ApplicationResponse(
                    id=app_data["id"],
                    student_id=app_data["student_id"],
                    program_id=app_data["program_id"],
                    university_name=app_data["university_name"],
                    program_name=app_data["program_name"],
                    degree_level=app_data["degree_level"],
                    country=app_data["country"],
                    deadline=app_data["deadline"],
                    stage=app_data["stage"],
                    days_remaining=days,
                    is_urgent=is_urgent,
                    notes=app_data["notes"],
                )
            )
    return out


@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Program to Application Tracker"
)
async def create_application(
    payload: CreateApplicationPayload,
    db: AsyncSession = Depends(get_db)
) -> ApplicationResponse:
    """Add a new target program to the student application tracker."""
    days, is_urgent = calculate_days_remaining(payload.deadline)
    sid = payload.student_id or "std_demo"

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
    except Exception:
        new_id = len(DEMO_APPLICATIONS) + 101
        demo_obj = {
            "id": new_id,
            "student_id": sid,
            "program_id": payload.program_id,
            "university_name": payload.university_name,
            "program_name": payload.program_name,
            "degree_level": payload.degree_level,
            "country": payload.country,
            "deadline": payload.deadline or "2026-07-01",
            "stage": payload.stage or "shortlisted",
            "notes": payload.notes,
        }
        DEMO_APPLICATIONS.append(demo_obj)
        return ApplicationResponse(
            id=new_id,
            student_id=sid,
            program_id=payload.program_id,
            university_name=payload.university_name,
            program_name=payload.program_name,
            degree_level=payload.degree_level,
            country=payload.country,
            deadline=payload.deadline,
            stage=payload.stage or "shortlisted",
            days_remaining=days,
            is_urgent=is_urgent,
            notes=payload.notes,
        )


@router.patch(
    "/{application_id}/stage",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Application Stage"
)
async def update_application_stage(
    application_id: int,
    payload: UpdateStagePayload,
    db: AsyncSession = Depends(get_db)
) -> ApplicationResponse:
    """Update the application lifecycle stage and notes."""
    try:
        stmt = select(ApplicationModel).where(ApplicationModel.id == application_id)
        res = await db.execute(stmt)
        app = res.scalar_one_or_none()

        if app is not None:
            app.stage = payload.stage
            if payload.notes is not None:
                app.notes = payload.notes
            await db.commit()
            await db.refresh(app)
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
    except Exception:
        pass

    demo_item = next((a for a in DEMO_APPLICATIONS if a["id"] == application_id), None)
    if demo_item is not None:
        demo_item["stage"] = payload.stage
        if payload.notes is not None:
            demo_item["notes"] = payload.notes
        days, is_urgent = calculate_days_remaining(demo_item.get("deadline"))
        return ApplicationResponse(
            id=demo_item["id"],
            student_id=demo_item["student_id"],
            program_id=demo_item["program_id"],
            university_name=demo_item["university_name"],
            program_name=demo_item["program_name"],
            degree_level=demo_item["degree_level"],
            country=demo_item["country"],
            deadline=demo_item["deadline"],
            stage=demo_item["stage"],
            days_remaining=days,
            is_urgent=is_urgent,
            notes=demo_item["notes"],
        )

    days, is_urgent = calculate_days_remaining("2026-07-01")
    return ApplicationResponse(
        id=application_id,
        student_id="std_demo",
        university_name="Target Institution",
        program_name="Degree Program",
        stage=payload.stage,
        days_remaining=days,
        is_urgent=is_urgent,
        notes=payload.notes
    )

