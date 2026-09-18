"""Tests for target institution catalog and gap analysis endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_target_catalog_returns_items():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/routes/catalog")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "university_name" in first
    assert "country_code" in first
    assert "level" in first


@pytest.mark.asyncio
async def test_target_gap_blocked_germany_attestat():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/routes/target-gap",
            json={
                "university_name": "Technical University of Munich",
                "level": "bachelor",
                "qualification_held": "attestat",
                "gpa": 4.5,
                "gpa_scale": "5.0",
                "ielts": 6.5,
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is True
    assert data["country_code"] == "DE"
    assert data["route_status"] == "BLOCKED"
    assert "Studienkolleg" in " ".join(data["unlock_steps"])
    assert data["unlock_time_months"] == 12
    # Checklist verification
    checklist = {item["name"]: item for item in data["checklist"]}
    assert "Entry Qualification" in checklist
    assert checklist["Entry Qualification"]["status"] == "GAP"


@pytest.mark.asyncio
async def test_target_gap_turkey_attestat_open():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/routes/target-gap",
            json={
                "university_name": "Bogazici University",
                "level": "bachelor",
                "qualification_held": "attestat",
                "gpa": 4.8,
                "gpa_scale": "5.0",
                "ielts": 7.0,
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is True
    assert data["country_code"] == "TR"
    assert data["route_status"] == "OPEN"


@pytest.mark.asyncio
async def test_target_gap_uncurated_university_returns_honest_gap():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/routes/target-gap",
            json={
                "university_name": "Nonexistent University Of Mars",
                "level": "bachelor",
                "qualification_held": "attestat",
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is False
    assert "catalogue gap" in data["route_gap_statement"].lower()
    assert len(data["alternatives"]) > 0
