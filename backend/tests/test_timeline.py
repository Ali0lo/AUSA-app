"""Pytest test suite for Admissions Timeline, Milestone Tracking & iCalendar (.ics) export."""

from datetime import date
import pytest
from starlette.testclient import TestClient

from app.domain.timeline import (
    CountryCode,
    CustomReminderRequest,
    DegreeLevel,
    IntakeSeason,
    MilestoneFilter,
    MilestoneType,
    RAW_MILESTONES,
    UrgencyLevel,
    calculate_milestone_status,
    create_custom_event_ics,
    filter_milestones,
    generate_icalendar_content,
    get_timeline_schedule,
)
from app.main import app

client = TestClient(app)


# ==============================================================================
# Domain Engine Unit Tests
# ==============================================================================

def test_raw_milestones_integrity():
    """Verifies that all 24 curated milestones have valid required keys and https URLs."""
    assert len(RAW_MILESTONES) >= 24
    ids = set()
    for m in RAW_MILESTONES:
        assert m["id"] not in ids, f"Duplicate milestone id found: {m['id']}"
        ids.add(m["id"])
        assert isinstance(m["target_date"], date)
        assert m["official_portal_url"].startswith("https://")
        assert len(m["requirements_summary"]) >= 1


def test_get_timeline_schedule_default():
    """Verifies default schedule construction without filters."""
    schedule = get_timeline_schedule()
    assert schedule.total_milestones >= 24
    assert len(schedule.milestones) == schedule.total_milestones
    # Sorted by target_date
    for i in range(len(schedule.milestones) - 1):
        assert schedule.milestones[i].target_date <= schedule.milestones[i + 1].target_date


def test_calculate_milestone_status_tiers():
    """Tests urgency classification across different date deltas."""
    ref = date(2026, 9, 1)

    # 1. Past deadline (negative delta)
    delta, urgency = calculate_milestone_status(date(2026, 8, 15), ref)
    assert delta == -17
    assert urgency == UrgencyLevel.PASSED

    # 2. Critical (<= 14 days)
    delta, urgency = calculate_milestone_status(date(2026, 9, 10), ref)
    assert delta == 9
    assert urgency == UrgencyLevel.CRITICAL

    # 3. Upcoming (15 - 60 days)
    delta, urgency = calculate_milestone_status(date(2026, 10, 15), ref)
    assert delta == 44
    assert urgency == UrgencyLevel.UPCOMING

    # 4. Open (> 60 days)
    delta, urgency = calculate_milestone_status(date(2027, 1, 15), ref)
    assert delta > 60
    assert urgency == UrgencyLevel.OPEN


def test_filter_milestones_by_country():
    """Verifies filtering by destination country."""
    schedule_gb = get_timeline_schedule(filters=MilestoneFilter(country_code=CountryCode.GB))
    assert schedule_gb.total_milestones >= 4
    for m in schedule_gb.milestones:
        assert m.country_code == CountryCode.GB

    schedule_de = get_timeline_schedule(filters=MilestoneFilter(country_code=CountryCode.DE))
    assert schedule_de.total_milestones >= 3
    for m in schedule_de.milestones:
        assert m.country_code == CountryCode.DE


def test_filter_milestones_by_degree_level():
    """Verifies filtering by Bachelor vs Master level."""
    schedule_bachelor = get_timeline_schedule(filters=MilestoneFilter(degree_level=DegreeLevel.BACHELOR))
    for m in schedule_bachelor.milestones:
        assert m.degree_level in (DegreeLevel.BACHELOR, DegreeLevel.ALL)

    schedule_master = get_timeline_schedule(filters=MilestoneFilter(degree_level=DegreeLevel.MASTER))
    for m in schedule_master.milestones:
        assert m.degree_level in (DegreeLevel.MASTER, DegreeLevel.ALL)


def test_filter_milestones_by_intake():
    """Verifies filtering by intake season."""
    schedule_fall26 = get_timeline_schedule(filters=MilestoneFilter(intake=IntakeSeason.FALL_2026))
    assert schedule_fall26.total_milestones > 10
    for m in schedule_fall26.milestones:
        assert m.intake == IntakeSeason.FALL_2026


def test_filter_milestones_by_state_programme():
    """Verifies filtering by State Programme 2022-2026 eligibility."""
    schedule_dp = get_timeline_schedule(filters=MilestoneFilter(is_state_programme_eligible=True))
    assert schedule_dp.total_milestones > 10
    for m in schedule_dp.milestones:
        assert m.is_state_programme_eligible is True


def test_filter_milestones_by_search_query():
    """Verifies full-text search matching across title, country, portal."""
    schedule_assist = get_timeline_schedule(filters=MilestoneFilter(search_query="uni-assist"))
    assert schedule_assist.total_milestones >= 2
    for m in schedule_assist.milestones:
        text = f"{m.title} {m.description} {m.portal_name} {m.country_name}".lower()
        assert "uni-assist" in text

    schedule_baku = get_timeline_schedule(filters=MilestoneFilter(search_query="baku"))
    assert schedule_baku.total_milestones >= 2


def test_generate_icalendar_content_rfc5545():
    """Verifies standard-compliant RFC 5545 iCalendar content."""
    schedule = get_timeline_schedule()
    ics = generate_icalendar_content(schedule.milestones)

    # Core headers
    assert "BEGIN:VCALENDAR" in ics
    assert "VERSION:2.0" in ics
    assert "PRODID:-//AUSA//Admissions Timeline Engine" in ics
    assert "CALSCALE:GREGORIAN" in ics
    assert "METHOD:PUBLISH" in ics

    # VEVENT blocks
    assert ics.count("BEGIN:VEVENT") == schedule.total_milestones
    assert ics.count("END:VEVENT") == schedule.total_milestones
    assert ics.count("BEGIN:VALARM") == schedule.total_milestones
    assert "TRIGGER:-P3D" in ics
    assert "END:VCALENDAR" in ics


def test_create_custom_event_ics():
    """Verifies custom user deadline reminder .ics generator."""
    req = CustomReminderRequest(
        title="Technical University of Munich Direct Portal Submission",
        target_date=date(2026, 7, 15),
        country_name="Germany",
        description="Submit translated transcripts and VPD",
        portal_url="https://tumonline.tum.de",
        reminder_days_before=5,
    )
    ics = create_custom_event_ics(req)
    assert "BEGIN:VCALENDAR" in ics
    assert "BEGIN:VEVENT" in ics
    assert "TUM" in ics or "Technical University of Munich" in ics
    assert "TRIGGER:-P5D" in ics
    assert "https://tumonline.tum.de" in ics
    assert "END:VCALENDAR" in ics


# ==============================================================================
# FastAPI REST Endpoint Integration Tests
# ==============================================================================

def test_api_get_milestones_success():
    """Tests GET /api/v1/timeline/milestones."""
    res = client.get("/api/v1/timeline/milestones")
    assert res.status_code == 200
    data = res.json()
    assert "total_milestones" in data
    assert data["total_milestones"] >= 24
    assert len(data["milestones"]) == data["total_milestones"]


def test_api_get_milestones_with_filters():
    """Tests GET /api/v1/timeline/milestones with country_code and degree_level."""
    res = client.get("/api/v1/timeline/milestones?country_code=GB&degree_level=bachelor")
    assert res.status_code == 200
    data = res.json()
    assert data["total_milestones"] >= 2
    for m in data["milestones"]:
        assert m["country_code"] == "GB"


def test_api_get_milestone_by_id_success():
    """Tests GET /api/v1/timeline/milestones/{id} for valid milestone."""
    res = client.get("/api/v1/timeline/milestones/gb_ucas_oxbridge_2026")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "gb_ucas_oxbridge_2026"
    assert "Oxbridge" in data["title"]
    assert data["country_code"] == "GB"


def test_api_get_milestone_by_id_not_found():
    """Tests GET /api/v1/timeline/milestones/{id} for nonexistent milestone returns 404."""
    res = client.get("/api/v1/timeline/milestones/nonexistent_id_9999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_api_export_ics_stream():
    """Tests GET /api/v1/timeline/export.ics returns valid text/calendar attachment."""
    res = client.get("/api/v1/timeline/export.ics?country_code=DE")
    assert res.status_code == 200
    assert "text/calendar" in res.headers["content-type"]
    assert 'filename="ausa-admissions-deadlines.ics"' in res.headers["content-disposition"]
    assert "BEGIN:VCALENDAR" in res.text
    assert "BEGIN:VEVENT" in res.text
    assert "Uni-Assist" in res.text or "Germany" in res.text


def test_api_export_single_milestone_ics():
    """Tests GET /api/v1/timeline/milestones/{id}/export.ics."""
    res = client.get("/api/v1/timeline/milestones/stipendium_hungaricum_2027/export.ics")
    assert res.status_code == 200
    assert "text/calendar" in res.headers["content-type"]
    assert "stipendium_hungaricum_2027" in res.headers["content-disposition"]
    assert "Stipendium Hungaricum" in res.text
    assert "BEGIN:VALARM" in res.text


def test_api_create_custom_reminder():
    """Tests POST /api/v1/timeline/custom-reminder."""
    payload = {
        "title": "Baku State University Document Submission",
        "target_date": "2026-08-01",
        "country_name": "Azerbaijan",
        "description": "Submit bachelor diploma copy and attestat",
        "portal_url": "https://bsu.edu.az",
        "reminder_days_before": 7,
    }
    res = client.post("/api/v1/timeline/custom-reminder", json=payload)
    assert res.status_code == 200
    assert "text/calendar" in res.headers["content-type"]
    assert "Baku State University" in res.text
    assert "TRIGGER:-P7D" in res.text
