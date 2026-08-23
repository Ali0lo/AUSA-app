# ADR-0003 — Temporal + cold-start evaluation against a persistence baseline

**Status:** Accepted
**Date:** 2026-08-23
**Depends on:** [ADR-0001](0001-cutoff-prediction-replaces-weighted-scoring.md), [ADR-0002](0002-per-country-models-and-normalization.md)

---

## Context

Two failure modes make an ML model look successful while being worthless. Both are
easy to fall into and both would survive casual review.

**Leakage through random splits.** The model forecasts the *next* intake's cutoff.
Under a random train/test split, 2024 for a programme can land in train while 2023
lands in test — the model sees the answer's neighbour. Random k-fold on a time-series
target produces excellent, meaningless scores.

**No baseline.** Cutoffs are strongly autocorrelated year to year. The naive predictor
`next_cutoff = last_cutoff` is already a strong model. **If gradient-boosted trees
cannot beat one line of code, the model has no value** — and reporting accuracy without
that comparison hides exactly that fact.

There is also a second generalization question a temporal split does not answer.
Programmes are hand-curated and added continuously, and many will have **no cutoff
history at all**. "Can it forecast next year for a programme it knows" and "can it
estimate a cutoff for a programme it has never seen" are different abilities. Only the
second determines whether newly added programmes can be ranked.

## Decision

**1. Temporal split.** Train on 2019–2022, validate on 2023, test on 2024. Never
random, never shuffled across years.

**2. Cold-start split.** A second evaluation holding out **entire programmes**, so the
test set contains programmes with zero history. Measures whether newly curated
programmes are rankable.

**3. Persistence baseline is mandatory and reported everywhere.** `next = last` is the
number every model must beat. Primary metric: MAE in native units.

**4. Metrics are reported per country, not pooled**, so a weak model cannot hide behind
a strong one — consistent with the per-country models in ADR-0002.

**5. "The baseline won" is a publishable result.** If persistence beats the trees, the
honest response is to ship persistence and report it, not to tune until the number
looks better. See open question C4 for whether the course grades this as failure.

## Consequences

**Good**

- Reported performance reflects real forecasting ability.
- The cold-start number tells the team directly whether curation can outrun the model.
- The persistence comparison is the first thing a reviewer or grader will ask for, and
  it is built in rather than retrofitted.
- Per-country reporting surfaces which markets the model actually helps in.

**Bad / risky**

- Two evaluation harnesses instead of one.
- Countries with few programmes will produce unstable metrics on small test sets;
  these must be reported with sample sizes, not as bare numbers.
- The temporal split consumes the most recent year as test data, so it cannot be used
  for training — costly when history is short.
- A genuine risk that the trees do not beat persistence. This is known in advance and
  accepted; it is a finding, not a bug.
