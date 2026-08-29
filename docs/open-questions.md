# AUSA — Open Questions

**Deadline: 15 September 2026.** Updated 29 August — **17 days left**.

**13 of 22 answered.** Fill in the `**Answer:**` line under each remaining question.
Every question carries a recommendation — accept it, override it, or write something
better. Decisions already settled are recorded in [`adr/`](adr/) and are not repeated here.
Current status of the whole project is in [`PROJECT-STATE.md`](PROJECT-STATE.md).

Legend: 🔴 blocks implementation · 🟡 blocks a specific country or feature · 🟢 can be deferred

## Still required — read this first

Answered so far: **A4**, **B1**, **B2**, **B3**, **B4**, **B5**, **C1**, **C2**, **C3**,
**C4**, **F1** (process, owner still unnamed), and the scope/positioning decisions from
the 28 August grilling session.

Given 17 days, these are the ones that actually block work now:

| Answer today | Why it blocks |
|---|---|
| **G1, G2, G3, G4** — admission routes | Blocks ADR-0006 acceptance and the schema key. Determines whether the Turkish data we already have serves the product or only the model |
| **F1 owner** — the *name* is still missing | The Q4 decision to scrape sec.az / uniaz.info makes this a hard prerequisite, not background work. No DIM collection code runs until it is named |

| Answer within 3 days | Why |
|---|---|
| **A1** — Germany aggregator or direct? | Only if the **5 September** Germany go/no-go passes. Otherwise moot |

| Can wait | |
|---|---|
| **A2, A3** (Poland, China) | Out of locked scope |
| **A5** (US granularity) | Recommendation is "accept and label it" — only needs a no |
| **D1, D2, D3** (web/mobile, accounts, languages) | Frontend can start on the recommendations |
| **E1, E2, E3** (retraining, artifacts, `admitted_profiles`) | Recommendations are safe defaults; confirm when convenient |

**Not a question, but the biggest risk:** Azerbaijan DIM data does not exist yet and is
on the critical path. If it has not landed by **5 September**, Germany is dropped and
the ML ships on Turkey + USA only.

---

## A. Data acquisition

The ML model predicts each programme's **next-intake admission cutoff**, trained on
published cutoff history. Each country publishes that history differently, and three
of the seven have no confirmed source yet.

Confirmed so far:

| Country | Source | Unit | Confidence |
|---|---|---|---|
| Turkey | YÖK Atlas via `izcir/turkish-university-admissions-dataset` — 128,352 records, 2019–2024, MIT | YKS rank / score | High — clean and licensed |
| USA | College Scorecard API — 6,000+ institutions, admit rate + SAT/ACT 25th–75th pct, free, no registration | SAT/ACT percentile | High — official federal open data |
| UK | UCAS entry grades — accepted-student grade profiles, 3 cycles (2023–2025), plus offer rates | UCAS Tariff points | High — published per course |
| Germany | NC-Werte.info (29,000+ thresholds, 1,700+ programmes), Studis Online (through 2026/27) | Abiturnote (**lower is better**) | Medium — see A1 |
| Azerbaijan | DIM published cutoffs | 0–700 score | Medium — needs collection |
| Poland | — | — | **None** |
| China | — | — | **None** |

### A1 🔴 Germany — aggregator or direct?

The German NC data exists, but only two routes reach it. `data-sourcing.md` warns
specifically that *"aggregators typically have stricter terms of use than individual
universities, precisely because the data is their product"* — and NC-Werte.info is an
ad-supported commercial site whose database **is** the product.

- **Aggregator** (NC-Werte.info / Studis Online) — 29,000 thresholds in one place, fast, but ToS risk and the reputational risk `data-sourcing.md` flags about scraping institutions you later want to partner with
- **Direct from universities** — auswahlgrenzen.de links to official university NC pages; slower, per-institution, but clean
- **Partnership / licence** — approach an aggregator to licence the data

**Recommendation:** direct from universities for the MVP's curated set. At 30–50
programmes this is hours of work, not weeks, and it keeps Germany — your top market —
free of legal ambiguity. Revisit licensing when the catalogue outgrows manual collection.

**Answer:**

### A2 🟡 Poland — where does cutoff data come from?

No source identified. Polish public universities typically admit on a recruitment
points formula with published thresholds per programme per year, but I have not
confirmed a central database.

**Recommendation:** timebox to half a day. Check IRK/eRekrutacja recruitment portals
and the individual universities you plan to curate. If nothing central exists, Poland
ships as `admission_type = open` with deterministic ranking only, and the ML model
skips it — that is an acceptable outcome, not a failure.

**Answer:**

### A3 🟡 China — where does cutoff data come from?

No source identified. Admission for international students is largely documents plus
institutional discretion, often routed through CSC scholarship processes, which may
mean there is no cutoff to predict at all.

**Recommendation:** classify China as `admission_type = competitive` and defer it.
It is 7th on your priority list and has the weakest data story.

**Answer:**

### A4 🔴 Azerbaijan — who collects the DIM data, and in what form?

Your home market. DIM publishes cutoff scores, but nobody has scoped the collection —
how many years back, which programmes, manual or scripted.

**Recommendation:** collect the last 5 years for every programme you curate, by hand,
into CSV. This is the one market where you have language access and local knowledge
that no competitor has, so it is worth doing carefully rather than quickly.

**Answer (28 Aug, grilling Q3/Q4/Q5):** Azerbaijan DIM is **committed scope**, not a
stretch goal. The official source (Abiturient journal) is paywalled, so the route is to
**scrape sec.az / uniaz.info** — sec.az carries 1,030 specialties × 3 years. Collection
proceeds under the Q5 protocol: named owner, robots.txt and ToS checked and recorded,
rate-limited, with a permission email sent **in parallel** rather than blocking on a
reply.

> Noted once and not re-argued: the aggregator route was chosen over buying the official
> journal. The consequence is that **F1 stops being a background task and becomes a hard
> prerequisite** — no collection code runs before the sign-off owner is named.

**Still open:** *who* on the team does it, and starting when.

### A5 🟡 USA/UK granularity mismatch — accept it or work around it?

College Scorecard is **institution-level and undergraduate-focused**; UCAS is
per-course but UK-domiciled. Your product ranks *programmes* for international
students. Test-optional policies have also degraded SAT coverage since 2020.

**Recommendation:** accept it, and label it. A US result explains "institution-level
admission data — programme requirements may differ", which is honest and still useful.
Do not synthesise programme-level precision you do not have.

**Answer:**

---

## B. Scope

### B1 🔴 How many programmes, in which countries, for the MVP?

`architecture-decisions.md` recommends 30–50 programmes across 2–3 countries. You have
now named **seven**. Those two positions are not compatible — seven countries at 30–50
programmes total is ~5 programmes each, which is too thin to rank meaningfully, and at
30–50 *per country* it is 350 programmes of hand-curation.

**Recommendation:** MVP on **Germany, Turkey, Azerbaijan** — your top three, and the
three with the strongest cutoff data. 40–50 programmes each. UK and USA next, since
their data is already clean and free. Poland and China last.

**Answer: Yes but UK and China last USA and Poland before them**

**Refined 28 Aug (grilling Q8) — scope is now locked.** ML ships on **Turkey + USA +
Azerbaijan**. **Germany is added only if DIM data lands early**, decided at a **go/no-go
on 5 September**; if it is added it gets **no ML** — hand-curated programmes with
deterministic ranking. Poland and China are out of scope for this delivery.

### B2 🔴 Which degree levels?

The schema supports bachelor / master / PhD. Each level has different requirements,
different cutoff mechanisms and separate curation cost — supporting all three roughly
triples the work and splits the training data three ways.

**Recommendation:** ~~master's only~~ — **withdrawn, it was wrong.** All three collected
datasets are undergraduate and contain **zero** master's rows. (The Turkish
`is_undergraduate=False` flag marks *Meslek Yüksekokulu* two-year vocational programmes,
not master's.) Recommending master's would have meant discarding every row of data we
have.

**Answer (28 Aug, grilling Q7): bachelor's only.** It is what the data supports.

### B3 🔴 Coverage check — what fraction of the catalogue is cutoff-based?

Flagged as the top risk in the design review. If your curated set skews toward
tuition-free **open-admission** German programmes — exactly what Azerbaijani students
gravitate to — the ML model touches only a minority of the catalogue, and the course
requirement is met on paper while the product stays mostly deterministic.

**Recommendation:** during week one of curation, tag every programme with
`admission_type` and count. If cutoff-based programmes are under ~40% of the catalogue,
deliberately re-weight curation toward NC programmes and the Turkish/Azerbaijani
markets before writing any model code.

**Answer: with your recommendation**

### B4 🟡 Who on the team does what?

Four people: Irada Nuraliyeva, Əli İskəndərli, Fariz Əkbərzadə, Turan Əlizadə. The work
splits cleanly into four tracks — data collection/curation, ML pipeline, backend/API,
frontend.

**Recommendation:** data curation is the critical path and the biggest risk, so it
should have two people, not one, at least for the first two weeks.

**Answer (28 Aug, grilling Q6):** **Fariz builds the ML pipeline and the backend
integration.** The team owns **data collection/curation, frontend, and the report.**
Curation keeps two people per the recommendation.

### B5 🔴 What is the deadline?

Unknown, and it determines everything above.

**Answer: 15 september. and today 23 Augest**

---

## C. Course requirements

### C1 🔴 Does "use ML instead of hardcoded" permit keeping deterministic hard filters?

**The single most important question in this document.** The agreed design keeps
eligibility (budget, language minimums, degree level, deadline) as deterministic SQL,
and applies ML only to ranking. If your course requires that *all* rule-based logic be
replaced, this design does not satisfy it.

The argument for keeping them: a student told they qualify for something they don't
will not come back — and for Germany and Azerbaijan, deterministic rules are not a
shortcut, they are an accurate model of how admission actually works.

**Recommendation:** confirm with your instructor **before building**, not at submission.
If they insist on full replacement, say so and we will reopen the design.

**Answer: If there is a ML model that is enough**

### C2 🟡 Is a specific algorithm or library mandated?

Tree-based is specified. Whether that means a single decision tree, Random Forest, or
gradient boosting (XGBoost / LightGBM) is unclear, and it affects the explainability
story.

**Recommendation:** train Decision Tree, Random Forest and gradient boosting, and report
all three against the persistence baseline. Model comparison is usually graded well and
costs almost nothing once the pipeline exists.

**Answer (28 Aug): accepted.** Decision Tree, Random Forest and HistGradientBoosting,
all three on both evaluation splits, all three against their honest baselines.

### C3 🟡 What are the deliverables — notebook, report, running app, or all three?

Determines whether the training code lives in `notebooks/` for presentation or in
`backend/` as a production job.

**Recommendation:** both, deliberately — an EDA/training notebook in `notebooks/` for the
report, and a thin production training script that imports the same functions, so the
notebook and the app cannot drift apart.

**Answer (28 Aug): accepted.** `backend/scripts/train_cutoff_models.py` plus an
EDA/comparison notebook importing the same functions, plus a committed metrics JSON per
run so any `predicted_cutoff` in the database traces to the exact model that made it.

### C4 🟡 Is "the baseline won" an acceptable result?

Cutoffs are strongly autocorrelated year-to-year, so *"next year's cutoff = last year's
cutoff"* is a strong predictor. The trees may not beat it. Scientifically that is a
legitimate and publishable finding; as coursework it may be graded as failure.

**Recommendation:** ask now. If it would be graded as failure, we need a second ML
component with a softer baseline planned in from the start rather than improvised in
week five.

**Answer (28 Aug, grilling Q1):** The question is now settled empirically, not
hypothetically — see [`PROJECT-STATE.md`](PROJECT-STATE.md) §3.

- **Forecasting:** persistence MAE **13.77**, best model **15.77** — the baseline wins.
- **Cold start:** department-mean MAE **38.96**, HistGradientBoosting **17.96** — the
  model wins by **53.9%**.

**Decision: train and report both. Ship the cold-start model.** Cold start is a real
product need (every hand-curated programme arrives with no history, so persistence is
structurally unavailable) *and* it is where trees genuinely win. The forecasting result
ships as a rigorous negative finding, with the failed remedies — delta target, training
window restriction, shrinkage — as evidence of a real investigation.

---

## D. Product

Carried over from `architecture-decisions.md`, still unanswered.

### D1 🟡 Web or mobile first?

**Recommendation:** web. The reference branch already has a Next.js frontend to
cannibalise, and students research universities on laptops.

**Answer:**

### D2 🟡 Do students need accounts from day one?

Determines whether saved programmes, comparison and deadline tracking ship in Phase 1.

**Recommendation:** no accounts in Phase 1. Prove the matching first — accounts add auth,
sessions, GDPR obligations and password reset flows without improving the core result.

**Answer:**

### D3 🟢 Which language(s) does the interface ship in?

Azerbaijani, English, Russian, or several. Not raised anywhere in the existing docs, but
it affects every UI string and both the explanation templates and the RAG layer later.

**Recommendation:** Azerbaijani and English. Your users are Azerbaijani; your programme
data is in English.

**Answer:**

---

## E. Technical

### E1 🟡 How often do we retrain, and what triggers it?

Cutoffs update roughly once per intake cycle, so this is annual or semi-annual — not
continuous.

**Recommendation:** manual retrain per intake cycle, triggered by a maintainer, with the
model artifact and its metrics committed. No scheduler, no MLflow, no orchestration at
this scale.

**Answer:**

### E2 🟡 Where do model artifacts and their metrics live?

**Recommendation:** joblib artifacts in object storage or a repo directory, with a JSON
metrics file per training run committed to git so `predicted_cutoff` values in the
database can always be traced to the exact model that produced them.

**Answer:**

### E3 🟢 Do we keep the `admitted_profiles` table?

It was designed for the admission-probability model we are no longer building, and it
cannot produce a training label as written — it stores admitted students only, with no
rejections and no outcome flag.

**Recommendation:** drop it. Replace with `program_cutoff_history`, which is what the
agreed design actually trains on.

**Answer:**

---

## F. Legal

### F1 🔴 Who signs off on the scraping position, and by when?

`data-sourcing.md` §6 is unambiguous: resolve this **early**, it is cheap now and
expensive later. It directly gates A1 (German aggregators) and any Azerbaijani or
Polish collection.

Of the confirmed sources, College Scorecard is US federal open data and the Turkish
dataset is MIT-licensed — both are unambiguously fine. UCAS, DIM and the German
aggregators all need checking.

**Recommendation:** one named person, terms-of-service and robots.txt checked per source,
recorded in a table in this repo, done **before** any collection code is written.

**Answer (28 Aug, grilling Q5) — process agreed, owner still missing.** The protocol is
"ask in parallel, scrape politely": robots.txt and ToS checked and recorded per source,
rate-limited requests, identifying user-agent, and a permission email sent at the same
time rather than blocking on a reply.

**Escalated to 🔴 blocking.** The Q4 decision to scrape sec.az / uniaz.info means this is
no longer a background task — **no DIM collection code runs until a person is named
here.** Fill in a name.

---

## G. Admission routes

Programs accept **several alternative entrance qualifications**, not one. A Turkish
university may admit international applicants on **SAT ≥ 1200 *or* YÖS ≥ 60**. ADR-0001
models a single cutoff per program and cannot express that.

Full analysis in [`adr/0006-admission-routes.md`](adr/0006-admission-routes.md)
(status: **Proposed** — these three questions block acceptance).

The uncomfortable part, stated up front: an Azerbaijani student applying to Turkey
never sits YKS — they go through **YÖS** or the **international quota**, and many
Turkish universities accept **SAT**. So the 115,482 rows of YKS cutoffs we collected
describe **a route our users will never take**. Still valid as ML training data and as
a selectivity signal; not valid as "the score you need".

Note that language tests (IELTS / TOEFL / Duolingo / TestDaF) are **not** part of this
question. They are pass/fail thresholds, already correctly handled as deterministic
Layer 1 filters by ADR-0001. Only *entrance qualifications* are competitive.

### G1 🔴 Which admission routes does the MVP support?

Each supported route means separate cutoff history to collect, curate and
human-verify, per program.

Candidates: **DIM** (Azerbaijan), **YÖS** (Turkey, international), **SAT** (accepted by
many Turkish and all US institutions), **converted GPA / Abiturnote** (Germany),
**UCAS tariff** (UK).

**Recommendation:** ~~SAT and YÖS first~~ — **partly superseded by research on 29 Aug.**
DIM has signed **recognition protocols with Turkish universities**, so an Azerbaijani
student can apply to some of them on their DIM score directly, with no YÖS and no SAT.
DIM is therefore not only the home-market route — it is a Turkey route too, which makes
it far better value per unit of collection work than the recommendation assumed.

**Answer (29 Aug): three routes, YÖS dropped.**

| Route | Destinations | Cutoff source | ML or deterministic |
|---|---|---|---|
| **DIM** (0–700) | Azerbaijan + Turkey (protocol universities) | sec.az, 2023–2025 | **ML** once collected |
| **SAT** | USA + Turkish international quota | College Scorecard (US); TR quota largely unpublished | **ML** for US; deterministic + labelled for TR |
| **Attestat GPA** | Germany + Turkish private universities | n/a — conversion, not a cutoff | **Deterministic** (Bavarian formula) |

**YÖS is out of scope.** Its cutoffs are rarely published per programme, so the
collection cost is high and the resulting data thin.

**Consequence, stated plainly:** no product route uses **YKS**. The 115,482 YKS rows
serve as ML training data and as a programme-selectivity signal only — never as "the
score you need". See G4.

### G2 🔴 Does intake capture every qualification up front, or per country on demand?

`architecture-decisions.md` §5 deliberately keeps Phase 1 intake minimal. Asking a
student for DIM *and* SAT *and* YÖS *and* IELTS up front works against that, and most
students hold only one or two.

**Recommendation:** ask for what they have, not for everything — a short "which of these
do you have?" step, with the rest optional. Routes they hold no qualification for are
simply not scored, and are never counted against them.

**Answer (29 Aug): accepted.** A single "which of these do you have?" step covering
DIM / attestat GPA / SAT, plus language certificates. Everything optional. A route the
student holds no qualification for is not scored and **never counted against them** —
it must not appear as a low score or a penalty, only as absent.

### G3 🟡 If a route has no cutoff data, do we show it or hide it?

Likely common for YÖS and SAT international quotas, where cutoffs are often unpublished.

**Recommendation:** **show it, labelled honestly** — "requirements known, competitiveness
unknown" — under the ADR-0001 `open` / `competitive` taxonomy. Hiding a viable route
because we lack data is worse for the student than admitting we don't know. Never invent
a cutoff to fill the gap.

**Answer (29 Aug): accepted.** Shown as `admission_type = competitive` with
"requirements known, competitiveness unknown". This applies immediately to the **Turkish
international-quota SAT route**, whose cutoffs are mostly unpublished. Never invent a
cutoff to fill the gap — that is the ADR-0004 no-fabrication rule applied to the UI.

### G4 🟡 Do we accept that the ML trains on routes the product may not serve?

The likely end state: the model is trained on YKS and College Scorecard (real, recent,
defensible, gradeable) while the product ranks SAT/YÖS routes deterministically because
their cutoffs aren't published.

**Recommendation:** accept it, and state it explicitly in the course report as a data
limitation. It is a legitimate position — but it must be a recorded decision, not
something discovered while writing up.

**Answer (29 Aug): accepted, and it follows directly from G1.** With YÖS dropped, **no
product route uses YKS.** The split is now explicit:

- **Trained on:** YKS (Turkey, 115,482 rows) and College Scorecard (USA) — real, recent,
  licensed, gradeable. DIM joins this list once collected.
- **Served to students:** DIM, SAT and attestat-GPA routes.
- **Overlap:** SAT (US) and DIM are both trained *and* served. YKS is trained only.

YKS earns its place as a **selectivity signal** — it tells us how competitive a Turkish
programme is relative to its peers, which is exactly what the Q2 selectivity index needs,
and that transfers across routes even though the score does not. This is a stated
decision, to be repeated verbatim in the report's limitations section.

---

## Answered — for the record

These were open in `architecture-decisions.md` and are now settled:

- **Target countries** — Germany, Poland, Turkey, Azerbaijan, USA, UK, China (priority order)
- **Scoring formula and weights** — superseded. The hand-set 0.5 / 0.3 / 0.2 weights are
  replaced by a learned cutoff prediction; the match score becomes headroom above the
  predicted cutoff
- **Primary data source** — published admission cutoff history per country, not scraped
  programme pages

Added 28 August from the grilling session — decisions that were not previously questions:

- **How competitiveness is shown to the student** (grilling Q2) — a **selectivity
  index**: the programme's percentile within its country, presented as **Reach / Match /
  Safety** bands. Absolute probabilities are never displayed, per ADR-0001. Headroom
  above the predicted cutoff drives the band; the raw number is not the headline.
- **Product positioning** (grilling Q9) — AUSA does **application preparation and route
  recommendation only**. It makes no submission claims, does not submit applications,
  and does not promise an admission outcome. This bounds both the legal surface and what
  the UI is allowed to say.
