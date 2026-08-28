import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_my_applications():
    response = client.get("/api/v1/applications/my-applications?student_id=std_demo")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "id" in item
    assert "university_name" in item
    assert "stage" in item
    assert "days_remaining" in item
    assert "is_urgent" in item


def test_create_application():
    payload = {
        "student_id": "std_demo",
        "program_id": 102,
        "university_name": "ADA University",
        "program_name": "M.S. Data Analytics",
        "degree_level": "master",
        "country": "Azerbaijan",
        "deadline": "2026-06-01",
        "stage": "shortlisted",
        "notes": "Target scholarship program"
    }
    response = client.post("/api/v1/applications/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["university_name"] == "ADA University"
    assert data["stage"] == "shortlisted"


def test_update_application_stage():
    payload = {
        "stage": "submitted",
        "notes": "Documents submitted successfully."
    }
    response = client.patch("/api/v1/applications/1/stage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "submitted"

