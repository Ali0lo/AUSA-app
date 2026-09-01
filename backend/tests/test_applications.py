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
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.application import StudentApplication as ApplicationModel


@pytest_asyncio.fixture
async def db_session():
    """A real SQLite database holding only `student_applications`."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[ApplicationModel.__table__])

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        async def _get_test_db():
            yield session

        app.dependency_overrides[get_db] = _get_test_db
        yield session
        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_my_applications_returns_a_real_row(db_session):
    """A row this test wrote is the row the endpoint must return -- not a fixture."""
    db_session.add(
        ApplicationModel(
            student_id="std_test_apps",
            university_name="Test University",
            program_name="B.Sc. Testing",
            degree_level="bachelor",
            country="Testland",
            stage="shortlisted",
        )
    )
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/applications/my-applications?student_id=std_test_apps")

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["university_name"] == "Test University"
    assert data[0]["stage"] == "shortlisted"


@pytest.mark.asyncio
async def test_empty_applications_returns_empty_list_not_demo_data(db_session):
    """A student with zero tracked applications gets an empty list.

    This previously fell through to DEMO_APPLICATIONS (TUM, ADA, BHOS, RWTH Aachen)
    for any student_id, including one nobody has ever used.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/applications/my-applications?student_id=nobody_has_this_id")

    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
async def test_database_outage_is_reported_not_hidden_as_an_empty_result(db_session):
    """A store that cannot be read is an outage (503), not zero applications."""

    class FailingSession:
        async def execute(self, *args, **kwargs):
            raise RuntimeError("connection refused")

    async def _get_failing_db():
        yield FailingSession()

    app.dependency_overrides[get_db] = _get_failing_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            res = await c.get("/api/v1/applications/my-applications?student_id=std_test_apps")
        assert res.status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_application_persists_to_the_database(db_session):
    """Creation must actually write a row -- 201 with an echoed payload is not enough.

    This previously passed via the `except Exception` fallback, which invented an id
    and appended to an in-memory list without writing anything. Reading the row back
    from this test's own database session is what a removed database path fails.
    """
    payload = {
        "student_id": "std_test_apps",
        "program_id": 102,
        "university_name": "ADA University",
        "program_name": "M.S. Data Analytics",
        "degree_level": "master",
        "country": "Azerbaijan",
        "deadline": "2026-06-01",
        "stage": "shortlisted",
        "notes": "Target scholarship program",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.post("/api/v1/applications/", json=payload)

    assert res.status_code == 201
    data = res.json()
    assert data["university_name"] == "ADA University"

    stmt = select(ApplicationModel).where(ApplicationModel.id == data["id"])
    row = (await db_session.execute(stmt)).scalar_one_or_none()
    assert row is not None, "creation returned 201 but wrote no row"
    assert row.university_name == "ADA University"
    assert row.student_id == "std_test_apps"


@pytest.mark.asyncio
async def test_create_application_failure_is_reported_not_faked(db_session):
    """A write that cannot happen must not return 201."""

    class FailingSession:
        def add(self, *args, **kwargs):
            pass

        async def commit(self, *args, **kwargs):
            raise RuntimeError("write refused")

        async def rollback(self, *args, **kwargs):
            pass

    async def _get_failing_db():
        yield FailingSession()

    app.dependency_overrides[get_db] = _get_failing_db
    try:
        payload = {
            "university_name": "ADA University",
            "program_name": "M.S. Data Analytics",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            res = await c.post("/api/v1/applications/", json=payload)
        assert res.status_code == 503
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_application_stage_persists(db_session):
    """The new stage must actually be saved, not just echoed in the response."""
    app_row = ApplicationModel(
        student_id="std_test_apps",
        university_name="Existing University",
        program_name="Existing Program",
        stage="shortlisted",
    )
    db_session.add(app_row)
    await db_session.commit()
    await db_session.refresh(app_row)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.patch(
            f"/api/v1/applications/{app_row.id}/stage",
            json={"stage": "submitted", "notes": "Documents submitted successfully."},
        )

    assert res.status_code == 200
    assert res.json()["stage"] == "submitted"

    await db_session.refresh(app_row)
    assert app_row.stage == "submitted"
    assert app_row.notes == "Documents submitted successfully."


@pytest.mark.asyncio
async def test_update_unknown_application_returns_404_not_a_fabricated_record(db_session):
    """An id we do not hold cannot be updated.

    This previously answered 200 with university_name="Target Institution" and
    program_name="Degree Program" -- the same literals removed from pdf_export.py.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.patch(
            "/api/v1/applications/999999/stage",
            json={"stage": "submitted"},
        )

    assert res.status_code == 404
    assert "Target Institution" not in res.text
    assert "Degree Program" not in res.text
