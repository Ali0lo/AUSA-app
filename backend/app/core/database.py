from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# asyncpg waits 60 seconds for a connection by default, and the OS often waits ~20
# before that. Neither is a useful answer to "is the database there?" -- the
# catalogue endpoints hold a curated-CSV fallback and cannot reach it until the
# connection attempt gives up, so an absent or misconfigured PostgreSQL turns every
# page into a minute of blank screen instead of an instant answer.
CONNECT_TIMEOUT_SECONDS = 5


def build_engine(database_url: str):
    """Build the async engine for a database URL, bounding how long a connect may take."""
    connect_args = {}
    if database_url.startswith("postgresql"):
        connect_args["timeout"] = CONNECT_TIMEOUT_SECONDS

    return create_async_engine(
        database_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


# Initialize Async Engine
engine = build_engine(settings.DATABASE_URL)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base model class for all SQLAlchemy ORM models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an asynchronous database session.
    Yields an AsyncSession instance and closes it after the request is finished.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
