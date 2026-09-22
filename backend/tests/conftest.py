"""Test settings, pinned before the application configuration is imported.

Without this the suite inherits whatever `backend/.env` the developer happens to
have, so `pytest` on one machine dials a real PostgreSQL and on another does not.
CI never hit it because the workflow writes a throwaway `.env` first -- which meant
the green badge was reporting on a configuration no developer actually ran.

Environment variables take precedence over the `.env` file in pydantic-settings, so
setting them here overrides a local file without editing or reading it.

This pins configuration only. It does not stub the database away: tests that want a
real PostgreSQL still ask for one by name through AUSA_TEST_POSTGRES_URL.
"""
import os

os.environ.setdefault("ENVIRONMENT", "testing")
# In-memory SQLite, matching the CI workflow. A test that reaches a database at all
# should reach a disposable one; a test that reaches the developer's database is
# reporting on their data, not on the code.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
