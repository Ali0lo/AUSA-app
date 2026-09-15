"""Opt-in migration checks. AUSA_TEST_POSTGRES_URL MUST name a disposable database.

These tests reset its public schema. They never use the application's DATABASE_URL.
"""
import asyncio
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

URL = os.environ.get('AUSA_TEST_POSTGRES_URL')
pytestmark = pytest.mark.skipif(not URL, reason='Set AUSA_TEST_POSTGRES_URL to a disposable PostgreSQL database for migration checks')
BACKEND = Path(__file__).resolve().parents[1]
ENV = {**os.environ, 'DATABASE_URL': URL or '', 'DEBUG': 'false'}


def sql(statement):
    async def run():
        engine = create_async_engine(URL)
        try:
            async with engine.begin() as connection:
                result = await connection.execute(text(statement))
                return result.fetchall() if result.returns_rows else []
        finally:
            await engine.dispose()
    return asyncio.run(run())


def command(*args):
    return subprocess.run([sys.executable, *args], cwd=BACKEND, env=ENV, capture_output=True, text=True, timeout=90)


@pytest.fixture(autouse=True)
def empty_database():
    sql('DROP SCHEMA public CASCADE')
    sql('CREATE SCHEMA public')


def test_fresh_migration_bootstrap_repeat_and_null_uniqueness():
    result = command('-m', 'scripts.bootstrap_catalogue')
    assert result.returncode == 0, result.stderr
    assert sql('SELECT version_num FROM alembic_version')[0][0] == 'e5f6a7b8c9d0'
    assert sql('SELECT count(*) FROM program_requirements')[0][0] == 47
    assert sql('SELECT count(*) FROM dp_catalogue')[0][0] == 4121
    result = command('-m', 'scripts.bootstrap_catalogue')
    assert result.returncode == 0, result.stderr
    assert sql('SELECT count(*) FROM program_requirements')[0][0] == 47
    assert sql('SELECT count(*) FROM dp_catalogue')[0][0] == 4121
    sql("INSERT INTO program_requirements (university_name,program_name,level,intake_year,country_code,source_url,retrieved_at) VALUES ('Test','Nullable','master',2026,'GB','https://example.edu',now())")
    # Assert the server's precise constraint, with an internal exception block so
    # the test also works with embedded PostgreSQL wire adapters.
    sql("""DO $$ DECLARE caught BOOLEAN := FALSE; violated TEXT;
    BEGIN
      BEGIN
        INSERT INTO program_requirements (university_name,program_name,level,intake_year,country_code,source_url,retrieved_at)
        VALUES ('Test','Nullable','master',2026,'GB','https://example.edu',now());
      EXCEPTION WHEN unique_violation THEN
        GET STACKED DIAGNOSTICS violated = CONSTRAINT_NAME;
        IF violated <> 'uq_program_requirement_entry' THEN RAISE; END IF;
        caught := TRUE;
      END;
      IF NOT caught THEN RAISE EXCEPTION 'Nullable duplicate was accepted'; END IF;
    END $$""")


def test_versioned_upgrade_keeps_team_records_and_existing_reviews():
    result = command('-m', 'alembic', 'upgrade', 'd4e5f6a7b8c9')
    assert result.returncode == 0, result.stderr
    sql("INSERT INTO students (email,gpa,gpa_scale) VALUES ('team@example.invalid',4.5,'5.0')")
    sql("INSERT INTO program_requirements (university_name,program_name,level,intake_year,country_code,source_url,retrieved_at,provenance,verified_by) VALUES ('Team University','Team Programme','master',2026,'DE','https://example.edu',now(),'human-verified','team@example.invalid')")
    result = command('-m', 'scripts.bootstrap_catalogue')
    assert result.returncode == 0, result.stderr
    assert sql("SELECT gpa,gpa_scale FROM students WHERE email='team@example.invalid'")[0] == (4.5,'5.0')
    assert sql("SELECT provenance,verified_by FROM program_requirements WHERE university_name='Team University'")[0] == ('human-verified','team@example.invalid')
    assert sql('SELECT count(*) FROM program_requirements')[0][0] == 48


def test_original_unversioned_schema_is_adopted_but_unknown_shapes_are_not():
    # Reconstruct the original migration schema plus the tracker table that create_all
    # historically made outside Alembic. Remove version metadata to emulate that setup.
    result = command('-m', 'alembic', 'upgrade', 'd4e5f6a7b8c9')
    assert result.returncode == 0, result.stderr
    result = command('-c', 'import asyncio; from app.core.database import engine; from app.models.application import StudentApplication\nasync def run():\n async with engine.begin() as c: await c.run_sync(StudentApplication.__table__.create)\n await engine.dispose()\nasyncio.run(run())')
    assert result.returncode == 0, result.stderr
    sql('DROP TABLE alembic_version')
    sql("INSERT INTO student_applications (student_id,university_name,program_name,stage) VALUES ('team','Existing university','Existing programme','shortlisted')")
    sql('ALTER TABLE students ADD COLUMN team_custom_column TEXT')
    rejected = command('-m', 'scripts.bootstrap_catalogue')
    assert rejected.returncode != 0 and 'No automatic stamp was made' in rejected.stderr
    assert not sql("SELECT tablename FROM pg_tables WHERE tablename='alembic_version'")
    sql('ALTER TABLE students DROP COLUMN team_custom_column')
    adopted = command('-m', 'scripts.bootstrap_catalogue')
    assert adopted.returncode == 0, adopted.stderr
    assert 'Recognised the original' in adopted.stdout
    assert sql("SELECT program_name FROM student_applications WHERE student_id='team'")[0][0] == 'Existing programme'
