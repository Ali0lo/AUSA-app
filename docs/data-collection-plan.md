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
| **Azerbaijan** | DIM published cutoff scores | ❌ Local knowledge, likely Azerbaijani-language PDFs | **Team** |
| **Poland** | IRK / eRekrutacja recruitment portals. No central database confirmed — see A2 | ❓ Unknown until scoped | **Team scopes, then decide** |
| **UK** | [UCAS entry grades](https://www.ucas.com/applying/before-you-apply/what-and-where-to-study/entry-requirements/understanding-historical-entry-grades-data) — accepted-grade profiles + offer rates, 2023–2025 | ⚠️ Per-course fetching | Deferred (B1) |
| **China** | None identified. Likely `admission_type = competitive` — see A3 | ❌ | Deferred (A3) |

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
