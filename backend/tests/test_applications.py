"""
Application tracker tests.

These run against a real in-memory SQLite database, exactly like test_auth.py and
test_admin.py. The previous version used a plain `TestClient(app)` with no `get_db`
override, so every request hit the real (unreachable in test) DATABASE_URL, fell into
`except Exception: pass`, and every assertion was actually satisfied by the module's
DEMO_APPLICATIONS fixtures -- `test_create_application` passed when creation was
impossible, and the tests mutated shared module-global state across test order. These
tests instead assert against rows this test itself put in (or did not put in) the
database, so a mutation that removes the database path from an endpoint fails them.

The endpoints also previously took the owner from a `student_id` query parameter or
request body with a default value, and looked records up by primary key alone. Any
caller could therefore read another student's applications and notes, create records
under someone else's account, and mutate their stages. Ownership now comes from the
bearer token only, so the behavioural tests below authenticate via the `tracker_env`
fixture, and the route-level boundary sweep further down needs no database at all --
an unauthenticated request is rejected by the dependency before any query runs.
Cross-account tests (student A cannot see student B) require a live Postgres and
belong in an integration suite.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.application import StudentApplication as ApplicationModel
from app.models.student import Student

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


@pytest_asyncio.fixture
async def tracker_env():
    """A database holding `student_applications` and `students`, plus one authenticated student.

    Yields (session, headers, owner_id).

    Base.metadata as a whole cannot be created here: university_documents uses pgvector's
    Vector type, which SQLite has no equivalent for.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[ApplicationModel.__table__, Student.__table__],
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        student = Student(email="tracker_test@ausa.edu.az")
        session.add(student)
        await session.commit()
        await session.refresh(student)

        async def _get_test_db():
            yield session

        app.dependency_overrides[get_db] = _get_test_db
        yield (
            session,
            {"Authorization": f"Bearer {create_access_token(subject=student.id)}"},
            str(student.id),
        )
        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_my_applications_returns_a_real_row(tracker_env):
    """A row this test wrote is the row the endpoint must return -- not a fixture."""
    session, headers, owner_id = tracker_env
    session.add(
        ApplicationModel(
            student_id=owner_id,
            university_name="Test University",
            program_name="B.Sc. Testing",
            degree_level="bachelor",
            country="Testland",
            stage="shortlisted",
        )
    )
    await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/applications/my-applications", headers=headers)

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["university_name"] == "Test University"
    assert data[0]["stage"] == "shortlisted"


@pytest.mark.asyncio
async def test_empty_applications_returns_empty_list_not_demo_data(tracker_env):
    """A student with zero tracked applications gets an empty list.

    This previously fell through to DEMO_APPLICATIONS (TUM, ADA, BHOS, RWTH Aachen)
    for any student_id, including one nobody has ever used.
    """
    _, headers, _ = tracker_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/applications/my-applications", headers=headers)

    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_database_outage_is_reported_not_hidden_as_an_empty_result():
    """A store that cannot be read is an outage (503), not zero applications."""

    class FailingSession:
        async def execute(self, *args, **kwargs):
            raise SQLAlchemyError("connection refused")

    async def _get_failing_db():
        yield FailingSession()

    app.dependency_overrides[get_db] = _get_failing_db
    try:
        token = create_access_token(subject=1)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            res = await c.get(
                "/api/v1/applications/my-applications",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert res.status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_application_persists_to_the_database(tracker_env):
    """Creation must actually write a row -- 201 with an echoed payload is not enough.

    This previously passed via the `except Exception` fallback, which invented an id
    and appended to an in-memory list without writing anything. Reading the row back
    from this test's own database session is what a removed database path fails.
    """
    session, headers, owner_id = tracker_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.post("/api/v1/applications/", json=CREATE_PAYLOAD, headers=headers)

    assert res.status_code == 201
    data = res.json()
    assert data["university_name"] == "ADA University"

    stmt = select(ApplicationModel).where(ApplicationModel.id == data["id"])
    row = (await session.execute(stmt)).scalar_one_or_none()
    assert row is not None, "creation returned 201 but wrote no row"
    assert row.university_name == "ADA University"
    assert row.student_id == owner_id


@pytest.mark.asyncio
async def test_create_application_failure_is_reported_not_faked(tracker_env, monkeypatch):
    """A write that cannot happen must not return 201."""
    session, headers, _ = tracker_env

    async def _explode_commit(*args, **kwargs):
        raise SQLAlchemyError("write refused")

    monkeypatch.setattr(session, "commit", _explode_commit)

    payload = {
        "university_name": "ADA University",
        "program_name": "M.S. Data Analytics",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.post("/api/v1/applications/", json=payload, headers=headers)
    assert res.status_code == 503


@pytest.mark.asyncio
async def test_update_application_stage_persists(tracker_env):
    """The new stage must actually be saved, not just echoed in the response."""
    session, headers, owner_id = tracker_env
    app_row = ApplicationModel(
        student_id=owner_id,
        university_name="Existing University",
        program_name="Existing Program",
        stage="shortlisted",
    )
    session.add(app_row)
    await session.commit()
    await session.refresh(app_row)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.patch(
            f"/api/v1/applications/{app_row.id}/stage",
            json={"stage": "submitted", "notes": "Documents submitted successfully."},
            headers=headers,
        )

    assert res.status_code == 200
    assert res.json()["stage"] == "submitted"

    await session.refresh(app_row)
    assert app_row.stage == "submitted"
    assert app_row.notes == "Documents submitted successfully."


@pytest.mark.asyncio
async def test_update_unknown_application_returns_404_not_a_fabricated_record(tracker_env):
    """An id we do not hold cannot be updated.

    This previously answered 200 with university_name="Target Institution" and
    program_name="Degree Program" -- the same literals removed from pdf_export.py.
    """
    _, headers, _ = tracker_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.patch(
            "/api/v1/applications/999999/stage",
            json={"stage": "submitted"},
            headers=headers,
        )

    assert res.status_code == 404
    assert "Target Institution" not in res.text
    assert "Degree Program" not in res.text


# ---------------------------------------------------------------------------
# Route-level boundary sweep: no database needed, rejected before any query runs.
# ---------------------------------------------------------------------------

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
