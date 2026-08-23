import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
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


@pytest.mark.asyncio
async def test_auth_register_and_login_flow():
    test_email = "test_student_auth@ausa.edu.az"
    test_password = "password123"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "gpa": 3.7,
                "budget": 20000.0,
                "degree_level": "master"
            }
        )
        assert reg_res.status_code in [201, 400]  # Created or already exists

        # Login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": test_password}
        )
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data
        token = token_data["access_token"]

        # Fetch profile via /me
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_res.status_code == 200
        profile = me_res.json()
        assert profile["email"] == test_email
        assert profile["gpa"] == 3.7
