"""Seed a local SQLite database with the curated catalogue, for the demo.

`run_backend.bat` provisions PostgreSQL with pgvector, which every teammate would
otherwise have to install to see the product run. The guest walkthrough -- routes,
target gap, funding, timeline, SOP, DIM, the Azerbaijan section -- needs exactly one
table, so for a demo that cost buys nothing.

This seeds the real catalogue from the same curated CSVs the PostgreSQL bootstrap
reads. Nothing is stubbed or invented: the rows are identical, only the engine differs.
Accounts, saved applications and document search still need PostgreSQL, and are
deliberately not part of the demo.

    cd backend
    ..\\.venv\\Scripts\\python.exe -m scripts.demo_seed

Then start the API against the same file:

    set DATABASE_URL=sqlite+aiosqlite:///./demo.db
    ..\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --port 8000
"""
import asyncio
import os
import sys

# Pinned before app.core.config is imported. Environment variables take precedence
# over `.env` in pydantic-settings, so this leaves a teammate's PostgreSQL settings
# untouched -- and an explicit DATABASE_URL still wins, for seeding somewhere else.
DEMO_DATABASE_URL = "sqlite+aiosqlite:///./demo.db"
os.environ.setdefault("DATABASE_URL", DEMO_DATABASE_URL)

from app.core.database import AsyncSessionLocal, Base, engine  # noqa: E402
from app.models.qualifications import ProgramRequirement  # noqa: E402
from scripts.load_program_requirements import (  # noqa: E402
    CATALOGUE_FILES,
    load_program_requirements,
)


async def seed() -> int:
    missing = [path for path in CATALOGUE_FILES if not path.exists()]
    if missing:
        # Loading nothing and reporting success would leave an empty catalogue that
        # looks like a product with no universities in it.
        for path in missing:
            print(f"ERROR: curated catalogue file not found: {path}", file=sys.stderr)
        return 1

    async with engine.begin() as connection:
        # Only the catalogue table. The full schema carries JSONB and pgvector columns
        # that SQLite cannot render, and the demo does not read them.
        await connection.run_sync(
            Base.metadata.create_all, tables=[ProgramRequirement.__table__]
        )

    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                for path in CATALOGUE_FILES:
                    counts = await load_program_requirements(session, path, commit=False)
                    print(f"{path.name}: {counts}")
    finally:
        await engine.dispose()

    print(f"\nSeeded {os.environ['DATABASE_URL']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(seed()))
