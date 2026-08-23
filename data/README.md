# Data — how to get it

**This directory is empty in git on purpose.** `.gitignore` excludes `data/raw/*`,
`data/processed/*` and all `*.csv` / `*.zip`, because the collected data is ~700 MB and
git is the wrong place for it.

Nothing is lost. Every dataset here is **public and reproducible from scripts in this
repo**. Run the commands below and you get byte-for-byte what everyone else has.

Design rationale for what we collect and why: [`../docs/adr/0001`](../docs/adr/0001-cutoff-prediction-replaces-weighted-scoring.md).
Sources, ownership and schedule: [`../docs/data-collection-plan.md`](../docs/data-collection-plan.md).

---

## Prerequisites

```bash
pip install -r backend/requirements.txt      # needs pandas >= 2.2
git --version                                 # needed for the Turkey pull
```

Run every command **from the repository root**, not from inside `data/`.

Budget roughly **20 minutes** and **~1.2 GB** of free disk for both countries.

---

## 1. Turkey — 115,482 rows (~2 min, 230 MB)

Source: [izcir/turkish-university-admissions-dataset](https://github.com/izcir/turkish-university-admissions-dataset)
— YÖK Atlas / ÖSYM, **MIT licensed**, 2019–2024.

```bash
git clone --depth 1 https://github.com/izcir/turkish-university-admissions-dataset.git data/raw/turkey
python backend/scripts/collect_turkey.py
```

Produces `data/processed/turkey_cutoff_history.csv`.

**You should see exactly this** — if your numbers differ, something went wrong:

```
institution-year rows with a cutoff : 115,482
unique programs                     : 29,293
years                               : 2019-2024
trainable programs (>=3 years)      : 20,341
persistence baseline 2023->2024     : MAE 13.670  r=0.9659
```

> ⚠️ **This is domestic YKS placement data for Turkish nationals.** Azerbaijani students
> apply through the separate **YÖS / international quota** route, which has its own
> cutoffs. Valid as ML training data and as a programme-selectivity signal — but a YKS
> cutoff must **never** be shown to an Azerbaijani student as "the score you need".

---

## 2. USA — 14,798 rows (~15 min, 448 MB download)

Source: [College Scorecard bulk data](https://collegescorecard.ed.gov/data/)
— US Department of Education, **public domain**, per-year files 1996–2026.

```bash
python backend/scripts/collect_usa.py --download     # 448 MB, one file, slow
python backend/scripts/collect_usa.py --years 2016-2024
```

Produces `data/processed/usa_cutoff_history.csv`.

**Expected output:**

```
institution-year rows : 14,798
unique institutions   : 1,853
years                 : 2016-2024
admission_rate non-null : 100.0%
persistence baseline 2023->2024 : admission_rate MAE 0.0623 | sat_avg MAE 23.98
```

> ⚠️ **Do not use the College Scorecard API.** The unregistered `DEMO_KEY` is throttled
> to roughly **30 requests/hour per IP** — not the 1,000 the docs claim — and a full
> time-series pull needs 200+. It returns HTTP 429 partway through. The bulk zip has no
> rate limit and more history. This was already tried; don't repeat it.

> ⚠️ **Start SAT modelling at 2017, not 2016.** The SAT was redesigned in 2016
> (2400-point → 1600-point). The 2016→2017 `sat_avg` persistence MAE is **68.7** against
> ~17–24 for every later year — that gap is the scale change, not real movement.
> `admission_rate` has no such break and is safe from 2016.

---

## 3. Germany, Azerbaijan, Poland, UK, China — not yet automated

| Country | Status | Blocked on |
|---|---|---|
| **Germany** | Not started | Open question **A1** (aggregator vs direct) and **F1** (legal sign-off). Top priority market, least certain data path |
| **Azerbaijan** | Not started | Open question **A4** — team-only task, needs local knowledge and Azerbaijani-language sources |
| **Poland** | Not scoped | Open question **A2** |
| **UK** | Deferred | UCAS entry-grade data confirmed to exist; deprioritised per **B1** |
| **China** | Deferred | Open question **A3** — likely no cutoff exists to predict |

See [`../docs/open-questions.md`](../docs/open-questions.md).

---

## Output schema

Both files share the shape defined in
[`../docs/data-collection-plan.md`](../docs/data-collection-plan.md) §1:

| Column | Meaning |
|---|---|
| `country` | ISO-2 code (`TR`, `US`) |
| `intake_year` | The admission cycle |
| `cutoff_value` | **The target variable.** In native units |
| `cutoff_unit` | `yks_score_012`, `sat_p25_and_admit_rate`, … |
| `lower_is_better` | `TRUE` for German Abiturnote and YKS *rank*; `FALSE` for scores |
| `source_url` | Provenance for every single row |
| `verified_by` | **Empty until a human checks the row.** See below |

Country-specific feature columns (quota, enrolment, city, department, ownership …) sit
between `lower_is_better` and `source_url` and differ per country by design — ADR-0002
trains one model per country, so the feature sets are not required to match.

---

## Before any of this reaches a student

`verified_by` is `NULL` on every row these scripts produce. That is deliberate.
`../data-sourcing.md` §4 is explicit:

> *"A human confirms every record before it goes live. Extraction confidence is never
> high enough to publish blind on data students make financial decisions from."*

Collected ≠ verified. These files are fine to train and experiment on today. Nothing
from them goes in front of a student until a person has checked it and signed the row.

---

## Troubleshooting

**`Dataset not found at data/raw/turkey/data/processed`** — the clone didn't run, or it
landed in the wrong place. Re-run the `git clone` from the repository root.

**`scorecard_raw.zip not found`** — run `collect_usa.py --download` first. It is a
separate step because it is a 448 MB download.

**HTTP 429 from College Scorecard** — you're using the API instead of the bulk zip. See
the warning in §2.

**Turkish characters look like `SÃ–Z` or `DÄ°L`** — that's your terminal, not the data.
The files are UTF-8 and the scripts read them as UTF-8. On Windows PowerShell try
`chcp 65001`, or just open the CSV in pandas.
