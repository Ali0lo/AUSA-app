# Track B — The Azerbaijan DİM section

**One person. ~3 days.**

This is the project's only machine learning, and it is a **separate section of the product**
from the abroad routing — its own page, its own words, its own question. Read the boundary
rule in [`README.md`](README.md) before you start; the short version is that a DİM cutoff
*we predicted* stays in this section, while a DİM score the *student told us* is used freely
by the abroad features, including the State Programme.

---

## What the model is, and what it is not

The student's DİM score is **not a model input and cannot be.** The features are
`(university_name, department_name, score_type, scholarship_type, intake_year)`. The model
predicts **the programme's cutoff**. The student's score enters afterwards as arithmetic:

```
headroom = your score − predicted cutoff
```

That separation is the whole reason the claim is honest here. DİM admission is mechanical —
clearing the cutoff *is* admission — so `P(next year's cutoff ≤ your score)` is the success
rate rather than a proxy for it. Nowhere else in this project survives that test.

**The field group (1–4) is not a model input either.** It is a filter over which specialties
are relevant, and it is the same input the State Programme's band check needs (400 for group
1, 550 otherwise). Ask it once; both halves of the product use it.

---

## Steps, in order

### B1 · Fix the forecasting split — half a day. **Do this first; B3 depends on it.**

`models/metrics.json` records for Azerbaijan:

> `"forecasting": {"skipped": "too few intake years for a temporal split (train<=2023 has 0 rows, test=2025 has 928)"}`

**That reads as a data limitation and it is not one.** The data holds three intake years —
2023 (805 rows), 2024 (743), 2025 (1,028) — and 748 programmes appear in more than one.

The cause is in `backend/scripts/train_cutoff_models.py`. `temporal_split_years` returns
`(test_year-2, test_year-1, test_year)` = `(2023, 2024, 2025)`, then `evaluate_forecasting`
drops every row without a `cut_lag1`. The 2023 rows have no prior year to lag from, so they
vanish, and `train = d[d.intake_year <= 2023]` is empty. **The generic rule produces an empty
training set specifically when a country has exactly three years.**

1. Add a one-step split for that case: **train = 2024** (500 programmes carry a 2023→2024
   pair), **test = 2025** (583 carry 2024→2025).
2. Evaluate all three algorithms against the **persistence baseline** (*next cutoff = last
   cutoff*). Persistence is the hard baseline in this problem — it beat every model on
   Turkish forecasting at 13.77 MAE.
3. Re-run training, commit the updated `models/metrics.json`.

**Done when:** `metrics.json` carries real AZ forecasting numbers with a named split, and no
`"skipped"` key with a reason that is not the real one.

**Either outcome is a result, and you report it either way.** Beating persistence on
Azerbaijani data is a stronger claim than the cold-start result. Losing to it is a
publishable negative finding against a strong baseline, exactly as Turkey's was. **Do not
tune until it wins** — that is how the honest version of this project dies.

### B2 · Serve the model — half a day

Nothing loads the artifacts. `grep -r joblib backend/` returns only the training script, and
nothing in the running application would change if all three `.joblib` files were deleted.

1. `backend/app/services/prediction/` — load `models/cutoff_coldstart_AZ.joblib` **once at
   startup**, not per request.
2. An endpoint returning, per programme: the predicted cutoff **as an interval**, the model
   run id, and which model answered.
3. **Refuse rather than guess.** A programme with fewer than two years of history gets the
   cold-start answer *labelled as such*; anything the model cannot answer returns a named
   absence, never a substituted number.

**Which model answers which question** — this matters and is easy to get backwards:

| Question | Model | When |
|---|---|---|
| *"What will this programme's cutoff be in 2026?"* | **forecasting** (B1) | The programme has history. **Most of the 1,028 do.** |
| *"This programme has no history — what would a similar one score?"* | **cold start** | New or single-year programmes, where persistence is structurally unavailable |

If B1 shows persistence beating the models, then **persistence is what the endpoint serves**
— *"last year's cutoff, unchanged"* — labelled honestly, and the model comparison ships as
the reported finding. Decide from B1's evidence. Do not pre-commit.

**Done when:** an endpoint returns a predicted interval for a real programme, and a test
proves it refuses on thin history instead of answering.

### B3 · The Azerbaijan page — 1 day

Its own section, working at two depths so it is useful before the student enters anything:

| Input | Shows |
|---|---|
| **Nothing** | Predicted 2026 cutoffs, filterable by field group and university. Nobody in Azerbaijan publishes this |
| **+ DİM score** | The same list split into **clears / too close to call / below**, measured against the *interval* |
| **+ field group (1–4)** | Filters the list — and turns the State Programme verdict from "we could not tell" into a definite yes or no |

**Bands, never a point estimate.** MAE is 41.34 on a 0–700 scale with an observed sd of
131.5. Printing "predicted cutoff: 482" claims a precision we do not have. The interval with
"too close to call" in the middle is the same claim, honestly sized.

**The page must say in its own words that these are Azerbaijani universities.** It must not
appear inside a route plan, where the number would read as a claim about admission abroad.

**Done when:** the page renders with no input, refines with a score, and states what it
predicts and what it does not.

### B4 · The comparison notebook — 1 day

`notebooks/` is empty. Write an EDA and model-comparison notebook that **imports
`train_cutoff_models.py`** rather than re-implementing it, so the report and production
cannot drift.

It must show: the DİM distribution, both baselines (global mean and department mean),
all three algorithms on both tasks, and the failed remedies from the Turkish forecasting
investigation — delta target, restricted training window, shrinkage — as evidence of a real
investigation rather than one run.

**Done when:** the notebook runs top to bottom and reproduces the numbers in
`models/metrics.json`.

> **B4's shape depends on an unanswered question** (open-questions C3): what the course
> actually grades — notebook, report, running app, or all three. If it grades only a
> notebook, B2 and B3 can be cut and the README states that the artifacts are evaluated but
> not served, which is true and costs nothing.

---

## Files this track owns

```
backend/scripts/train_cutoff_models.py
backend/app/services/prediction/          (new)
models/metrics.json
notebooks/
frontend/src/app/azerbaijan/              (new, B3)
```

## What not to do

- **Do not feed the model into a route plan.** No destination country has cutoff data
  describing the route an Azerbaijani applicant actually takes; that is why this model is
  Azerbaijan-only ([ADR-0008](../adr/0008-selectivity-replaces-cutoff-prediction.md)).
- **Do not add a second country to make the story thicker.** The US Scorecard model was cut
  deliberately: institution-wide admit rates that Scorecard does not break out for
  international applicants, on a segment the State Programme funds zero places in. One
  defensible model beats two where the second exists to be counted.
- **Do not report a tuned number without its baseline.** Every table in `metrics.json`
  carries its baseline, and that is what makes it gradeable.
