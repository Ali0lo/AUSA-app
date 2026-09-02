# Architecture Decision Records

Each ADR records one decision: what was decided, why, and what it costs.
They are immutable once accepted — to change a decision, add a new ADR that
supersedes the old one rather than editing it.

| # | Decision | Status |
|---|---|---|
| [0001](0001-cutoff-prediction-replaces-weighted-scoring.md) | Cutoff prediction replaces weighted scoring | Accepted |
| [0002](0002-per-country-models-and-normalization.md) | One model per country, normalize after prediction | Accepted |
| [0003](0003-evaluation-protocol.md) | Temporal + cold-start evaluation against a persistence baseline | Accepted |
| [0004](0004-batch-serving-and-explainability.md) | Batch-precomputed predictions, two-audience explanations | Accepted |
| [0005](0005-scholarship-pass-precedes-budget-filter.md) | Scholarship matching runs before the budget filter | Accepted |
| [0006](0006-admission-routes.md) | Programs accept several qualifications, not one | Accepted |
| [0007](0007-three-number-model-and-honesty-tiers.md) | Three numbers, honesty tiers, and the LLM/ML contract | Accepted |

**Start with [0001](0001-cutoff-prediction-replaces-weighted-scoring.md) for the central
reframe and [0007](0007-three-number-model-and-honesty-tiers.md) for what the product
actually is.** 0007 is the current spec; the five before it are the reasoning that
produced it.

## Background

ADRs 0001–0005 come out of a single design review (2026-08-23) that stress-tested
the plan to replace AUSA's hand-weighted matching engine with a tree-based ML model,
as required by the course.

The review's central finding is recorded in ADR-0001: the seven target countries do
not share one admission mechanism, and five of them admit by **threshold**, not by
holistic review. That reframed the ML target from "predict admission probability" —
which has no available training labels — to "predict the admission cutoff", which
has published training data in every priority market.

ADR-0006 (29 August) added that a programme accepts *several* qualifications, not one.
ADR-0007 (30 August) came out of a second stress-testing session and answers the question
0001 left open: given one predicted cutoff, what does the product actually show a student,
and what is it allowed to claim. Its reference material on how Azerbaijani study-abroad
agencies operate is in [../reference/](../reference/).

Open questions not yet settled are in [../open-questions.md](../open-questions.md).
