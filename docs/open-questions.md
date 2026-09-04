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

**Superseded 4 September — the answer conflated two different products.**

"Bachelor's only" was correct about the **ML**, and was then wrongly applied to the
**route engine**, which needs no training data at all. The two are now separated:

| | Levels | Why |
|---|---|---|
| **ML (cutoff / selectivity)** | bachelor only, **Azerbaijan-internal only** | All three collected datasets are undergraduate. The model serves the domestic DİM question, not the abroad routes |
| **Route engine + DP + curation** | **bachelor AND master's** | Hand-written routes and curated requirement rows. No training data involved, so the constraint above never applied |

Two findings forced this. The Dövlət Proqramı funds **353 master's places against 125
bachelor** (Brief 01), so bachelor-only pointed the product at the smallest queue. And
`dp-master-2026.csv` — 2,907 rows, 223 universities, 33 countries — had been on disk
unused since collection. It is loaded now: a master's profile reaches **1,692 funded
programmes against the bachelor's 601**, and the USA funds **zero** DP bachelor places
against **289** at master's.

Consequence to act on: every one of the 15 curated `program_requirements` rows is
`level=bachelor`, so master's plans currently return universities with a named "we have
not collected this" explanation rather than a list. That is honest, and it is the next
curation gap.

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

## H. Funding

Spec §5.2 named ten funding instruments across three tiers and stated that **a funding
programme IS a route**, so scholarships run through the same eligibility engine as
programmes. Implementation-plan Step 8 budgeted 2 person-days for it. Until 4 Sep 2026 the
product modelled **one** of the ten — the Dövlət Proqramı.

**The reason was data-availability bias, and it is worth recording as such.** The DP was
the only funder publishing a downloadable catalogue (4,121 rows, one fetch); everything
else needs hand-curation. So the product optimised for what was machine-readable rather
than for what students need. The cost is visible in our own general research brief, whose
advice is that a school-leaver should prioritise **Türkiye Bursları or the CSC** over the
DP because the DP caps bachelor at 25% of its quota — meaning we had built the instrument
the research says undergraduates should skip.

### H1 ✅ Does the product model funders other than the DP?

**Answered (4 Sep 2026): yes — ten instruments, each carrying the gate that actually
decides it.** `domain/scholarship_definitions.py`, assessed by
`services/scholarship_eligibility.py`, returned on `/routes/assess` as `scholarships`.

The gates are the point, and several have nothing to do with academic merit:

| Instrument | Level | The gate that excludes |
|---|---|---|
| Dövlət Proqramı | b · m · PhD | DİM 400/550 + C1 + listed university (assessed separately) |
| SOCAR Xarici Təqaüd | master | **SOCAR group employment** — nothing academic opens it |
| Türkiye Bursları | bachelor · master | **under 21** at bachelor |
| CSC / Silk Road | bachelor · master | Chinese-taught at bachelor; CSCA + HSK 4 (on the route) |
| Chevening | master only | **2,800 documented hours** |
| Fulbright | master only | professional experience; 2-year home-residency after |
| DAAD | master only | per-grant; database is `Disallow:` in robots |
| NAWA Banach | master only | field of study — **our two sources contradict** |
| Erasmus Mundus | master only | per-consortium |
| GREAT | master only | per-university; a £10,000 **reduction**, not full funding |

**Seven of the ten are master's-only and exactly two reach bachelor.** That is spec §2.3's
finding rendered rather than described, and it is why the honest answer to a school-leaver
is short: apply to the two that exist, and treat affordability — not scholarships — as the
lever.

The DP stays out of this catalogue deliberately. It is assessed by
`services/dp_eligibility.py` against its own regulation, with a funded-programme catalogue
and a quota split nothing in the scholarship shape could express. One award, one assessor;
two would diverge on the first correction.

Three profile inputs were added for these gates and nothing else: `age`,
`work_experience_hours`, `employer`. Every one is optional, and an omission is reported as
`gates_unknown` — a fourth outcome beside met/missing/blocked, which **never contributes to
`open`**. That is ADR-0004 applied to money: an award whose age limit we never checked must
not read as one the student clears.

### H2 ✅ Can the engine surface the prep-year / Türkiye Bursları trade-off?

Spec §11 recorded this as a known interaction the engine "should surface; whether it can is
untested". **Answered (4 Sep 2026): it can, now that the profile carries an age.**

The prep year at an Azerbaijani university is the product's central finding — it is what
opens Germany and the UK to a school-leaver. It also costs twelve months, and Türkiye
Bursları' bachelor award is under-21. A 20-year-old who takes the prep year to open Germany
is 21 at the next Turkish window and loses a fully funded place in the same move.
`prep_year_scholarship_warning` reports it; `prep_year_warning` carries it on the response.

It fires only for a student the trade-off is real for — currently under the limit and over
it after the year. Someone **already** past 21 is not told the prep year costs them the
award, because it is already closed to them and its own gate says so.

### H3 🔴 NAWA Banach — which fields, for Azerbaijanis?

Our two sources give **exactly opposite** lists:

- spec §5.2 — *"for Azerbaijanis, humanities/social sciences only"*
- the 4 Sep general research brief — *"engineering, technical, agricultural, and natural
  sciences"*

These are complements, so one is wrong and we cannot tell which. The gate is reported as
unresolved rather than resolved: picking a side would produce a confident answer with a 50%
chance of being backwards.

**This is also why no `field_of_study` input exists yet.** It was considered and deferred:
its only consumers would be Banach (whose own sources contradict), the DP's 15 priority
fields (unverified list) and Türkiye Bursları/CSC priority fields (unread). Adding the
input before any of those is readable would let the engine compute a wrong answer
confidently. **Read `nawa.gov.pl` first, then add the field.**

### H4 🔴 Every figure in the funding catalogue is `research-brief` provenance

One rung below `claude-extracted`: taken from spec §5.2 and the Deep Research briefs, whose
primary pages **this project has not opened**. Nothing is verified by having been loaded.

Pages to open, in rough order of how much a wrong figure would cost a student:

1. **turkiyeburslari.gov.tr** — the under-21 limit and the 10 Jan–20 Feb window. No official
   URL is recorded; the nearest source we hold is `studyinturkiye.gov.tr`. This is the most
   load-bearing unverified figure in the catalogue, because it is one of only two
   instruments open at bachelor level.
2. **chevening.org/resource-hub/guidance/eligibility/** — the 2,800 hours.
3. **nawa.gov.pl** — H3's conflict.
4. **The SOCAR programme page** — no URL identified at all. Age ≤40 (45 MBA) and the
   language bar are both unverified, and the MBA exception is deliberately **not** applied
   in code because nothing in a profile says the degree is an MBA.
5. **az.usembassy.gov/fulbright-foreign-student-program/** — whether a published experience
   minimum exists.
6. **DAAD** — the scholarship database is `Disallow:` in robots.txt and DAAD's terms of use
   have not been read. Every grant must be hand-read from a page that allows it, or DAAD
   ships as the named gap it currently is.

---

## I. The ML — what actually blocks "a solid model, not partly worked"

**Written 4 Sep 2026, 11 days from the deadline. These are the questions I cannot answer
alone.** The stated standard is *"a solid ML model, not partly worked and assumed with
fabricated data."* This section says where we actually are against that standard, then asks
the decisions that are yours.

**I1 was answered while this was being written** — the ML is an Azerbaijan feature with its
own section of the product, separate from the abroad routing. **I2, I3, I4 and I5 are open
and are what a new session should start from.** I4 is the one that decides how the remaining
eleven days are spent, so answer it even if you skip the others.

### The state, measured not remembered

I read `models/metrics.json` and the training script rather than working from memory.

**The model is not weak. It is disconnected.** That distinction matters, because the two
have completely different fixes and only one of them is expensive.

What is genuinely defensible today — the Azerbaijani cold-start model:

| | MAE | RMSE | R² |
|---|---:|---:|---:|
| global-mean baseline | 107.12 | 130.46 | ~0.00 |
| **department-mean baseline** | **57.37** | 82.16 | 0.60 |
| DecisionTree | 54.04 | 76.17 | 0.66 |
| RandomForest | 42.12 | 59.80 | 0.79 |
| **HistGradientBoosting (shipped)** | **41.34** | **59.10** | **0.79** |

**+27.9% against the department-mean baseline**, on 2,576 rows / 1,028 programmes, split
`GroupShuffleSplit` on `program_key` so every test programme is unseen. The DİM scale is
0–700 with an observed **sd of 131.5**, so an MAE of 41 is real signal, not noise fitting.
This clears spec Step 6's own success criterion (*"beats the department-mean baseline,
baseline 57.37"*). **It is a legitimate coursework result and it is honestly evaluated.**

So the problem is not model quality. It is these four:

### Problem 1 — the model and the product serve different students ✅ settled, see I1

The ML predicts **DİM cutoffs at Azerbaijani domestic universities.** The product routes
students **abroad** (TR/DE/GB/US/PL/CN). A student who opens AUSA to find a German master's
gets nothing from the model, however good it is.

This was raised as the deepest problem in the list. **It is now a decision instead: the ML
ships as its own Azerbaijan section, separate from the abroad routing (I1).** The ML has
become a second product sharing a repository, and rather than force the two together, we
say so and give each its own section.

Left here rather than deleted, because the *reason* still binds everything downstream: any
future proposal to feed the model into a route plan runs into the same wall — no destination
country has cutoff data describing the route an Azerbaijani applicant actually takes.

### Problem 2 — nothing serves the model 🔴

Three artifacts exist: `models/cutoff_coldstart_{AZ,TR,US}.joblib`. Grepping the whole
backend for `joblib` returns **only the training scripts.** No endpoint, no service, no
router loads any of them.

The ML currently exists as a training run that produced a metrics file. It is not a feature.
Nothing in the running application would change if all three artifacts were deleted.

### Problem 3 — the forecasting evaluation was skipped by a bug, not by a data limit 🔴

`metrics.json` records for Azerbaijan:

> `"forecasting": {"skipped": "too few intake years for a temporal split (train<=2023 has 0 rows, test=2025 has 928)"}`

**That reads as a data limitation and it is not one.** The data holds three intake years —
2023 (805 rows), 2024 (743), 2025 (1,028) — and 748 programmes appear in more than one.

The cause is in `train_cutoff_models.py`. `temporal_split_years` returns
`(test_year-2, test_year-1, test_year)` = `(2023, 2024, 2025)`, then `evaluate_forecasting`
drops every row without a `cut_lag1`. The 2023 rows have no prior year to lag from, so they
vanish, and `train = d[d.intake_year <= 2023]` is empty. The generic rule produces an empty
training set **specifically when a country has exactly three years.**

A one-step split is available and was never run:

- **train = 2024** (500 programmes carry a 2023→2024 pair)
- **test = 2025** (583 programmes carry a 2024→2025 pair)

That yields a real comparison against the **persistence baseline** (*next cutoff = last
cutoff*), which is the hard baseline in this problem — it beat all three models for Turkey.
Beating it on Azerbaijani data would be a much stronger claim than the cold-start result,
and losing to it is also a publishable finding. **Right now we have neither, and the metrics
file states a reason that is not the real one.**

This is the single highest-value ML fix available, and it is roughly a half-day.

### Problem 4 — two obsolete artifacts contradict an accepted ADR 🟡

`backend/scripts/train_prediction_models.py` trains a **classifier** and calls
`predict_proba` — that is P(admit), which ADR-0008 removed and commit `9a61f28` deleted from
the product. Its outputs `backend/app/models/ml_weights/{turkey,usa}_cutoff_model.joblib`
are still committed, dated 28 Aug, superseded by the 29 Aug retrain.

Nothing loads them, so they mislead a reader rather than a student. Still: a repo that ships
an admission-probability trainer while its ADR says admission probability is not published
is a repo that contradicts itself in front of a marker.

---

### I1 ✅ Must the ML serve the abroad product, or is a domestic DİM predictor acceptable?

**Answered by the user, 4 Sep 2026: the ML is an Azerbaijan feature and ships as its own
section of the product, separate from the abroad routing.** Problem 1 is therefore not a
defect to fix — it is the architecture, stated.

The option this rules out, and why it was right to rule it out: making the model serve the
abroad product would mean predicting something about the six destination countries, and
**we hold no cutoff data for any of them that describes the route an Azerbaijani applicant
actually takes.** Turkish YKS describes the domestic route; German NC excludes
`Bildungsausländer` outright. Collecting real international-quota cutoffs in 11 days is not
credible, so that path ends either in a new modelling task or in invented data — the failure
mode this project has already had to reverse out of three times.

**What this decision now requires of the code and the writing:**

- The two halves get **separate sections in the UI**, not one blended results page. A DİM
  cutoff prediction must never appear inside a route plan for Germany, where it would read
  as a claim about German admission.
- Each section states who it is for, in its own words: *"this predicts cutoffs at
  Azerbaijani universities"* against *"this plans routes to six countries abroad"*.
- The report says the same thing rather than implying one system. Two products in one
  repository is a defensible design; two products described as one is the thing a marker
  would catch.
- **Nothing else in this section changes.** Problems 2, 3 and 4 are all inside the
  Azerbaijan feature and all still stand.

Supersedes the framing in G4, which accepted the train/serve split as a *limitation*. It is
now a product boundary.

### I2 🔴 Which task is the ML deliverable — cold-start, forecasting, or both?

They answer different questions and only one of them is what a person would call
"predicting the cutoff":

- **Cold-start** — *"this programme has no history; what would a similar programme's cutoff
  be?"* Currently shipped, +27.9% over baseline, honestly evaluated.
- **Forecasting** — *"this programme has history; what will its cutoff be next year?"* Never
  evaluated for Azerbaijan (Problem 3). This is the one a student actually asks.

**My recommendation: run forecasting, report both.** Half a day, and it converts "we
compared models on one task" into "we compared them on both tasks and here is where each
wins". If forecasting loses to persistence — as it did for Turkey — **say so**; a negative
result against a strong baseline is a real finding and C4 already accepted that.

### I3 🟡 Does the Azerbaijan section ship as a working page, or as a report?

I1 settled *where* the model lives. This asks whether that section is **running code** or
**a written result**.

Wiring it is about half a day: an endpoint that loads `cutoff_coldstart_AZ.joblib`, plus a
page under the Azerbaijan section. Now that I1 has given it its own section, the framing
problem is gone — a domestic prediction on a domestic page is not a bug, it is the label.

C3 asks what the course deliverables are (notebook / report / running app) and is still
open. **I3 cannot be answered before C3.** If you know the course's actual requirement,
answering C3 settles this one for free.

**My recommendation: wire it.** I1 made this cheaper than it was an hour ago, and an ML
section with nothing behind it invites the question of whether the model runs at all. If C3
turns out to want only a notebook, leave it unwired and state in the README that the
artifacts are evaluated but not served — true, and costs nothing.

**One thing this must not do:** the predicted cutoff is for **Azerbaijani universities**,
and the page has to say so in its own words. It must not appear anywhere near a route plan,
where a number would read as a claim about admission abroad.

### I4 🔴 Eleven days. What gets cut?

Everything below is real work that a reasonable person would want. It does not all fit.
Ranked by what I would keep, and I need to know where you draw the line:

| | Work | Cost | Why it earns the slot |
|---|---|---|---|
| 1 | **Fix the forecasting split (Problem 3)** | 0.5 d | Turns a false "skipped" into a real result; highest value per hour in the repo |
| 2 | **Delete `train_prediction_models.py` + its two artifacts** | 0.5 h | Repo stops contradicting its own ADR |
| 3 | **Verify Türkiye Bursları' under-21 limit** (§H4) | 0.5 d | One of only two bachelor-level awards; a wrong figure here is the most expensive error we ship |
| 4 | **Master's `program_requirements` rows** | 2 d | All 15 curated rows are `level=bachelor`, so every master's plan returns "not collected" — and master's is where 353 of the DP's 500 places are |
| 5 | **Build the Azerbaijan section and serve the model (I1, I3)** | 0.5 d | I1 made this a product section rather than an awkward graft; an ML section with nothing behind it invites the question of whether the model runs |
| 6 | **Run the 57 Brief 00 URLs through `check_sources_robots`** | 0.5 d | Gate before any of them enter `sources.csv` |
| 7 | **Fix `students.gpa` `le=4.0`** | 1 h | Known-broken: rejects a valid Azerbaijani 4.5/5 |

**My recommendation: 1, 2, 3, 7 are non-negotiable (about 1.5 days total).** Item 4 is the
biggest single product gap but is also the one I would cut first if the course grades the
ML, because it buys a better *product* and zero ML marks. **Tell me which of those two the
grade actually rewards and I will spend the eleven days accordingly.**

### I5 🟡 Who verifies the DİM rows? `verified_by` is empty for all 2,576

Every row of `azerbaijan_cutoff_history.csv` has an empty `verified_by`. Under ADR-0004 that
is correct — nobody has checked them — but it means **the model's training data is entirely
unverified**, and "trained on unverified data" is a fair thing for a marker to ask about.

The rows came from official DİM publications, so this is a signing-off task rather than a
re-collection task. **Question: does anyone on the team have time to spot-check a sample
(say 30 rows against the source PDFs) so we can state a verified fraction instead of
zero?** A verified 30 out of 2,576 with a stated method beats 0 out of 2,576, and it is an
hour's work for someone who is not me.

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
