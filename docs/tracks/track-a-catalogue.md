# Track A — Catalogue and curation

**Two people. ~7.5 days of work. The critical path.**

Read [`../../data/curation/README.md`](../../data/curation/README.md) first — it holds the
column rules, the forbidden sources, and the 30-university priority worklist. This file is
the *order of work* and the definition of done; it does not repeat the rules.

---

## Why this is the critical path

Everything else is built and waiting on these rows. The route engine works, the endpoint
works, the funding gates work — and the catalogue behind them holds **15 rows**:

```
DE bachelor  3     GB bachelor  5     TR bachelor  2     CN bachelor  5
PL           0     US           0     master's     0
tuition_per_year populated on 2 of 15
```

Three consequences a user meets today:

- Every master's plan returns *"we have not collected this"*. The State Programme funds
  **2,907 master's places against 1,214 bachelor**, so that is the larger half of the
  product, missing.
- **Ranking by total cost to degree cannot run**, because 13 of 15 rows have no cost.
- **The product's headline claim resolves to nothing.** Run `python demo_walkthrough.py` and
  look at the `az-prep-year → de-bachelor-direct` plan: *"None of the DE universities we
  have collected documents accepting `one_year_university`."* All three German rows are
  `feststellungspruefung`. The UK half works and names Cambridge and Manchester; the German
  half — the finding the README leads with — has no university behind it.

This is human work. No amount of code makes it faster.

---

## Steps, in order

### A1 · Close the German prep-year gap — half a day, do this first

The smallest task with the largest effect on what the product can honestly say.

1. Take TUM, LMU and Heidelberg (already in the file at `feststellungspruefung`).
2. On each university's own international-admissions page, find its stance on an applicant
   who has **completed one year of university study in Azerbaijan**. anabin/KMK says this
   grants direct, subject-restricted access; confirm what each university actually states.
3. Add a **new row per university** with `entry_qualification_accepted=one_year_university`.
   Do not edit the `feststellungspruefung` rows — both are true, and they are different
   routes with different requirements.
4. Re-run `python demo_walkthrough.py`. The `az-prep-year → de-bachelor-direct` plan must
   now list universities instead of an explanation.

**Done when:** the demo names at least two German universities on the prep-year plan.

### A2 · Tuition and deadline on every existing row — 1 day

Cost ranking is specified and cannot run. For each of the 15 rows, find on the source page:

- `tuition_per_year` — **the international figure.** The domestic or EU number is usually
  the more prominent one and is the wrong one. If only a domestic figure is published,
  **leave it blank** and say so in `notes`.
- `currency`, `application_fee`, `application_deadline` (ISO date, or blank — never
  "usually August"), `living_cost_estimate_per_year` where the university publishes one.

**Done when:** every row either carries a tuition figure with its currency, or carries a
note saying the page publishes no international figure.

### A3 · Master's rows — 3 days, the biggest single gap

Both people. Use the priority worklist's suggested split. Start where the State Programme
funds the most master's places: **China** (Zhejiang 68, USTC 58, Wuhan 46), **the UK**
(Imperial 50, UCL 40, Edinburgh 27), **Turkey** (Istanbul Technical 45, Ankara 43, Ege 38),
then **Germany** (TUM 43, RWTH 27).

The entry qualification at master's is `bachelor_degree`, and the findings **invert** from
bachelor: Germany and the UK are *open* to a bachelor holder where they are closed to a
school-leaver. Never copy a bachelor row up to master.

**Done when:** ≥25 master rows across at least four countries, and a master's profile in
the demo returns named universities for TR, GB and CN.

### A4 · Poland and the USA — 1.5 days

Both currently return "not collected" at both levels. Note two verified facts before you
start, so you do not go looking for something that is not there: **the State Programme funds
zero bachelor places in the USA and zero in Poland.** That is an answer, not a gap. Poland
has 8 master programmes across 3 universities, total.

So: master's only for both, and keep it small — Poland is first in the cut order.

**Done when:** ≥5 US master rows and the 3 Polish universities are covered, or a written
note saying why a page could not produce a row.

### A5 · Verify the funding figures — 1.5 days

**Every figure in `backend/app/domain/scholarship_definitions.py` is `research-brief`
provenance** — taken from a research summary whose primary pages nobody in this project has
opened. Open them, in this order:

1. **turkiyeburslari.gov.tr** — the **under-21** bachelor limit and the 10 Jan–20 Feb window.
   *The most load-bearing unverified number we ship*, because Türkiye Bursları is one of only
   two awards open at bachelor level. No official URL is recorded; the nearest source we hold
   is `studyinturkiye.gov.tr`.
2. **chevening.org/resource-hub/guidance/eligibility/** — the 2,800 hours.
3. **nawa.gov.pl** — our two sources give **opposite** field lists (spec §5.2 says
   humanities/social sciences only; the research brief says engineering and natural sciences).
   One is wrong. Read the primary page and settle it.
4. **The SOCAR programme page** — no URL identified at all. Age ≤40 (45 for MBA) and the
   language bar are both unverified.
5. **az.usembassy.gov/fulbright-foreign-student-program/** — whether a published experience
   minimum exists.

For each: update the figure if it is wrong, and change `provenance` to `human-verified` with
the real `citation` URL. If a page contradicts what we ship, **say so in the commit message**
— that is a finding, not a correction to bury.

**Done when:** at least Türkiye Bursları, Chevening and NAWA carry a URL somebody opened.

### A6 · DİM spot-check — half a day

`verified_by` is empty on all 2,576 rows of `azerbaijan_cutoff_history.csv`, so the model's
training data is entirely unverified. Take a random **30 rows**, check each against the
source DİM publication, and record: how you sampled, how many matched, and what any mismatch
looked like. Write it into `data/README.md`.

A verified 30 out of 2,576 with a stated method is a real answer to *"was this checked?"*
Zero out of 2,576 is not.

---

## How to submit

1. Work in `data/curation/program_requirements_<yourname>.csv`, using the template's exact
   header (`data/curation/program_requirements_template.csv`).
2. Dry-run it before you commit:
   ```bash
   cd backend
   python -m scripts.load_program_requirements --file ../data/curation/program_requirements_<yourname>.csv --dry-run
   ```
   The loader parses every row before writing any, and aborts whole on a bad one — so a
   dry-run that passes means the file is clean. A `CuratedRowError` names the line and the
   column.
3. Commit the CSV. **Do not hand-write rows into the database.**

`verified_by` must stay empty in the file — the loader rejects a file that sets it. A file
cannot record that a person read a page; the admin review queue stamps that from the
authenticated account.
