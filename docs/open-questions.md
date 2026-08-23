# AUSA — Open Questions

**Deadline: 15 September 2026.** Updated 23 August — **23 days left**.

**4 of 18 answered.** Fill in the `**Answer:**` line under each remaining question.
Every question carries a recommendation — accept it, override it, or write something
better. Decisions already settled are recorded in [`adr/`](adr/) and are not repeated here.

Legend: 🔴 blocks implementation · 🟡 blocks a specific country or feature · 🟢 can be deferred

## Still required — read this first

Answered so far: **B1** (country order), **B3** (coverage check), **B5** (deadline),
**C1** (deterministic hard filters are acceptable — the ADR-0001 design stands).

Given 23 days, the remaining questions are no longer equally urgent. These are the ones
that actually block work now:

| Answer today | Why it blocks |
|---|---|
| **B2** — which degree levels? | Decides what gets curated starting tomorrow. Curation is the critical path and cannot start without it |
| **B4** — who does what? | Four tracks, four people, 23 days. Nobody can start until this is assigned |
| **A4** — who collects Azerbaijan DIM data? | Only the team can do this one. Nothing else unblocks it |
| **C4** — is "the persistence baseline won" acceptable? | If it would be graded as failure, the ML plan needs a second component designed in *now*, not in week three |

| Answer within 3 days | Why |
|---|---|
| **A1** — Germany aggregator or direct? | Gates all German collection, and Germany is the top market |
| **F1** — who signs off on scraping legality? | Gates A1. Must happen before any German collection code runs |
| **C2, C3** — algorithms and deliverables | Shapes the training pipeline and where the code lives |

| Can wait | |
|---|---|
| **A2, A3** (Poland, China) | Both deferred to last per B1 |
| **A5** (US granularity) | Recommendation is "accept and label it" — only needs a no |
| **D1, D2, D3** (web/mobile, accounts, languages) | Frontend can start on the recommendations |
| **E1, E2, E3** (retraining, artifacts, `admitted_profiles`) | Recommendations are safe defaults; confirm when convenient |

**Not a question, but the biggest risk:** three countries × 40–50 programmes, plus five
years of cutoff history each, plus backend, frontend, model and report, in 23 days with
four people is very aggressive. See [`data-collection-plan.md`](data-collection-plan.md) §5
for what to drop first if it slips.

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

**Answer:**

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

### B2 🔴 Which degree levels?

The schema supports bachelor / master / PhD. Each level has different requirements,
different cutoff mechanisms and separate curation cost — supporting all three roughly
triples the work and splits the training data three ways.

**Recommendation:** **master's only** for the MVP. It is where Azerbaijani outbound
mobility concentrates, where DAAD data is richest, and where the cutoff mechanism is
cleanest. Bachelor's second.

**Answer:**

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

**Answer:**

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

**Answer:**

### C3 🟡 What are the deliverables — notebook, report, running app, or all three?

Determines whether the training code lives in `notebooks/` for presentation or in
`backend/` as a production job.

**Recommendation:** both, deliberately — an EDA/training notebook in `notebooks/` for the
report, and a thin production training script that imports the same functions, so the
notebook and the app cannot drift apart.

**Answer:**

### C4 🟡 Is "the baseline won" an acceptable result?

Cutoffs are strongly autocorrelated year-to-year, so *"next year's cutoff = last year's
cutoff"* is a strong predictor. The trees may not beat it. Scientifically that is a
legitimate and publishable finding; as coursework it may be graded as failure.

**Recommendation:** ask now. If it would be graded as failure, we need a second ML
component with a softer baseline planned in from the start rather than improvised in
week five.

**Answer:**

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

**Answer:**

---

## Answered — for the record

These were open in `architecture-decisions.md` and are now settled:

- **Target countries** — Germany, Poland, Turkey, Azerbaijan, USA, UK, China (priority order)
- **Scoring formula and weights** — superseded. The hand-set 0.5 / 0.3 / 0.2 weights are
  replaced by a learned cutoff prediction; the match score becomes headroom above the
  predicted cutoff
- **Primary data source** — published admission cutoff history per country, not scraped
  programme pages
