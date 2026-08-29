# AUSA — Project State

**Written 29 August 2026. Deadline 15 September 2026 — 17 days left.**

This is the single clean starting point. It records what is decided, what is built, what
is measured, what is still open, and what happens next. The ADRs hold the *reasoning*;
this file holds the *status*.

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

| Gap | Impact |
|---|---|
| `agent/tools.py` fabricates GPA/IELTS on parse failure | Fake numbers drive match scores and an exported PDF |
| **`collect_germany.py` has the identical fabrication pattern** — bare `except`, then mock HTML for Heidelberg / RWTH / TU Munich | Same defect as the Azerbaijan collector removed on 29 Aug. Not fixed, because Germany is gated on the 5 Sep go/no-go — **fix or delete it before any German collection runs** |
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
6. **5 September — Germany go/no-go.** If yes, `collect_germany.py` must be fixed or deleted first (§7).
7. Clear the rest of the §7 defect list.

---

## 9. Repository state

- `main` @ `9a85541` — security fixes merged (PR #4)
- `docs/admission-routes` — ADR-0006 draft, **PR #5 open**
- Reference branches: `feature/initial-setup`, `feature/clean-start`, `feature/frontend-ui`
