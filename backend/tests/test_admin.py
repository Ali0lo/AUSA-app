import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.v1.admin import DEMO_FLAGGED_PROGRAMS
from app.core.database import Base, get_db
from app.main import app
from app.models.program import Program as ProgramModel

client = TestClient(app)


@pytest_asyncio.fixture
async def db_session():
    """A real SQLite database holding only `programs`.

    Base.metadata as a whole cannot be created here: university_documents uses pgvector's
    Vector type, which SQLite has no equivalent for. The review queue touches only programs.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[ProgramModel.__table__])

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        async def _get_test_db():
            yield session

        app.dependency_overrides[get_db] = _get_test_db
        yield session
        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.mark.asyncio
async def test_empty_review_queue_returns_nothing_not_demo_data(db_session):
    """An empty queue is an empty list -- never the demo programmes.

    This previously asserted `len(data) >= 1`, which held only because the endpoint fell
    through to DEMO_FLAGGED_PROGRAMS whenever the database was empty or unreadable. A
    reviewer was shown four invented programmes (Heidelberg, TUM and friends) as records
    awaiting approval, and the test guarding the review queue asserted the fabrication.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/v1/admin/programs/flagged")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_flagged_queue_returns_real_rows_and_preserves_unscored_confidence(db_session):
    """A row nobody scored reports confidence null, not an invented number.

    `p.confidence_score or 70.0` used to fill one in -- and because 0.0 is falsy it also
    rewrote a genuine zero-confidence record as 70.0, which is the difference between
    "worthless extraction" and "nearly good enough to publish".
    """
    db_session.add_all([
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
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/v1/admin/programs/flagged")

    assert response.status_code == 200
    data = response.json()
    by_name = {item["university_name"]: item for item in data}

    assert by_name["Real University"]["confidence_score"] is None
    assert by_name["Zero Confidence University"]["confidence_score"] == 0.0

    demo_ids = {p["id"] for p in DEMO_FLAGGED_PROGRAMS}
    assert not demo_ids & {item["id"] for item in data}


def test_verify_and_approve_program():
    payload = {
        "university_name": "Heidelberg University",
        "program_name": "B.Sc. Computer Science",
        "tuition_fee": 3000.0,
        "min_gpa": 3.0,
        "min_ielts": 6.5,
        "verified_by": "admin@ausa.edu.az"
    }
    response = client.put("/api/v1/admin/programs/1001/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verification_status"] == "verified"
    assert data["program_id"] == 1001


def test_seed_database_endpoint():
    response = client.post("/api/v1/admin/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "programs_seeded" in data
    assert "scholarships_seeded" in data
    assert "documents_seeded" in data
