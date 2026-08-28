"""Security boundary tests for the application tracker.

These endpoints previously took the owner from a `student_id` query parameter or
request body with a default value, and looked records up by primary key alone. Any
caller could therefore read another student's applications and notes, create records
under someone else's account, and mutate their stages.

Ownership now comes from the bearer token only. The assertions below need no database
-- an unauthenticated request is rejected by the dependency before any query runs.
Cross-account tests (student A cannot see student B) require a live Postgres and
belong in an integration suite.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

CREATE_PAYLOAD = {
    "program_id": 102,
    "university_name": "ADA University",
    "program_name": "M.S. Data Analytics",
    "degree_level": "master",
    "country": "Azerbaijan",
    "deadline": "2026-06-01",
    "stage": "shortlisted",
    "notes": "Target scholarship program",
}

TRACKER_ROUTES = [
    ("get", "/api/v1/applications/my-applications", None),
    ("post", "/api/v1/applications/", CREATE_PAYLOAD),
    ("patch", "/api/v1/applications/1/stage", {"stage": "submitted"}),
]


@pytest.mark.parametrize("method,path,payload", TRACKER_ROUTES)
def test_tracker_routes_reject_anonymous_callers(method, path, payload):
    response = getattr(client, method)(path, **({"json": payload} if payload else {}))
    assert response.status_code == 401, (
        f"{method.upper()} {path} returned {response.status_code} without credentials"
    )


def test_student_id_query_parameter_no_longer_grants_access():
    """The old IDOR: passing someone else's id used to return their applications."""
    response = client.get("/api/v1/applications/my-applications?student_id=std_demo")
    assert response.status_code == 401


def test_create_cannot_choose_its_own_owner():
    """A student_id in the body must not authenticate or reassign ownership."""
    response = client.post(
        "/api/v1/applications/",
        json={**CREATE_PAYLOAD, "student_id": "some-other-student"},
    )
    assert response.status_code == 401
