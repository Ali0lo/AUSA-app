# AUSA — Project State

**Rewritten 5 September 2026. Deadline 15 September 2026 — 10 days left.**

Everything here was checked against the running code, the test suite and the files on disk
on 5 September. Where a number is quoted, the command that produced it is named.

> **The previous version of this file (30 August) was wrong in its headline claims** — it
> described a selectivity index in the UI, "bachelor's only", and Azerbaijan inside the
> abroad flow. All three were superseded on 31 August and 4 September. This rewrite replaces
> it. See §8 for which other documents are now deprecated.

**Reading order for a new person:** this file → the
[route-first design spec](superpowers/specs/2026-08-31-route-first-advisor-design.md) (the
current product spec) → [`open-questions.md`](open-questions.md) §H, §I.

---

## 1. What the product is, in one paragraph

AUSA answers one question for an Azerbaijani student: **where can you actually go, and who
pays?** The student enters what they hold — level sought, school certificate or degree, exam
scores, language certificates, age, budget — and gets back the **routes** that are open to
them, the ones that are blocked and what would unlock them, the **universities** on each
route with what each one requires, and the **funding** they meet the published gates for.
This is the work Baku study-abroad agencies do by hand, minus the commission incentive — and
they largely do not surface scholarships at all.

A **separate Azerbaijan section** carries the machine learning: predicting next year's DİM
cutoff for domestic university programmes. It is a different question for a different
decision, and it is deliberately not blended into the abroad results.

**Two levels: bachelor and master's.** Six destinations: Turkey, Germany, the UK, the USA,
Poland, China. PhD is out of scope.

---

## 2. Why the product is not a match score — the three moves

This has been re-decided twice and the reasoning is worth carrying, because it is the part a
new reader gets wrong first.

**Move 1 — hand-set weights out, cutoff prediction in (23 August,
[ADR-0001](adr/0001-cutoff-prediction-replaces-weighted-scoring.md)).**
The original engine ranked programmes on `0.50 × academic + 0.30 × budget + 0.20 × language`.
Nobody could say where those weights came from, and a number nobody can defend is worse than
no number. The replacement was a learned one: predict each programme's published admission
**cutoff**, and let the match be *headroom* — the student's score minus that cutoff. A
`P(admit)` classifier was rejected in the same decision, because it needs labelled
accept/reject outcomes for Azerbaijani applicants, which do not exist and cannot be honestly
manufactured.

**Move 2 — cutoff prediction is invalid for the abroad product (31 August,
[ADR-0008](adr/0008-selectivity-replaces-cutoff-prediction.md)).**
The published cutoffs we collected describe the **domestic** admission pool in every
destination, not our student:

| Corpus | What it actually measures |
|---|---|
| Turkish YKS — 115,482 rows, our largest dataset | Turkish nationals competing in the domestic pool. An Azerbaijani enters through the international quota, TR-YÖS or SAT, and is never ranked against a YKS score |
| German NC | Verified on Marburg's own page: the tables are footnoted *"ohne Bildungsausländer\*innen"* — international applicants **excluded**. Non-EU applicants are allocated from a separate ~5–8% quota |
| Polish *próg punktowy* | The state-funded matura route. International admission is a separate, generally less competitive track |

This is structural. Collecting more published cutoffs does not fix it, because the number
being collected describes a different population from the user. A score — any score — was
answering the wrong question.

**Move 3 — routes, because a score cannot express the finding that matters (31 August,
[route-first spec](superpowers/specs/2026-08-31-route-first-advisor-design.md)).**
For a school-leaver the binding question is not *what score do I need* but *which paths are
even open*:

> An attestat holder **cannot apply directly to Germany or the UK at all.** Both are closed
> on the qualification, not on the score. **One year at an Azerbaijani university opens
> both**, because it converts the attestat into a qualification those systems recognise.

No percentage can carry that. A route can. And where admission *is* the question, it usually
is not the bottleneck — the College Scorecard admit-rate distribution is median 0.74 — so
**funding and eligibility are what actually decide the outcome**, which is what the engine
now computes.

**Where a learned score survives: Azerbaijan, and only there.** DİM admission is mechanical —
clearing the cutoff *is* admission — so `P(next year's cutoff ≤ your score)` is the success
rate rather than a proxy for it. That is the one honest home for the model, and it is
load-bearing rather than domestic trivia: the prep year that unlocks Germany and the UK is a
DİM admission, and the state programme's own academic gate is a DİM band.

---

## 3. What is actually built — verified 5 September

**286 backend tests pass** (`cd backend && python -m pytest -q`).

### Working end to end

| Area | State |
|---|---|
| **Route engine** | `services/route_engine.py` + `domain/route_definitions.py` — **16 routes** across 7 country codes, both levels, each cited. Classifies OPEN / UNLOCKABLE / BLOCKED and composes to a two-hop cap, so `az-prep-year → de-bachelor-direct` falls out of the data, not an `if` |
| **`POST /routes/assess`** | The product's spine. Profile in; blocked routes, costed plans, the universities each plan reaches, DP eligibility, and 10 scholarship assessments out |
| **State Programme** | `services/dp_eligibility.py` against the regulation; `dp_catalogue` holds the official **4,121 rows** (1,214 bachelor / 2,907 master, 2026) |
| **Scholarships** | `domain/scholarship_definitions.py` — **10 instruments** beside the DP, each carrying the gate that actually decides it (SOCAR: employment. Türkiye Bursları: under 21. Chevening: 2,800 hours). An unchecked gate returns `gates_unknown` and never counts as open |
| **Grade comparison** | `domain/grades.py` — attestat 5.0, 100-point, 4.0 and German scales, with `exact=False` when the comparison crosses scales |
| **Frontend `/plan`** | `RoutePlanner.tsx` calls `assessRoutes` against the real endpoint |
| **Platform** | Auth + access control (the 30 Aug bypass is fixed and tested), admin review queue, application tracker, PDF export, extraction pipeline with robots checking, CI |

### Built, measured, but not serving anything

| Area | State |
|---|---|
| **ML** | `models/cutoff_coldstart_{AZ,TR,US}.joblib` + `models/metrics.json`. AZ cold start: department-mean baseline **57.37 MAE → HistGradientBoosting 41.34, +27.9%**, on 2,576 rows / 1,028 programmes, `GroupShuffleSplit` on `program_key`. Honest and defensible — and **nothing loads it.** `grep -r joblib backend/` returns only the training script |
| **RAG / agent** | `chat.py`, `services/rag/`, `services/agent/` all run, but the agent's four tools are `check_missing_documents`, `get_program_deadline`, `draft_motivation_letter`, `extract_and_update_profile`. **None of them can see a route, a scholarship gate or the DP catalogue** — the LLM cannot answer the question the product exists to answer |

---

## 4. The five gaps between here and the goal

Ordered by what actually blocks the product, not by effort.

### Gap 1 — there is almost no catalogue 🔴

`data/curation/program_requirements_2026.csv` holds **15 rows**:

```
DE bachelor  3     GB bachelor  5     TR bachelor  2     CN bachelor  5
PL           0     US           0     master's     0
tuition_per_year populated on 2 of 15
```

Consequence, exactly as the code reports it: a master's profile gets *"we have not collected
this"* for every country; Poland and the USA get it at both levels; and **"rank by total cost
to degree" cannot run at all**, because there is no cost on 13 of 15 rows. The engine is
finished and the shelves are empty. This is the single biggest gap and it is human work, not
code.

The DP catalogue (4,121 rows) partly covers it — but only for the ~400 students a year the
state funds, and it carries university and programme names with **no requirements, no
tuition, no deadline**.

### Gap 2 — the ML is not a feature 🔴

Three artifacts, no endpoint, no page. Nothing in the running application would change if all
three were deleted. Two sub-problems inside it:

- **The AZ forecasting evaluation was skipped by a bug, not a data limit.** `metrics.json`
  says *"too few intake years for a temporal split"*. The data has three years — 2023 (805
  rows), 2024 (743), 2025 (1,028) — and 748 programmes appear in more than one.
  `temporal_split_years` returns `(2023, 2024, 2025)`, then `evaluate_forecasting` drops every
  row without a `cut_lag1`; the 2023 rows have no prior year, so `train = year <= 2023` is
  empty. The generic rule breaks *specifically* at exactly three years. A one-step split
  (train 2024 → test 2025) is available and was never run. **Forecasting is the question a
  student actually asks**, and it is the one where the persistence baseline is hard — which
  makes either outcome a real result. Roughly half a day.
- **No serving path.** An endpoint that loads `cutoff_coldstart_AZ.joblib` plus a page in the
  Azerbaijan section. Roughly half a day.

### Gap 3 — the LLM is not wired to the product 🟡

The spec's §8 job for the LLM is: interpret *"I'm interested in robotics"*, explain **why** a
route is blocked, narrate the gap, and walk the student through applying. Today the chat layer
retrieves documents from an empty index and the agent drafts a generic motivation letter. The
route assessment, the DP verdict and the scholarship gates — all of which are structured,
cited and already computed — are invisible to it. Wiring `/routes/assess` output in as agent
tools is what turns the LLM from a demo into the recommender and explainer.

### Gap 4 — a second, older product still ships beside the new one 🟡

`services/matching/` still computes `0.50 / 0.30 / 0.20` weighted scores, `/matching/evaluate`
still serves it, and the frontend `/match` page still runs it against seven hardcoded
`DEMO_PROGRAMS`. It is labelled *"Prototype scoring"*, which is honest, but it is the exact
thing ADR-0001 removed, live on a route a marker or a user can reach. Decide: delete it, or
keep it and say in one line why.

### Gap 5 — the headline demo is broken 🔴 *(found 5 September)*

`python demo_walkthrough.py` — the README's front door, "no database, ~10 seconds" — **crashes**:

```
sqlalchemy.exc.OperationalError: no such table: program_requirements
```

`demo_walkthrough.py:93` creates only `DPCatalogueEntry.__table__`. When commit `bbac7ab`
joined route plans to `program_requirements`, the demo was not updated, and no test runs it.
One-line fix, plus a smoke test so it cannot rot again.

---

## 5. Smaller defects, verified

| Defect | Impact |
|---|---|
| `schemas/matching.py:9` and `api/v1/auth.py:43` bound GPA `le=4.0` | **Rejects a valid Azerbaijani attestat average of 4.5/5 at registration.** `/routes/assess` already handles this correctly via `gpa_scale`; the older paths do not |
| `README.md` "Built but not yet connected: the frontend still shows demo programmes" | Stale — `/plan` calls the route engine as of `fdf230a`. Test count also stale (says 186 / 233; actual 286) |
| `docs/adr/README.md` | Does not list ADR-0008, and does not mark 0001/0002/0007 as amended |
| `models/metrics.json` AZ forecasting reason | States a cause that is not the real one (Gap 2) |
| DİM `verified_by` empty on all 2,576 rows | The training corpus is entirely unverified. A spot-check of 30 rows with a stated method beats zero |

---

## 6. What is decided, and what still needs a human

**Decided and not to be reopened:** routes over scores (§2) · six destinations, two levels ·
ML is Azerbaijan-DİM only and lives in its own section · scholarships run through the same
eligibility engine as programmes · no fabricated value ever substitutes for a missing one
(ADR-0004) · AUSA prepares and recommends, it does not submit applications and never claims
an admission outcome.

**Still needs a person, not a re-reading** — full text in
[`open-questions.md`](open-questions.md):

| # | Question | Why it blocks |
|---|---|---|
| **H4** | Every figure in the funding catalogue is `research-brief` provenance — no primary page opened. Türkiye Bursları' under-21 limit is the most load-bearing unverified number we ship | It is one of only two awards open at bachelor level |
| **H3** | NAWA Banach fields: our two sources give **opposite** lists | Reported as unresolved rather than guessed |
| **§11** | Does the DP's DİM 400–550 band apply above bachelor? The spec contradicts itself | Code currently treats it as unconfirmed, which is safe but is an unknown wearing the shape of an answer |
| **F1** | Nobody is named as the scraping sign-off owner | Gates the `/kod/` DİM enrichment |
| **I5** | Who spot-checks DİM rows against source PDFs | "Trained on unverified data" is a fair question to be asked |
| **C3** | What the course actually grades — notebook, report, running app, or all three | Decides whether the ML ships wired or written up, and whether `notebooks/` (currently empty) must be filled |

---

## 7. Task split — four tracks, 10 days

Written so the tracks do not touch the same files. Sizes are working days.

### Track A — Catalogue and curation *(two people; the critical path)*

| | Task | Days |
|---|---|---|
| A1 | **Master's requirement rows** — the DP funds 2,907 master's places against 1,214 bachelor, and we hold zero master's rows. Start with TR, GB, DE | 3 |
| A2 | **Tuition and deadline on every existing row** — 13 of 15 have no cost, so cost ranking cannot run | 1 |
| A3 | **Poland and the USA**, both levels, from the §5.1 schema | 1.5 |
| A4 | **Verify the funding figures (H4)** — Türkiye Bursları first, then Chevening, NAWA, SOCAR. Promote each from `research-brief` to a real citation | 1.5 |
| A5 | **DİM spot-check (I5)** — 30 rows against source publications; record the method and the fraction | 0.5 |

Everything here is `data/curation/*.csv` plus `scripts/load_program_requirements.py`. No
application code.

### Track B — ML, the Azerbaijan section *(one person)*

| | Task | Days |
|---|---|---|
| B1 | **Fix the forecasting split** (Gap 2) — one-step train 2024 / test 2025 against the persistence baseline. Report the result either way | 0.5 |
| B2 | **Serve the model** — an endpoint loading `cutoff_coldstart_AZ.joblib`, with quantile bands, refusing to predict where history is thin | 0.5 |
| B3 | **The Azerbaijan page** — its own section, saying in its own words that this predicts cutoffs at Azerbaijani universities | 1 |
| B4 | **EDA / comparison notebook** importing `train_cutoff_models.py`, so report and production cannot drift (`notebooks/` is empty) | 1 |

### Track C — Product and LLM *(one person)*

| | Task | Days |
|---|---|---|
| C1 | **Fix `demo_walkthrough.py`** + a smoke test (Gap 5) | 0.5 |
| C2 | **Agent tools over the route engine** (Gap 3) — assess routes, explain a block, list funding gates, all cite-or-drop | 2 |
| C3 | **Resolve the legacy matcher** (Gap 4) — delete `/matching/*` and the demo programmes, or keep with a stated reason | 0.5 |
| C4 | **Fix the `le=4.0` GPA bound** on registration and the matching schema | 0.25 |

### Track D — Frontend and report *(one person)*

| | Task | Days |
|---|---|---|
| D1 | **Discovery flow** — one profile step, results refining live, destination ranks and never excludes | 2 |
| D2 | **Target flow** — name a university, get gap + requirement checklist + process checklist + alternatives | 1.5 |
| D3 | **Provenance and `last_checked` visible on every row**, and `unknown_fields` rendered as a named absence rather than a blank | 0.5 |
| D4 | **Report / README pass** — correct the stale claims in §5, and state plainly that this is two products in one repository | 1 |

**Cut order if the schedule slips** (unchanged): Poland first, then the USA bachelor path,
then curation depth — fewer universities per country rather than dropping a country. **Not
cuttable:** the DP path, because it is the only segment where the data is already
authoritative.

---

## 8. Document status — what to read and what to ignore

| Document | Status |
|---|---|
| [`superpowers/specs/2026-08-31-route-first-advisor-design.md`](superpowers/specs/2026-08-31-route-first-advisor-design.md) | **Current product spec.** Authoritative |
| This file | **Current status.** Authoritative |
| [`open-questions.md`](open-questions.md) | Current for §H and §I. §A–§G are historical record — several answers there are superseded by ADR-0008 and the route-first spec |
| ADR [0004](adr/0004-batch-serving-and-explainability.md), [0005](adr/0005-scholarship-pass-precedes-budget-filter.md), [0006](adr/0006-admission-routes.md) | Still governing |
| ADR [0001](adr/0001-cutoff-prediction-replaces-weighted-scoring.md), [0002](adr/0002-per-country-models-and-normalization.md), [0003](adr/0003-evaluation-protocol.md), [0007](adr/0007-three-number-model-and-honesty-tiers.md), [0008](adr/0008-selectivity-replaces-cutoff-prediction.md) | Amended. Read as the reasoning trail of §2, **not as current instructions** |
| `architecture-decisions.md`, `data-sourcing.md`, `university-matching-platform-notes.md` (root, 28 Aug) | Pre-pivot design notes. Still hold live material (`data-sourcing.md` §5.3's source order is binding), but their product framing is superseded |
| `data-collection-plan.md` | Pre-pivot. Aimed at ML corpus collection; `data/README.md` is the live version |
| `docs/database_schema.md`, `docs/schema.sql` | Superseded by the Alembic chain. Kept only as a reading aid |
| **Deleted 5 September** | `scripts/train_prediction_models.py` and its two `ml_weights/*.joblib` (a `predict_proba` admission-probability trainer, contradicting ADR-0008) · `superpowers/plans/2026-08-30-catalogue-join.md` (self-declared superseded) |

### Data on disk that earns no keep

`data/raw/usa/scorecard_raw.zip` is **469 MB** and `usa_cutoff_history.csv` trains nothing
since the ML narrowed to Azerbaijan. `data/raw/turkey/` is ~200 MB and feeds only the model
that loses to persistence. Both are gitignored, so this is disk, not repository — but neither
is on the path to anything now.
