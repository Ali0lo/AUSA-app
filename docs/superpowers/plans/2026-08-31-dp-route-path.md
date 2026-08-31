# DP Route Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the six blocking defects, then ship the Dövlət Proqramı path end to end — a student's qualifications in, a classified set of routes and a funded programme list out.

**Architecture:** Three layers, added on the existing FastAPI/SQLAlchemy spine without a rewrite. (1) A catalogue layer: the two official DP CSVs loaded idempotently into `dp_catalogue`, keyed by level. (2) A profile layer: `student_qualifications` and `program_requirements`, both level-keyed. (3) A pure-Python route engine that classifies each hand-written, cited route against a profile as OPEN / UNLOCKABLE / BLOCKED, composes them to a two-hop cap, and treats the DP itself as one more route.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, Postgres/asyncpg (SQLite/aiosqlite + StaticPool in tests), pydantic v2 / pydantic-settings, pandas, pytest + pytest-asyncio, httpx. **No new dependencies.**

**Spec:** [`docs/superpowers/specs/2026-08-31-route-first-advisor-design.md`](../specs/2026-08-31-route-first-advisor-design.md) — steps 0 through 4 of its §10 build order.

## Global Constraints

- **ADR-0004, no silent fallbacks.** No `except Exception` that invents a value and continues. A failure raises or returns an honest error; an empty result is returned as empty. This is the project's central promise and three of the defects below are it being broken in code.
- **`verified_by` is written only by a human action** through the verify endpoint. No loader, seeder or extractor ever sets it.
- **Provenance is one of `seed` / `claude-extracted` / `human-verified`.** Loaded catalogue rows are `seed`. Nothing becomes `human-verified` without a person opening the source.
- **Every extracted or loaded row carries `source_url` and `retrieved_at`.**
- **Level is `bachelor` or `master`, and it is part of every key** — never a filter applied afterwards. **PhD is out of scope** (spec §7).
- **Scholarship wording: "possibly eligible", never "you will get it"** (spec §5.2). No generated text or UI label may promise an award. Permitted form: "you meet the published requirements for this award", with the gate that was checked shown beside it.
- **Six countries:** Turkey (TR), Germany (DE), United Kingdom (GB), USA (US), Poland (PL), China (CN).
- **Numbers come from the source or from arithmetic, never from a default.** A missing value renders as "not stated", not as a plausible figure.
- **Tests run from `backend/`.** The virtualenv is at the repository root: `.venv` (not `backend/.venv` — the README is wrong and Task 5 fixes it). Baseline before this plan: **78 passed**.
- **The per-task "expected N passed" figures drift, and the delta is what binds.** Review rounds legitimately add covering tests the plan did not predict, so by Task 4 the actual count already ran ahead of the projection. Verify the **number of tests your task adds** and that the suite is **green**, and report the actual total. A count below the projection means something was skipped; a count above it is normal and needs only a line in your report saying what the extra tests cover.
- **Every task ends green.** Run the whole suite, not only the new test.

---

## File Structure

**Task 1-5 — the defects (spec §9):**

| File | Responsibility |
|---|---|
| `backend/app/core/config.py` | gains `ADMIN_EMAILS`, the admin allowlist. Fails closed when unset |
| `backend/app/api/v1/admin.py` | real `require_admin_user`; database-first verify; demo store deleted |
| `backend/app/api/v1/export.py` | rejects an empty payload instead of inventing a student |
| `backend/app/services/pdf_export.py` | renders "not stated" instead of a fabricated default |
| `backend/scripts/quarantine_fallback_rows.py` | finds and quarantines rows written by the deleted extraction fallback |
| `README.md` | corrected: links, the ML claim, the venv path, the deleted scrapers |

**Task 6-10 — the DP path (spec §10 steps 1-4):**

| File | Responsibility |
|---|---|
| `backend/app/models/dp_catalogue.py` | `dp_catalogue` — the funded-programme spine, one row per (level, country, university, programme, year) |
| `backend/app/models/qualifications.py` | `student_qualifications` and `program_requirements`, both level-keyed |
| `backend/alembic/versions/2026_08_31_0002-*.py` | one migration creating all three tables |
| `backend/scripts/collect_dp_catalogue.py` | downloads the two official CSVs to `data/raw/azerbaijan/` |
| `backend/scripts/load_dp_catalogue.py` | idempotent CSV → `dp_catalogue` loader |
| `backend/app/domain/routes.py` | `Route`, `ExamRequirement`, `StudentRouteProfile`, `RouteAssessment` — pure data, no I/O |
| `backend/app/domain/route_definitions.py` | the hand-written cited routes. **The highest-value data in the product** |
| `backend/app/services/route_engine.py` | `classify_route`, `assess_routes`, `compose_two_hop` |
| `backend/app/services/dp_eligibility.py` | the DP funding gate, and the funded programme query |
| `backend/app/api/v1/routes.py` | `POST /api/v1/routes/assess` |

Route definitions live in **code, not a table**, deviating from spec §9's `routes` table. Reason: there are ~17 of them, they change roughly once a year, and each must be read alongside its citation in review. A Python module gets that review in git for free; a table needs a migration, a seeder, and a way to diff what a seeder changed. Reversible in one task if a route ever needs editing without a deploy.

---

## Task 1: Authenticate the admin endpoints

`require_admin_user` currently returns `{"is_admin": True}` unconditionally. Every admin endpoint — including the one that publishes unverified programme data to students — is open to anyone who can reach the API. This is the most serious defect in the repository.

**Approach:** an email allowlist in settings, checked against the authenticated student from the existing JWT flow. It fails closed (empty allowlist denies everyone), needs no migration, and reuses `get_current_user` rather than inventing a second identity path. The trade-off is that granting admin means an env change and a restart; with two or three curators on a 15-day deadline that is the right side of the trade.

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/api/v1/admin.py:107-111` (the dependency), and the three endpoint signatures at `:186-189`, `:242-247`, `:332-335`
- Modify: `backend/tests/test_admin.py` (the fixture and the two existing queue tests now need a token)
- Test: `backend/tests/test_admin.py`

**Interfaces:**
- Consumes: `app.api.deps.get_current_user` (returns a `Student`, raises 401 on a missing/invalid token), `app.core.config.settings`
- Produces: `require_admin_user(current_user: Student = Depends(get_current_user)) -> Student` — raises 403 for an authenticated non-admin. Endpoints receive a `Student`, so `admin.email` replaces `admin.get("email")`.

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_admin.py`. Note the fixture change: `get_current_user` reads `students`, so the test database needs that table too.

```python
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.program import Program as ProgramModel
from app.models.student import Student

ADMIN_EMAIL = "curator@ausa.edu.az"
STUDENT_EMAIL = "ordinary_student@ausa.edu.az"


@pytest_asyncio.fixture
async def admin_env(monkeypatch):
    """A database holding `programs` and `students`, plus one admin and one non-admin.

    Yields (session, admin_headers, student_headers).

    Base.metadata as a whole cannot be created here: university_documents uses pgvector's
    Vector type, which SQLite has no equivalent for.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[ProgramModel.__table__, Student.__table__],
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        admin = Student(email=ADMIN_EMAIL)
        ordinary = Student(email=STUDENT_EMAIL)
        session.add_all([admin, ordinary])
        await session.commit()
        await session.refresh(admin)
        await session.refresh(ordinary)

        monkeypatch.setattr(settings, "ADMIN_EMAILS", [ADMIN_EMAIL])

        async def _get_test_db():
            yield session

        app.dependency_overrides[get_db] = _get_test_db
        yield (
            session,
            {"Authorization": f"Bearer {create_access_token(subject=admin.id)}"},
            {"Authorization": f"Bearer {create_access_token(subject=ordinary.id)}"},
        )
        app.dependency_overrides.clear()

    await engine.dispose()


@pytest.mark.asyncio
async def test_admin_queue_rejects_an_anonymous_caller(admin_env):
    """No token, no queue. This endpoint used to be open to the entire internet."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        assert (await c.get("/api/v1/admin/programs/flagged")).status_code == 401


@pytest.mark.asyncio
async def test_admin_queue_rejects_an_authenticated_non_admin(admin_env):
    """A valid student token is not an admin token."""
    _, _, student_headers = admin_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/admin/programs/flagged", headers=student_headers)
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_verify_endpoint_rejects_an_anonymous_caller(admin_env):
    """Publishing unverified data to students required no credentials at all."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.put("/api/v1/admin/programs/1/verify", json={"program_name": "X"})
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_admin_on_the_allowlist_is_admitted(admin_env):
    _, admin_headers, _ = admin_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/admin/programs/flagged", headers=admin_headers)
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_an_empty_allowlist_admits_nobody(admin_env, monkeypatch):
    """The default is deny-all. An unconfigured deployment must not be an open one."""
    _, admin_headers, _ = admin_env
    monkeypatch.setattr(settings, "ADMIN_EMAILS", [])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.get("/api/v1/admin/programs/flagged", headers=admin_headers)
        assert res.status_code == 403
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_admin.py -v -k "anonymous or non_admin or allowlist or admitted"`

Expected: FAIL — the anonymous and non-admin cases return 200, and `settings` has no attribute `ADMIN_EMAILS` (monkeypatch raises `AttributeError`).

- [ ] **Step 3: Add the setting**

In `backend/app/core/config.py`, after the JWT block:

```python
    # Administrator allowlist. Empty means nobody is an administrator -- an
    # unconfigured deployment must be a closed one, not an open one.
    ADMIN_EMAILS: List[str] = Field(
        default_factory=list,
        description="Emails permitted to use /api/v1/admin. Empty denies everyone.",
    )
```

- [ ] **Step 4: Implement the dependency**

Replace `backend/app/api/v1/admin.py:107-111` entirely:

```python
async def require_admin_user(
    current_user: Student = Depends(get_current_user),
) -> Student:
    """Admit only an authenticated student whose email is on the allowlist.

    This previously returned {"is_admin": True} for every caller, so the entire admin
    surface -- including the endpoint that publishes unverified programme data to
    students -- was open to anyone who could reach the API. An empty allowlist denies
    everyone: a deployment that forgot to configure this is closed, not open.
    """
    allowed = {email.strip().lower() for email in settings.ADMIN_EMAILS if email.strip()}
    if not current_user.email or current_user.email.strip().lower() not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required for this endpoint.",
        )
    return current_user
```

Add the imports at the top of `admin.py`:

```python
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.student import Student
```

- [ ] **Step 5: Update the three endpoint signatures**

In all three endpoints (`get_flagged_programs`, `verify_and_approve_program`, `seed_database_endpoint`) change the parameter from

```python
    admin: Dict[str, Any] = Depends(require_admin_user),
```

to

```python
    admin: Student = Depends(require_admin_user),
```

and in `verify_and_approve_program` change line 250 from

```python
    verified_by_email = payload.verified_by or admin.get("email", "admin@ausa.edu.az")
```

to

```python
    # The signed-in administrator is the authority on who verified a row. A caller-supplied
    # verified_by is a claim about a third party, and ADR-0004 rule 2 gives that field to
    # the person who actually opened the source.
    verified_by_email = admin.email
```

Delete `verified_by` from `VerifyProgramPayload` (line 154) — it is now decided by the token, not the body.

- [ ] **Step 6: Update the two existing queue tests to authenticate**

`test_empty_review_queue_returns_nothing_not_demo_data` and
`test_flagged_queue_returns_real_rows_and_preserves_unscored_confidence` currently use the
`db_session` fixture and send no token, so they will now get 401. Change both to take
`admin_env`, unpack it, and pass the header:

```python
@pytest.mark.asyncio
async def test_empty_review_queue_returns_nothing_not_demo_data(admin_env):
    """An empty queue is an empty list -- never the demo programmes."""
    _, admin_headers, _ = admin_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/v1/admin/programs/flagged", headers=admin_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_flagged_queue_returns_real_rows_and_preserves_unscored_confidence(admin_env):
    """A row nobody scored reports confidence null, not an invented number."""
    session, admin_headers, _ = admin_env
    session.add_all([
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
    await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/api/v1/admin/programs/flagged", headers=admin_headers)

    assert response.status_code == 200
    by_name = {item["university_name"]: item for item in response.json()}
    assert by_name["Real University"]["confidence_score"] is None
    assert by_name["Zero Confidence University"]["confidence_score"] == 0.0
```

Delete the now-unused `db_session` fixture from this file, and delete the
`DEMO_FLAGGED_PROGRAMS` assertion at the end of the second test — Task 2 deletes that
constant, and the import would break.

The other two tests in this file (`test_verify_and_approve_program`,
`test_seed_database_endpoint`) will now fail with 401. **Leave them failing; Task 2
replaces them.** Note this in your report.

- [ ] **Step 7: Run the tests**

Run: `cd backend && python -m pytest tests/test_admin.py -v`

Expected: the five new auth tests and the two updated queue tests PASS.
`test_verify_and_approve_program` and `test_seed_database_endpoint` FAIL with 401 — expected, and Task 2's problem.

- [ ] **Step 8: Document the setting**

Add to `.env.example` (create it if absent, and check it is not caught by `.gitignore`'s `*.env` — the filename `.env.example` does not match that pattern, so it is committable):

```
# Comma-free JSON list of administrator emails. Empty (the default) denies everyone.
ADMIN_EMAILS=["curator@ausa.edu.az"]
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/core/config.py backend/app/api/v1/admin.py backend/tests/test_admin.py .env.example
git commit -m "Require a real administrator to reach the admin endpoints"
```

---

## Task 2: Make the verify endpoint write to the database, and delete the demo store

Three defects in one endpoint. `verify_and_approve_program` checks the in-memory
`DEMO_FLAGGED_PROGRAMS` list *before* the database, so verifying id 1001 returns
"successfully verified and published" having written nothing. If the row is in neither
place it *still* returns success. And `except Exception: pass` at line 312 swallows a write
failure into that same success. `seed_database_endpoint` has the matching defect: any
failure returns `status="success"` with invented counts.

**Files:**
- Modify: `backend/app/api/v1/admin.py:24-101` (delete `DEMO_FLAGGED_PROGRAMS`), `:242-322` (verify), `:332-348` (seed)
- Modify: `backend/tests/test_admin.py` (replace the two tests left failing by Task 1)
- Test: `backend/tests/test_admin.py`

**Interfaces:**
- Consumes: `require_admin_user` from Task 1, yielding a `Student`
- Produces: `PUT /api/v1/admin/programs/{id}/verify` → 200 only when a row was written; 404 when the programme does not exist; 503 when the database is unreachable

- [ ] **Step 1: Write the failing tests**

Replace `test_verify_and_approve_program` and `test_seed_database_endpoint` in
`backend/tests/test_admin.py` with:

```python
@pytest.mark.asyncio
async def test_verify_writes_to_the_database(admin_env):
    session, admin_headers, _ = admin_env
    program = ProgramModel(
        university_name="Real University",
        program_name="B.Sc. Real Programme",
        verification_status="flagged_for_review",
    )
    session.add(program)
    await session.commit()
    await session.refresh(program)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.put(
            f"/api/v1/admin/programs/{program.id}/verify",
            json={"program_name": "B.Sc. Corrected Name", "min_ielts": 6.5},
            headers=admin_headers,
        )

    assert res.status_code == 200
    assert res.json()["verification_status"] == "verified"

    await session.refresh(program)
    assert program.program_name == "B.Sc. Corrected Name"
    assert program.min_ielts == 6.5
    assert program.verification_status == "verified"
    assert program.verified_by == ADMIN_EMAIL


@pytest.mark.asyncio
async def test_verify_reports_404_for_a_programme_that_does_not_exist(admin_env):
    """The endpoint used to answer 'successfully verified and published' for any id.

    Ids 1001-1004 hit an in-memory demo list and returned success having written nothing;
    every other unknown id fell through to a success response at the end of the function.
    """
    _, admin_headers, _ = admin_env
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        for unknown_id in (1001, 424242):
            res = await c.put(
                f"/api/v1/admin/programs/{unknown_id}/verify",
                json={"program_name": "Does Not Exist"},
                headers=admin_headers,
            )
            assert res.status_code == 404, f"id {unknown_id} was not reported missing"


@pytest.mark.asyncio
async def test_seed_endpoint_reports_failure_as_failure(admin_env, monkeypatch):
    """A failed seed used to return status='success' with invented counts (7/3/3)."""
    _, admin_headers, _ = admin_env

    async def _explode(session):
        raise RuntimeError("seeding is broken")

    monkeypatch.setattr("scripts.seed_db.seed_database", _explode)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        res = await c.post("/api/v1/admin/seed", headers=admin_headers)

    assert res.status_code == 503
    assert "success" not in res.text.lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_admin.py -v -k "writes_to_the_database or 404 or failure_as_failure"`

Expected: FAIL — the 404 test gets 200 for both ids, and the seed test gets 200 with `status="success"`.

- [ ] **Step 3: Delete the demo store**

Delete `backend/app/api/v1/admin.py:21-101` in full — the `DEMO_FLAGGED_PROGRAMS` comment block and list. Nothing may import it afterwards.

- [ ] **Step 4: Rewrite the verify endpoint body**

Replace the body of `verify_and_approve_program` (everything from line 249 to the end of the function) with:

```python
    now_iso = datetime.now(timezone.utc).isoformat()
    # The signed-in administrator is the authority on who verified a row.
    verified_by_email = admin.email

    try:
        stmt = select(ProgramModel).where(ProgramModel.id == program_id)
        result = await db.execute(stmt)
        prog = result.scalar_one_or_none()
    except Exception as exc:
        # A write that could not be attempted is not a verification. This used to be
        # `except Exception: pass` followed by an unconditional success response.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot reach the programs store; nothing was verified.",
        ) from exc

    if prog is None:
        # A programme we do not hold cannot be verified. The endpoint previously answered
        # "successfully verified and published" here -- for ids 1001-1004 from an in-memory
        # demo list, and for every other unknown id from a trailing success response.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No programme with id {program_id}.",
        )

    if payload.university_name: prog.university_name = payload.university_name
    if payload.program_name: prog.program_name = payload.program_name
    if payload.degree_level: prog.degree_level = payload.degree_level
    if payload.field: prog.field = payload.field
    if payload.country: prog.country = payload.country
    if payload.min_gpa is not None: prog.min_gpa = payload.min_gpa
    if payload.min_ielts is not None: prog.min_ielts = payload.min_ielts
    if payload.tuition_fee is not None: prog.tuition_fee = payload.tuition_fee
    if payload.currency: prog.currency = payload.currency

    prog.verification_status = "verified"
    prog.confidence_score = 100.0
    prog.verified_by = verified_by_email

    try:
        await db.commit()
        await db.refresh(prog)
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The verification could not be saved.",
        ) from exc

    return VerifyProgramResponse(
        message=f"Program '{prog.program_name}' verified in the database.",
        program_id=program_id,
        verification_status="verified",
        verified_by=verified_by_email,
        last_updated=now_iso,
        program_details={
            "id": prog.id,
            "university_name": prog.university_name,
            "program_name": prog.program_name,
            "tuition_fee": prog.tuition_fee,
            "min_gpa": prog.min_gpa,
            "min_ielts": prog.min_ielts,
        },
    )
```

- [ ] **Step 5: Rewrite the seed endpoint's failure path**

Replace the `except` clause of `seed_database_endpoint`:

```python
    except Exception as exc:
        # A seed that failed did not seed anything. This used to return status="success"
        # with counts of 7/3/3 that nobody had written, so a broken seeder looked healthy.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database seeding failed: {exc}",
        ) from exc
```

- [ ] **Step 6: Run the whole suite**

Run: `cd backend && python -m pytest -q`

Expected: PASS. The count changes from the 78 baseline: `test_admin.py` had four tests and now has ten (five added in Task 1, two replaced by three here), so expect **84 passed**. If any other test imported `DEMO_FLAGGED_PROGRAMS`, fix that import — nothing should reference it.

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/admin.py backend/tests/test_admin.py
git commit -m "Verify against the database, and delete the demo store that faked it"
```

---

## Task 3: Stop the PDF export inventing a student

`export.py:40-56` supplies a default student (`gpa 3.65`, `ielts 7.0`) and a default
programme (TU Munich, `blocked_account_eur 11208.0`) when the payload carries neither. A
caller who sends only a motivation letter gets back a dossier about a person who does not
exist. `except Exception: pass` at lines 73-74 and 90-91 does the same thing when the
lookup fails: the invented student stays and is rendered. This is the same fabrication
class fixed in `extraction.py` on 31 August, in a second location.

**Files:**
- Modify: `backend/app/api/v1/export.py:40-91`
- Modify: `backend/app/services/pdf_export.py:176-182`
- Test: `backend/tests/test_pdf_export.py`

**Interfaces:**
- Produces: `POST /api/v1/export/motivation-letter/pdf` → 422 when neither student data nor a resolvable `student_id` is present; 404 when a supplied id does not exist; 503 when the database is unreachable

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_pdf_export.py`:

```python
def test_export_refuses_to_invent_a_student():
    """An empty payload used to produce a dossier about a fictional person.

    The defaults were gpa 3.65, ielts 7.0, and a TU Munich programme with an
    11208.0 EUR blocked account -- rendered into a PDF the student could submit.
    """
    response = client.post(
        "/api/v1/export/motivation-letter/pdf",
        json={"motivation_letter_text": "Dear Admissions Committee, ..."},
    )
    assert response.status_code == 422
    assert b"%PDF" not in response.content


def test_export_refuses_when_only_the_programme_is_known():
    """Half a dossier is still a fabricated dossier."""
    response = client.post(
        "/api/v1/export/motivation-letter/pdf",
        json={
            "motivation_letter_text": "Dear Admissions Committee, ...",
            "program_data": {
                "university_name": "TU Munich",
                "program_name": "M.Sc. Informatics",
            },
        },
    )
    assert response.status_code == 422


def test_pdf_renders_missing_values_as_not_stated():
    """A missing GPA is 'not stated', never 3.5. A missing blocked account is not
    'Not Required' either -- we were not told, and that is a different claim."""
    pdf_bytes = generate_application_dossier_pdf(
        student_data={"email": "someone@ausa.edu.az"},
        program_data={"university_name": "Some University", "program_name": "Some Programme"},
        motivation_letter="Dear Admissions Committee, ...",
    )
    assert pdf_bytes.startswith(b"%PDF")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_pdf_export.py -v -k "invent or only_the_programme or not_stated"`

Expected: the first two FAIL with 200 instead of 422. The third passes already (it exercises the renderer directly) — it is a regression guard for Step 4.

- [ ] **Step 3: Reject an incomplete payload**

Replace `backend/app/api/v1/export.py:40-91` with:

```python
    student_dict: Optional[Dict[str, Any]] = payload.student_data
    program_dict: Optional[Dict[str, Any]] = payload.program_data

    if payload.student_id:
        try:
            stmt = select(StudentModel).where(StudentModel.id == payload.student_id)
            res = await db.execute(stmt)
            st = res.scalar_one_or_none()
        except Exception as exc:
            # A profile we could not read is not a profile we may invent.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot reach the student store; no dossier was generated.",
            ) from exc
        if st is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No student with id {payload.student_id}.",
            )
        student_dict = {
            "email": st.email,
            "gpa": st.gpa,
            "ielts": st.ielts,
            "toefl": st.toefl,
            "degree_level": st.degree_level,
            "field_of_study": st.field_of_study,
        }

    if payload.program_id:
        try:
            stmt = select(ProgramModel).where(ProgramModel.id == payload.program_id)
            res = await db.execute(stmt)
            pr = res.scalar_one_or_none()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot reach the programs store; no dossier was generated.",
            ) from exc
        if pr is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No programme with id {payload.program_id}.",
            )
        program_dict = {
            "university_name": pr.university_name,
            "program_name": pr.program_name,
            "degree_level": pr.degree_level,
            "country": pr.country,
            "tuition_fee": pr.tuition_fee,
            "deadline": str(pr.deadline) if pr.deadline else None,
        }

    # A dossier is a document the student submits under their own name. Filling either half
    # of it with a plausible default -- gpa 3.65, a TU Munich programme, an 11208 EUR
    # blocked account -- is the fabrication ADR-0004 forbids, and it is worse here than in
    # the pipeline because the output leaves the building.
    if not student_dict or not program_dict:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "A dossier needs both a student and a programme. Supply student_data or a "
                "resolvable student_id, and program_data or a resolvable program_id."
            ),
        )
```

Add `HTTPException` to the `fastapi` import line at the top of the file.

- [ ] **Step 4: Remove the fabricated defaults from the renderer**

Replace `backend/app/services/pdf_export.py:176-182` with:

```python
    # No defaults. A student who did not give us a GPA has no GPA, and printing 3.5 or a
    # 11,208 EUR blocked account into a document they submit invents a fact about them.
    # `is not None` rather than truthiness: a genuine 0.0 is a value, not a blank.
    gpa = student_data.get("gpa")
    gpa_val = f"{gpa:.2f}" if gpa is not None else "Not stated"
    ielts = student_data.get("ielts")
    ielts_val = f"{ielts:.1f}" if ielts is not None else "Not stated"
    toefl = student_data.get("toefl")
    toefl_val = str(toefl) if toefl is not None else "Not stated"

    tuition = program_data.get("tuition_fee")
    tuition_val = f"${tuition:,.2f} USD" if tuition is not None else "Not stated"
    dim = program_data.get("dim_score_required")
    dim_req = str(dim) if dim is not None else "Not stated"
    blocked = program_data.get("blocked_account_eur")
    # "Not Required" was a claim about the country's visa rules that we had not checked.
    blocked_acc = f"€{blocked:,.2f}" if blocked is not None else "Not stated"
```

- [ ] **Step 5: Run the whole suite**

Run: `cd backend && python -m pytest -q`

Expected: **87 passed** (84 from Task 2, plus three).

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/export.py backend/app/services/pdf_export.py backend/tests/test_pdf_export.py
git commit -m "Refuse to export a dossier about a student who does not exist"
```

---

## Task 4: Quarantine the rows the deleted extraction fallback wrote

The fallback removed on 31 August wrote rows with `university_name="Extracted University"`,
`program_name="Extracted Program"`, a hardcoded `blocked_account_eur=11208.0`, and a
confidence score that reached 100.0 from three regex hits — high enough to clear the 85%
review threshold and publish without a human ever seeing it. Deleting the code does not
remove what it wrote. Any such row must stop being served before the catalogue is trusted.

**Files:**
- Create: `backend/scripts/quarantine_fallback_rows.py`
- Test: `backend/tests/test_quarantine_fallback_rows.py`

**Interfaces:**
- Produces: `find_suspect_programs(session) -> list[Program]` and
  `quarantine(session, programs) -> int`. The script's `--dry-run` reports without writing.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_quarantine_fallback_rows.py`:

```python
"""The deleted extraction fallback left rows behind. This finds them.

Marker values, all from the removed code path: a university named "Extracted University",
a programme named "Extracted Program", and the note "Extracted via fallback parser."
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.program import Program as ProgramModel
from scripts.quarantine_fallback_rows import find_suspect_programs, quarantine


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[ProgramModel.__table__])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_finds_only_the_fallback_rows(session):
    session.add_all([
        ProgramModel(university_name="Extracted University", program_name="B.Sc. Something"),
        ProgramModel(university_name="TU Munich", program_name="Extracted Program"),
        ProgramModel(
            university_name="Real University",
            program_name="B.Sc. Real",
            requirements_text="Extracted via fallback parser.",
        ),
        ProgramModel(university_name="Honest University", program_name="B.Sc. Honest"),
    ])
    await session.commit()

    suspects = await find_suspect_programs(session)
    assert {p.university_name for p in suspects} == {
        "Extracted University", "TU Munich", "Real University",
    }


@pytest.mark.asyncio
async def test_quarantine_deactivates_without_deleting(session):
    """Deactivated, not deleted. A human still needs to look at what the fallback wrote."""
    session.add(ProgramModel(university_name="Extracted University", program_name="B.Sc. X"))
    await session.commit()

    count = await quarantine(session, await find_suspect_programs(session))
    assert count == 1

    row = (await session.execute(select(ProgramModel))).scalars().one()
    assert row.is_active is False
    assert row.verification_status == "quarantined_fallback_extraction"
    assert row.confidence_score is None


@pytest.mark.asyncio
async def test_a_clean_database_yields_nothing(session):
    session.add(ProgramModel(university_name="Honest University", program_name="B.Sc. Honest"))
    await session.commit()
    assert await find_suspect_programs(session) == []
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend && python -m pytest tests/test_quarantine_fallback_rows.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.quarantine_fallback_rows'`.

- [ ] **Step 3: Write the script**

Create `backend/scripts/quarantine_fallback_rows.py`:

```python
"""Quarantine programme rows written by the extraction fallback deleted on 31 Aug 2026.

That fallback invented a record from regex hits when the LLM call failed: university
"Extracted University", programme "Extracted Program", a hardcoded 11208.0 EUR blocked
account, and a confidence score that reached 100.0 from three matches -- clearing the 85%
review threshold and publishing without a human ever seeing the row.

Rows are deactivated and marked, never deleted: a person still has to decide what the
fallback got wrong, and deleting the evidence would make that impossible.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.program import Program  # noqa: E402

QUARANTINE_STATUS = "quarantined_fallback_extraction"

FALLBACK_UNIVERSITY_NAME = "Extracted University"
FALLBACK_PROGRAM_NAME = "Extracted Program"
FALLBACK_NOTE = "Extracted via fallback parser."


async def find_suspect_programs(session: AsyncSession) -> list[Program]:
    """Every row carrying a marker the deleted fallback is known to have written."""
    stmt = select(Program).where(
        or_(
            Program.university_name == FALLBACK_UNIVERSITY_NAME,
            Program.program_name == FALLBACK_PROGRAM_NAME,
            Program.requirements_text == FALLBACK_NOTE,
        )
    )
    return list((await session.execute(stmt)).scalars().all())


async def quarantine(session: AsyncSession, programs: list[Program]) -> int:
    """Deactivate and mark. Returns how many rows were changed."""
    for program in programs:
        program.is_active = False
        program.verification_status = QUARANTINE_STATUS
        # The fallback's confidence was computed from regex hit count, so it measured
        # nothing. NULL is what "nobody scored this" looks like.
        program.confidence_score = None
    await session.commit()
    return len(programs)


async def _main(dry_run: bool) -> None:
    async with AsyncSessionLocal() as session:
        suspects = await find_suspect_programs(session)
        for program in suspects:
            print(f"  id={program.id}  {program.university_name} / {program.program_name}")
        if dry_run:
            print(f"{len(suspects)} row(s) would be quarantined. Nothing was written.")
            return
        print(f"{await quarantine(session, suspects)} row(s) quarantined.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    asyncio.run(_main(parser.parse_args().dry_run))
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && python -m pytest tests/test_quarantine_fallback_rows.py -v`

Expected: PASS, 3 tests.

- [ ] **Step 5: Run it against the real database and record the answer**

Run: `cd backend && python scripts/quarantine_fallback_rows.py --dry-run`

Record the count in your report. If the database is not reachable in your environment, say
so explicitly rather than reporting zero — "no rows" and "could not look" are different
answers, and `docs/review/2026-08-31-root-docs-review.md` §5 asks this question directly.

- [ ] **Step 6: Run the whole suite and commit**

Run: `cd backend && python -m pytest -q` — expected **90 passed**.

```bash
git add backend/scripts/quarantine_fallback_rows.py backend/tests/test_quarantine_fallback_rows.py
git commit -m "Quarantine the rows the deleted extraction fallback wrote"
```

---

## Task 5: Correct the README

The README is the public face of a graded project and it is wrong in four ways: three ADR
links point at files that do not exist, it claims the ML predicts admission probability
(ADR-0008 withdrew that), it advertises DAAD scrapers that were deleted, and it gives a
virtualenv path that is not where the virtualenv is.

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Find every broken claim**

Run these and keep the output; you are fixing exactly what they report:

```bash
grep -n "docs/adr" README.md
ls docs/adr/
grep -ni "probability\|success rate\|venv\|daad\|scraper" README.md
```

- [ ] **Step 2: Fix the ADR links**

Every `docs/adr/...` link in README.md must resolve to a file that `ls docs/adr/` listed.
Correct the path where the file exists under another name; delete the link where the file
does not exist at all. Do not invent a target.

- [ ] **Step 3: Correct the ML claim**

Replace any wording that says the model predicts admission probability or success rate.
The accurate claim, from spec §4.2:

> The model predicts **next year's DİM cutoff** for Azerbaijani university programmes —
> the one place in the project where admission is mechanical, so `P(cutoff ≤ your score)`
> is the success rate rather than a proxy for it. Measured against a department-mean
> baseline of 57.37, the model scores 41.34. Elsewhere the product gives eligibility and
> cost, and shows no probability at all.

- [ ] **Step 4: Fix the venv path and remove the deleted scrapers**

The virtualenv is `.venv` at the repository root, so the setup instructions are:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r backend/requirements.txt
cd backend && python -m pytest -q
```

Delete any section describing DAAD scrapers that no longer exist. If you want to say what
replaced them: DAAD is now read through its JSON API (spec §5.3), which is not yet built.

- [ ] **Step 5: Verify every link resolves**

```bash
grep -o "](\./[^)]*\|](docs/[^)]*\|](backend/[^)]*" README.md | sed 's/](//' | while read -r p; do [ -e "$p" ] || echo "BROKEN: $p"; done
```

Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "Correct the README: broken links, the withdrawn ML claim, the venv path"
```

---

## Task 6: Load the DP catalogue

The two official CSVs are the catalogue spine (spec §2.2). Both were downloaded and profiled
on 31 August, and every count in the spec was confirmed against the files themselves.

**What the data actually looks like** — verified, not assumed:

```
dp-bakalavr-2026.csv   1,214 rows   123 universities   15 countries   level "bakalavriat"
dp-master-2026.csv     2,907 rows   223 universities   33 countries   level "magistratura"
Columns: Nömrə, Təhsil səviyyəsi, Ölkə, Universitet, Təhsil proqramı
Encoding: utf-8-sig (the files carry a BOM; utf-8 alone mangles the first column name)
No nulls in any column of either file.
Zero duplicates on (Təhsil səviyyəsi, Ölkə, Universitet, Təhsil proqramı).
```

**Two traps.** First, `Universitet` values are wrapped in literal double-quote characters
*inside* the field — `"Technical University of Munich"` arrives as a Python string with a
leading and trailing `"`. This is true of 4121/4121 university values and 4120/4121
programme values (one programme row is unquoted), and it is not true of `Ölkə` at all. Strip
them, or every name is stored wrong and no join to any other source will ever match. Second,
`Nömrə` is a per-file sequence number, not an identifier — it restarts at 1 in each file and
carries no meaning across years. It is not part of the key and is not stored.

**Files:**
- Create: `backend/app/models/dp_catalogue.py`
- Create: `backend/alembic/versions/2026_08_31_0002-b2c3d4e5f6a7_add_dp_catalogue.py`
- Create: `backend/scripts/collect_dp_catalogue.py`
- Create: `backend/scripts/load_dp_catalogue.py`
- Test: `backend/tests/test_load_dp_catalogue.py`

**Interfaces:**
- Produces:
  - `DPCatalogueEntry` ORM model, table `dp_catalogue`
  - `rows_from_csv(path: Path, source_url: str) -> list[dict]`
  - `load_csv(session: AsyncSession, path: Path, source_url: str) -> int` — returns rows inserted
  - `LEVEL_BY_SOURCE_VALUE: dict[str, str]`, `COUNTRY_CODE_BY_SOURCE_NAME: dict[str, str]`
  - Task 10 consumes `DPCatalogueEntry` and both mappings.

- [ ] **Step 1: Write the model**

Create `backend/app/models/dp_catalogue.py`:

```python
from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from app.core.database import Base


class DPCatalogueEntry(Base):
    """One funded programme from the Dövlət Proqramı list.

    The state publishes exactly which universities and programmes it will pay for, per
    level, as open data. This table is that list and nothing else -- no requirements, no
    fees. Those live in program_requirements and join to this on (university, programme).
    """
    __tablename__ = "dp_catalogue"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 'bachelor' | 'master'. Part of the key, never a filter: the state publishes two
    # separate lists with different countries in them -- the USA and Poland have zero
    # bachelor programmes against 289 and 8 master's.
    level = Column(String(20), nullable=False, index=True)
    # The country exactly as the source names it, in Azerbaijani. Kept verbatim so a row
    # can always be traced back to its line in the CSV.
    country_source = Column(String(120), nullable=False)
    # ISO-3166 alpha-2, and only for the six countries in scope. NULL for the other 27:
    # we have not checked how the ministry spells them and will not guess.
    country_code = Column(String(2), nullable=True, index=True)
    university_name = Column(String(300), nullable=False, index=True)
    program_name = Column(String(500), nullable=False)
    intake_year = Column(Integer, nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=False)
    # Stays NULL. Only a person who has opened the source may set it (ADR-0004 rule 2).
    verified_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "level", "country_source", "university_name", "program_name", "intake_year",
            name="uq_dp_catalogue_entry",
        ),
    )
```

- [ ] **Step 2: Write the migration**

Create `backend/alembic/versions/2026_08_31_0002-b2c3d4e5f6a7_add_dp_catalogue.py`:

```python
"""add dp_catalogue

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-31
"""
import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dp_catalogue",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("country_source", sa.String(length=120), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("university_name", sa.String(length=300), nullable=False),
        sa.Column("program_name", sa.String(length=500), nullable=False),
        sa.Column("intake_year", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "level", "country_source", "university_name", "program_name", "intake_year",
            name="uq_dp_catalogue_entry",
        ),
    )
    op.create_index("ix_dp_catalogue_id", "dp_catalogue", ["id"])
    op.create_index("ix_dp_catalogue_level", "dp_catalogue", ["level"])
    op.create_index("ix_dp_catalogue_country_code", "dp_catalogue", ["country_code"])
    op.create_index("ix_dp_catalogue_university_name", "dp_catalogue", ["university_name"])
    op.create_index("ix_dp_catalogue_intake_year", "dp_catalogue", ["intake_year"])


def downgrade() -> None:
    op.drop_table("dp_catalogue")
```

- [ ] **Step 3: Write the failing loader test**

Create `backend/tests/test_load_dp_catalogue.py`:

```python
"""Loader tests for the Dövlət Proqramı catalogue.

The fixture CSV reproduces the real file's two traps: a utf-8 BOM, and university and
programme values wrapped in literal double-quote characters inside the field.
"""

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.dp_catalogue import DPCatalogueEntry
from scripts.load_dp_catalogue import load_csv, rows_from_csv

SOURCE_URL = "https://admin.opendata.az/dataset/example/resource/example/download/dp-test.csv"

CSV_BODY = (
    "﻿Nömrə,Təhsil səviyyəsi,Ölkə,Universitet,Təhsil proqramı\n"
    '1,bakalavriat,Almaniya Federativ Respublikası,"""Technical University of Munich""","""Architecture"""\n'
    '2,bakalavriat,Türkiyə Respublikası,"""Bogazici University""","""Computer Engineering"""\n'
    '3,bakalavriat,Malayziya,"""Universiti Malaya""","""Chemistry"""\n'
)


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "dp-bakalavr-2026.csv"
    path.write_text(CSV_BODY, encoding="utf-8")
    return path


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[DPCatalogueEntry.__table__])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def test_quotes_are_stripped_from_names(csv_path):
    """Every university value in the real file is wrapped in literal double quotes.

    Storing them keeps the quote characters in the name, and no join to any other source
    will ever match.
    """
    rows = rows_from_csv(csv_path, SOURCE_URL)
    assert rows[0]["university_name"] == "Technical University of Munich"
    assert rows[0]["program_name"] == "Architecture"


def test_level_and_country_are_mapped(csv_path):
    rows = rows_from_csv(csv_path, SOURCE_URL)
    assert rows[0]["level"] == "bachelor"
    assert rows[0]["country_code"] == "DE"
    assert rows[1]["country_code"] == "TR"


def test_a_country_outside_scope_gets_no_code_rather_than_a_guess(csv_path):
    """27 of the 33 countries are out of scope. NULL is the honest answer for them."""
    rows = rows_from_csv(csv_path, SOURCE_URL)
    malaysia = next(r for r in rows if r["country_source"] == "Malayziya")
    assert malaysia["country_code"] is None
    assert malaysia["university_name"] == "Universiti Malaya"


def test_an_unknown_level_raises_rather_than_loading(tmp_path):
    """A level we cannot map is a changed source file, not a row to guess at."""
    path = tmp_path / "dp-broken-2026.csv"
    path.write_text(
        "﻿Nömrə,Təhsil səviyyəsi,Ölkə,Universitet,Təhsil proqramı\n"
        '1,doktorantura,Malayziya,"""X University""","""Y"""\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="doktorantura"):
        rows_from_csv(path, SOURCE_URL)


def test_a_missing_column_raises_rather_than_loading_a_partial_table(tmp_path):
    path = tmp_path / "dp-missing-2026.csv"
    path.write_text("﻿Nömrə,Ölkə\n1,Malayziya\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        rows_from_csv(path, SOURCE_URL)


@pytest.mark.asyncio
async def test_loading_twice_inserts_nothing_the_second_time(session, csv_path):
    assert await load_csv(session, csv_path, SOURCE_URL) == 3
    assert await load_csv(session, csv_path, SOURCE_URL) == 0
    total = (await session.execute(select(func.count()).select_from(DPCatalogueEntry))).scalar()
    assert total == 3


@pytest.mark.asyncio
async def test_every_row_carries_its_source(session, csv_path):
    """ADR-0004: a row that cannot be traced back to where it came from is not evidence."""
    await load_csv(session, csv_path, SOURCE_URL)
    rows = (await session.execute(select(DPCatalogueEntry))).scalars().all()
    assert all(r.source_url == SOURCE_URL for r in rows)
    assert all(r.retrieved_at is not None for r in rows)
    assert all(r.verified_by is None for r in rows)
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_load_dp_catalogue.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.load_dp_catalogue'`.

- [ ] **Step 5: Write the loader**

Create `backend/scripts/load_dp_catalogue.py`:

```python
"""Load the Dövlət Proqramı catalogue CSVs into dp_catalogue.

Idempotent: a row is identified by (level, country_source, university_name, program_name,
intake_year). The real files have zero duplicates on that key, verified 31 Aug 2026.

Nothing here fills a gap. A missing column or an unmappable level raises rather than
loading a partial table, and verified_by is never written -- only a person who has opened
the source may set it (ADR-0004 rule 2).
"""

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.models.dp_catalogue import DPCatalogueEntry  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402

COLUMN_LEVEL = "Təhsil səviyyəsi"
COLUMN_COUNTRY = "Ölkə"
COLUMN_UNIVERSITY = "Universitet"
COLUMN_PROGRAM = "Təhsil proqramı"
REQUIRED_COLUMNS = {COLUMN_LEVEL, COLUMN_COUNTRY, COLUMN_UNIVERSITY, COLUMN_PROGRAM}

# The source's own words for the two levels in scope. Doktorantura also appears in the
# ministry's programme but PhD is out of scope (spec §7), so it raises rather than loading.
LEVEL_BY_SOURCE_VALUE = {
    "bakalavriat": "bachelor",
    "magistratura": "master",
}

# The ministry writes country names in Azerbaijani long form. These six strings were read
# off the real files on 31 Aug 2026 -- note Poland is "Polşa", not "Polşa Respublikası".
# The other 27 countries map to None: they are out of scope and guessing their spelling
# would put a code on a row nobody checked.
COUNTRY_CODE_BY_SOURCE_NAME = {
    "Türkiyə Respublikası": "TR",
    "Almaniya Federativ Respublikası": "DE",
    "Birləşmiş Krallıq": "GB",
    "Amerika Birləşmiş Ştatları": "US",
    "Polşa": "PL",
    "Çin Xalq Respublikası": "CN",
}


def _clean_name(value: Any) -> str:
    """Strip the literal double quotes the source wraps every name in.

    In dp-bakalavr-2026.csv and dp-master-2026.csv the Universitet field contains
    `"Technical University of Munich"` -- quote characters inside the value, present on
    4121 of 4121 university rows. Left in place they become part of the stored name and
    nothing joins to it.
    """
    return str(value).strip().strip('"').strip()


def rows_from_csv(path: Path, source_url: str) -> list[dict]:
    """Parse one DP CSV into ORM kwargs. Raises if the file is not what we expect."""
    # utf-8-sig, not utf-8: both files carry a BOM, which otherwise ends up glued to the
    # first column name and makes every column lookup miss.
    frame = pd.read_csv(path, encoding="utf-8-sig")

    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: {sorted(missing)}. "
            "Re-download from the portal rather than loading a partial table."
        )

    # The year is in the filename, which is how the ministry versions these files
    # (dp-bakalavr-2026.csv). A file without one is a file we cannot date, and dating a
    # catalogue wrongly silently mixes two academic years in one table.
    digits = "".join(c for c in path.stem if c.isdigit())
    if len(digits) < 4:
        raise ValueError(
            f"{path.name} has no four-digit intake year in its filename. Keep the "
            "ministry's own name, e.g. dp-bakalavr-2026.csv."
        )
    intake_year = int(digits[-4:])
    retrieved_at = datetime.now(timezone.utc)

    rows: list[dict] = []
    for record in frame.to_dict(orient="records"):
        source_level = str(record[COLUMN_LEVEL]).strip()
        if source_level not in LEVEL_BY_SOURCE_VALUE:
            raise ValueError(
                f"{path.name} contains education level {source_level!r}, which this loader "
                f"does not map. Known: {sorted(LEVEL_BY_SOURCE_VALUE)}. PhD is out of scope."
            )
        country_source = str(record[COLUMN_COUNTRY]).strip()
        rows.append({
            "level": LEVEL_BY_SOURCE_VALUE[source_level],
            "country_source": country_source,
            "country_code": COUNTRY_CODE_BY_SOURCE_NAME.get(country_source),
            "university_name": _clean_name(record[COLUMN_UNIVERSITY]),
            "program_name": _clean_name(record[COLUMN_PROGRAM]),
            "intake_year": intake_year,
            "source_url": source_url,
            "retrieved_at": retrieved_at,
        })
    return rows


def _natural_key(level, country_source, university_name, program_name, intake_year):
    """The one place allowed to build the identity key, for CSV rows and database rows alike.

    Both sides route through here so a type difference between a parsed value and a value
    read back from the database cannot silently defeat the "is this row already there"
    check and duplicate the whole file on a re-run.
    """
    return (
        str(level), str(country_source), str(university_name),
        str(program_name), int(intake_year),
    )


async def load_csv(session: AsyncSession, path: Path, source_url: str) -> int:
    """Insert rows not already present. Returns the number inserted."""
    rows = rows_from_csv(path, source_url)

    existing = {
        _natural_key(*db_row)
        for db_row in (
            await session.execute(
                select(
                    DPCatalogueEntry.level,
                    DPCatalogueEntry.country_source,
                    DPCatalogueEntry.university_name,
                    DPCatalogueEntry.program_name,
                    DPCatalogueEntry.intake_year,
                )
            )
        ).all()
    }

    inserted = 0
    for row in rows:
        key = _natural_key(
            row["level"], row["country_source"], row["university_name"],
            row["program_name"], row["intake_year"],
        )
        if key in existing:
            continue
        session.add(DPCatalogueEntry(**row))
        existing.add(key)
        inserted += 1

    await session.commit()
    return inserted


async def _main(pairs: list[tuple[Path, str]]) -> None:
    async with AsyncSessionLocal() as session:
        for path, source_url in pairs:
            print(f"{path.name}: {await load_csv(session, path, source_url)} new rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="a DP CSV from data/raw/azerbaijan/")
    parser.add_argument("--source-url", required=True, help="the portal URL it came from")
    args = parser.parse_args()
    asyncio.run(_main([(args.csv, args.source_url)]))
```

- [ ] **Step 6: Run the tests**

Run: `cd backend && python -m pytest tests/test_load_dp_catalogue.py -v`

Expected: PASS, 7 tests.

- [ ] **Step 7: Write the collector**

Create `backend/scripts/collect_dp_catalogue.py`. The two resource URLs were read off the
IDDA open-data portal on 31 August 2026 and both download successfully:

```python
"""Download the Dövlət Proqramı catalogue CSVs from the national open-data portal.

Publisher: Elm və Təhsil Nazirliyi (Ministry of Science and Education), via IDDA's CKAN
portal at opendata.az. Updated once a year, so this is not a job that needs scheduling --
run it when the ministry publishes the next academic year's list.

Downloads only. Parsing and loading are load_dp_catalogue.py's job.
"""

import argparse
import urllib.request
from pathlib import Path

DEFAULT_DESTINATION = Path(__file__).resolve().parents[2] / "data" / "raw" / "azerbaijan"

RESOURCES = {
    "dp-bakalavr-2026.csv": (
        "https://admin.opendata.az/dataset/6d33d639-af0a-46a8-89f5-c20c606cc0f3"
        "/resource/f28081ed-31d0-4ca6-aeb5-4d5a419e986c/download/dp-bakalavr-2026.csv"
    ),
    "dp-master-2026.csv": (
        "https://admin.opendata.az/dataset/0f00bf5a-c10d-4109-80b5-9beecc783027"
        "/resource/7907fba0-acb0-4017-95a7-2411774243a0/download/dp-master-2026.csv"
    ),
}


def download(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for filename, url in RESOURCES.items():
        target = destination / filename
        request = urllib.request.Request(url, headers={"User-Agent": "AUSA/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response:
            target.write_bytes(response.read())
        print(f"{filename}: {target.stat().st_size:,} bytes -> {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    download(parser.parse_args().destination)
```

- [ ] **Step 8: Load the real files and check the counts against the spec**

```bash
cd backend
python scripts/collect_dp_catalogue.py
python scripts/load_dp_catalogue.py ../data/raw/azerbaijan/dp-bakalavr-2026.csv \
  --source-url "https://admin.opendata.az/dataset/6d33d639-af0a-46a8-89f5-c20c606cc0f3/resource/f28081ed-31d0-4ca6-aeb5-4d5a419e986c/download/dp-bakalavr-2026.csv"
python scripts/load_dp_catalogue.py ../data/raw/azerbaijan/dp-master-2026.csv \
  --source-url "https://admin.opendata.az/dataset/0f00bf5a-c10d-4109-80b5-9beecc783027/resource/7907fba0-acb0-4017-95a7-2411774243a0/download/dp-master-2026.csv"
```

Expected: `1214 new rows` then `2907 new rows`. Run the second pair again — both must
report `0 new rows`. If a database is not available in your environment, say so in your
report and note that the idempotence test in Step 3 covers the same property.

- [ ] **Step 9: Run the whole suite and commit**

Run: `cd backend && python -m pytest -q` — expected **97 passed**.

```bash
git add backend/app/models/dp_catalogue.py backend/alembic/versions/2026_08_31_0002-b2c3d4e5f6a7_add_dp_catalogue.py backend/scripts/collect_dp_catalogue.py backend/scripts/load_dp_catalogue.py backend/tests/test_load_dp_catalogue.py
git commit -m "Load the 4,121-row state programme catalogue"
```

---

## Task 7: Student qualifications and programme requirements

Two tables, both keyed by level. `students` today holds `gpa`, `ielts`, `toefl` and no entry
qualification at all — so nothing in the database can answer "does this person hold a
qualification Germany accepts", which is the question the whole route engine turns on.

**Files:**
- Create: `backend/app/models/qualifications.py`
- Modify: `backend/alembic/versions/2026_08_31_0002-b2c3d4e5f6a7_add_dp_catalogue.py` (same migration; it has not shipped)
- Test: `backend/tests/test_qualifications_model.py`

**Interfaces:**
- Produces: `StudentQualification` (table `student_qualifications`) and `ProgramRequirement`
  (table `program_requirements`). Task 8 reads `StudentQualification` field names; Task 10
  queries both.

- [ ] **Step 1: Write the models**

Create `backend/app/models/qualifications.py`:

```python
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
)
from app.core.database import Base

# The qualification a student holds. This is the field that decides whether a route is
# open: an attestat opens Turkey and Poland directly but opens only the Studienkolleg in
# Germany, while a completed year of university study opens Germany and the UK both.
QUALIFICATION_ATTESTAT = "attestat"
QUALIFICATION_ONE_YEAR_UNIVERSITY = "one_year_university"
QUALIFICATION_A_LEVEL = "a_level"
QUALIFICATION_IB = "ib"
QUALIFICATION_FOUNDATION_YEAR = "foundation_year"
QUALIFICATION_FESTSTELLUNGSPRUEFUNG = "feststellungspruefung"
QUALIFICATION_BACHELOR_DEGREE = "bachelor_degree"


class StudentQualification(Base):
    """What a student holds and what they are aiming at. One row per student per level.

    Separate from `students` because a person can hold one profile and ask two different
    questions -- "where can I go for a bachelor's now" and "where could I go for a master's
    after that" -- and the answers share no requirements.
    """
    __tablename__ = "student_qualifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)

    # 'bachelor' | 'master'. Part of the key.
    level_sought = Column(String(20), nullable=False)
    # One of the QUALIFICATION_* constants above.
    qualification_held = Column(String(50), nullable=False)

    # Every score is nullable and stays nullable. "Did not sit the exam" and "scored zero"
    # are different facts, and a default would erase the difference.
    dim_score = Column(Float, nullable=True)
    ielts = Column(Float, nullable=True)
    toefl = Column(Integer, nullable=True)
    sat = Column(Integer, nullable=True)
    act = Column(Integer, nullable=True)
    # One column per exam. Sharing one would silently credit a student with an exam they
    # never sat -- an SAT score standing in for TestAS turns a blocked route into an open one.
    tr_yos = Column(Float, nullable=True)
    test_as = Column(Float, nullable=True)
    csca = Column(Float, nullable=True)
    hsk = Column(Integer, nullable=True)
    # CEFR level of the strongest language certificate held: 'B2', 'C1', 'C2'.
    language_certificate_level = Column(String(10), nullable=True)
    has_international_olympiad_medal = Column(Boolean, nullable=True)

    budget_azn_per_year = Column(Float, nullable=True)
    field_of_interest = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "level_sought", name="uq_student_qualification_level"),
    )


class ProgramRequirement(Base):
    """What one university asks of an international applicant, for one programme and level.

    The schema is spec §5.1 and is fixed before collection rather than discovered during
    it. Every row carries where it came from and when it was read.
    """
    __tablename__ = "program_requirements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    university_name = Column(String(300), nullable=False, index=True)
    program_name = Column(String(500), nullable=False)
    # 'bachelor' | 'master'. Part of the key: the same university publishes different
    # requirements, fees and deadlines per level.
    level = Column(String(20), nullable=False, index=True)
    intake_year = Column(Integer, nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)

    # The field that decides whether a route is open. One of the QUALIFICATION_* constants.
    entry_qualification_accepted = Column(String(50), nullable=True)
    foundation_required = Column(Boolean, nullable=True)
    foundation_providers = Column(Text, nullable=True)

    language_test = Column(String(30), nullable=True)
    language_minimum_score = Column(Float, nullable=True)
    language_of_instruction = Column(String(50), nullable=True)

    entrance_exam = Column(String(30), nullable=True)
    entrance_exam_minimum = Column(Float, nullable=True)

    gpa_minimum = Column(Float, nullable=True)
    # The scale the minimum is expressed in -- '4.0', '5.0', '100'. A GPA without its
    # scale is not a number, and mixing scales silently is how a 3.0 becomes a rejection.
    gpa_scale = Column(String(10), nullable=True)

    # For INTERNATIONAL students. The domestic or EU figure is the wrong one and is
    # usually the more prominent number on the page (spec §5.1).
    tuition_per_year = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    living_cost_estimate_per_year = Column(Float, nullable=True)
    application_fee = Column(Float, nullable=True)

    application_deadline = Column(Date, nullable=True)
    application_portal = Column(String(60), nullable=True)
    documents_required = Column(Text, nullable=True)

    # 'seed' | 'claude-extracted' | 'human-verified' (ADR-0007 §5).
    provenance = Column(String(30), nullable=False, default="claude-extracted")
    source_url = Column(Text, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=False)
    # Shown to the student. Honesty beats false confidence (spec §5.4).
    last_checked = Column(DateTime(timezone=True), nullable=True)
    # A fingerprint of the page this was read from, so a re-fetch can skip an unchanged
    # page without re-extracting it (spec §5.4).
    source_text_hash = Column(String(64), nullable=True)
    verified_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "university_name", "program_name", "level", "intake_year",
            name="uq_program_requirement_entry",
        ),
    )
```

- [ ] **Step 2: Add both tables to the migration**

Append to the `upgrade()` of `2026_08_31_0002-b2c3d4e5f6a7_add_dp_catalogue.py`:

```python
    op.create_table(
        "student_qualifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("level_sought", sa.String(length=20), nullable=False),
        sa.Column("qualification_held", sa.String(length=50), nullable=False),
        sa.Column("dim_score", sa.Float(), nullable=True),
        sa.Column("ielts", sa.Float(), nullable=True),
        sa.Column("toefl", sa.Integer(), nullable=True),
        sa.Column("sat", sa.Integer(), nullable=True),
        sa.Column("act", sa.Integer(), nullable=True),
        sa.Column("tr_yos", sa.Float(), nullable=True),
        sa.Column("test_as", sa.Float(), nullable=True),
        sa.Column("csca", sa.Float(), nullable=True),
        sa.Column("hsk", sa.Integer(), nullable=True),
        sa.Column("language_certificate_level", sa.String(length=10), nullable=True),
        sa.Column("has_international_olympiad_medal", sa.Boolean(), nullable=True),
        sa.Column("budget_azn_per_year", sa.Float(), nullable=True),
        sa.Column("field_of_interest", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "level_sought", name="uq_student_qualification_level"),
    )
    op.create_index("ix_student_qualifications_id", "student_qualifications", ["id"])
    op.create_index("ix_student_qualifications_student_id", "student_qualifications", ["student_id"])

    op.create_table(
        "program_requirements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("university_name", sa.String(length=300), nullable=False),
        sa.Column("program_name", sa.String(length=500), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("intake_year", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("entry_qualification_accepted", sa.String(length=50), nullable=True),
        sa.Column("foundation_required", sa.Boolean(), nullable=True),
        sa.Column("foundation_providers", sa.Text(), nullable=True),
        sa.Column("language_test", sa.String(length=30), nullable=True),
        sa.Column("language_minimum_score", sa.Float(), nullable=True),
        sa.Column("language_of_instruction", sa.String(length=50), nullable=True),
        sa.Column("entrance_exam", sa.String(length=30), nullable=True),
        sa.Column("entrance_exam_minimum", sa.Float(), nullable=True),
        sa.Column("gpa_minimum", sa.Float(), nullable=True),
        sa.Column("gpa_scale", sa.String(length=10), nullable=True),
        sa.Column("tuition_per_year", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("living_cost_estimate_per_year", sa.Float(), nullable=True),
        sa.Column("application_fee", sa.Float(), nullable=True),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("application_portal", sa.String(length=60), nullable=True),
        sa.Column("documents_required", sa.Text(), nullable=True),
        sa.Column("provenance", sa.String(length=30), nullable=False, server_default="claude-extracted"),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_text_hash", sa.String(length=64), nullable=True),
        sa.Column("verified_by", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "university_name", "program_name", "level", "intake_year",
            name="uq_program_requirement_entry",
        ),
    )
    op.create_index("ix_program_requirements_id", "program_requirements", ["id"])
    op.create_index("ix_program_requirements_university_name", "program_requirements", ["university_name"])
    op.create_index("ix_program_requirements_level", "program_requirements", ["level"])
    op.create_index("ix_program_requirements_country_code", "program_requirements", ["country_code"])
    op.create_index("ix_program_requirements_intake_year", "program_requirements", ["intake_year"])
```

Then add the deferred unique index on the **existing** `program_cutoff_history` table. This
is Ruling 6 of the 2026-08-30 catalogue-join run, which decided the constraint and deferred
it to "the next migration" — this is that migration, and it was omitted from this plan by
oversight:

```python
    # Deferred from the 2026-08-30 run (its Ruling 6). The 4-column key considered there
    # includes variant_index, which is NULL on all 115,482 Turkey rows and 1,598 of 2,576 AZ
    # rows -- and NULL is distinct from NULL in unique indexes on both SQLite and Postgres,
    # so that version would have protected 0.8% of rows while reading as full protection.
    # These three columns are NOT NULL, and the reviewer verified zero duplicates across
    # both real files. Safe because collect_azerbaijan.py already bakes the variant into the
    # code itself (f"{base}--v{index}"), so every variant row carries a --vN suffix and the
    # collision variant_index was invented for never reaches this key.
    op.create_index(
        "uq_cutoff_history_natural_key",
        "program_cutoff_history",
        ["country", "source_program_code", "intake_year"],
        unique=True,
    )
```

If this index fails to create because the target database already holds duplicates, **do not
drop rows and do not weaken the index to non-unique.** Stop and report it: the loader is
idempotent on a 4-column key, so a duplicate on these three columns means a collector emitted
two distinct competitions under one code and year without suffixing, which is a data question
for a person, not a migration to force through.

And in `downgrade()`, before the existing `op.drop_table("dp_catalogue")`:

```python
    op.drop_index("uq_cutoff_history_natural_key", table_name="program_cutoff_history")
    op.drop_table("program_requirements")
    op.drop_table("student_qualifications")
```

- [ ] **Step 2b: Declare the same index on the model**

A migration alone is not enough: the tests build their schema with `Base.metadata.create_all`,
which reads the model, so an index declared only in the migration is unenforced in every test
and the two definitions drift apart silently. Add it to `backend/app/models/cutoff_history.py`,
alongside the existing `ix_cutoff_history_series` in `__table_args__` (keep that one — it is a
non-unique lookup index on a different column set and both are wanted):

```python
    __table_args__ = (
        Index(
            "ix_cutoff_history_series",
            "country",
            "source_program_code",
            "variant_index",
            "intake_year",
        ),
        # One published cutoff per country, programme code and intake year. Deferred from
        # the 2026-08-30 run (its Ruling 6), which established these three NOT NULL columns
        # as the only portable key: the 4-column version including variant_index protects
        # 0.8% of rows, because NULL is distinct from NULL in a unique index on both SQLite
        # and Postgres.
        Index(
            "uq_cutoff_history_natural_key",
            "country",
            "source_program_code",
            "intake_year",
            unique=True,
        ),
    )
```

- [ ] **Step 3: Write the test**

Create `backend/tests/test_qualifications_model.py`:

```python
"""The two tables the route engine reads. Level is part of the key in both."""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.cutoff_history import ProgramCutoffHistory
from app.models.dp_catalogue import DPCatalogueEntry
from app.models.qualifications import (
    QUALIFICATION_ATTESTAT,
    ProgramRequirement,
    StudentQualification,
)
from app.models.student import Student


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                Student.__table__,
                StudentQualification.__table__,
                ProgramRequirement.__table__,
                DPCatalogueEntry.__table__,
                ProgramCutoffHistory.__table__,
            ],
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_one_student_can_hold_a_profile_per_level(session):
    """Bachelor and master are different questions with different answers."""
    student = Student(email="two_levels@ausa.edu.az")
    session.add(student)
    await session.commit()
    await session.refresh(student)

    session.add_all([
        StudentQualification(
            student_id=student.id,
            level_sought="bachelor",
            qualification_held=QUALIFICATION_ATTESTAT,
            dim_score=520.0,
        ),
        StudentQualification(
            student_id=student.id,
            level_sought="master",
            qualification_held="bachelor_degree",
            ielts=7.0,
        ),
    ])
    await session.commit()

    rows = (await session.execute(select(StudentQualification))).scalars().all()
    assert {r.level_sought for r in rows} == {"bachelor", "master"}


@pytest.mark.asyncio
async def test_a_second_profile_for_the_same_level_is_rejected(session):
    student = Student(email="duplicate@ausa.edu.az")
    session.add(student)
    await session.commit()
    await session.refresh(student)

    session.add(StudentQualification(
        student_id=student.id, level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
    ))
    await session.commit()

    session.add(StudentQualification(
        student_id=student.id, level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
    ))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
async def test_unset_scores_stay_null(session):
    """'Did not sit the exam' and 'scored zero' are different facts."""
    student = Student(email="no_scores@ausa.edu.az")
    session.add(student)
    await session.commit()
    await session.refresh(student)

    session.add(StudentQualification(
        student_id=student.id, level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
    ))
    await session.commit()

    row = (await session.execute(select(StudentQualification))).scalars().one()
    assert row.dim_score is None
    assert row.ielts is None
    assert row.sat is None


@pytest.mark.asyncio
async def test_the_same_programme_carries_different_requirements_per_level(session):
    """One university, one subject, two levels, two sets of requirements and fees."""
    now = datetime.now(timezone.utc)
    session.add_all([
        ProgramRequirement(
            university_name="Technical University of Munich",
            program_name="Informatics", level="bachelor", intake_year=2026,
            country_code="DE", entry_qualification_accepted="one_year_university",
            tuition_per_year=0.0, currency="EUR",
            source_url="https://www.tum.de/en/studies", retrieved_at=now,
        ),
        ProgramRequirement(
            university_name="Technical University of Munich",
            program_name="Informatics", level="master", intake_year=2026,
            country_code="DE", entry_qualification_accepted="bachelor_degree",
            language_test="IELTS", language_minimum_score=6.5,
            tuition_per_year=0.0, currency="EUR",
            source_url="https://www.tum.de/en/studies", retrieved_at=now,
        ),
    ])
    await session.commit()

    rows = (await session.execute(select(ProgramRequirement))).scalars().all()
    by_level = {r.level: r for r in rows}
    assert by_level["bachelor"].entry_qualification_accepted == "one_year_university"
    assert by_level["master"].entry_qualification_accepted == "bachelor_degree"


@pytest.mark.asyncio
async def test_the_cutoff_history_natural_key_is_unique(session):
    """Deferred from the 2026-08-30 run (its Ruling 6): one row per country, code and year.

    The 4-column key considered there included variant_index, which is NULL on 99.2% of rows,
    and NULL is distinct from NULL in a unique index -- so it would have read as protection
    while protecting almost nothing.
    """
    def _row():
        return ProgramCutoffHistory(
            country="TR", source_program_code="100110027", intake_year=2025,
            cutoff_value=412.5, cutoff_unit="score", lower_is_better=False,
            university_name="Some University",
        )

    session.add(_row())
    await session.commit()

    session.add(_row())
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()


@pytest.mark.asyncio
async def test_a_requirement_row_must_carry_its_source(session):
    """source_url is NOT NULL: a requirement nobody can trace is not a requirement."""
    session.add(ProgramRequirement(
        university_name="Nowhere University", program_name="Something",
        level="bachelor", intake_year=2026, country_code="TR",
        retrieved_at=datetime.now(timezone.utc),
    ))
    with pytest.raises(IntegrityError):
        await session.commit()
    await session.rollback()
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && python -m pytest tests/test_qualifications_model.py -v`

Expected: PASS, 5 tests.

- [ ] **Step 5: Check the migration applies**

Run: `cd backend && python -m alembic upgrade head`

Expected: no error, and the three new tables exist. If no database is reachable in your
environment, run `python -m alembic upgrade head --sql` instead, which renders the SQL
without connecting, and say in your report that you verified it that way.

- [ ] **Step 6: Run the whole suite and commit**

Run: `cd backend && python -m pytest -q` — expected **102 passed**.

```bash
git add backend/app/models/qualifications.py backend/alembic/versions/2026_08_31_0002-b2c3d4e5f6a7_add_dp_catalogue.py backend/tests/test_qualifications_model.py
git commit -m "Add student qualifications and programme requirements, keyed by level"
```

---

## Task 8: The route domain and single-hop classification

The primary object is a Route, not a university (spec §4.1). This task builds the data
types, the ~17 hand-written cited route definitions, and the classifier that answers OPEN /
UNLOCKABLE / BLOCKED for one route against one profile. Composition is Task 9.

**Files:**
- Create: `backend/app/domain/__init__.py` (empty)
- Create: `backend/app/domain/routes.py`
- Create: `backend/app/domain/route_definitions.py`
- Create: `backend/app/services/route_engine.py`
- Test: `backend/tests/test_route_engine.py`

**Interfaces:**
- Produces:
  - `RouteStatus` — `OPEN` / `UNLOCKABLE` / `BLOCKED`
  - `ExamRequirement(name: str, minimum: float | None, profile_field: str)`
  - `Route(key, country_code, level, mechanism, requires_qualification: tuple[str, ...], produces_qualification: str | None, exams: tuple[ExamRequirement, ...], time_cost_months: int, money_cost_azn: tuple[int, int], citation: str, provenance: str)`
  - `StudentRouteProfile(level_sought, qualification_held, dim_score, ielts, toefl, sat, act, language_certificate_level, has_international_olympiad_medal, budget_azn_per_year)`
  - `RouteAssessment(route: Route, status: RouteStatus, missing: tuple[str, ...])`
  - `classify_route(route, profile) -> RouteAssessment`
  - `assess_routes(profile, routes=ALL_ROUTES) -> list[RouteAssessment]`
  - `ALL_ROUTES: tuple[Route, ...]`
- Task 9 consumes `Route.produces_qualification` and `Route.requires_qualification`; Task 10
  consumes `assess_routes` and `StudentRouteProfile`.

- [ ] **Step 1: Write the domain types**

Create `backend/app/domain/__init__.py` (empty), then `backend/app/domain/routes.py`:

```python
"""The route domain: pure data and no I/O.

A Route is `qualification held -> entry mechanism -> country, at a level`. It is the
primary object in the product, because for a school-leaver the binding question is not
"where do I qualify" but "which paths are even open to me" (spec §4.1).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RouteStatus(str, Enum):
    # Every precondition met.
    OPEN = "open"
    # Met except for a named, obtainable set -- an exam not yet sat, a score not yet high
    # enough. The student can act on this within a cycle.
    UNLOCKABLE = "unlockable"
    # A precondition that cannot be obtained this cycle: the qualification itself is wrong.
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ExamRequirement:
    """One exam or score bar. `profile_field` names the StudentRouteProfile attribute."""
    name: str
    minimum: Optional[float]
    profile_field: str


@dataclass(frozen=True)
class Route:
    key: str
    country_code: str
    # 'bachelor' | 'master'. Part of the key, not a filter: Germany and the UK are blocked
    # to a school-leaver but open to a bachelor holder (spec §4.1).
    level: str
    mechanism: str
    # Any one of these qualifications satisfies the route.
    requires_qualification: tuple[str, ...]
    # What holding this route's completion gives you, for two-hop composition. None for a
    # route that terminates in a degree rather than in another qualification.
    produces_qualification: Optional[str]
    exams: tuple[ExamRequirement, ...]
    time_cost_months: int
    money_cost_azn: tuple[int, int]
    # Where this was read. Every route carries one; this is the highest-value data in the
    # product and none of it is scraped.
    citation: str
    # 'seed' until a person has opened the citation and confirmed it.
    provenance: str = "seed"


@dataclass(frozen=True)
class StudentRouteProfile:
    """What the engine needs from student_qualifications. Every score may be None."""
    level_sought: str
    qualification_held: str
    dim_score: Optional[float] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    sat: Optional[int] = None
    act: Optional[int] = None
    # One field per exam, never a shared one. Routing TestAS and TR-YÖS at the `sat` field
    # would mean a student who sat the SAT is silently credited with an exam they have
    # never taken -- and the route would come back OPEN when it is not.
    tr_yos: Optional[float] = None
    test_as: Optional[float] = None
    csca: Optional[float] = None
    hsk: Optional[int] = None
    language_certificate_level: Optional[str] = None
    has_international_olympiad_medal: Optional[bool] = None
    budget_azn_per_year: Optional[float] = None


@dataclass(frozen=True)
class RouteAssessment:
    route: Route
    status: RouteStatus
    # Human-readable, one entry per unmet requirement. Empty when OPEN.
    missing: tuple[str, ...]
```

- [ ] **Step 2: Write the route definitions**

Create `backend/app/domain/route_definitions.py`:

```python
"""The hand-written routes. The highest-value data in the product, and none of it scraped.

Every route carries a citation. Provenance is 'seed' until a person opens that citation and
confirms it -- loading a route does not verify it (ADR-0004 rule 2).

Money ranges are annual, in AZN, and are order-of-magnitude figures for ranking, not
quotes. Where the spec verified a figure it is used; where it did not, the range is wide
rather than precise, because a narrow invented number reads as measured.
"""

from app.domain.routes import ExamRequirement, Route
from app.models.qualifications import (
    QUALIFICATION_A_LEVEL,
    QUALIFICATION_ATTESTAT,
    QUALIFICATION_BACHELOR_DEGREE,
    QUALIFICATION_FESTSTELLUNGSPRUEFUNG,
    QUALIFICATION_FOUNDATION_YEAR,
    QUALIFICATION_IB,
    QUALIFICATION_ONE_YEAR_UNIVERSITY,
)

ANABIN = "https://anabin.kmk.org/ -- attestat 'eröffnet den Zugang zum Studienkolleg/Feststellungsprüfung'"
UK_ENIC = "UK ENIC: an Azerbaijani attestat is 'not accepted for direct entry to undergraduate programmes'"
STUDY_IN_TURKIYE = "https://www.studyinturkiye.gov.tr/"
CAMPUS_CHINA = "https://www.campuschina.org/"
DP_RULES = "https://dp.edu.az/ -- Dövlət Proqramı eligibility rules"
SPEC_2_1 = "docs/superpowers/specs/2026-08-31-route-first-advisor-design.md §2.1"

# --- The unlock. Both blocked countries share this one escape hatch (spec §2.1). ---

AZ_PREP_YEAR = Route(
    key="az-prep-year",
    country_code="AZ",
    level="bachelor",
    mechanism="One year of study at a recognised Azerbaijani university",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    produces_qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    exams=(ExamRequirement("DİM", None, "dim_score"),),
    time_cost_months=12,
    money_cost_azn=(1000, 4000),
    citation=ANABIN,
)

# --- Bachelor, direct ---

TR_BACHELOR_DIRECT = Route(
    key="tr-bachelor-direct",
    country_code="TR",
    level="bachelor",
    mechanism="Direct application on the diploma and grades; most private universities require no YÖS",
    requires_qualification=(QUALIFICATION_ATTESTAT, QUALIFICATION_A_LEVEL, QUALIFICATION_IB),
    produces_qualification=None,
    exams=(),
    time_cost_months=0,
    money_cost_azn=(1700, 12000),
    citation=STUDY_IN_TURKIYE,
)

TR_BACHELOR_YOS = Route(
    key="tr-bachelor-yos",
    country_code="TR",
    level="bachelor",
    mechanism="TR-YÖS, required by some public universities for competitive programmes",
    requires_qualification=(QUALIFICATION_ATTESTAT, QUALIFICATION_A_LEVEL, QUALIFICATION_IB),
    produces_qualification=None,
    # Sat twice a year by ÖSYM, in six languages; Turkish is not required to take it.
    exams=(ExamRequirement("TR-YÖS", None, "tr_yos"),),
    time_cost_months=0,
    money_cost_azn=(1200, 6000),
    citation=STUDY_IN_TURKIYE,
)

PL_BACHELOR_DIRECT = Route(
    key="pl-bachelor-direct",
    country_code="PL",
    level="bachelor",
    mechanism="Direct application; the attestat is accepted with an apostille",
    requires_qualification=(QUALIFICATION_ATTESTAT, QUALIFICATION_A_LEVEL, QUALIFICATION_IB),
    produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.0, "ielts"),),
    time_cost_months=0,
    money_cost_azn=(3400, 8500),
    citation=SPEC_2_1,
)

US_BACHELOR_DIRECT = Route(
    key="us-bachelor-direct",
    country_code="US",
    level="bachelor",
    mechanism="Direct application; many institutions are test-optional, but the 11-vs-12-year gap is assessed per institution",
    requires_qualification=(QUALIFICATION_ATTESTAT, QUALIFICATION_A_LEVEL, QUALIFICATION_IB),
    produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0,
    money_cost_azn=(30000, 100000),
    citation=SPEC_2_1,
)

CN_BACHELOR_CSC = Route(
    key="cn-bachelor-csc",
    country_code="CN",
    level="bachelor",
    # CSC bachelor recipients must register for CHINESE-taught courses; English-taught is
    # open to graduate and non-degree students only (spec §5.2).
    mechanism="CSC-funded study, taught in Chinese, with a CSCA score",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    exams=(
        ExamRequirement("CSCA", None, "csca"),
        ExamRequirement("HSK", 4.0, "hsk"),
    ),
    produces_qualification=None,
    time_cost_months=0,
    money_cost_azn=(0, 0),
    citation=CAMPUS_CHINA,
)

# --- Bachelor, blocked-then-unlocked ---

DE_BACHELOR_STUDIENKOLLEG = Route(
    key="de-bachelor-studienkolleg",
    country_code="DE",
    level="bachelor",
    mechanism="Studienkolleg, ending in the Feststellungsprüfung",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    produces_qualification=QUALIFICATION_FESTSTELLUNGSPRUEFUNG,
    exams=(ExamRequirement("TestAS", None, "test_as"),),
    time_cost_months=12,
    money_cost_azn=(6000, 14000),
    citation=ANABIN,
)

DE_BACHELOR_DIRECT = Route(
    key="de-bachelor-direct",
    country_code="DE",
    level="bachelor",
    mechanism="Direct, subject-restricted entry",
    # An attestat alone does NOT appear here, and that is the whole point: it opens the
    # Studienkolleg and nothing else. Applies to attestats from 2015 onward.
    requires_qualification=(
        QUALIFICATION_ONE_YEAR_UNIVERSITY,
        QUALIFICATION_FESTSTELLUNGSPRUEFUNG,
        QUALIFICATION_A_LEVEL,
        QUALIFICATION_IB,
    ),
    produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0,
    money_cost_azn=(0, 1200),
    citation=ANABIN,
)

UK_BACHELOR_FOUNDATION = Route(
    key="uk-bachelor-foundation",
    country_code="GB",
    level="bachelor",
    mechanism="International foundation year",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    produces_qualification=QUALIFICATION_FOUNDATION_YEAR,
    exams=(ExamRequirement("IELTS", 5.5, "ielts"),),
    time_cost_months=12,
    money_cost_azn=(25000, 45000),
    citation=UK_ENIC,
)

UK_BACHELOR_DIRECT = Route(
    key="uk-bachelor-direct",
    country_code="GB",
    level="bachelor",
    mechanism="Direct entry via UCAS",
    requires_qualification=(
        QUALIFICATION_FOUNDATION_YEAR,
        QUALIFICATION_ONE_YEAR_UNIVERSITY,
        QUALIFICATION_A_LEVEL,
        QUALIFICATION_IB,
    ),
    produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0,
    money_cost_azn=(30000, 70000),
    citation=UK_ENIC,
)

# --- Master's. A completed bachelor's is an accepted entry qualification everywhere,
# which is why Germany and the UK invert from blocked to open at this level. ---

TR_MASTER_DIRECT = Route(
    key="tr-master-direct", country_code="TR", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.0, "ielts"),),
    time_cost_months=0, money_cost_azn=(1700, 12000), citation=STUDY_IN_TURKIYE,
)

DE_MASTER_DIRECT = Route(
    key="de-master-direct", country_code="DE", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0, money_cost_azn=(0, 1200), citation=SPEC_2_1,
)

UK_MASTER_DIRECT = Route(
    key="uk-master-direct", country_code="GB", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0, money_cost_azn=(35000, 80000), citation=SPEC_2_1,
)

US_MASTER_DIRECT = Route(
    key="us-master-direct", country_code="US", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0, money_cost_azn=(35000, 100000), citation=SPEC_2_1,
)

PL_MASTER_DIRECT = Route(
    key="pl-master-direct", country_code="PL", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.0, "ielts"),),
    time_cost_months=0, money_cost_azn=(3400, 8500), citation=SPEC_2_1,
)

CN_MASTER_DIRECT = Route(
    key="cn-master-direct", country_code="CN", level="master",
    # English-taught master's: IELTS 6.5 / TOEFL 80, or two years of prior English-medium
    # study. Chinese-taught needs HSK 4 plus a year of Chinese (spec §5.2).
    mechanism="Direct application with a completed bachelor's degree; English-taught available",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0, money_cost_azn=(0, 20000), citation=CAMPUS_CHINA,
)

ALL_ROUTES: tuple[Route, ...] = (
    AZ_PREP_YEAR,
    TR_BACHELOR_DIRECT, TR_BACHELOR_YOS, PL_BACHELOR_DIRECT, US_BACHELOR_DIRECT,
    CN_BACHELOR_CSC, DE_BACHELOR_STUDIENKOLLEG, DE_BACHELOR_DIRECT,
    UK_BACHELOR_FOUNDATION, UK_BACHELOR_DIRECT,
    TR_MASTER_DIRECT, DE_MASTER_DIRECT, UK_MASTER_DIRECT, US_MASTER_DIRECT,
    PL_MASTER_DIRECT, CN_MASTER_DIRECT,
)
```

- [ ] **Step 3: Write the failing classifier test**

Create `backend/tests/test_route_engine.py`:

```python
"""The route engine. The case that matters most is the attestat-only school-leaver:
Germany and the UK must come back BLOCKED, with both unlocks named."""

import pytest

from app.domain.route_definitions import ALL_ROUTES
from app.domain.routes import RouteStatus, StudentRouteProfile
from app.models.qualifications import (
    QUALIFICATION_ATTESTAT,
    QUALIFICATION_BACHELOR_DEGREE,
    QUALIFICATION_ONE_YEAR_UNIVERSITY,
)
from app.services.route_engine import assess_routes, classify_route

SCHOOL_LEAVER = StudentRouteProfile(
    level_sought="bachelor",
    qualification_held=QUALIFICATION_ATTESTAT,
    dim_score=520.0,
    ielts=7.0,
)


def _by_key(assessments):
    return {a.route.key: a for a in assessments}


def test_every_route_carries_a_citation_and_seed_provenance():
    """A route without a source is not a route. Loading one does not verify it."""
    for route in ALL_ROUTES:
        assert route.citation, f"{route.key} has no citation"
        assert route.provenance in ("seed", "human-verified")


def test_germany_and_the_uk_are_blocked_to_a_school_leaver():
    """The finding the whole design rests on: an attestat opens the Studienkolleg, not
    a German degree, and the UK does not accept it for direct undergraduate entry."""
    assessed = _by_key(assess_routes(SCHOOL_LEAVER))
    assert assessed["de-bachelor-direct"].status is RouteStatus.BLOCKED
    assert assessed["uk-bachelor-direct"].status is RouteStatus.BLOCKED


def test_turkey_and_poland_are_open_to_the_same_student():
    assessed = _by_key(assess_routes(SCHOOL_LEAVER))
    assert assessed["tr-bachelor-direct"].status is RouteStatus.OPEN
    assert assessed["pl-bachelor-direct"].status is RouteStatus.OPEN


def test_the_unlocks_are_offered_not_merely_the_blockage():
    """Studienkolleg and the prep year both accept an attestat, so both are actionable."""
    assessed = _by_key(assess_routes(SCHOOL_LEAVER))
    assert assessed["de-bachelor-studienkolleg"].status is not RouteStatus.BLOCKED
    assert assessed["az-prep-year"].status is not RouteStatus.BLOCKED


def test_a_missing_exam_is_unlockable_not_blocked():
    """A score you have not got yet is a gap you can close. A qualification you do not
    hold is not -- that distinction is the entire point of the two statuses."""
    no_english = StudentRouteProfile(
        level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
        ielts=None,
    )
    assessed = _by_key(assess_routes(no_english))
    poland = assessed["pl-bachelor-direct"]
    assert poland.status is RouteStatus.UNLOCKABLE
    assert any("IELTS" in m for m in poland.missing)


def test_a_score_below_the_bar_names_the_bar():
    low_english = StudentRouteProfile(
        level_sought="bachelor",
        qualification_held=QUALIFICATION_ATTESTAT,
        ielts=5.0,
    )
    poland = _by_key(assess_routes(low_english))["pl-bachelor-direct"]
    assert poland.status is RouteStatus.UNLOCKABLE
    assert any("6.0" in m for m in poland.missing)


def test_the_prep_year_opens_germany_directly():
    """After a year at an Azerbaijani university the same person is no longer blocked."""
    after_prep = StudentRouteProfile(
        level_sought="bachelor",
        qualification_held=QUALIFICATION_ONE_YEAR_UNIVERSITY,
        ielts=7.0,
    )
    assessed = _by_key(assess_routes(after_prep))
    assert assessed["de-bachelor-direct"].status is RouteStatus.OPEN
    assert assessed["uk-bachelor-direct"].status is RouteStatus.OPEN


def test_a_bachelor_holder_sees_only_master_routes():
    """Level is a key, not a filter: the bachelor routes are not applicable at all."""
    graduate = StudentRouteProfile(
        level_sought="master",
        qualification_held=QUALIFICATION_BACHELOR_DEGREE,
        ielts=7.0,
    )
    assessed = assess_routes(graduate)
    assert {a.route.level for a in assessed} == {"master"}
    assert _by_key(assessed)["de-master-direct"].status is RouteStatus.OPEN


def test_germany_inverts_between_the_two_levels():
    """Blocked to a school-leaver, open to a bachelor holder. A level-agnostic engine
    would give a confident wrong answer to one of these two students."""
    school_leaver = _by_key(assess_routes(SCHOOL_LEAVER))["de-bachelor-direct"]
    graduate = _by_key(assess_routes(StudentRouteProfile(
        level_sought="master",
        qualification_held=QUALIFICATION_BACHELOR_DEGREE,
        ielts=7.0,
    )))["de-master-direct"]
    assert school_leaver.status is RouteStatus.BLOCKED
    assert graduate.status is RouteStatus.OPEN


def test_classify_route_names_what_is_missing_and_why():
    from app.domain.route_definitions import DE_BACHELOR_DIRECT

    assessment = classify_route(DE_BACHELOR_DIRECT, SCHOOL_LEAVER)
    assert assessment.status is RouteStatus.BLOCKED
    assert assessment.missing
    assert any(QUALIFICATION_ATTESTAT in m or "qualification" in m.lower()
               for m in assessment.missing)
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_route_engine.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.route_engine'`.

- [ ] **Step 5: Write the engine**

Create `backend/app/services/route_engine.py`:

```python
"""Classify routes against a student profile.

The distinction the two non-open statuses draw is the product's core idea: a score you
have not got yet is a gap you can close this cycle (UNLOCKABLE), while a qualification you
do not hold is not (BLOCKED) -- it needs a different route first, which is what Task 9's
composition is for.
"""

from app.domain.route_definitions import ALL_ROUTES
from app.domain.routes import (
    ExamRequirement,
    Route,
    RouteAssessment,
    RouteStatus,
    StudentRouteProfile,
)


def _exam_gap(requirement: ExamRequirement, profile: StudentRouteProfile) -> str | None:
    """Return a description of the gap, or None when the requirement is met."""
    held = getattr(profile, requirement.profile_field, None)
    if held is None:
        if requirement.minimum is None:
            return f"{requirement.name} required"
        return f"{requirement.name} required, minimum {requirement.minimum}"
    if requirement.minimum is None:
        return None
    # Every exam requirement points at its own numeric field, so this comparison is always
    # like-for-like. If a route ever points one at a non-numeric field, that is a bug in the
    # definition and should fail loudly here rather than quietly passing the requirement.
    if float(held) < requirement.minimum:
        return f"{requirement.name} {held} is below the minimum {requirement.minimum}"
    return None


def classify_route(route: Route, profile: StudentRouteProfile) -> RouteAssessment:
    """OPEN when every precondition is met, UNLOCKABLE when only scores are missing,
    BLOCKED when the qualification itself is wrong."""
    if profile.qualification_held not in route.requires_qualification:
        return RouteAssessment(
            route=route,
            status=RouteStatus.BLOCKED,
            missing=(
                f"This route needs one of: {', '.join(route.requires_qualification)}. "
                f"You hold: {profile.qualification_held}.",
            ),
        )

    gaps = tuple(
        gap for gap in (_exam_gap(exam, profile) for exam in route.exams) if gap is not None
    )
    if gaps:
        return RouteAssessment(route=route, status=RouteStatus.UNLOCKABLE, missing=gaps)
    return RouteAssessment(route=route, status=RouteStatus.OPEN, missing=())


def assess_routes(
    profile: StudentRouteProfile,
    routes: tuple[Route, ...] = ALL_ROUTES,
) -> list[RouteAssessment]:
    """Assess every route at the level the student is asking about.

    Routes at other levels are not filtered out -- they are not applicable. A master's
    route is not a blocked option for a school-leaver, it is a different question.
    The one exception is the Azerbaijani prep year, which is defined at bachelor level but
    is the unlock for a school-leaver, so it is always in scope for one.
    """
    return [
        classify_route(route, profile)
        for route in routes
        if route.level == profile.level_sought
    ]
```

- [ ] **Step 6: Run the tests**

Run: `cd backend && python -m pytest tests/test_route_engine.py -v`

Expected: PASS, 10 tests.

- [ ] **Step 7: Run the whole suite and commit**

Run: `cd backend && python -m pytest -q` — expected **112 passed**.

```bash
git add backend/app/domain backend/app/services/route_engine.py backend/tests/test_route_engine.py
git commit -m "Add the route domain and single-hop classification"
```

---

## Task 9: Two-hop composition — the prep-year mechanic

Classification alone says Germany is blocked. The product's answer is *"blocked today, and
here are two ways to open it"*. That is composition: a route whose `produces_qualification`
satisfies another route's `requires_qualification`, capped at two hops (spec §4.1).

**Files:**
- Modify: `backend/app/services/route_engine.py`
- Test: `backend/tests/test_route_engine.py`

**Interfaces:**
- Consumes: `classify_route`, `ALL_ROUTES`, `Route.produces_qualification` from Task 8
- Produces: `RoutePlan(hops: tuple[Route, ...], total_months: int, total_cost_azn: tuple[int, int], status: RouteStatus, missing: tuple[str, ...])` and
  `compose_two_hop(profile, routes=ALL_ROUTES) -> list[RoutePlan]`
- Task 10 consumes `compose_two_hop`.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_route_engine.py`:

```python
from app.services.route_engine import compose_two_hop


def test_composition_produces_the_prep_year_path_to_germany():
    """The sentence the product exists to say: Germany is blocked, and one year at an
    Azerbaijani university opens it."""
    plans = compose_two_hop(SCHOOL_LEAVER)
    german = [p for p in plans if p.hops[-1].country_code == "DE"]
    assert german, "no two-hop plan reaches Germany"

    via_prep = [p for p in german if p.hops[0].key == "az-prep-year"]
    assert via_prep, "the prep-year unlock was not found"
    assert via_prep[0].hops[-1].key == "de-bachelor-direct"
    assert via_prep[0].total_months == 12


def test_both_german_unlocks_are_offered():
    """Studienkolleg and the prep year are different trades -- 12 months either way, but
    one costs 6,000-14,000 AZN and the other keeps Turkey and Poland open."""
    plans = compose_two_hop(SCHOOL_LEAVER)
    first_hops = {p.hops[0].key for p in plans if p.hops[-1].country_code == "DE"}
    assert {"az-prep-year", "de-bachelor-studienkolleg"} <= first_hops


def test_the_prep_year_also_opens_the_uk():
    """One unlock, two countries. This is why it is the mechanic the design is built on."""
    plans = compose_two_hop(SCHOOL_LEAVER)
    uk_via_prep = [
        p for p in plans
        if p.hops[-1].country_code == "GB" and p.hops[0].key == "az-prep-year"
    ]
    assert uk_via_prep


def test_composition_costs_are_the_sum_of_both_hops():
    plans = compose_two_hop(SCHOOL_LEAVER)
    plan = next(p for p in plans if p.hops[0].key == "az-prep-year"
                and p.hops[-1].key == "de-bachelor-direct")
    assert plan.total_months == plan.hops[0].time_cost_months + plan.hops[1].time_cost_months
    assert plan.total_cost_azn[0] == plan.hops[0].money_cost_azn[0] + plan.hops[1].money_cost_azn[0]


def test_no_plan_is_longer_than_two_hops():
    """Deeper chains exist but do not help a 17-year-old, and uncapped graph search turns
    a product into a research project."""
    assert all(len(p.hops) <= 2 for p in compose_two_hop(SCHOOL_LEAVER))


def test_a_student_who_is_already_open_gets_no_detour():
    """Composition answers a blockage. It must not propose a prep year to someone who can
    already go directly."""
    after_prep = StudentRouteProfile(
        level_sought="bachelor",
        qualification_held=QUALIFICATION_ONE_YEAR_UNIVERSITY,
        ielts=7.0,
    )
    plans = compose_two_hop(after_prep)
    assert all(p.hops[-1].country_code != "DE" for p in plans if len(p.hops) == 2)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_route_engine.py -v -k "composition or unlocks or two_hops or detour or also_opens"`

Expected: FAIL — `ImportError: cannot import name 'compose_two_hop'`.

- [ ] **Step 3: Implement composition**

Append to `backend/app/services/route_engine.py`, and add `from dataclasses import dataclass, replace`
to its imports:

```python
@dataclass(frozen=True)
class RoutePlan:
    """One or two routes end to end, with their costs summed."""
    hops: tuple[Route, ...]
    total_months: int
    total_cost_azn: tuple[int, int]
    status: RouteStatus
    missing: tuple[str, ...]


def _plan_from_hops(hops: tuple[Route, ...], assessments: tuple[RouteAssessment, ...]) -> RoutePlan:
    return RoutePlan(
        hops=hops,
        total_months=sum(hop.time_cost_months for hop in hops),
        total_cost_azn=(
            sum(hop.money_cost_azn[0] for hop in hops),
            sum(hop.money_cost_azn[1] for hop in hops),
        ),
        # A plan is only as open as its weakest hop.
        status=(
            RouteStatus.UNLOCKABLE
            if any(a.status is RouteStatus.UNLOCKABLE for a in assessments)
            else RouteStatus.OPEN
        ),
        missing=tuple(gap for a in assessments for gap in a.missing),
    )


def compose_two_hop(
    profile: StudentRouteProfile,
    routes: tuple[Route, ...] = ALL_ROUTES,
) -> list[RoutePlan]:
    """Every reachable plan, one or two hops, cheapest in time first.

    A second hop is only proposed where the direct route is BLOCKED. Composition exists to
    answer a blockage; proposing a 12-month detour to a student who can already go directly
    would be the steering behaviour this product refuses.

    The cap is two. Deeper chains exist but do not help a 17-year-old, and uncapped graph
    search turns a product into a research project (spec §4.1).
    """
    at_level = tuple(r for r in routes if r.level == profile.level_sought)
    plans: list[RoutePlan] = []
    blocked_keys: set[str] = set()

    for route in at_level:
        assessment = classify_route(route, profile)
        if assessment.status is RouteStatus.BLOCKED:
            blocked_keys.add(route.key)
            continue
        plans.append(_plan_from_hops((route,), (assessment,)))

    # Second hop: a route the student CAN start, whose completion satisfies a route that
    # is blocked today.
    unlockers = [
        (r, classify_route(r, profile)) for r in at_level
        if r.produces_qualification is not None
    ]
    for first, first_assessment in unlockers:
        if first_assessment.status is RouteStatus.BLOCKED:
            continue
        # The same student, after finishing the first hop. `replace` rather than rebuilding
        # from __dict__: it fails loudly if the field is ever renamed, instead of silently
        # dropping every score the profile carries.
        after = replace(profile, qualification_held=first.produces_qualification)
        for second in at_level:
            if second.key == first.key or second.key not in blocked_keys:
                continue
            second_assessment = classify_route(second, after)
            if second_assessment.status is RouteStatus.BLOCKED:
                continue
            plans.append(
                _plan_from_hops((first, second), (first_assessment, second_assessment))
            )

    return sorted(plans, key=lambda p: (p.total_months, p.total_cost_azn[0]))
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && python -m pytest tests/test_route_engine.py -v`

Expected: PASS, 16 tests.

- [ ] **Step 5: Run the whole suite and commit**

Run: `cd backend && python -m pytest -q` — expected **118 passed**.

```bash
git add backend/app/services/route_engine.py backend/tests/test_route_engine.py
git commit -m "Compose routes to two hops, so a blocked country arrives with its unlocks"
```

---

## Task 10: The DP funding gate, and the assessment endpoint

The Dövlət Proqramı has preconditions, produces funded access, costs nothing in time or
money, and gates a fixed list — the Route shape exactly (spec §5.2). Modelling it as one
lets the engine say that the prep year both opens Germany *and* preserves DP eligibility,
which neither concept could express alone.

**One honesty constraint this task must hold.** The DP's bachelor threshold is *"DİM 400–550
depending on field"*, and the per-field table has not been verified. So the engine reports
the band it checked, never a single invented number: at 550+ the student clears the whole
band; between 400 and 550 they clear some fields and the exact bar is field-dependent;
below 400 they do not clear it on the DİM route and the SAT and Olympiad alternatives are
named instead.

**Files:**
- Create: `backend/app/services/dp_eligibility.py`
- Create: `backend/app/api/v1/routes.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_dp_eligibility.py`

**Interfaces:**
- Consumes: `DPCatalogueEntry` and `COUNTRY_CODE_BY_SOURCE_NAME` (Task 6),
  `StudentRouteProfile`, `assess_routes`, `compose_two_hop` (Tasks 8-9)
- Produces:
  - `DPEligibility(status: RouteStatus, band_checked: str, gates_met: tuple[str, ...], gates_missing: tuple[str, ...])`
  - `assess_dp_eligibility(profile) -> DPEligibility`
  - `funded_programmes(session, level, country_codes) -> list[DPCatalogueEntry]`
  - `POST /api/v1/routes/assess`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_dp_eligibility.py`:

```python
"""The DP funding gate.

The wording rule matters as much as the logic here: clearing the published gates is
"possibly eligible", never a promise of an award. The DP funds roughly 400 places against
a much larger pool, and the selection that follows the gates is a committee decision no
dataset in this project models (spec §5.2).
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.domain.routes import RouteStatus, StudentRouteProfile
from app.models.dp_catalogue import DPCatalogueEntry
from app.models.qualifications import QUALIFICATION_ATTESTAT
from app.services.dp_eligibility import (
    assess_dp_eligibility,
    funded_programmes,
)

from datetime import datetime, timezone


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=[DPCatalogueEntry.__table__])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        now = datetime.now(timezone.utc)
        s.add_all([
            DPCatalogueEntry(
                level="bachelor", country_source="Türkiyə Respublikası", country_code="TR",
                university_name="Bogazici University", program_name="Computer Engineering",
                intake_year=2026, source_url="https://example.az/dp", retrieved_at=now,
            ),
            DPCatalogueEntry(
                level="bachelor", country_source="Almaniya Federativ Respublikası",
                country_code="DE", university_name="Technical University of Munich",
                program_name="Architecture", intake_year=2026,
                source_url="https://example.az/dp", retrieved_at=now,
            ),
            DPCatalogueEntry(
                level="master", country_source="Amerika Birləşmiş Ştatları", country_code="US",
                university_name="Some US University", program_name="Data Science",
                intake_year=2026, source_url="https://example.az/dp", retrieved_at=now,
            ),
        ])
        await s.commit()
        yield s
    await engine.dispose()


def test_a_clear_dim_score_and_c1_is_possibly_eligible():
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.OPEN
    assert "550" in result.band_checked


def test_a_score_inside_the_band_says_so_rather_than_inventing_a_threshold():
    """400-550 'depending on field', and the per-field table is not verified. The band is
    reported; a single number would be invented."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=470.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert "400" in result.band_checked and "550" in result.band_checked
    assert any("field" in gate.lower() for gate in result.gates_missing)


def test_a_missing_language_certificate_is_named_as_a_gate():
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0,
    )
    result = assess_dp_eligibility(profile)
    assert result.status is RouteStatus.UNLOCKABLE
    assert any("C1" in gate for gate in result.gates_missing)


def test_an_olympiad_medal_is_an_alternative_to_the_dim_route():
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        language_certificate_level="C1", has_international_olympiad_medal=True,
    )
    assert assess_dp_eligibility(profile).status is RouteStatus.OPEN


def test_the_gate_never_promises_an_award():
    """Prohibited output, in generated text and UI labels alike (spec §5.2)."""
    profile = StudentRouteProfile(
        level_sought="bachelor", qualification_held=QUALIFICATION_ATTESTAT,
        dim_score=560.0, language_certificate_level="C1",
    )
    result = assess_dp_eligibility(profile)
    rendered = " ".join((result.band_checked, *result.gates_met, *result.gates_missing)).lower()
    for promise in ("you will receive", "guaranteed", "you qualify for a full scholarship"):
        assert promise not in rendered


@pytest.mark.asyncio
async def test_funded_programmes_are_filtered_by_level_and_country(session):
    rows = await funded_programmes(session, level="bachelor", country_codes=("TR", "DE"))
    assert {r.university_name for r in rows} == {
        "Bogazici University", "Technical University of Munich",
    }


@pytest.mark.asyncio
async def test_a_level_with_no_funded_programmes_returns_empty_not_a_substitute(session):
    """The USA has zero DP bachelor programmes. That is an answer, not a gap to fill."""
    assert await funded_programmes(session, level="bachelor", country_codes=("US",)) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_dp_eligibility.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.dp_eligibility'`.

- [ ] **Step 3: Write the eligibility service**

Create `backend/app/services/dp_eligibility.py`:

```python
"""The Dövlət Proqramı funding gate, modelled as a route.

The DP has preconditions (C1, and DİM 400-550 or SAT/ACT at the 75th percentile or an
international Olympiad medal), produces funded access, costs nothing in time or money, and
gates a fixed list of universities. That is the Route shape, which is why it composes with
the others: the prep year at an Azerbaijani university opens Germany AND preserves DP
eligibility, and only one engine can say both.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.routes import RouteStatus, StudentRouteProfile
from app.models.dp_catalogue import DPCatalogueEntry

# "DİM 400-550 depending on field" (dp.edu.az). The per-field table has NOT been verified,
# so the engine reports the band it checked and never a single threshold. Inventing the
# midpoint would be a number that looks measured.
DIM_BAND_LOW = 400.0
DIM_BAND_HIGH = 550.0
BAND_DESCRIPTION = f"DİM {DIM_BAND_LOW:.0f}-{DIM_BAND_HIGH:.0f}, the exact bar depending on field"

ACCEPTED_LANGUAGE_LEVELS = ("C1", "C2")


@dataclass(frozen=True)
class DPEligibility:
    status: RouteStatus
    band_checked: str
    gates_met: tuple[str, ...]
    gates_missing: tuple[str, ...]


def assess_dp_eligibility(profile: StudentRouteProfile) -> DPEligibility:
    """Check the published gates. Clearing them is 'possibly eligible', never an award.

    The DP funds roughly 400 places a year against a much larger pool. What is checkable
    is whether the student clears the stated gates; the selection that follows is a
    committee decision no dataset in this project models.
    """
    met: list[str] = []
    missing: list[str] = []

    if profile.language_certificate_level in ACCEPTED_LANGUAGE_LEVELS:
        met.append(f"Language certificate at {profile.language_certificate_level}")
    else:
        missing.append("A language certificate at C1 or above is required")

    # Three alternative academic gates. Any one of them satisfies this half.
    if profile.has_international_olympiad_medal:
        met.append("International Olympiad medal")
    elif profile.dim_score is not None and profile.dim_score >= DIM_BAND_HIGH:
        met.append(f"DİM {profile.dim_score:.0f} clears the whole {BAND_DESCRIPTION}")
    elif profile.dim_score is not None and profile.dim_score >= DIM_BAND_LOW:
        met.append(f"DİM {profile.dim_score:.0f} is inside the band")
        missing.append(
            f"DİM {profile.dim_score:.0f} clears some fields but not all: the requirement is "
            f"{BAND_DESCRIPTION}, and the bar for your field has not been confirmed here"
        )
    elif profile.sat is not None:
        met.append(f"SAT {profile.sat} offered against the 75th-percentile alternative")
    else:
        missing.append(
            f"One of: {BAND_DESCRIPTION}; SAT/ACT at the 75th percentile; "
            "or an international Olympiad medal"
        )

    status = RouteStatus.OPEN if not missing else RouteStatus.UNLOCKABLE
    return DPEligibility(
        status=status,
        band_checked=BAND_DESCRIPTION,
        gates_met=tuple(met),
        gates_missing=tuple(missing),
    )


async def funded_programmes(
    session: AsyncSession,
    level: str,
    country_codes: tuple[str, ...],
) -> list[DPCatalogueEntry]:
    """The funded programmes for one level in the given countries.

    An empty list is a real answer -- the state funds zero bachelor programmes in the USA
    and Poland -- and is returned as one.
    """
    stmt = (
        select(DPCatalogueEntry)
        .where(DPCatalogueEntry.level == level)
        .where(DPCatalogueEntry.country_code.in_(country_codes))
        .order_by(DPCatalogueEntry.country_code, DPCatalogueEntry.university_name)
    )
    return list((await session.execute(stmt)).scalars().all())
```

- [ ] **Step 4: Run the service tests**

Run: `cd backend && python -m pytest tests/test_dp_eligibility.py -v`

Expected: PASS, 7 tests.

- [ ] **Step 5: Write the endpoint**

Create `backend/app/api/v1/routes.py`:

```python
"""Route assessment: a student's qualifications in, their open paths out."""

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.routes import StudentRouteProfile
from app.services.dp_eligibility import assess_dp_eligibility, funded_programmes
from app.services.route_engine import assess_routes, compose_two_hop

router = APIRouter(prefix="/routes", tags=["Route Planning"])


class AssessRoutesPayload(BaseModel):
    level_sought: str = Field(..., description="'bachelor' or 'master'")
    qualification_held: str = Field(..., description="attestat, one_year_university, bachelor_degree, a_level, ib")
    dim_score: Optional[float] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    sat: Optional[int] = None
    act: Optional[int] = None
    tr_yos: Optional[float] = None
    test_as: Optional[float] = None
    csca: Optional[float] = None
    hsk: Optional[int] = None
    language_certificate_level: Optional[str] = None
    has_international_olympiad_medal: Optional[bool] = None
    budget_azn_per_year: Optional[float] = None


class RouteHop(BaseModel):
    key: str
    country_code: str
    mechanism: str
    time_cost_months: int
    money_cost_azn_low: int
    money_cost_azn_high: int
    citation: str
    provenance: str


class RoutePlanResponse(BaseModel):
    hops: List[RouteHop]
    total_months: int
    total_cost_azn_low: int
    total_cost_azn_high: int
    status: str
    missing: List[str]


class FundedProgrammeResponse(BaseModel):
    country_code: Optional[str]
    university_name: str
    program_name: str
    source_url: str


class DPEligibilityResponse(BaseModel):
    status: str
    band_checked: str
    gates_met: List[str]
    gates_missing: List[str]
    # Deliberate wording. Clearing the published gates is not an award (spec §5.2).
    note: str = (
        "Meeting these published requirements makes you possibly eligible to apply. "
        "It is not an award: selection is competitive and is decided by a committee."
    )
    funded_programmes: List[FundedProgrammeResponse]


class AssessRoutesResponse(BaseModel):
    blocked: List[str]
    plans: List[RoutePlanResponse]
    dp: DPEligibilityResponse


@router.post(
    "/assess",
    response_model=AssessRoutesResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess which routes are open, unlockable or blocked",
)
async def assess(
    payload: AssessRoutesPayload,
    db: AsyncSession = Depends(get_db),
) -> AssessRoutesResponse:
    profile = StudentRouteProfile(**payload.model_dump())

    blocked = [
        f"{a.route.country_code}: {a.route.mechanism} -- {a.missing[0]}"
        for a in assess_routes(profile)
        if a.status.value == "blocked"
    ]

    plans = [
        RoutePlanResponse(
            hops=[
                RouteHop(
                    key=hop.key,
                    country_code=hop.country_code,
                    mechanism=hop.mechanism,
                    time_cost_months=hop.time_cost_months,
                    money_cost_azn_low=hop.money_cost_azn[0],
                    money_cost_azn_high=hop.money_cost_azn[1],
                    citation=hop.citation,
                    provenance=hop.provenance,
                )
                for hop in plan.hops
            ],
            total_months=plan.total_months,
            total_cost_azn_low=plan.total_cost_azn[0],
            total_cost_azn_high=plan.total_cost_azn[1],
            status=plan.status.value,
            missing=list(plan.missing),
        )
        for plan in compose_two_hop(profile)
    ]

    dp = assess_dp_eligibility(profile)
    reachable = tuple({hop.country_code for plan in plans for hop in plan.hops})
    funded = await funded_programmes(db, level=profile.level_sought, country_codes=reachable)

    return AssessRoutesResponse(
        blocked=blocked,
        plans=plans,
        dp=DPEligibilityResponse(
            status=dp.status.value,
            band_checked=dp.band_checked,
            gates_met=list(dp.gates_met),
            gates_missing=list(dp.gates_missing),
            funded_programmes=[
                FundedProgrammeResponse(
                    country_code=row.country_code,
                    university_name=row.university_name,
                    program_name=row.program_name,
                    source_url=row.source_url,
                )
                for row in funded
            ],
        ),
    )
```

- [ ] **Step 6: Register the router**

In `backend/app/api/v1/router.py`, import the new module and include it exactly as the
existing routers are included. Read the file first and follow its pattern — do not invent
a different one:

```python
from app.api.v1 import routes as routes_router

api_router.include_router(routes_router.router)
```

- [ ] **Step 7: Write the endpoint test**

Append to `backend/tests/test_dp_eligibility.py`:

```python
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app


@pytest.mark.asyncio
async def test_the_endpoint_answers_the_walkthrough_profile(session):
    """Spec §6's walkthrough: attestat, DİM 520, IELTS 7.0, bachelor.

    Germany and the UK blocked, both unlocks offered, the DP band shown, and the funded
    programme list filtered to what is reachable.
    """
    async def _get_test_db():
        yield session

    app.dependency_overrides[get_db] = _get_test_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            res = await c.post(
                "/api/v1/routes/assess",
                json={
                    "level_sought": "bachelor",
                    "qualification_held": "attestat",
                    "dim_score": 520.0,
                    "ielts": 7.0,
                    "language_certificate_level": "C1",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()

    assert any("DE" in entry for entry in body["blocked"])
    assert any("GB" in entry for entry in body["blocked"])

    prep_plans = [
        p for p in body["plans"]
        if len(p["hops"]) == 2 and p["hops"][0]["key"] == "az-prep-year"
    ]
    assert prep_plans, "the prep-year unlock was not offered"
    assert all(hop["citation"] for plan in body["plans"] for hop in plan["hops"])

    assert "400" in body["dp"]["band_checked"]
    assert "not an award" in body["dp"]["note"].lower()
```

- [ ] **Step 8: Run the whole suite**

Run: `cd backend && python -m pytest -q`

Expected: **126 passed**.

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/dp_eligibility.py backend/app/api/v1/routes.py backend/app/api/v1/router.py backend/tests/test_dp_eligibility.py
git commit -m "Model the state programme as a route, and expose route assessment"
```

---

## Done when

| Spec step | Satisfied by | Check |
|---|---|---|
| §10 step 0 — defects | Tasks 1-5 | No endpoint publishes without authentication; no code path fabricates a record; the §9 table is closed |
| §10 step 1 — DP loader | Task 6 | Both files load idempotently; a second run inserts 0 rows; counts match §2.2 exactly (1,214 / 2,907) |
| §10 step 2 — qualifications + requirements | Task 7 | A profile round-trips; every requirement row carries provenance and `source_url`; level is in both keys |
| §10 step 3 — routes + engine | Tasks 8-9 | An attestat-only profile returns Germany and the UK **BLOCKED** with both unlocks named, and Turkey/Poland **OPEN**; two-hop composition produces the prep-year path |
| §10 step 4 — DP eligibility as a route | Task 10 | DİM 520 + IELTS 7.0 returns the funded programme set filtered by country and level, with the band that decided it shown |

**Not in this plan**, and each needs its own: DAAD import (§10 step 5), the DİM cutoff model
(step 6), manual curation of 50 programmes (step 7 — **must start in parallel, today**), the
scholarship layer beyond the DP (step 8), and the results UI (step 9).

## Known deviations from the spec

1. **Route definitions live in code, not in a `routes` table** (spec §9 lists one). Reasoning
   is in the File Structure section above. Reversible in one task.
2. **Admin access is an email allowlist in settings**, not an `is_admin` column. It fails
   closed, needs no migration, and reuses the existing JWT path. If the team later needs to
   grant admin without a deploy, the column is the upgrade.
3. **The DP's per-field DİM thresholds are not modelled**, because they are not verified.
   The band is reported instead. Closing this needs the per-field table from dp.edu.az, and
   it is worth doing — it is the difference between "you clear some fields" and a definite
   answer.
