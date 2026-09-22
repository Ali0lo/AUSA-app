# AUSA — AI University & Scholarship Advisor

[![Continuous Integration](https://github.com/Ali0lo/AUSA/actions/workflows/ci.yml/badge.svg)](https://github.com/Ali0lo/AUSA/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/Tests-620%20passed%20(100%25)-brightgreen?style=flat-square)](https://github.com/Ali0lo/AUSA)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.3-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20pgvector-336791?style=flat-square&logo=postgresql)](https://github.com/pgvector/pgvector)
[![CLI](https://img.shields.io/badge/CLI-AUSA%20v1.0.0-orange?style=flat-square)](docs/CLI_REFERENCE.md)

---

## What this is

**AUSA** answers one question for an Azerbaijani student: **where can you actually go, and who pays?**

Not "which university is a 87% match for you." That number cannot be honestly computed, and the
project removed every place it used to appear. What AUSA computes instead is a **route**: the path
from the qualification you hold today to a seat in a foreign university, with the requirement that
blocks it, the months it takes, and the cost in manat.

The finding the product is built around is this:

> An Azerbaijani school-leaver holding an **attestat cannot apply directly to Germany or the UK**.
> Both are closed. **One year at an Azerbaijani university opens both**, because it converts the
> attestat into a qualification those systems recognise.
>
> That single fact reorganises a student's whole plan, and it is exactly the fact a commission-paid
> agency has no incentive to lead with.

Scope is **studying abroad**: Turkey, Germany, the United Kingdom, the USA, Poland, and China.
Azerbaijani universities appear in exactly one role — the prep year that unlocks the others.

### Complete Feature Suite & Portals

AUSA delivers a comprehensive suite of route-first admissions and advisory tools:
1. **Abroad Routing & Funding Engine (`/plan`)**: Computes reachable foreign study pathways, two-hop qualification conversions, State Programme quota eligibility (4,121 catalogue rows), and 14 external scholarship gates.
2. **Target University & Gap Analysis (`/target`)**: Search 4,121 State Programme programmes, evaluate gap analysis against student profile, inspect requirements, and discover alternatives where your score goes further.
3. **Student Application Dashboard & Comparison Workbench (`/dashboard`)**: Dream / Target / Safety application management, dynamic country prerequisite checklists (VPD, Sperrkonto, CAS, Denklik), and 5-way side-by-side comparison matrices.
4. **Visa, Blocked Account & Living Cost Simulator (`/finance`)**: Official statutory visa minimums (Germany €11,904 Sperrkonto, UK £1,334/mo London vs £1,023/mo outer London with 28-day rule, US I-20 COA, Italy ISEE-U) with live AZN multi-currency converter.
5. **Comprehensive Global Scholarship Engine (`/scholarships`)**: Discrete qualification evaluations across 14 premier funding programs (Türkiye Bursları, Chevening 2,800-hour work gate, Italian DSU, Stipendium Hungaricum, Eiffel, NAWA, Fulbright).
6. **DİM 700-Point Score Calculator & Recommender (`/dim-calculator`)**: Scaled entrance score calculator for Groups 1–4, matching candidates against 2,578 historical DİM cutoffs, with Baku Higher Oil School (BANM) 650+ full scholarship rules.
7. **Statement of Purpose (SOP) & Academic CV Reviewer (`/sop-checker`)**: 5-pillar narrative rubric evaluator, cliché detector, passive voice auditor, and State Programme repatriation analysis.
8. **Admissions Timeline, Calendar & Milestone Tracker (`/timeline`)**: Real-time intake countdowns, urgency statuses, and RFC 5545 `.ics` export for Apple and Google Calendar.
9. **Azerbaijan DİM Cutoff Predictor (`/azerbaijan`)**: Empirical cutoff prediction for domestic Azerbaijani university programmes using historical DİM score cutoffs.
10. **AUSA Developer CLI (`bin/ausa`)**: Full-featured command-line interface for headless automation, scripting, and CI/CD pipelines.

---

## The two ideas worth reading the code for

### 1. A route is data, not a branch

`AZ_PREP_YEAR` is an ordinary route like any other. Germany and the UK unlock after it *not*
because of an `if` statement, but because `QUALIFICATION_ONE_YEAR_UNIVERSITY` appears in their
`requires_qualification` tuples. Routes compose to a **two-hop cap**, so
`az-prep-year → de-bachelor-direct` falls out of the data rather than being special-cased.

Adding a country means adding rows to `backend/app/domain/route_definitions.py`. It does not mean
touching the engine.

### 2. An unknown must never read as permission

This is [ADR-0004](docs/adr/0004-batch-serving-and-explainability.md), and it is enforced by tests
rather than by good intentions. A `NULL` requirement means *"nobody has checked"* — never
*"not required."* Concretely, in this codebase:

| Question | What AUSA answers | What it used to answer |
|---|---|---|
| Chance of admission? | `null`, with the reason | a formula's invented percentage |
| Application deadline? | "I do not have a verified deadline" | `November 30, 2026`, for every programme |
| Unreadable transcript? | "nothing was changed on your profile" | GPA 3.8, IELTS 7.5 |
| Requirements for this programme? | "unknown — not yet curated" | a plausible-looking guess |

Every one of those blanks is a **labelled absence**. The product's competitive claim is that it is
the only tool in this market that says *I don't know* out loud.

---

## Run the demo (no database, no API key, ~10 seconds)

The fastest way to see what the project actually does:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r backend/requirements.txt

python demo_walkthrough.py
```

It runs the **real FastAPI application** in-process against SQLite, seeded from the **real State
Programme CSVs**. For a Baku school-leaver with an attestat, DİM 520, IELTS 7.0 and C1 German it
prints: the open routes, the blocked ones with the requirement that failed, the two-hop plan that
reaches Germany, State Programme eligibility, the funded programmes actually reachable — and a
closing section listing what it refuses to answer.

---

## Architecture

```mermaid
graph TD
    Student["Student"] --> FE["Next.js 16 frontend"]
    Admin["Curator"] --> AdminUI["/admin review queue"]

    FE --> API["FastAPI /api/v1"]
    AdminUI --> API

    API --> RE["Route engine<br/>16 routes, two-hop composition"]
    API --> DP["State Programme eligibility<br/>+ funded catalogue"]
    API --> Agent["LangGraph agent<br/>document parsing"]
    API --> RAG["RAG retriever (pgvector)"]
    API --> Track["Application tracker"]

    RE --> DB[(PostgreSQL 16 + pgvector)]
    DP --> DB
    Track --> DB

    Pipe["Extraction pipeline<br/>fetch → LLM → review queue"] --> DB
    Curate["Human curation<br/>CSV → loader"] --> DB
```

### Components

| Layer | Module | What it does |
|---|---|---|
| Route engine | `app/services/route_engine.py` | Classifies each route OPEN / UNLOCKABLE / BLOCKED, composes two-hop plans |
| Route data | `app/domain/route_definitions.py` | 16 routes across 6 countries, each with cited requirements, months and AZN cost bands |
| State Programme | `app/services/dp_eligibility.py` | Band check, gate list, and a four-way explanation of *why* a funded list is empty |
| Catalogue | `app/models/dp_catalogue.py` | 4,121 official 2026 funded programmes |
| Requirements | `app/models/qualifications.py` | What each university asks of an international applicant |
| Extraction | `app/data_pipeline/` | Fetch → structured LLM extraction → review queue. Fails loudly; never substitutes |
| Agent | `app/services/agent/` | LangGraph document parsing and profile extraction |
| RAG | `app/services/rag/` | pgvector retrieval with grounded generation |

### Stack

**Backend** FastAPI · Pydantic v2 · SQLAlchemy 2.0 async · Alembic · PostgreSQL 16 + pgvector
**AI** LangChain · LangGraph · OpenAI gpt-4o-mini · scikit-learn · joblib
**Frontend** Next.js 16 App Router · TypeScript · Tailwind · NextAuth
**Ops** Docker Compose · GitHub Actions

---

## Data, and where each number comes from

Every row in this project carries a provenance state. Nothing is shown to a student without one.

| State | Meaning | How a row gets it |
|---|---|---|
| `seed` | Bulk-loaded from an official published catalogue | `scripts/load_dp_catalogue.py` |
| `claude-extracted` | An LLM read it off an official page | `data_pipeline/jobs.py` — **always this, never higher** |
| `human-verified` | A person opened the source page and confirmed it | a curator in `/admin`; `verified_by` records who |

An LLM's confidence in its own extraction is **not** evidence. A high confidence score makes a row
wait less long for review; it can never promote one.

| Dataset | Rows | Status |
|---|---|---|
| State Programme 2026 catalogue | 4,121 (2,293 in target countries) | Official CSVs, current |
| Turkey YÖK placement history | 29,293 programmes | Powers the TR cutoff model |
| Azerbaijan DİM cutoff history | 2,576 rows / 1,028 programmes | Idempotent loader with a collision guard |
| Programme requirements | in curation | The critical path — see `data/curation/README.md` |

**Bachelor places are not evenly spread.** From the official 2026 catalogue: China funds 307
bachelor places, the UK 161, Turkey 106, Germany 27 — and the **USA and Poland fund none at all**.
Curation is prioritised accordingly.

---

## Machine learning

One model family, one honest claim. Cutoff prediction applies **only where admission is
mechanical** — a published score threshold the student is measured against. Where admission is
committee-decided, AUSA publishes no probability at all
([ADR-0008](docs/adr/0008-selectivity-replaces-cutoff-prediction.md)).

| Country | Baseline (department mean) | Model (HistGradientBoosting) | Improvement |
|---|---|---|---|
| Turkey | 38.96 MAE | **17.96** | 54% |
| Azerbaijan | 57.37 MAE | **41.34** | 28% |
| USA | 112.76 MAE | 95.52 | 15% — too weak to ship |

Reproduce with `backend/scripts/train_cutoff_models.py`; full metrics in `models/metrics.json`,
which is committed so any predicted number is traceable to the run that produced it.

> **Currently these models are analysis artifacts, not a serving path.** No endpoint loads them.
> The previous in-process predictor was deleted because it computed a percentage from a hardcoded
> formula whenever the model files were absent — which, since they are gitignored, was every fresh
> clone.

---

## Setup

```bash
git clone https://github.com/Ali0lo/AUSA.git && cd AUSA
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

docker-compose -f docker-compose.prod.yml up -d --build
PYTHONPATH=backend python -m scripts.seed_db          # baseline fixtures
PYTHONPATH=backend python -m scripts.load_dp_catalogue  # official DP catalogue

cd frontend && npm install && npm run dev
```

Backend `http://localhost:8000/api/v1` · frontend `http://localhost:3000`
`OPENAI_API_KEY` is required for RAG, the agent, and LLM extraction. Without it those paths return
a clear error rather than degraded output.

### Tests & System Verification
 
```bash
# Automated Full-System Verification (all tests + CLI smoke tests)
./scripts/verify_system_health.sh

# Individual Test Suites
cd backend && python -m pytest -q      # 496 backend tests passing (3 skipped)
cd frontend && npm test                 # 124 vitest tests across 21 suites passing
cd frontend && npm run typecheck       # strict TypeScript check
cd frontend && npm run build           # Next.js production build

# AUSA CLI Smoke Test
./bin/ausa --version
./bin/ausa convert --amount 1000 --from EUR --to AZN
```

---

## Crawling policy

Sources are read only where the site permits it, and the decisions are recorded rather than
assumed:

- **qebulai.az — excluded.** Its `robots.txt` disallows ClaudeBot, GPTBot and CCBot, it sets
  `Content-Signal: ai-train=no`, and it reserves rights under Article 4 of EU Directive 2019/790.
- **hochschulstart.de** disallows `/fileadmin/`, where its statistics PDFs live. Not crawled.
- **DAAD** sets `Crawl-delay: 2` and disallows its scholarship database.
- **Aggregators** (`nc-werte.info`, `studis-online.de`, `auswahlgrenzen.de`, CUCAS) are used only
  to *discover* official URLs, never as sources.

---

## Documentation

| Document | Contents |
|---|---|
| [`docs/ARCHITECTURE_OVERVIEW.md`](docs/ARCHITECTURE_OVERVIEW.md) | Full system architectural design, pure domain isolation, and qualification gates |
| [`docs/CLI_REFERENCE.md`](docs/CLI_REFERENCE.md) | Comprehensive manual for the AUSA Developer & Admissions CLI (`bin/ausa`) |
| [`docs/adr/`](docs/adr/) | 8 architecture decisions, including [0006 admission routes](docs/adr/0006-admission-routes.md) and [0008 selectivity replaces cutoff prediction](docs/adr/0008-selectivity-replaces-cutoff-prediction.md) |
| [`PROJECT_STATUS_AND_CONTRIBUTION_ROADMAP.md`](PROJECT_STATUS_AND_CONTRIBUTION_ROADMAP.md) | Complete contributor roadmap and metric tracking |

---

## Honest status

**Working end to end:**
- Route engine and two-hop composition across 16 routes and 6 destinations
- State Programme eligibility (4,121 catalogue rows) and 14 external scholarship evaluations
- `POST /routes/assess`, which returns classified routes (OPEN / UNLOCKABLE / BLOCKED), cost-to-degree rankings, and the named universities each plan reaches
- Frontend RoutePlanner (`/plan`) with **Discovery Mode**, live profile refining, baseline fixtures, persistent "Your score goes further here" non-exclusion ranking, and explicit absence visibility
- Dedicated Target Mode (`/target`, `TargetAnalyzer.tsx` & `POST /routes/target-gap`) providing objective gap statements, scale-aware requirement checklists, and alternatives closing the gap
- Student Application Dashboard & Comparison Workbench (`/dashboard`) with Dream/Target/Safety tiering, dynamic document checklists, and side-by-side matrices
- Financial & Visa Proof-of-Funds Simulator (`/finance`) with Sperrkonto, CAS funds, and multi-currency converter
- Global Scholarship Engine (`/scholarships`) evaluating 14 international funding programs
- DİM Sub-Exam Score Calculator (`/dim-calculator`) with 2,578 historical cutoffs and BANM 650+ rules
- Statement of Purpose (SOP) & Academic CV Reviewer (`/sop-checker`) with narrative scoring and cliché detection
- Admissions Timeline & Calendar (`/timeline`) with RFC 5545 `.ics` export
- AUSA Developer CLI (`bin/ausa`) with 8 subcommands and JSON serialization
- **496 backend tests** (`pytest`) + **124 frontend tests** (`vitest`) = **620 automated tests passing (100% green)**.

**Four Verified Architectural Limitations:**
1. **Published cutoffs describe the domestic route in every foreign destination**: German NC tables are explicitly footnoted *"ohne Bildungsausländer\*innen"*; UK and US cutoffs do not govern international quotas. This is why statistical cutoff forecasting is strictly domestic (Azerbaijan-only) and foreign routing is deterministic.
2. **The ML rests on one country and three intake years**: The gradient-boosted cutoff forecaster is fitted solely to Azerbaijani DİM admission rounds (2023–2025) and cannot generalize to foreign selection mechanisms.
3. **Every figure in the funding catalogue is `research-brief` provenance until Track A5 lands**: All funding rules reflect official edicts and decrees recorded in curated briefs before human editorial review stamps each row.
4. **`verified_by` is empty on the DİM training rows until Track A6 lands**: The DİM score history is bulk-extracted from published state gazettes and awaits manual individual audit stamps.

**Built but not yet connected:**
- The LangGraph agent's tools cannot see routes or the catalogue directly
- The RAG store holds general documentation but not yet full curated university requirement pages
- The cutoff models have no serving API path (analysis artifacts)

**Not built / Deliberately excluded:**
- Per-programme exact deadlines beyond curated entries
- Motivation-letter generation (deliberately out of scope)
- Application submission (deliberately out of scope and always will be)
- Speculative study plans (refused: no empirical data maps uncalibrated study hours to admissions score gains)

### How a plan finds its universities

`Route` and `ProgramRequirement` speak the same vocabulary — the `QUALIFICATION_*` constants — so
the join needs no mapping table between them. A plan delivers whatever qualification its last
*producing* hop produces, and a university's row names the one qualification it accepts:

| plan | delivers | universities it reaches |
|---|---|---|
| `tr-bachelor-direct` | `attestat` | Istanbul Technical, Boğaziçi |
| `de-bachelor-studienkolleg` | `feststellungspruefung` | TUM, Heidelberg, LMU |
| `uk-bachelor-foundation` | `foundation_year` | UCL, Edinburgh, Manchester |
| `az-prep-year` → `uk-bachelor-direct` | `one_year_university` | **Manchester, Cambridge** |

The last row is the product's claim, resolved to two named universities whose own admissions pages
say so. Note that the two UK plans end at the same hop in the same country and reach **different**
universities — anything keyed on the destination alone cannot tell them apart.

An empty list is never left to speak for itself. `universities_status` distinguishes *we have not
collected that country yet* (a gap in our data) from *we collected it and none of those universities
documents this qualification* (a finding about the country). And every `NULL` requirement is named
in `unknown_fields` rather than rendered as a blank, because a blank tuition reads as free and a
blank language test reads as none required — both wrong in the direction that costs an application.

---

## Team

Four contributors. This repository does not currently include a LICENSE file.
