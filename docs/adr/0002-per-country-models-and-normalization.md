# ADR-0002 — One model per country, normalize after prediction

**Status:** Accepted
**Date:** 2026-08-23
**Depends on:** [ADR-0001](0001-cutoff-prediction-replaces-weighted-scoring.md)

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
