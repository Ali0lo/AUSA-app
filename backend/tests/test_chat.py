"""
Chat/agent endpoint tests covering the profile-fabrication defect.

/chat/agent/state defaults student_id to "std_demo". The store it reads used to be
pre-seeded with an invented profile (gpa 3.5, ielts 6.5, degree_level "master"), so
calling this endpoint with no parameters at all returned fabricated data as fact
(ADR-0004). These tests assert the honest behaviour: an unknown/unseeded student has
a null profile, not a plausible-looking one.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.services.agent.tools import STUDENT_PROFILE_STORE

client = TestClient(app)


def test_agent_state_for_an_unseeded_student_returns_a_null_profile():
    # Deliberately no .pop() here: no other test in this suite writes to the "std_demo"
    # key, so this exercises the module's actual import-time state. If STUDENT_PROFILE_STORE
    # is ever re-seeded with a fabricated "std_demo" entry, this must catch it -- popping
    # the key first would silently defeat that.
    assert "std_demo" not in STUDENT_PROFILE_STORE or STUDENT_PROFILE_STORE["std_demo"].get("gpa") is None

    response = client.get("/api/v1/chat/agent/state")

    assert response.status_code == 200
    profile = response.json()["student_profile"]
    assert profile["gpa"] is None
    assert profile["ielts"] is None
    assert profile["toefl"] is None
    assert profile["degree_level"] is None


def test_agent_state_reflects_a_real_profile_once_one_exists():
    """The store is honest in both directions: real data it holds is still returned."""
    STUDENT_PROFILE_STORE["std_state_real"] = {"gpa": 3.1, "ielts": 6.0, "toefl": None, "degree_level": "bachelor"}

    response = client.get("/api/v1/chat/agent/state?student_id=std_state_real")

    assert response.status_code == 200
    profile = response.json()["student_profile"]
    assert profile["gpa"] == 3.1
    assert profile["degree_level"] == "bachelor"
