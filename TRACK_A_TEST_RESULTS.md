# Track A validation — 15 September 2026

| Check | Result | What it establishes |
|---|---|---|
| Backend suite, `python -m pytest -q` | **331 passed, 3 skipped** | Existing route, funding, authentication, application, ingestion and export regressions; new CSV validation, catalogue APIs, review and sampling checks. The three opt-in PostgreSQL tests were run separately below. |
| PostgreSQL migration suite | **3 passed** | Fresh migration/bootstrap, repeated imports, null-safe uniqueness, preservation of existing team records/reviews, original unversioned-schema adoption, refusal of unknown schema changes and preservation of application tracker records. |
| Frontend, `npm test` | **63 passed in 11 files** | Existing UI regressions plus catalogue response validation/pagination, changing profiles, stale responses, retry, evidence acknowledgement and review conflicts. |
| `npm run lint` | **Passed** | No lint errors or warnings from project code. |
| `npm run build` | **Passed, including TypeScript** | Production Next.js build with `ignoreBuildErrors: false`; all 11 pages generated. |
| Playwright Chromium suite, `npm run test:e2e` | **9 passed** | Navigation/mobile menu, missing routes, advisor error recovery, application workflow, registration/sign-in and the new catalogue/review browser flows. API responses are controlled fixtures in this suite. |
| Production frontend + real HTTP API | **Passed** | Actual Next.js production server, FastAPI and a disposable SQLite catalogue loaded through the production CSV loaders: 30 masters, UCL's three programmes, IELTS changes, review caveats, uncollected university and no browser exceptions. |
| `demo_walkthrough.py` | **Passed** | Original school-leaver flow, TUM/LMU on the German prep-year route and named master's universities in TR/GB/CN (also DE/US/PL). |
| Dependency consistency | **Passed** | The 100 installed Python packages are compatible; resolving the supplied requirements with `constraints-tested.txt` requires no changes. Frontend uses the included npm lockfile. |
| CSV release checks | **Passed** | 47 requirement identities; 30 distinct masters in six countries; original 15 identities retained; original three FSP rows retained; every original row has tuition/currency or an unknown-cost note. DP imports contain 1,214 bachelor and 2,907 master entries. |
| Patch integrity | **Passed** | Archive CRCs and file hashes checked. Applying the changed files to the supplied baseline reconstructs the intended project files. The preflight detects conflicting teammate edits and accepts already-applied files. |

## Environment and limits

Executed on Linux with CPython **3.12.14**, Node **24.19.0** and Chromium
**153.0.8010.0**. The backend suite reported four upstream deprecation warnings,
not failing tests. Browser installation used a compatible local Chromium executable.

PostgreSQL-specific SQL was executed by **PostgreSQL 18.3 in PGlite**, including
pgvector and the real Alembic/asyncpg bootstrap. A disposable socket adapter supplied
session cleanup for sequential tests. This verifies database syntax, schema/data
preservation and import behaviour; it is not a native PostgreSQL concurrency/load test.
The production HTTP/browser check used SQLite for its disposable catalogue; it does
not substitute for the separate PostgreSQL migration checks.

Not executed: native Windows `.bat`, Python 3.13, the team's actual database or later
unshared edits, paid live OpenAI requests, production deployment/load, Firefox/Safari,
or the missing DİM publication audit. No API key was needed for catalogue startup or the
catalogue/route checks. Human review remains pending on the curated sources. Testing
cannot guarantee the absence of every possible defect.

## Repeat the checks

In `backend`, after installing the tested dependencies:

```bash
python -m pytest -q
python -m scripts.load_program_requirements --file ../data/curation/program_requirements_2026.csv --validate-only
python -m scripts.load_program_requirements --file ../data/curation/program_requirements_track_a.csv --validate-only
python ../demo_walkthrough.py
```

In `frontend`:

```bash
npm ci
npm test
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
```

For a production stack check, build the frontend with its default API URL
`http://localhost:8000/api/v1`, then from `backend` run:

```bash
python -m scripts.check_catalogue_stack
```

That helper starts temporary servers on ports 8000 and 3100, uses a newly created
temporary SQLite database, and cleans up afterwards. Stop your local servers on those
ports first. An existing browser can be supplied with `PLAYWRIGHT_EXECUTABLE_PATH`.

For migrations, create a **separate disposable PostgreSQL database** with pgvector
available. Set `AUSA_TEST_POSTGRES_URL` to its asyncpg URL, then run
`python -m pytest tests/test_catalogue_postgres.py -q` from `backend`.
**Those three tests drop and recreate the public schema of that test database. Never
point this variable at a team, development or production database that contains data
you need.** The tests do not read the application's `DATABASE_URL` as their target.
