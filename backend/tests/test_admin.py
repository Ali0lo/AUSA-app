import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_flagged_programs():
    response = client.get("/api/v1/admin/programs/flagged")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "id" in item
    assert "university_name" in item
    assert "confidence_score" in item
    assert item["verification_status"] == "flagged_for_review"


def test_verify_and_approve_program():
    payload = {
        "university_name": "Heidelberg University",
        "program_name": "B.Sc. Computer Science",
        "tuition_fee": 3000.0,
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "verified_by": "admin@ausa.edu.az"
    }
    response = client.put("/api/v1/admin/programs/1001/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verification_status"] == "verified"
    assert data["program_id"] == 1001

