# Data Collection Plan

**Deadline: 15 September 2026.** Written 23 August — 23 days.

What data the ML model needs, where it comes from, and **who collects it**.
Companion to [adr/0001](adr/0001-cutoff-prediction-replaces-weighted-scoring.md).

---

## 1. What we actually need

Per ADR-0001 the model trains on **published admission cutoff history**, not student
outcomes. That is one new table:

```sql
CREATE TABLE program_cutoff_history (
    id              SERIAL PRIMARY KEY,
    program_id      INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    intake_year     INTEGER NOT NULL,        -- 2019..2025
    intake_term     VARCHAR(10),             -- 'winter' | 'summer' | NULL
    cutoff_value    DECIMAL(10,3) NOT NULL,  -- native units
    cutoff_unit     VARCHAR(30) NOT NULL,    -- 'abiturnote'|'yks_rank'|'dim_score'|'ucas_tariff'|'sat_p25'
    lower_is_better BOOLEAN NOT NULL,        -- TRUE for Germany, YKS rank
    quota           INTEGER,                 -- places available, if published
    applicants      INTEGER,                 -- if published
    source_url      TEXT NOT NULL,
    collected_at    DATE DEFAULT CURRENT_DATE,
    verified_by     VARCHAR(100)             -- NOT NULL before it trains anything
);
```

**Minimum viable training set:** each programme needs **at least 3 intake years** to
contribute anything the persistence baseline cannot already do. Programmes with 1–2
years are still useful as cold-start test cases (ADR-0003) but cannot train a trend.

Plus one column on `programs`: `admission_type` (`open` | `cutoff` | `competitive`).

---

## 2. Sources and ownership, by country

Ordered by the priority confirmed in open question B1: **Germany, Turkey, Azerbaijan**
first; then **USA, Poland**; **UK, China** last.

| Country | Source | Automatable? | Owner |
|---|---|---|---|
| **Turkey** | [`izcir/turkish-university-admissions-dataset`](https://github.com/izcir/turkish-university-admissions-dataset) — 128,352 records, 32,505 programmes, 2019–2024, cutoffs + quotas, **MIT licensed** | ✅ Fully — it is a git repo | **Claude** |
| **USA** | **College Scorecard bulk zip** — 448 MB, per-year files 1996–2026, public domain. ✅ **Collected: 14,798 institution-year rows.** See §2a for why not the API, and for the Common Data Set alternatives | ✅ Done | **Claude** |
| **Germany** | Official university NC pages, indexed via [auswahlgrenzen.de](https://www.auswahlgrenzen.de/). Aggregators (NC-Werte.info, Studis Online) hold 29,000+ thresholds but carry ToS risk — see open question A1 | ⚠️ Partly — needs the programme list first | **Claude fetches, team picks and verifies** |
| **Azerbaijan** | **sec.az `/kecid-ballari`** — 1,028 specialty × university rows, 42 universities, 2023–2025 state-funded cutoffs. ✅ **Collected: 2,576 rows.** See §2b | ✅ Done — one request | **Claude collects, team verifies** |
| **Poland** | IRK / eRekrutacja recruitment portals. No central database confirmed — see A2 | ❓ Unknown until scoped | **Team scopes, then decide** |
| **UK** | [UCAS entry grades](https://www.ucas.com/applying/before-you-apply/what-and-where-to-study/entry-requirements/understanding-historical-entry-grades-data) — accepted-grade profiles + offer rates, 2023–2025 | ⚠️ Per-course fetching | Deferred (B1) |
| **China** | None identified. Likely `admission_type = competitive` — see A3 | ❌ | Deferred (A3) |

### 2b. Azerbaijan — what was evaluated and what was chosen

Reproduce with:

```bash
python backend/scripts/collect_azerbaijan.py
# -> 2,576 rows / 1,028 programs / 42 universities, years 2023-2025
```

**What the cutoff means.** The `keçid balı` is **not** set in advance by DİM. It is the
score of the *last applicant admitted* to a specialty that year, known only once
specialty selection closes. That is the same quantity as the Turkish `final_score_012`,
so the two countries are semantically consistent targets — they differ in unit (DİM is
0–700, higher is better), which is why ADR-0002 keeps them in separate models.

**Sources evaluated:**

| Source | Coverage | Verdict |
|---|---|---|
| **sec.az** `/kecid-ballari` | 1,028 specialty × university, 42 universities, **2023 + 2024 + 2025**, state-funded. Server-rendered HTML, one request. `/kod/NNNNNN` detail pages add quota, tuition and the paid track | ✅ **Chosen** |
| 2xacademy.az | 461 specialties, **2025 only**, both funding tracks | Useful cross-check for 2025; too little history to train on |
| uniaz.info | per-group cutoff pages | Not evaluated in depth — sec.az already covers it |
| **DİM official** (dim.gov.az) | Free PDFs, 2018–2025. The `n12` series is 706 pages of statistical analysis | ⚠️ **Not a bulk source, but a free official verifier** — see below |
| **"Abituriyent" journal** (abiturient.az) | The authoritative per-specialty minimums | ❌ Paywalled. Would be the way to get pre-2023 history — see the limitation below |
| **qebulai.az** | 2020–2025 | ❌ **Excluded on legal grounds — see below** |

#### The official DİM PDFs — what they actually contain (checked 29 Aug)

`dim.gov.az/az/fealiyyet/tetqiqat/statistik-tehlil` publishes free PDFs going back to
2018. They were opened and searched rather than judged from the listing page:

- **`n12-<year>.pdf`** — the *Abituriyent* №12 scientific-statistical analysis. The 2025
  edition is **706 pages, 2.3 M characters, text extracts cleanly** with `pypdf`.
- **`secim-<year>.pdf`** — the specialty-selection booklet, 112 pages.

**They do not contain a full per-specialty cutoff table.** What they contain is:

- **Only the extremes** — Cədvəl 1.64, *"ƏN YÜKSƏK VƏ ƏN AŞAĞI KEÇİD BALLI İXTİSASLAR"*,
  lists the highest- and lowest-cutoff specialty per group, not all 1,028.
- Group-level admission plans split by **Azərbaycan bölməsi / Rus bölməsi / Birgə**.
- Per-subject correct-answer percentages, school rankings, score-interval distributions.

**But they are genuinely valuable for three things:**

1. **Free official verification.** The 2025 journal states BANM *İnformasiya
   təhlükəsizliyi* = **681.0**; our sec.az row for that programme is **681.0 — exact
   match**. This is how `verified_by` gets filled without paying for the journal.

   One caveat found while checking: ADA *Dizayn* reads 237.1 in the journal against 241.9
   in our data. That is **not** a discrepancy — the journal quotes *"minimal **test
   imtahanı** balı"* for Group V, where an aptitude exam (`qabiliyyət imtahanı`) adds
   points on top. Group V rows are measuring a different quantity and must not be
   verified against this figure.

2. **It confirms our target definition, officially.** *"qəbul olan abituriyentlər
   arasında ən aşağı bal toplayan abituriyentin balı minimal bal kimi götürülmüşdür"* —
   the cutoff is the score of the lowest-scoring admitted applicant. Identical semantics
   to the Turkish `final_score_012`. Quote this in the report.

3. **It explains the 163 unlabelled variants.** The booklet states DİM prepares
   **separate admission plans for the Azerbaijani and Russian sections**, and notes that
   same-name specialties differ significantly between Baku and the regions. That is the
   discriminator sec.az drops.

The booklet also draws a distinction worth keeping straight in the UI: **`müsabiqə şərti`**
(the minimum score to enter the competition at all, set in advance) is *not* the
**`keçid balı`** (the resulting cutoff, known only afterwards). We predict the latter.

**qebulai.az must not be used, as a source or a cross-check.** Its robots.txt disallows
`ClaudeBot`, `GPTBot`, `CCBot` and `Google-Extended`, sets `Content-Signal: ai-train=no`,
and asserts an **express reservation of rights under Article 4 of EU Directive 2019/790**.
It is also a direct competitor: a freemium DİM cutoff-prediction product (7.99–49.99 ₼)
built by Emin Baxışlı and İskəndər Məmmədov, which — unlike AUSA — presents results as
absolute admission probabilities. One idea from it is worth adopting independently: it
models the **Azerbaijani and Russian sections separately**, because they compete in
different pools.

By contrast sec.az's robots.txt **explicitly allows** general crawlers and names
`ClaudeBot` and `GPTBot` as permitted; only `/app`, `/login` and similar gated paths are
disallowed. 2xacademy.az likewise allows all agents outside `/dashboard` and `/auth`.

**Still open for the F1 owner:** robots.txt permission is not the whole answer. sec.az
carries `© 2026 İxtisas Seç MMC` and links "İstifadə şərtləri", but that path 404s — the
real terms must be found and read. The underlying cutoff *figures* are public DİM results
that nobody owns; the *compilation* may attract database rights. The collector currently
issues **one** request for the list page; the ~500-request `/kod/` enrichment is gated
behind `--i-have-f1-signoff` and refuses to run without it.

**Two limitations to carry into the report:**

1. **Only three years.** Forecasting needs at least four intake years to build a lag and
   still leave a training split, so the Azerbaijan forecasting evaluation is **skipped**,
   not failed. Pre-2023 history exists only in the paywalled journal. This is the
   strongest remaining argument for buying it.
2. **163 unlabelled variants (38% of rows).** sec.az publishes several rows for the same
   (specialty, university, group) with different scores — DİM admits separately by
   language section and by əyani/qiyabi — but the list page **does not say which is
   which**; the rows are byte-identical apart from the scores. They are kept as separate
   programs with a `variant_index`, never merged: collapsing them would interleave
   unrelated series and silently corrupt every lag feature. The discriminator is on the
   `/kod/` pages ("1-ci qrup əyani Azərbaycan bölməsi") and in the journal. `verified_by`
   is empty on every row until a human resolves this.

### 2a. USA — what was evaluated and what was chosen

**Chosen: the College Scorecard bulk zip.** The API was tried first and abandoned —
the unregistered `DEMO_KEY` throttles to roughly **30 requests/hour per IP**, not the
1,000 the docs imply, and a full time-series pull needs 200+. It returned HTTP 429 on
page 8. The bulk zip has no rate limit and carries more history.

Three **Common Data Set** aggregators were also evaluated. CDS is genuinely richer than
Scorecard — it carries enrolled-freshman **GPA distributions**, **admission-factor
importance rankings** and waitlist data, none of which Scorecard has:

| Source | Format | Verdict |
|---|---|---|
| [collegedata.fyi](https://www.collegedata.fyi/) | **MIT licensed**, open source ([repo](https://github.com/bolewood/collegedata-fyi)), public no-auth API, 4,071 archived CDS documents, 262,537 field rows | **Best of the three.** But the friendly API is a *current snapshot*, not a per-year series — and the model needs a time series. The historical depth sits behind PDF extraction or authenticated PostgREST. Note: the documented host `api.collegedata.fyi` 404s; the working base is `https://www.collegedata.fyi/api` |
| [collegetransitions.com](https://www.collegetransitions.com/dataverse/common-data-set-repository) | Links to per-school Google Drive PDFs, 2017-18 → 2024-25, hundreds of schools | Rich but unstructured. PDF extraction per school per year. No explicit reuse licence |
| [commondatasets.com](https://commondatasets.com/index.html) | Web interface only, **33 schools**, 2024-25 cycle only | Too narrow — one cycle gives no time series at all |

**Recommendation: do not invest further here yet.** Scorecard already yields a working
US training set, and **the USA is 4th priority under B1 while Germany is 1st and still
has no confirmed data path.** Spending days on CDS extraction while the top market is
unsolved is the wrong trade. Revisit collegedata.fyi as an enrichment pass if time
remains — its per-field quality flags ("withheld because internally inconsistent")
model exactly the honesty ADR-0004 requires, and it is worth learning from regardless.

---

## 3. The split: what Claude does, what the team must do

### Claude can do, starting now, with no input needed

1. **Turkey** — pull the MIT-licensed dataset, map it onto `program_cutoff_history`,
   report actual coverage per programme per year.
2. **USA** — query College Scorecard, extract admit rates and SAT/ACT percentile bands
   across available years, map onto the same table.

These two are free, legally unambiguous, and give a **real training set within days**
— enough to build and validate the entire pipeline end to end before a single German
programme is curated.

### Claude can do, once the team supplies a list

3. **Germany** — given a list of universities and programmes, fetch the official NC
   pages and extract published cutoff values per intake.
4. **UK** — same, given a course list.

The blocker is not fetching. It is *which programmes*.

### Only the team can do

5. **Choose the programmes.** Which programmes Azerbaijani students actually apply to
   is domain knowledge that exists in your heads and nowhere on the internet. This is
   the single highest-value input to the whole project and it cannot be automated.
6. **Azerbaijan / DIM.** Language access and local knowledge.
7. **Verify every record.** `data-sourcing.md` §4 is explicit: *"A human confirms every
   record before it goes live. Extraction confidence is never high enough to publish
   blind on data students make financial decisions from."* `verified_by` stays NULL
   until a person has checked it.
8. **Legal sign-off** per source (open question F1) — before any German collection runs.

---

## 4. Recommended sequence for the 23 days

The ordering matters more than the volume. **Do not curate Germany first**, even
though it is the top market — it is the slowest source and the one with an unresolved
legal question. Start where data is already free and clean, so the pipeline is proven
before the slow work begins.

| Days | Work | Owner |
|---|---|---|
| 1–3 | Turkey + USA data pulled, `program_cutoff_history` populated, coverage reported | Claude |
| 1–5 | Choose ~40 Germany + ~40 Turkey + ~30 Azerbaijan programmes. Tag every one with `admission_type` and **count the cutoff-based share** (open question B3) | Team (2 people) |
| 3–7 | Schema migration, training pipeline, persistence baseline, temporal + cold-start evaluation on Turkish data | Claude + ML owner |
| 5–12 | Germany NC collection against the chosen list; Azerbaijan DIM collection | Claude + team |
| 8–14 | Matching pipeline rebuilt per ADR-0001/0005; batch prediction job | Backend owner |
| 12–18 | Frontend: cutoff history, headroom bands, net-cost display | Frontend owner |
| 18–23 | Verification pass, report, SHAP interpretability section, buffer | All |

**The gate at day 5:** if the cutoff-based share of the catalogue is under ~40%,
re-weight curation toward NC and Turkish/Azerbaijani programmes *before* writing model
code (ADR-0001, consequences).

---

## 5. Honest risks

- **23 days is tight for three countries.** If something has to give, drop Azerbaijan
  collection to a stretch goal and ship Turkey + Germany. Turkey alone can carry the
  ML deliverable; Germany carries the product story.
- **Germany may yield thin history.** Official university pages often publish only the
  current intake's NC, not five years of it. If per-university history turns out to be
  1–2 years, Germany becomes a cold-start case and the aggregator question (A1) gets
  sharper — that is a decision point around day 7, not a surprise at day 20.
- **US data is institution-level**, not programme-level (open question A5).
- **Verification is not optional and is not fast.** Budget real hours for it.
