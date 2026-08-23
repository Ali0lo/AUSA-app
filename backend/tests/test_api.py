from unittest.mock import AsyncMock
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app


@pytest.fixture
def override_db_dependency():
    """Override database session dependency for API testing."""
    from unittest.mock import MagicMock
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    async def _get_test_db():
        yield mock_session

    app.dependency_overrides[get_db] = _get_test_db
    yield mock_session
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_root = await client.get("/")
        assert res_root.status_code == 200
        assert res_root.json()["status"] == "online"

        res_health = await client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"

        res_v1_health = await client.get("/api/v1/health")
        assert res_v1_health.status_code == 200
        assert res_v1_health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_matching_evaluate_endpoint():
    payload = {
        "student": {
            "gpa": 3.8,
            "budget": 20000.0,
            "ielts": 7.5,
            "degree_level": "master",
            "field_of_study": "Computer Science"
        },
        "program": {
            "university_name": "TU Munich",
            "program_name": "M.Sc. Informatics",
            "degree_level": "master",
            "min_gpa": 3.0,
            "tuition_fee": 15000.0,
            "currency": "EUR",
            "min_ielts": 6.5
        }
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/matching/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_eligible"] is True
        assert data["overall_match_percentage"] == 100.0
        assert data["program_name"] == "M.Sc. Informatics"
        assert "breakdown" in data


@pytest.mark.asyncio
async def test_chat_ask_rag_endpoint(override_db_dependency):
    payload = {
        "question": "What is the minimum IELTS requirement?",
        "top_k": 3
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/chat/ask", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "answer" in data
        assert "sources" in data


@pytest.mark.asyncio
async def test_chat_agent_endpoint():
    payload = {
        "message": "What documents am I missing?",
        "student_id": "std_100",
        "target_program_id": "prog_200"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/chat/agent", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "response" in data
        assert data["student_id"] == "std_100"
        assert "application_stage" in data
