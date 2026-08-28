"""Security boundary tests for the admin curation endpoints.

These routes can mark scraped programs as human-verified, and that verification is
the guardrail data-sourcing.md requires before data is shown to a student. They were
previously reachable by anyone: require_admin_user took no request and returned
{"is_admin": True} unconditionally.

The assertions below need no database -- an unauthenticated request is rejected by the
dependency before any query runs. Tests covering an authenticated non-admin (403) and a
successful admin call require a live Postgres and belong in an integration suite.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN_ROUTES = [
    ("get", "/api/v1/admin/programs/flagged", None),
    (
        "put",
        "/api/v1/admin/programs/1001/verify",
        {
            "university_name": "Heidelberg University",
            "program_name": "B.Sc. Computer Science",
            "tuition_fee": 3000.0,
            "min_gpa": 3.0,
            "min_ielts": 6.5,
            "verified_by": "admin@ausa.edu.az",
        },
    ),
    ("post", "/api/v1/admin/seed", None),
]


@pytest.mark.parametrize("method,path,payload", ADMIN_ROUTES)
def test_admin_routes_reject_anonymous_callers(method, path, payload):
    """No credentials must never reach a curation endpoint."""
    response = getattr(client, method)(path, **({"json": payload} if payload else {}))
    assert response.status_code == 401, (
        f"{method.upper()} {path} returned {response.status_code} without credentials"
    )


@pytest.mark.parametrize("method,path,payload", ADMIN_ROUTES)
def test_admin_routes_reject_invalid_tokens(method, path, payload):
    """A malformed bearer token must not authenticate."""
    kwargs = {"headers": {"Authorization": "Bearer not-a-real-token"}}
    if payload:
        kwargs["json"] = payload
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


def test_admin_allowlist_is_empty_by_default():
    """Fail-closed: a deployment that configures no admins grants nobody access."""
    from app.core.config import settings

    assert settings.ADMIN_EMAILS == [], (
        "ADMIN_EMAILS must default to empty so a misconfigured deployment locks "
        "the curation endpoints rather than opening them"
    )
