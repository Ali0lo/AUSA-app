# ADR-0002 — One model per country, normalize after prediction

**Status:** Accepted
**Date:** 2026-08-23 · **empirically confirmed 2026-08-29**
**Depends on:** [ADR-0001](0001-cutoff-prediction-replaces-weighted-scoring.md)

---

## Confirmed by experiment, 29 August 2026

The obvious alternative — **one model with `country` as a feature** — was raised and then
tested rather than argued. `evaluate_pooled()` in `backend/scripts/train_cutoff_models.py`
runs it on every training run, and the result is in `models/metrics.json`.

A pooled model is only meaningful on a **unit-free target**: raw cutoffs run 0–560 (YKS),
0–700 (DIM) and ~600–1500 (SAT p25), so a single regressor on raw values would mostly
learn which country a row came from, and its error would be dominated by the largest
scale. The comparable target is the cutoff's **percentile within its own country-year** —
which is also exactly the selectivity index the product displays, so a predicted
percentile converts back to native units through that country's own distribution.

Three arms, identical held-out programs, MAE on the percentile target:

| Country | dept-mean baseline | per-country | pooled | pooled, balanced | winner |
|---|---|---|---|---|---|
| TR | 0.1765 | **0.1035** | 0.1067 | 0.1165 | per-country |
| US | 0.2444 | 0.2640 | **0.2476** | 0.2488 | pooled |
| AZ | 0.1190 | **0.0874** | 0.1285 | 0.0968 | per-country |

**Per-country wins for two of three, so ADR-0002 stands.**

The reason is specific and worth recording: **there is no shared feature semantics to
transfer through.** Department and university names are in different languages, so a
Turkish and an Azerbaijani computer-engineering programme never share a category code.
Pooling therefore adds dilution without transfer. Azerbaijan — the smallest dataset, and
the one most likely to benefit from borrowing strength — got **47% worse** when pooled.
Weighting countries equally recovered most of that (0.1285 → 0.0968), confirming Turkey's
90% share was swamping it, but still did not beat its own model.

The US is the sole exception, and for an unflattering reason rather than a promising one:
College Scorecard is institution-level, so `department_name` is the constant
`"institution-level"` and its solo model has almost nothing to split on. Pooling gives it
mild regularisation. That is a symptom of weak US features, not evidence for pooling.

**What would change this verdict:** a shared programme taxonomy mapping
`Bilgisayar Mühendisliği` / `Kompüter mühəndisliyi` / US CIP codes onto one canonical
field. Then "medicine is competitive everywhere" could genuinely transfer and pooling
would deserve a re-test. That is curation work, not modelling work, and it is out of
scope for the 15 September delivery.

---

## Context

ADR-0001 makes the match score "headroom above the predicted cutoff". But cutoffs are
expressed in incompatible units across the seven markets, and **one of them runs
backwards**:

| Country | Unit | Direction |
|---|---|---|
| Germany | Abiturnote 1.0–4.0 | **Lower is better** |
| Azerbaijan | DIM score 0–700 | Higher is better |
| Turkey | YKS/YÖS rank *or* score | Rank: lower better. Score: higher better |
| UK | UCAS Tariff points | Higher is better |
| USA | SAT/ACT percentile | Higher is better |

Meanwhile the student arrives with an Azerbaijani school GPA, and the results page has
to rank a German and a Turkish programme in **one list**.

Two distinct problems hide here, and conflating them is the trap:

1. **Converting a student's grade into a target country's scale** — e.g. Azerbaijani
   grade → German Abiturnote. This is a *published deterministic formula* (the Bavarian
   formula and its equivalents). It is arithmetic, not inference.
2. **Predicting where that country's cutoff will land.** This is the learned part.

## Decision

**1. One tree model per country**, each predicting cutoffs in that country's native
units. No model ever reasons across scales.

**2. Grade conversion is deterministic and lives outside the model.** Published
conversion formulas, implemented as plain code in the deterministic layer, consistent
with ADR-0001's rule that the model never touches eligibility. Conversion is arithmetic;
prediction is learned.

**3. Cross-country ordering happens after prediction**, by converting each programme's
headroom into a **within-country-year percentile**. Percentiles are comparable across
scales and directions; raw headroom is not.

**4. The country model is a pluggable interface.** Adding a country means adding a
model plus a conversion function, not changing the ranking pipeline.

## Consequences

**Good**

- Each model stays faithful to how its country's admission system actually works.
- Models are independently evaluable — a weak Germany model is visible rather than
  hidden inside a pooled average (see ADR-0003).
- The direction problem (Germany's inverted scale) is handled once, in that country's
  model and conversion, instead of leaking into shared ranking code.
- Countries with no usable cutoff data degrade to `admission_type = open` and
  deterministic ranking without blocking anything else.

**Bad / risky**

- Up to seven models to train, evaluate, version and retrain.
- Countries with thin data cannot borrow signal from richer ones, which a single
  pooled model would have allowed.
- Percentile normalization needs a sufficient sample per country-year to be stable;
  with few curated programmes per country, percentiles will be coarse. This is
  acceptable for ordering but must not be presented as precision.
- Grade conversion formulas are themselves approximations, and errors there propagate
  into every ranking for that country.
