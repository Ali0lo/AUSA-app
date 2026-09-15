"""Catalogue release gates: real SQL imports, profile checks and authenticated review."""
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.domain.routes import StudentRouteProfile
from app.domain.scholarship_definitions import TURKIYE_BURSLARI
from app.services.scholarship_eligibility import assess_scholarship
from app.main import app
from app.models.student import Student
from app.models.qualifications import ProgramRequirement
from app.models.dp_catalogue import DPCatalogueEntry
from app.services.catalogue_evidence import content_fingerprint
from app.services.university_requirements import universities_accepting, assess_requirement
from scripts.bootstrap_catalogue import CATALOGUE_FILES, validate_catalogue
from scripts.load_program_requirements import CuratedRowError, read_rows, parse_row, load_program_requirements


def raw(**values):
    row = dict(university_name='Test University', program_name='Computing', level='master',
               intake_year='2026', country_code='GB', entry_qualification_accepted='bachelor_degree',
               source_url='https://example.edu/admissions', retrieved_at='2026-09-15T00:00:00Z',
               tuition_per_year='10000', currency='GBP', requirement_scope='degree',
               evidence=json.dumps([dict(url='https://example.edu/admissions', fields=['tuition_per_year'],
                                         checked_at='2026-09-15', note='Annual overseas fee.')]))
    row.update(values)
    return row


def csv_file(tmp_path, *records):
    path = tmp_path / 'curated.csv'
    fields = list(dict.fromkeys(k for row in records for k in row))
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    return path


def test_empty_file_still_requires_valid_headers(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("university_name,unexpected\n")
    with pytest.raises(CuratedRowError, match="invalid headers"):
        read_rows(path)


@pytest.mark.asyncio
async def test_shipped_catalogue_names_masters_and_both_german_paths(session):
    for path in CATALOGUE_FILES:
        await load_program_requirements(session, path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/routes/assess", json={
            "level_sought": "master", "qualification_held": "bachelor_degree", "ielts": 7,
        })
        assert response.status_code == 200, response.text
        plans = response.json()["plans"]
        for country in ("TR", "GB", "CN"):
            universities = [u for plan in plans if plan["destination_country"] == country for u in plan["universities"]]
            assert universities, country
            assert all(u["level"] == "master" and u["entry_qualification_accepted"] == "bachelor_degree" for u in universities)
    prep = await universities_accepting(session, country_code="DE", level="bachelor", qualification="one_year_university")
    fsp = await universities_accepting(session, country_code="DE", level="bachelor", qualification="feststellungspruefung")
    assert len(prep) >= 2 and len(fsp) == 3


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine('sqlite+aiosqlite://')
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=[Student.__table__, ProgramRequirement.__table__, DPCatalogueEntry.__table__])
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        async def database():
            yield session
        app.dependency_overrides[get_db] = database
        try:
            yield session
        finally:
            app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.parametrize('change', [
    {'tuition_per_year': 'nan'}, {'application_fee': '-1'}, {'intake_year': '2026.5'},
    {'language_minimum_score': '7'}, {'gpa_minimum': '4'}, {'currency': ''},
    {'entry_qualification_accepted': 'any'}, {'application_deadline': '20260228'},
    {'source_url': 'javascript:alert(1)'}, {'source_url': 'https://qebulai.az/list'},
    {'source_url': 'https://www.daad.de/deutschland/foerderung/stipendiendatenbank/00462.en.html'},
    {'verified_by': 'invented@example.edu'}, {'provenance': 'human-verified'},
    {'evidence': '[{}]'}, {'unexpected_column': 'x'},
])
def test_invalid_curated_claims_are_rejected(change):
    with pytest.raises(CuratedRowError):
        parse_row(raw(**change))


def test_release_data_has_distinct_masters_and_preserves_german_paths():
    assert validate_catalogue() >= 47
    rows = [row for path in CATALOGUE_FILES for row in read_rows(path)]
    masters = [r for r in rows if r['level'] == 'master']
    assert len(masters) >= 25
    assert len({r['country_code'] for r in masters}) >= 4
    assert len([r for r in masters if r['country_code'] == 'US']) >= 5
    assert all(r['entry_qualification_accepted'] == 'bachelor_degree' for r in masters)
    german = [r for r in rows if r['country_code'] == 'DE' and r['level'] == 'bachelor']
    assert len({r['university_name'] for r in german if r['entry_qualification_accepted'] == 'one_year_university'}) >= 2
    assert len([r for r in german if r['entry_qualification_accepted'] == 'feststellungspruefung']) == 3
    assert all(r['tuition_per_year'] is not None and r['currency'] or r['notes'] for r in rows)
    assert all(r['provenance'] != 'human-verified' and r['verified_by'] is None for r in rows)


@pytest.mark.asyncio
async def test_alternative_qualifications_survive_and_import_is_idempotent(session, tmp_path):
    path = csv_file(tmp_path, raw(entry_qualification_accepted='feststellungspruefung'), raw(entry_qualification_accepted='one_year_university'))
    assert (await load_program_requirements(session, path))['inserted'] == 2
    assert (await load_program_requirements(session, path))['inserted'] == 0
    assert await session.scalar(select(func.count()).select_from(ProgramRequirement)) == 2


@pytest.mark.asyncio
async def test_nullable_qualification_cannot_evade_unique_key(session):
    session.add_all([ProgramRequirement(**parse_row(raw(entry_qualification_accepted=''))) for _ in range(2)])
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
async def test_bad_later_row_and_dry_run_do_not_commit(session, tmp_path):
    with pytest.raises(CuratedRowError):
        await load_program_requirements(session, csv_file(tmp_path, raw(), raw(program_name='Other', tuition_per_year='nan')))
    assert await session.scalar(select(func.count()).select_from(ProgramRequirement)) == 0
    await load_program_requirements(session, csv_file(tmp_path, raw()), dry_run=True)
    assert await session.scalar(select(func.count()).select_from(ProgramRequirement)) == 0


@pytest.mark.asyncio
async def test_new_year_does_not_resurrect_an_old_qualification(session):
    session.add_all([ProgramRequirement(**parse_row(raw(intake_year='2025', entry_qualification_accepted='one_year_university'))),
                     ProgramRequirement(**parse_row(raw(intake_year='2026', entry_qualification_accepted='bachelor_degree')))])
    await session.commit()
    assert not await universities_accepting(session, country_code='GB', level='master', qualification='one_year_university')


def test_score_subscores_deadlines_and_foundation_scope_remain_advisory():
    row = ProgramRequirement(**parse_row(raw(language_test='IELTS', language_minimum_score='7', application_deadline='2026-03-27', requirement_scope='foundation')))
    match = assess_requirement(row, StudentRouteProfile(level_sought='master', qualification_held='bachelor_degree', ielts=6), today=date(2026, 9, 15))
    assert match.application_status == 'deadline_passed'
    assert any('below' in c for c in match.checks)
    assert any('foundation-entry' in c for c in match.checks)
    assert any('human review' in c for c in match.checks)


@pytest.mark.asyncio
async def test_review_requires_auth_current_revision_and_explicit_source_check(session, tmp_path, monkeypatch):
    path = csv_file(tmp_path, raw())
    await load_program_requirements(session, path)
    session.add(Student(email='reviewer@example.edu', hashed_password='test'))
    await session.commit()
    admin = await session.scalar(select(Student))
    monkeypatch.setattr(settings, 'ADMIN_EMAILS', ['reviewer@example.edu'])
    headers = {'Authorization': 'Bearer ' + create_access_token(subject=admin.id)}
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        assert (await client.get('/api/v1/admin/catalogue?level=master')).status_code == 401
        queue = (await client.get('/api/v1/admin/catalogue?level=master', headers=headers)).json()
        item = queue[0]
        url = f"/api/v1/admin/catalogue/{item['requirement']['id']}/verify"
        assert (await client.put(url, headers=headers, json={'revision':item['revision'], 'source_checked':False})).status_code == 422
        assert (await client.put(url, headers=headers, json={'revision':'0'*64, 'source_checked':True})).status_code == 409
        verified = await client.put(url, headers=headers, json={'revision':item['revision'], 'source_checked':True})
        assert verified.status_code == 200, verified.text
        assert verified.json()['requirement']['provenance'] == 'human-verified'
        record = await session.scalar(select(ProgramRequirement))
        assert record.verified_by == admin.email and record.verified_at is not None
        await load_program_requirements(session, path)
        assert record.provenance == 'human-verified', 'unchanged reimport must retain the real review'
        path = csv_file(tmp_path, raw(tuition_per_year='12000'))
        await load_program_requirements(session, path)
        assert record.provenance == 'claude-extracted' and record.verified_at is None
        assert record.verified_by is None
        assert (await client.put(url, headers=headers, json={'revision':item['revision'], 'source_checked':True})).status_code == 409
        response = await client.post('/api/v1/catalogue/assess?university=Test%20University', json={'level_sought':'master','qualification_held':'bachelor_degree'})
        assert response.status_code == 200 and response.json()['items'][0]['tuition_per_year'] == 12000
        empty = await client.get('/api/v1/catalogue?level=bachelor')
        assert empty.json() == {'status':'not_collected','total':0,'items':[]}
        invalid = await client.post('/api/v1/catalogue/assess?university=Test', json={'level_sought':'master','qualification_held':'bachelor_degree','ielts':10})
        assert invalid.status_code == 422


@pytest.mark.parametrize('level,age,blocked', [('bachelor',20,False),('bachelor',21,True),('master',29,False),('master',30,True)])
def test_turkiye_age_boundaries_are_level_specific(level, age, blocked):
    profile=StudentRouteProfile(level_sought=level, qualification_held='bachelor_degree' if level=='master' else 'attestat', age=age)
    assessed=assess_scholarship(TURKIYE_BURSLARI, profile, ('TR',))
    assert bool(assessed.gates_blocked) == blocked
    assert assessed.status != 'open', 'Other unmodelled published criteria require review'
