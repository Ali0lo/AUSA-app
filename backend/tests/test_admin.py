"""Security boundary tests for the admin curation endpoints.

These routes can mark scraped programs as human-verified, and that verification is
the guardrail data-sourcing.md requires before data is shown to a student. They were
previously reachable by anyone: require_admin_user took no request and returned
{"is_admin": True} unconditionally.

Most assertions run against a real in-memory SQLite database via the `admin_env`
fixture below, exactly like test_auth.py and test_applications.py, so the
authenticated non-admin (403) and successful-admin paths are exercised for real
rather than skipped without a live Postgres. The route-level parametrized tests
further down need no database at all -- an unauthenticated or malformed-token
request is rejected by the dependency before any query runs.
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.program import Program as ProgramModel
from app.models.student import Student

client = TestClient(app)

ADMIN_EMAIL = "curator@ausa.edu.az"
STUDENT_EMAIL = "ordinary_student@ausa.edu.az"


@pytest_asyncio.fixture
async def admin_env(monkeypatch):
    """A database holding `programs` and `students`, plus one admin and one non-admin.

    Yields (session, admin_headers, student_headers).

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
            tables=[ProgramModel.__table__, Student.__table__],
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        admin = Student(email=ADMIN_EMAIL)
        ordinary = Student(email=STUDENT_EMAIL)
        session.add_all([admin, ordinary])
        await session.commit()
        await session.refresh(admin)
        await session.refresh(ordinary)

        monkeypatch.setattr(settings, "ADMIN_EMAILS", [ADMIN_EMAIL])

        async def _get_test_db():
            yield session

        app.dependency_overrides[get_db] = _get_test_db
        yield (
            session,
            {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"},
            {"Authorization": f"Bearer {create_access_token(subject=ordinary.id)}"},
        )
        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.mark.asyncio
async def test_admin_queue_rejects_an_anonymous_caller(admin_env):
    """No token, no queue. This endpoint used to be open to the entire internet."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        assert (await c.get("/api/v1/admin/programs/flagged")).status_code == 401


@pytest.mark.asyncio
async def test_admin_queue_rejects_an_authenticated_non_admin(admin_env):
    """A valid student token is not an admin token."""
    _, _, student_headers = admin_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/admin/programs/flagged", headers=student_headers)
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_verify_endpoint_rejects_an_anonymous_caller(admin_env):
    """Publishing unverified data to students required no credentials at all."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.put("/api/v1/admin/programs/1/verify", json={"program_name": "X"})
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_on_the_allowlist_is_admitted(admin_env):
    _, admin_headers, _ = admin_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/admin/programs/flagged", headers=admin_headers)
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_an_empty_allowlist_admits_nobody(admin_env, monkeypatch):
    """The default is deny-all. An unconfigured deployment must not be an open one."""
    _, admin_headers, _ = admin_env
    monkeypatch.setattr(settings, "ADMIN_EMAILS", [])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/admin/programs/flagged", headers=admin_headers)
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_empty_review_queue_returns_nothing_not_demo_data(admin_env):
    """An empty queue is an empty list -- never the demo programmes."""
    _, admin_headers, _ = admin_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/v1/admin/programs/flagged", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_flagged_queue_returns_real_rows_and_preserves_unscored_confidence(admin_env):
    """A row nobody scored reports confidence null, not an invented number."""
    session, admin_headers, _ = admin_env
    session.add_all([
        ProgramModel(
            university_name="Real University",
            program_name="B.Sc. Real Programme",
            verification_status="flagged_for_review",
        ),
        ProgramModel(
            university_name="Zero Confidence University",
            program_name="B.Sc. Nothing Extracted",
            verification_status="flagged_for_review",
            confidence_score=0.0,
        ),
    ])
    await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/v1/admin/programs/flagged", headers=admin_headers)

    assert response.status_code == 200
    by_name = {item["university_name"]: item for item in response.json()}
    assert by_name["Real University"]["confidence_score"] is None
    assert by_name["Zero Confidence University"]["confidence_score"] == 0.0


@pytest.mark.asyncio
async def test_verify_writes_to_the_database(admin_env):
    session, admin_headers, _ = admin_env
    program = ProgramModel(
        university_name="Real University",
        program_name="B.Sc. Real Programme",
        verification_status="flagged_for_review",
    )
    session.add(program)
    await session.commit()
    await session.refresh(program)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.put(
            f"/api/v1/admin/programs/{program.id}/verify",
            json={"program_name": "B.Sc. Corrected Name", "min_ielts": 6.5},
            headers=admin_headers,
        )

    assert res.status_code == 200
    assert res.json()["verification_status"] == "verified"

    await session.refresh(program)
    assert program.program_name == "B.Sc. Corrected Name"
    assert program.min_ielts == 6.5
    assert program.verification_status == "verified"
    assert program.verified_by == ADMIN_EMAIL


@pytest.mark.asyncio
async def test_a_post_commit_refresh_failure_is_not_reported_as_a_failed_write(admin_env, monkeypatch):
    """commit() succeeding and refresh() then raising must not read as "could not be saved".

    The write already persisted by the time refresh() runs, so a failure there is a read
    failure, not a write failure. Reporting it with the same 503 as a genuinely failed
    commit would be a false failure -- the mirror image of the false success this whole
    endpoint used to report.
    """
    session, admin_headers, _ = admin_env
    program = ProgramModel(
        university_name="Real University",
        program_name="B.Sc. Real Programme",
        verification_status="flagged_for_review",
    )
    session.add(program)
    await session.commit()
    await session.refresh(program)
    program_id = program.id

    async def _explode_refresh(*args, **kwargs):
        raise RuntimeError("refresh exploded after a successful commit")

    monkeypatch.setattr(session, "refresh", _explode_refresh)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        res = await c.put(
            f"/api/v1/admin/programs/{program_id}/verify",
            json={"program_name": "B.Sc. Corrected Name"},
            headers=admin_headers,
        )

    assert res.status_code != 503
    assert "could not be saved" not in res.text.lower()

    # The endpoint's own lookup shares this session's identity map, so `program` was
    # mutated and committed in place -- no refresh needed to see the persisted write.
    assert program.program_name == "B.Sc. Corrected Name"
    assert program.verification_status == "verified"


@pytest.mark.asyncio
async def test_verify_reports_404_for_a_programme_that_does_not_exist(admin_env):
    """The endpoint used to answer 'successfully verified and published' for any id.

    Ids 1001-1004 hit an in-memory demo list and returned success having written nothing;
    every other unknown id fell through to a success response at the end of the function.
    """
    _, admin_headers, _ = admin_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for unknown_id in (1001, 424242):
            res = await c.put(
                f"/api/v1/admin/programs/{unknown_id}/verify",
                json={"program_name": "Does Not Exist"},
                headers=admin_headers,
            )
            assert res.status_code == 404, f"id {unknown_id} was not reported missing"


@pytest.mark.asyncio
async def test_seed_endpoint_reports_failure_as_failure(admin_env, monkeypatch):
    """A failed seed used to return status='success' with invented counts (7/3/3)."""
    _, admin_headers, _ = admin_env

    async def _explode(session):
        raise RuntimeError("seeding is broken")

    monkeypatch.setattr("scripts.seed_db.seed_database", _explode)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.post("/api/v1/admin/seed", headers=admin_headers)

    assert res.status_code == 503
    assert "success" not in res.text.lower()


# ---------------------------------------------------------------------------
# Route-level boundary sweep: no database needed, rejected before any query runs.
# ---------------------------------------------------------------------------

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
    assert settings.ADMIN_EMAILS == [], (
        "ADMIN_EMAILS must default to empty so a misconfigured deployment locks "
        "the curation endpoints rather than opening them"
    )
