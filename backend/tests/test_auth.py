"""
Authentication tests.

These run against a real in-memory SQLite database, exactly like test_admin.py and
test_applications.py. The previous version ran against no database at all: every
request hit an `except Exception` fallback that issued a token for student 101 and
returned a synthetic profile whose email and GPA were copied from this file. The flow
it asserted was therefore never executed -- the test certified an authentication
bypass rather than catching it. `test_auth_register_and_login_flow` used to also pass
with no database for the same reason: login fell back to minting a token for subject
101 and get_current_user fabricated a Student with email
"test_student_auth@ausa.edu.az" and gpa 3.7 -- the exact values this test asserts.
The register/login flow below is a real integration test against the SQLite fixture
rather than one skipped without a live Postgres, and the bypasses additionally have
regression coverage that needs no database at all.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.main import app
from app.models.student import Student


def _database_is_reachable() -> bool:
    async def _check() -> bool:
        from sqlalchemy import text

        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    try:
        return asyncio.run(_check())
    except Exception:
        return False


requires_db = pytest.mark.skipif(
    not _database_is_reachable(),
    reason="needs a live PostgreSQL; run docker-compose up first",
)


def test_password_hashing():
    pwd = "mysecretpassword123"
    hashed = get_password_hash(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_creation_and_decoding():
    token = create_access_token(subject=42)
    assert token != ""
    from app.core.security import decode_access_token

    sub = decode_access_token(token)
    assert sub == "42"


@pytest_asyncio.fixture
async def db_session():
    """A real SQLite database holding only `students`.

    Base.metadata as a whole cannot be created here: university_documents uses
    pgvector's Vector type, which SQLite has no equivalent for. Auth touches only
    students, so only that table is built.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[Student.__table__])

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        async def _get_test_db():
            yield session

        app.dependency_overrides[get_db] = _get_test_db
        yield session
        app.dependency_overrides.clear()

    await engine.dispose()


# ---------------------------------------------------------------------------
# Regression tests for the auth bypasses. These must hold with or without a DB.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_never_mints_a_token_for_unknown_credentials():
    """Login must not return 200 for credentials it could not verify.

    With a database up this is a 401; with it down it is a 503. It was previously
    a 200 with a valid signed token whenever the database was unreachable, turning
    any outage into a complete authentication bypass.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody-at-all@example.invalid", "password": "wrong-password"},
        )

    assert res.status_code != 200, "login returned a token for unverifiable credentials"
    assert res.status_code in (401, 503)
    assert "access_token" not in res.json()


@pytest.mark.asyncio
async def test_me_rejects_missing_and_invalid_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        anonymous = await client.get("/api/v1/auth/me")
        assert anonymous.status_code == 401

        malformed = await client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert malformed.status_code == 401


@pytest.mark.asyncio
async def test_signed_token_for_nonexistent_account_is_rejected():
    """A validly signed token whose subject has no account must not authenticate.

    This is the core of the deps.py bypass: a deleted user's token stayed valid for
    its full 7-day TTL because a missing row produced a fabricated Student.
    """
    token = create_access_token(subject=99999999)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

    assert res.status_code != 200, "a token for a nonexistent account authenticated"
    assert res.status_code in (401, 503)


# ---------------------------------------------------------------------------
# Integration: runs against the in-memory SQLite fixture above (no live DB needed).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_register_and_login_flow(db_session):
    test_email = "test_student_auth@ausa.edu.az"
    test_password = "password123"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "gpa": 3.7,
                "gpa_scale": "4.0",
                "budget": 20000.0,
                "degree_level": "master",
            },
        )
        assert reg_res.status_code == 201

        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": test_password},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        profile = me_res.json()
        assert profile["email"] == test_email
        assert profile["gpa"] == 3.7
        assert profile["gpa_scale"] == "4.0"


@pytest.mark.asyncio
async def test_an_azerbaijani_attestat_average_registers(db_session):
    """4.5 out of 5 is an excellent attestat, and `le=4.0` used to reject it as invalid.

    This is the product's own user being turned away at the door by a bound that assumed a
    US grading scale. The grade is stored with the scale it is on, and comes back with it,
    so no consumer can draw it against a four-point bar.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "attestat@ausa.edu.az",
                "password": "password123",
                "gpa": 4.5,
                "gpa_scale": "5.0",
            },
        )
        assert reg_res.status_code == 201

        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "attestat@ausa.edu.az", "password": "password123"},
        )
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login_res.json()['access_token']}"},
        )
        assert me_res.json()["gpa"] == 4.5
        assert me_res.json()["gpa_scale"] == "5.0"


@pytest.mark.asyncio
async def test_a_grade_without_its_scale_is_refused(db_session):
    """Storing 4.5 with no scale leaves a row nobody can read back: excellent attestat, or
    impossible US GPA? The registration is rejected rather than guessing which."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/register",
            json={"email": "noscale@ausa.edu.az", "password": "password123", "gpa": 4.5},
        )
        assert res.status_code == 422
        assert "gpa_scale is required" in res.text


@pytest.mark.asyncio
async def test_a_grade_outside_its_own_scale_is_refused(db_session):
    """4.5 on a four-point scale is not a strict grade, it is an impossible one -- almost
    always the wrong scale picked. Said now rather than silently failing every comparison
    downstream."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "outofrange@ausa.edu.az",
                "password": "password123",
                "gpa": 4.5,
                "gpa_scale": "4.0",
            },
        )
        assert res.status_code == 422
        assert "outside the 4.0 scale" in res.text


@pytest.mark.asyncio
async def test_register_without_academic_fields_stores_null_not_invented_defaults(db_session):
    """A student who registers with only email/password has no GPA, budget, etc.

    This previously persisted gpa=3.5, budget=15000, ielts=7.0, toefl=95,
    degree_level="master", field_of_study="Computer Science", country="Azerbaijan"
    for every such registration -- a fabricated profile, indistinguishable from data
    the student actually entered, that then drove every eligibility check made for
    them (evaluate_match's hard filters).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={"email": "bare_register@ausa.edu.az", "password": "password123"},
        )
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]

        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        profile = me_res.json()
        assert profile["gpa"] is None
        assert profile["budget"] is None
        assert profile["ielts"] is None
        assert profile["toefl"] is None
        assert profile["degree_level"] is None
        assert profile["field_of_study"] is None
        assert profile["country"] is None


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "someone@ausa.edu.az", "password": "correct-password"},
        )
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "someone@ausa.edu.az", "password": "wrong-password"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_unknown_email(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@ausa.edu.az", "password": "password123"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_valid_token_for_nonexistent_student_is_rejected(db_session):
    """A correctly signed token for a student who is not in the database is not valid.

    This is the case that previously returned a synthetic Student with gpa 3.7.
    """
    token = create_access_token(subject=999999)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_database_failure_never_issues_a_token():
    """A database outage must not authenticate anyone.

    Previously any exception here produced a valid token for student 101, so an
    outage -- or anything that could provoke one -- granted access to a real account.
    """
    class FailingSession:
        async def execute(self, *args, **kwargs):
            raise SQLAlchemyError("connection refused")

    async def _get_failing_db():
        yield FailingSession()

    app.dependency_overrides[get_db] = _get_failing_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            login_res = await client.post(
                "/api/v1/auth/login",
                json={"email": "test_student_auth@ausa.edu.az", "password": "password123"},
            )
            assert login_res.status_code == 503
            assert "access_token" not in login_res.json()

            me_res = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {create_access_token(subject=101)}"},
            )
            assert me_res.status_code == 503
    finally:
        app.dependency_overrides.clear()
