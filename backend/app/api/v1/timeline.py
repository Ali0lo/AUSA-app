"""FastAPI router for Admissions Timeline, Milestone Tracking & iCalendar (.ics) export.

Endpoints:
- GET  /api/v1/timeline/milestones: Returns filterable admissions schedule with countdowns and urgency status.
- GET  /api/v1/timeline/milestones/{milestone_id}: Returns detailed profile of a specific milestone.
- GET  /api/v1/timeline/export.ics: Exports filtered admissions deadlines as a standard RFC 5545 iCalendar file.
- GET  /api/v1/timeline/milestones/{milestone_id}/export.ics: Exports a single milestone event as an .ics file.
- POST /api/v1/timeline/custom-reminder: Generates an .ics calendar file for a user-specified custom application deadline.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response, status

from app.domain.timeline import (
    CountryCode,
    CustomReminderRequest,
    DegreeLevel,
    IntakeSeason,
    MilestoneFilter,
    MilestoneItem,
    MilestoneType,
    TimelineSchedule,
    UrgencyLevel,
    create_custom_event_ics,
    generate_icalendar_content,
    get_timeline_schedule,
)

router = APIRouter(prefix="/timeline", tags=["admissions-timeline"])


@router.get(
    "/milestones",
    summary="Get admissions milestones and deadlines with live countdowns",
    response_model=TimelineSchedule,
)
async def get_milestones(
    country_code: Optional[CountryCode] = Query(None, description="Filter by country code (GB, DE, US, AZ, TR, IT, HU, FR, PL)"),
    degree_level: Optional[DegreeLevel] = Query(None, description="Filter by study level (bachelor, master, phd, all)"),
    intake: Optional[IntakeSeason] = Query(None, description="Filter by intake (fall_2026, spring_2027, etc.)"),
    urgency: Optional[UrgencyLevel] = Query(None, description="Filter by urgency (CRITICAL, UPCOMING, OPEN, PASSED)"),
    milestone_type: Optional[MilestoneType] = Query(None, description="Filter by milestone category"),
    is_state_programme_eligible: Optional[bool] = Query(None, description="Filter State Programme qualifying milestones"),
    q: Optional[str] = Query(None, description="Text search across title, university, portal, or description"),
    reference_date: Optional[date] = Query(None, description="Simulate countdown relative to a specific date (defaults to today)"),
) -> TimelineSchedule:
    """Returns application milestones for 2026/2027 admissions cycles across UK, Germany, USA,
    Azerbaijan State Programme, Türkiye Bursları, Stipendium Hungaricum, and Italy DSU.
    """
    filters = MilestoneFilter(
        country_code=country_code,
        degree_level=degree_level,
        intake=intake,
        urgency=urgency,
        milestone_type=milestone_type,
        is_state_programme_eligible=is_state_programme_eligible,
        search_query=q,
    )
    return get_timeline_schedule(filters=filters, reference_date=reference_date)


@router.get(
    "/milestones/{milestone_id}",
    summary="Get single admissions milestone by ID",
    response_model=MilestoneItem,
)
async def get_milestone_by_id(
    milestone_id: str,
    reference_date: Optional[date] = Query(None, description="Simulate countdown relative to a specific date"),
) -> MilestoneItem:
    """Returns single milestone item details including portal instructions and key requirements."""
    schedule = get_timeline_schedule(reference_date=reference_date)
    for m in schedule.milestones:
        if m.id == milestone_id:
            return m

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Milestone with ID '{milestone_id}' not found.",
    )


@router.get(
    "/export.ics",
    summary="Export admissions deadlines to iCalendar (.ics) format",
    response_class=Response,
)
async def export_calendar_ics(
    country_code: Optional[CountryCode] = Query(None),
    degree_level: Optional[DegreeLevel] = Query(None),
    intake: Optional[IntakeSeason] = Query(None),
    urgency: Optional[UrgencyLevel] = Query(None),
    milestone_type: Optional[MilestoneType] = Query(None),
    is_state_programme_eligible: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
    reference_date: Optional[date] = Query(None),
) -> Response:
    """Exports matching admissions milestones as a standard RFC 5545 iCalendar stream.
    Compatible with Google Calendar, Apple Calendar, and Microsoft Outlook.
    """
    filters = MilestoneFilter(
        country_code=country_code,
        degree_level=degree_level,
        intake=intake,
        urgency=urgency,
        milestone_type=milestone_type,
        is_state_programme_eligible=is_state_programme_eligible,
        search_query=q,
    )
    schedule = get_timeline_schedule(filters=filters, reference_date=reference_date)
    ics_content = generate_icalendar_content(schedule.milestones)

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": 'attachment; filename="ausa-admissions-deadlines.ics"',
            "Cache-Control": "no-cache",
        },
    )


@router.get(
    "/milestones/{milestone_id}/export.ics",
    summary="Export a single milestone event to iCalendar (.ics)",
    response_class=Response,
)
async def export_single_milestone_ics(
    milestone_id: str,
    reference_date: Optional[date] = Query(None),
) -> Response:
    """Exports an individual milestone as an iCalendar file with a built-in reminder alarm."""
    schedule = get_timeline_schedule(reference_date=reference_date)
    matched = None
    for m in schedule.milestones:
        if m.id == milestone_id:
            matched = m
            break

    if not matched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Milestone with ID '{milestone_id}' not found.",
        )

    ics_content = generate_icalendar_content([matched], calendar_name=matched.title)

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f'attachment; filename="ausa-deadline-{matched.id}.ics"',
            "Cache-Control": "no-cache",
        },
    )


@router.post(
    "/custom-reminder",
    summary="Create a custom application deadline and generate .ics calendar event",
    response_class=Response,
)
async def create_custom_reminder(req: CustomReminderRequest) -> Response:
    """Allows students to enter custom university deadlines and immediately download
    an RFC 5545 iCalendar reminder event with notification alerts.
    """
    ics_content = create_custom_event_ics(req)
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": 'attachment; filename="ausa-personal-deadline.ics"',
            "Cache-Control": "no-cache",
        },
    )
