"""Authentication unit tests plus regression tests for the auth-bypass fixes.

Historical note: `test_auth_register_and_login_flow` used to pass with no database,
because login fell back to minting a token for subject 101 and get_current_user
fabricated a Student with email "test_student_auth@ausa.edu.az" and gpa 3.7 -- the
exact values this test asserts. The fallback existed to satisfy the test, and it made
any signed token authenticate and any credentials succeed during a database outage.
That flow is now a real integration test, and the bypasses have regression coverage
that needs no database.
"""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import engine
from app.core.security import create_access_token, get_password_hash, verify_password
from app.main import app


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
# Integration: needs a live database.
# ---------------------------------------------------------------------------


@requires_db
@pytest.mark.asyncio
async def test_auth_register_and_login_flow():
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
        assert reg_res.status_code in [201, 400]  # Created or already exists

        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": test_password},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]

        me_res = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200
        profile = me_res.json()
        assert profile["email"] == test_email
        assert profile["gpa"] == 3.7
