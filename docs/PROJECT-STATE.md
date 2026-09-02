# AUSA — Project State

**Written 29 August 2026, updated 30 August. Deadline 15 September 2026 — 16 days left.**

This is the single clean starting point. It records what is decided, what is built, what
is measured, what is still open, and what happens next. The ADRs hold the *reasoning*;
this file holds the *status*.

> **The product spec is [ADR-0007](adr/0007-three-number-model-and-honesty-tiers.md).**
> A grilling session on 29–30 August took seventeen decisions and closed the reframe that
> §9 used to hold open. §9 is now a summary and a pointer; ADR-0007 is authoritative.
>
> **The bottleneck is the catalogue, not the model.** `programs` holds 7 seed rows while
> 127k rows of cutoff history sit in CSVs with no table and no join. Do not propose more
> modelling work without checking whether that has changed.

---

## 1. What the product is, in one paragraph

AUSA advises Azerbaijani students on where to study abroad. It takes a student profile
(grades, entrance qualifications, language certificates, budget), filters to programs
they are actually eligible for, and ranks the rest by how comfortably they clear each
program's **admission cutoff**. A tree-based ML model predicts those cutoffs. The model
never decides eligibility, and the product never shows an admission probability.

---

## 2. The central decision, and why

**We predict cutoffs, not admission probability.** ([ADR-0001](adr/0001-cutoff-prediction-replaces-weighted-scoring.md))

The obvious ML framing — "given this student, what is P(admit)?" — is unbuildable here.
It needs labelled student outcomes: applications paired with accept/reject. Nobody has
that dataset for Azerbaijani applicants, we cannot generate it, and buying it is not an
option. Every path to it ends in synthetic labels, which would mean training a model on
our own assumptions and presenting the output as evidence.

Cutoff prediction dissolves the problem. Five of our seven target countries admit by
**threshold**: DIM, YKS, German NC, UCAS tariff, SAT percentiles. Those thresholds are
*published*, per program, per year, going back five or more years. That is a real,
labelled, public regression target — and it is the quantity the student actually wants
to know.

The match score becomes **headroom**: the student's score minus the predicted cutoff.

**What was rejected and why:**

| Rejected | Reason |
|---|---|
| P(admit) classifier | No labels exist, and none can be honestly manufactured |
| Hand-set weights (0.5 / 0.3 / 0.2) | The thing the course requires us to replace |
| LLM scoring | Same — not ML, not reproducible, not gradeable |
| Synthetic student outcomes | Trains on our assumptions, then reports them as findings |
| One global model | Incompatible units — see [ADR-0002](adr/0002-per-country-models-and-normalization.md) |

---

## 3. Empirical results — already measured, on real data

Turkey, 115,482 real YKS cutoff rows, 2019–2024. These are the actual numbers, not
projections.

| Task | Baseline | Best model | Verdict |
|---|---|---|---|
| **Forecasting** (next year's cutoff for a program with history) | persistence `next = last` → **MAE 13.77** | RandomForest **15.77** | **Model loses**, −14.5% |
| **Cold start** (cutoff for a program with *no* history) | department mean → **MAE 38.96** | HistGradientBoosting **17.96** | **Model wins**, +53.9% |

**Why forecasting loses:** cutoffs are ~0.97 autocorrelated year-over-year. Persistence
is an extremely strong baseline. Remedies were tried and all failed — predicting the
delta instead of the level (17.66), restricting the training window to recent years (all
worse), shrinking the predicted delta toward zero (monotonic, and `k=0` *is* the
baseline). Root cause: 2021–2022 were high-volatility years (mean |Δ| ≈ 34) while
2023–2024 were calm (≈ 7–10). The model learns turbulence that no longer exists.

**Why cold start wins:** a newly curated program has no lag features, so persistence is
structurally *unavailable*. The model has to infer the cutoff from university, city,
faculty, department, score type, scholarship type and quota — and it does that far
better than the department average. This is also a genuine product need: every program a
teammate curates by hand arrives with no history.

**Both results ship.** The negative forecasting result is reported as a rigorous
finding, with the failed remedies as evidence of a real investigation. That is stronger
coursework than a tuned number with no baseline.

---

## 4. Decisions locked in the grilling session

| # | Decision | Consequence |
|---|---|---|
| **Q1** | Train both tasks; **ship cold start**, report forecasting as a negative result | The demo runs on the model that actually wins |
| **Q2** | Present a **selectivity index** — within-country percentile, plus Reach / Match / Safety bands | Never an absolute probability. Enforced by ADR-0001 |
| **Q3** | **Azerbaijan DIM is committed scope**, not a stretch goal | Home market ships; raises data risk |
| **Q4** | Collect DIM by **scraping sec.az / uniaz.info** (official journal is paywalled) | Makes F1 legal sign-off a hard prerequisite, not background work |
| **Q5** | **Ask permission in parallel, scrape politely** — named owner, robots.txt + ToS check, rate-limited | Collection can start without waiting on a reply |
| **Q6** | **Fariz builds ML + backend. Team owns data collection, frontend, report** | Curation is the critical path and needs two people |
| **Q7** | **Bachelor's only** | Verified: all three datasets are undergraduate; zero master's rows |
| **Q8** | **Lock scope now.** Germany added only if DIM lands early — go/no-go **5 September** | Prevents a half-finished fourth country |
| **Q9** | **Preparation and route recommendation only** — no submission or application claims | Bounds the legal and product surface |

**Resulting locked scope:** ML on **Turkey + USA + Azerbaijan**, **bachelor's only**,
**cold-start model ships**, **selectivity index** in the UI, **three algorithms**
(Decision Tree / Random Forest / HistGradientBoosting) compared against honest
baselines, delivered as a **training script + notebook + committed metrics JSON**.
Germany, if it lands, has **no ML** — hand-curated programs with deterministic ranking.

---

## 5. What is actually built

### Documentation — done
- **ADR-0001** cutoff prediction replaces weighted scoring — *Accepted*
- **ADR-0002** per-country models and normalization — *Accepted*
- **ADR-0003** evaluation protocol (temporal + cold-start split, persistence baseline mandatory) — *Accepted*
- **ADR-0004** batch serving and explainability, **no silent fallbacks** — *Accepted*
- **ADR-0005** scholarship pass precedes budget filter — *Accepted*
- **ADR-0006** admission routes — **Proposed**, blocked on G1–G4
- `data-collection-plan.md`, `data/README.md` — reproducible sources and commands

### Data — two of three countries collected
| Country | Rows | Units | Status |
|---|---|---|---|
| Turkey | **115,482** across 29,293 programs (20,341 with ≥3 years) | YKS score | **Done**, MIT-licensed |
| USA | **14,798** across 1,853 institutions | admit rate, SAT percentiles | **Done**, US federal open data |
| Azerbaijan | **2,576** across 1,028 programs, 42 universities, 2023–2025 | DIM 0–700 | **Done** (29 Aug) from sec.az |
| Germany | 0 | Abiturnote | Conditional on 5 Sep go/no-go |

Data is gitignored. `data/README.md` reproduces it exactly.

### Backend — security hardened, merged
PR #4 (`main` @ `9a85541`) fixed real authentication and authorization holes:
- auth bypass — a DB outage let *any* credentials log in as a fabricated user
- admin authorization — now fail-closed against an `ADMIN_EMAILS` allowlist
- application tracker — ownership enforced on all three endpoints
- CORS `"*"` removed; production refuses to boot with a dev secret key
- tests rewritten (several had been asserting the vulnerable behaviour) — **49 pass, 1 skipped**

### ML — pipeline built and running (29 Aug)
`backend/scripts/train_cutoff_models.py` — three algorithms × two protocols × three
countries, importable by the notebook, writing `models/metrics.json` (committed;
`.joblib` artifacts are not). Current run:

| Country | Forecasting | Cold start |
|---|---|---|
| **TR** | persistence 13.77 → best 17.49 · **loses** | dept-mean 38.96 → **HGB 17.96, +53.9%** |
| **US** | persistence 34.52 → RF 33.92 · +1.7%, marginal | global-mean 112.76 → **RF 95.52, +15.3%** |
| **AZ** | *skipped* — only 3 intake years | dept-mean 57.37 → **HGB 41.34, +27.9%** |

Caveats kept visible rather than smoothed: the **US cold-start baseline is degenerate**
(Scorecard is institution-level, so department-mean collapses to global-mean, making
+15.3% a weaker claim than Turkey's); US rows drop 14,798 → 9,714 because SAT p25 is
missing for test-optional institutions post-2020; **AZ forecasting cannot be evaluated**
until a fourth intake year exists.

`backend/scripts/train_prediction_models.py` is the old pre-pivot script and still needs
deleting. Its stale `.joblib` files (sklearn 1.9.0) are what trigger the
`InconsistentVersionWarning` in the test run.

---

## 6. What still has to be decided

### G1–G4 — closed 29 August (ADR-0006 now Accepted)

Research established that **DIM has recognition protocols with Turkish universities**, so
an Azerbaijani student can apply there on their DIM score alone. DIM is a Turkey route,
not just the home-market one — which inverted the priority the draft assumed.

**Three routes in scope. YÖS dropped** (per-programme cutoffs rarely published).

| Student holds | Azerbaijan | Turkey | Germany | USA |
|---|---|---|---|---|
| **DIM** | native cutoff | protocol universities | — | — |
| **Attestat GPA** | — | private universities | → Abiturnote (Bavarian formula) | GPA |
| **SAT** | — | international quota | — | native |

Conversion is **arithmetic** (Bavarian formula, never learned); cutoff prediction is
**ML**. Intake asks only what the student has, all optional; a route they hold nothing
for is absent, never a penalty. Routes without published cutoffs are shown labelled
*"requirements known, competitiveness unknown"*.

**Consequence:** no product route uses **YKS**. Those 115,482 rows are training data and
a selectivity signal only — never "the score you need".

### Blocking within days
- **F1** — **still unnamed, and now the single hardest blocker.** sec.az robots.txt permits crawling, but its terms-of-service page 404s and must be found. The collector issues one request today; the ~500-request `/kod/` enrichment refuses to run without `--i-have-f1-signoff`.
- **A4** — who verifies the DIM rows against the Abituriyent journal, and resolves the 163 unlabelled variants.
- **A1** — Germany source, only if the 5 Sep go/no-go passes.

### Safe to default
- **A5** (US granularity), **D1–D3** (web, accounts, languages), **E1–E3** (retrain cadence, artifacts, drop `admitted_profiles`) — recommendations in `open-questions.md` stand unless overridden.
- **A2, A3** (Poland, China) — out of locked scope.

---

## 7. Known gaps and defects

**The recurring defect pattern:** `except Exception` → fabricate plausible data →
continue silently. It produced the auth bypass, and it still makes `agent/tools.py`
invent GPA 3.8 / IELTS 7.5 from a failed transcript parse and tell the student their
profile was updated. Forbidden by ADR-0004. Grep for it before trusting any module.

**Fixed 30 August** — see §7a below for what was removed and what remains.

| Gap | Impact |
|---|---|
| `applications.py`, `admin.py`, `export.py` fall back to `DEMO_*` records | Endpoints return invented rows indistinguishable from real ones |
| `prediction.py` still pre-pivot | Must become batch precompute per ADR-0004 |
| `engine.py` carries false attribution strings | Claims reasoning it does not perform |
| Missing `student_applications` migration | Table exists in code, not in Alembic |
| Scholarship filter uses `or_` where `and_` is meant | Wrong scholarship matches |
| `parse_scholarship_amount` substring-matches "full"/"free" | Misreads amounts |
| CI missing `aiosqlite` | Test job cannot run |
| `render.yaml` sync-vs-async DB URL mismatch | Deploy-time failure |
| `scikit-learn` unpinned | `InconsistentVersionWarning`; artifacts not reproducible |
| USA CSV has no `cutoff_value` column | Blocks a shared training path with Turkey |
| `lower_is_better` is one flag for two opposite polarities | Rank vs score confusion |

### 7a. Fabrication paths removed — 30 August

Five sites were deleted. All five shared one shape: catch everything, substitute invented
data, continue, and report success.

| Site | What it invented | Now |
|---|---|---|
| `services/embeddings.py` | A sha256-derived sine wave whenever the API key was missing or any call failed. Two near-identical strings hashed to unrelated vectors, so every similarity search returned arbitrary documents and nothing raised | No fallback exists. Raises `EmbeddingUnavailableError`; `/chat/ask` returns **503**, not an ungrounded answer |
| `scripts/collect_germany.py` | GPA, IELTS, tuition and deadlines for TU Munich, Heidelberg and RWTH Aachen. Its three target URLs were invented, so every fetch 404'd and **every run returned mock data**. Also hardcoded `blocked_account_eur = 11208.0` | **Deleted.** Germany will be collected from hochschulstart.de and official university pages |
| `data_pipeline/jobs.py` (Germany job) | Marked those mock records `"verified"` above 85% LLM confidence | **Deleted** with the collector |
| `data_pipeline/jobs.py` (generic job) | `"Sample University Program Catalog… GPA 3.2, IELTS 6.5, $15,000 USD"` on any fetch failure | A URL that cannot be fetched now yields `status: "failed"` and no data. Provenance is always `claude-extracted`; LLM confidence never promotes a record to verified |
| `api/v1/chat.py` + `agent/tools.py` | **The student's own GPA 3.8 / IELTS 7.5** when a transcript could not be parsed — then reported "successfully updated" | Unreadable upload returns **422**. A document yielding no metrics updates nothing and says so |

Three tests were removed with them. Each asserted `status == "success"` or a
correctly-shaped vector, so each stayed green *because* of the fabrication — the suite
was confirming the mock, not the source.

### 7b. Authentication bypass fixed — 30 August

`auth.py` login and register each ended in `except Exception:` → `create_access_token(subject=101)`.
**Any** database error — an outage, a timeout, anything that could provoke one — returned a
valid token for student 101 with no credential check performed. `deps.py` completed the
loop: a correctly signed token whose student row did not exist returned a synthetic
`Student(gpa=3.7, budget="20000.0")` instead of failing, so a deleted account still
authenticated and the invented profile then fed matching.

The synthetic student's email and GPA were copied verbatim from `test_auth.py`, which ran
against no database at all. Every request in that test fell into the fallback, so the flow
it claimed to assert was never executed — **the mock was written to satisfy the test, and
the test then certified the bypass.**

Now: a database error returns **503** and no token; a valid token for a missing student
returns **401**; `/auth/me` returns `null` for unset fields rather than substituting
gpa 3.5 / budget 15000. `test_auth.py` runs against a real in-memory SQLite database
(`aiosqlite`, added to requirements — this also closes the CI gap) and covers wrong
password, unknown email, missing student, and database failure.

Suite: **48 passing**, up from 40 defined before this work.

---

## 8. Next steps, in order

**Done 29 August:** G1–G4 closed and ADR-0006 accepted · Azerbaijan DIM collected
(2,576 rows) · `train_cutoff_models.py` written and running on all three countries ·
fabricating `collect_azerbaijan.py` and its job removed · `.gitignore` `data/` rules
restored · sklearn pinned to 1.7.2.

1. **Name the F1 owner.** Now the single hardest blocker — it gates `/kod/` enrichment, which is what resolves the 163 unlabelled variants and adds quota (the strongest feature we have in Turkey).
2. **Write the EDA / comparison notebook** importing `train_cutoff_models.py`, so the report and production cannot drift.
3. **Implement the qualification → route matrix** and the Bavarian-formula conversion as deterministic arithmetic.
4. **Wire the selectivity index** (within-country percentile, Reach / Match / Safety) into the match response.
5. **Rewrite `prediction.py`** as batch precompute; strip false attribution from `engine.py`; delete `train_prediction_models.py` and its stale sklearn 1.9.0 artifacts.
6. **Germany collection** from hochschulstart.de and official university pages. The fabricating `collect_germany.py` was deleted on 30 Aug (§7a), so there is nothing to fix first.
7. Clear the rest of the §7 defect list.

---

## 9. Product spec — decided 30 August

**Authoritative document: [ADR-0007](adr/0007-three-number-model-and-honesty-tiers.md).**
This section is the index; the ADR carries the reasoning and the costs.

Seventeen decisions were taken in a grilling session on 29–30 August, closing the reframe
this section previously held open.

| # | Decision | ADR-0007 |
|---|---|---|
| 1 | **Coursework first.** 15 Sep graded deliverable; real users after | Context |
| 2 | **Six countries**, requirements extracted by Claude at *university* level | §4, §11 |
| 3 | **Three provenance states**; unverified requirements filter but never silently | §5 |
| 4 | **Five countries carry a second number**; the UK is eligibility-only and says so | §3 |
| 5 | **Bands headline, percentage gated** on post-recalibration error ≤ ~2pt | §8 |
| 6 | **Field via offline LLM labelling** of ~1,200 unique names, served by indexed SQL | §9 |
| 7 | **Profile-first, one step.** Destination ranks, never excludes | §2 |
| 8 | **CatBoost ships** for point estimates and the quantile ladder | §8 |
| 9 | **~90 universities**: ~55 destination + ~35 aspiration | §4 |
| 10 | **New ADR-0007 + ADR-0004 amendment.** Nothing superseded, nothing reversed | header |
| 11 | **Mode B in scope**, full roadmap, no study plan | §2 |
| 12 | **Contract by claim type** — numeric ML-only, qualitative cite-or-drop | §6 |
| 13 | **Scholarships first-class**, ~15 funded programmes; closes Hungary and Italy | §10 |
| 14 | **Cut order: Poland → UK → gated percentage** | §12 |
| 15 | **Fabrication paths deleted before building on them** | §7a |
| 16 | **Cold-start calibration measured separately**, then decided from evidence | §8 |
| 17 | **Extraction: auto-discover, human-review, script the rest** | §11 |

### 9.1 The shape, in brief

**Two modes.** *Discovery* — one profile step (scores, GPA, budget, destination, field),
results refining live. *Mode B* — name a university, get a gap statement, requirement
checklist, process checklist, and alternatives that close the gap.

**Three blocks, grouped by what we can tell you**, not by geography:

| Block | Countries | Second number |
|---|---|---|
| Your chances | DE, PL | genuine success rate — admission is mechanical |
| How hard it is | TR | selectivity only |
| Requirements only | US, UK, all scholarships | none |

**AZ was removed from that first row on 30 Aug** (ADR-0007 §3, dated correction). AUSA
helps an Azerbaijani student find a university *abroad*; the 1,028 programmes at 42
Azerbaijani universities are the domestic market. The DİM corpus keeps three jobs — the
scale the student's score arrives on, the training corpus that shows the method works on
real published data, and the domestic baseline — none of which need it shown as a
recommendation. The cost is real and is not hidden: **the "Your chances" block now rests
on two countries for which we have collected zero cutoff rows.** German collection is
therefore the top data priority, and Germany is no longer cuttable (ADR-0007 §12).

**One model, one stored number.** Batch precompute writes `predicted_cutoff`, `p10..p90`,
band thresholds and `model_run_id`; both modes read that row and nothing is recomputed at
request time.

**No number reaches a student unless a model produced it** — enforced by a numeral check
against the payload, not by convention.

**AUSA takes no commission**, which is why destination ranks rather than excludes: a filter
that hides options is the steering behaviour the agency reference criticises, automated.

### 9.2 Still open, deliberately

Two items have code but no decided role. Left for a later grilling rather than settled by
default — see ADR-0007, *"Open, deliberately not decided here"*:

1. **Motivation letter drafting.** `agent/tools.py` ships a hardcoded generic template.
   The agency reference lists recycled motivation letters as an industry red flag that
   admissions boards detect and reject, and advises students to write their own.
   Recommendation, not decision: shift from **generation** to **critique** — the student
   writes, AUSA reviews against that programme's extracted criteria.
2. **Stateful application tracking.** `student_applications` is a model with no migration;
   stages, missing documents and dossier export exist as code. Whether tracking a student's
   live applications is in scope for 15 Sep was never decided.

### 9.3 Build order

**Claude:** fabrication deletions ✅ → ADR-0007 ✅ → `program_cutoff_history` + loader →
DE/PL cutoff collection → ~90 university extraction → field labelling → ~15 scholarships →
CatBoost + MultiQuantile + recalibration → notebook.

**Team:** `student_qualifications` → route join + filtered-out panel → batch precompute →
three UI surfaces → `student_applications` migration.

Task-level plans live in [`superpowers/plans/`](superpowers/plans/).

**Checkpoint 6 September.** If the tables and one UI surface are not working by then, apply
the cut order (§12) rather than discovering the problem on the 13th.


## 10. Repository state

- `main` @ `9a85541` — security fixes merged (PR #4)
- `docs/admission-routes` — ADR-0006 draft, **PR #5 open**
- Reference branches: `feature/initial-setup`, `feature/clean-start`, `feature/frontend-ui`
