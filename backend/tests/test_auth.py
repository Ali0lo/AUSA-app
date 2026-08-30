"""
Authentication tests.

These run against a real in-memory SQLite database. The previous version ran against
no database at all: every request hit an `except Exception` fallback that issued a
token for student 101 and returned a synthetic profile whose email and GPA were copied
from this file. The flow it asserted was therefore never executed -- the test certified
an authentication bypass rather than catching it.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.main import app
from app.models.student import Student


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
            raise RuntimeError("connection refused")

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
