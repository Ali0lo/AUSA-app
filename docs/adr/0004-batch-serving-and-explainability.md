# ADR-0004 — Batch-precomputed predictions, two-audience explanations

**Status:** Accepted
**Date:** 2026-08-23
**Depends on:** [ADR-0001](0001-cutoff-prediction-replaces-weighted-scoring.md)
**Amended by:** [ADR-0007](0007-three-number-model-and-honesty-tiers.md) — rule 2's
two provenance states become three (`seed` / `claude-extracted` / `human-verified`), and
rule 1's precomputed row gains the quantile ladder and `model_run_id`. Neither decision
here is reversed; see ADR-0007 §5 and §7 for what changed and why.

---

## Context

**Serving.** A cutoff is a property of a *programme and an intake*, not of a student.
Nothing about the prediction depends on who is asking, and cutoffs change roughly once
per intake cycle. Running inference in the request path would add a model server,
latency and a runtime failure mode for a value that changes once a year.

**Explainability.** `architecture-decisions.md` §7 promises every result shows why it
matched, "in plain language, straight from the deterministic filters." A tree ensemble
is not plain language. But ADR-0001's pivot bought something: because the model
predicts a *cutoff* — an intrinsically meaningful quantity — the prediction can be
explained without explaining the model. Under the rejected `P(admit)` framing, the only
explanation available would have been feature attributions, which students cannot read.

**Silent fallbacks.** The inherited code (`backend/app/data_pipeline/extraction.py`)
wraps its LLM call in a bare `except Exception` and, on failure, returns fabricated
values — `university_name="Extracted University"` — with an invented confidence score.
For a product whose stated risk is a student missing an application because of wrong
data, silently fabricating is the most dangerous pattern in the repository.

## Decision

**1. Batch precompute.** An offline job runs per intake cycle, predicts every
programme's cutoff, and writes `predicted_cutoff`, `predicted_cutoff_confidence` and
`predicted_at` onto the `programs` row. **The request path is pure SQL with zero
inference.** No model server, no feature store, no latency budget.

**2. No silent fallbacks, ever.** If a prediction is missing or stale, the programme
falls back to its **last known actual cutoff, explicitly labelled as such**, or drops
to deterministic-only ranking and says so in the UI. It never quietly guesses. This
rule applies to the inherited extraction and RAG code as well, which must be fixed.

**3. Two explanation audiences.**

| Audience | Sees | Purpose |
|---|---|---|
| **Students** | Past cutoffs, forecast cutoff, their converted score, resulting headroom band | Plain language, honours §7 |
| **Team / course report** | SHAP values, feature importance, per-country metrics | Debugging, drift monitoring, interpretability section |

Model internals never reach the UI. SHAP is a debugging and reporting tool, not a
student-facing feature.

**4. Predictions are traceable.** Every `predicted_cutoff` can be traced to the model
artifact and training run that produced it.

## Consequences

**Good**

- Keeps the promise in `university-matching-platform-notes.md` §3 that matching stays
  cheap and free of inference cost — a promise the LLM-in-the-loop design was straining.
- No serving infrastructure at all, which matters for a four-person team on a deadline.
- Rankings are auditable: the exact cutoff that produced a result is stored, not
  recomputed and possibly different.
- The §7 plain-language promise survives ML entirely intact.

**Bad / risky**

- Predictions are only as fresh as the last batch run. Acceptable for annual cutoffs;
  would not be for anything faster-moving.
- Newly curated programmes are not rankable by the model until the next batch run.
  Mitigated by the cold-start handling in ADR-0003, but a real gap.
- Two explanation paths to build and keep consistent.
- The no-fallback rule means the UI must have real "we don't know" states, which is
  more design work than silently showing a number.
