# AUSA — Project State

**Written 29 August 2026. Deadline 15 September 2026 — 17 days left.**

This is the single clean starting point. It records what is decided, what is built, what
is measured, what is still open, and what happens next. The ADRs hold the *reasoning*;
this file holds the *status*.

> **Read §9 first.** A design discussion late on 29 August reframed the product
> (success rate vs matching as separate numbers) and uncovered the real bottleneck: the
> catalogue has **7 programmes**, not the modelling. §9 is **open and undecided** —
> it goes to a grilling session before anything in it is built. Sections 1–8 describe
> what is already committed and working.

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

## 9. Product reframe — 29 August (OPEN, not yet decided)

A design discussion on 29 Aug reframed the product. **Nothing here is committed.** It is
recorded so the next session can resume, and the open items go to a grilling session.

### 9.1 The reframe

Success rate and matching are **orthogonal** and were being conflated. A student can have
a 100% success rate at 100 programmes — that does not help them choose. Split into three
numbers with three different mechanisms:

| # | Number | Mechanism | Honest about |
|---|---|---|---|
| 1. Eligibility | Do you meet the stated requirements? | **Deterministic**, from curated requirements | Binary, never guessed |
| 2. Success rate / selectivity | Can you get in? How hard is it? | **ML** — cutoff regression | See 9.2 — differs per country |
| 3. Fit | Does it match your goals? | **User-controlled** filters + sort | Your preference, not our judgment |

**On the fit score:** it must not become a system-weighted formula. There are no
preference labels to learn from, and inventing weights re-creates exactly the hardcoded
scoring the course requires removing. The user sets the weights. The ML requirement rests
entirely on number 2.

**Default ordering: hardest-you-can-still-get first.** A student sorted safest-first sees
places they are overqualified for. Sorted by most competitive where they still have a real
chance, they see the actual decision.

### 9.2 A genuine success rate is only possible where admission is mechanical

`P(admit)` is unlearnable — no labels. But **`P(next year's cutoff ≤ your score)` is
learnable** from cutoff variance, and where clearing the cutoff *is* admission, that is
not a proxy for the success rate — it is the success rate.

| Destination | Route our users take | Cutoff data | Real success rate? |
|---|---|---|---|
| **Azerbaijan** | DIM | ✅ collected, partly verified | ✅ **Yes — genuine** |
| **Germany** | attestat → Abiturnote | ❌ not collected | ✅ **Yes if collected** — NC is a true threshold |
| **Turkey** | DIM protocol / SAT / attestat | ❌ those routes unpublished | ❌ selectivity only |
| **USA** | SAT | ✅ collected, but holistic admission | ❌ selectivity only |

**Consequence to face:** demoting Azerbaijan removes the only market where the success
rate currently works. Germany is therefore the highest-value collection target — not just
the largest market.

### 9.3 Experiments run 29 Aug (scratchpad, not yet in the repo)

**CatBoost beats HistGradientBoosting by 25%** on Turkish cold start:

```
baseline department-mean                     38.96
HistGradientBoosting (label-encoded cats)    18.93   +51.4%
CatBoost (native categoricals)               14.18   +63.6%
```

Cause: `.cat.codes` tells the tree that university #47 sits between #46 and #48. It does
not. CatBoost's ordered target statistics handle high-cardinality categoricals properly.
**Recommendation: adopt CatBoost**, and keep all four algorithms in the comparison.

**Quantile regression for the success rate — works directionally, NOT shippable as a
percentage yet:**

```
nominal   empirical    error
   0.10       0.098   -0.002   excellent
   0.25       0.218   -0.032
   0.50       0.431   -0.069   meaningful miss
   0.75       0.678   -0.072
   0.90       0.838   -0.062
```

Two defects, one dangerous:

1. **Systematic over-optimism of 6–7 points.** Real cutoffs land *higher* than predicted
   more often than claimed. We would tell a student "you clear this 75% of the time" when
   the truth is 68% — telling students they are safer than they are, the exact failure
   ADR-0001 exists to prevent. Worst in the middle of the range, where most students sit.
2. **Quantile crossing** — independently fitted quantiles are not monotone (`p10=378.3`
   while `p25=375.1`), which breaks the interpolation the success rate depends on.

Both fixes are standard, not research: sort quantiles for monotonicity, then fit a
nominal→empirical recalibration on the validation year and invert it at serving time.
Estimated half a day. **Until the calibration table is flat, ship Reach/Match/Safe bands
only** — a 6-point shift rarely crosses a band boundary; it does corrupt a percentage.

### 9.4 The catalogue gap — the real bottleneck

Verified in the code on 29 Aug:

| | Reality |
|---|---|
| `programs` table | **7 hardcoded seed rows** — the entire product catalogue |
| `program_cutoff_history` | **No such table.** 127k rows exist only as CSVs |
| `students` table | `gpa`, `ielts`, `toefl` only — **no DIM, SAT or YÖS** |
| `student_applications` | Model exists, **migration never written** |

**We have cutoffs without requirements, and requirements without cutoffs.** The 29,293
Turkish programmes have competitiveness but no `min_ielts`, tuition, deadline or
international-route data, so the hard filter has nothing to filter on. The 7 seed
programmes have requirements but no cutoff history. The two datasets do not join.

**The modelling is nearly done; the catalogue barely exists.** Requirements curation for
~150–200 programmes is the critical path, and it is team work.

**Proposed fix — a two-tier catalogue:**

| Tier | Source | Shows | Count today |
|---|---|---|---|
| **Curated** | verified requirements + cutoff history | eligibility ✓, success rate, band, tuition, deadline | 7 → needs 150–200 |
| **Catalogue** | cutoff history alone | selectivity only, labelled *"requirements not yet verified"* | ~30,000 |

The student sees everything, but the system never claims to have filtered on requirements
it does not hold.

### 9.5 Proposed intake flow

**Field-first, country-grouped, never country-gated.**

1. **Field / career goal** — the only thing asked up front
2. **Qualifications** — four optional fields, refining the list live
3. **Budget** — blank or 0 means scholarship-only
4. **Country** — a *facet on the results*, not a gate. Default: all countries. Plus an
   optional must-have / rule-out for students with a hard constraint
5. Hard filter on the curated tier → results, **grouped by country**
6. Within each group, ordered hardest-achievable first, banded Reach / Match / Safe

**Why country must not be asked first.** It assumes the answer to the question the
product exists to answer. A student who already knows they want Germany goes to DAAD;
AUSA's highest-value output is *"consider Poland — your DIM score goes further there."*
Gating on country destroys that and reduces the product to a filtered search box. There
is also a plain asymmetry: students reliably know roughly *what* they want to study, and
much less reliably *where*. **Country is an output, not an input.**

> **Correction to an earlier recommendation in this session.** Claude first proposed
> asking field **and country** together, arguing that the chosen countries determine
> which exams to ask for. That argument is weak at this scale: an Azerbaijani
> school-leaver plausibly holds only attestat, DIM, a language certificate and possibly
> SAT — four optional fields, with YÖS already dropped. There was never a wall of inputs
> to save the user from, so the benefit did not justify gating on country.

**Do not build a wizard.** Multi-step forms lose users at every step. One page, result
list always visible, refining as fields are filled. Before any input it can show the most
competitive or most popular programmes in the field, so the page is never empty.

**The catch that forces country grouping.** The number means different things per
country: Azerbaijan and (once collected) Germany give a genuine success rate, while
Turkey and the USA give selectivity only. Showing "82%" beside "top 6% competitive" in
one ranked list is misleading, and sorting them against each other is worse. Grouping by
country preserves discovery while giving each block a place to state honestly what its
number means — e.g. *"Turkey: we can tell you how hard this is, not whether you'd clear
it."*

This supersedes the G2 answer's generic "which of these do you have?" step.

### 9.6 Build order implied

1. `program_cutoff_history` table + CSV loader (ADR-0004 specifies it; never built)
2. `student_qualifications` — DIM, SAT, YÖS, attestat beside the language fields
3. Route join: student qualification → programme requirement (ADR-0006)
4. Field taxonomy: "robotics" → {Mechatronics, Control, Mech Eng, Computer Eng}, ×3 languages
5. **Requirements curation, 150–200 programmes — critical path, team work**
6. Batch precompute of selectivity onto programme rows
7. `student_applications` migration (cheap, pre-existing bug)

### 9.7 Germany — committed to Claude on 29 Aug

The user directed that Claude collect German data rather than the team.

**Source choice:** official university NC pages and **hochschulstart.de** (official central
allocation, publishes real NC values for restricted subjects), indexed via
auswahlgrenzen.de. **Not** nc-werte.info — that aggregator's database *is* its product,
which is the ToS risk `data-sourcing.md` warns about. Official sources sidestep F1 rather
than gambling on it.

**Undecided:** breadth (many programmes, NC only → catalogue tier) vs depth (40–50
programmes with NC + language + tuition + deadline → curated tier). Recommendation:
**depth**, because requirements are the bottleneck, not cutoffs.

### 9.8 Open questions for the grilling session

0. **Confirm field-first / country-grouped intake (§9.5)** — the one place an earlier recommendation in this session was reversed.
1. **Success rate as a percentage or bands only?** Evidence says bands until recalibration ships.
2. **Does Azerbaijan stay** as a local section, given it is the only working success-rate market?
3. **Germany breadth vs depth.**
4. **Who builds the field taxonomy?** Curation, on the critical path for matching.
5. **Is 150–200 curated programmes achievable** by 15 Sep, and if not, what is the minimum viable catalogue?
6. **Does ML-does-ranking-not-eligibility satisfy the course?** C1 says yes; worth confirming once.
7. **Adopt CatBoost** as the shipped model?
8. **Do ADR-0001 and ADR-0006 get amended** for the three-number model, or superseded by a new ADR-0007?

---

## 10. Repository state

- `main` @ `9a85541` — security fixes merged (PR #4)
- `docs/admission-routes` — ADR-0006 draft, **PR #5 open**
- Reference branches: `feature/initial-setup`, `feature/clean-start`, `feature/frontend-ui`
