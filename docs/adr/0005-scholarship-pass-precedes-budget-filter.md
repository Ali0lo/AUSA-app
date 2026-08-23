# ADR-0005 — Scholarship matching runs before the budget filter

**Status:** Accepted
**Date:** 2026-08-23
**Amends:** `architecture-decisions.md` §6

---

## Context

ADR-0001 keeps budget as a Layer 1 hard filter. `architecture-decisions.md` §6 places
the scholarship pass *after* matching, as a second deterministic step whose results are
presented underneath the programme card.

Those two positions produce a bug that destroys the product's stated differentiator.

§6 says the differentiating number is **cost after funding** — *"that is the figure
students actually care about and almost nobody presents clearly."* But if the budget
filter runs first on **sticker tuition**, then a student with a €5,000 budget looking at
a €15,000 programme with a €12,000 DAAD scholarship they are eligible for has that
programme **silently deleted at Layer 1**, before the scholarship pass ever runs.

The single most valuable result the product could produce is the one it filters out.

## Decision

**1. Reorder the pipeline.** Scholarship matching moves before the budget filter:

```
1. Match scholarships to the student        (deterministic, rule-based)
2. Compute best-case cost after funding     per programme
3. Hard filter on NET cost, not sticker     (Layer 1)
4. Rank survivors                            (Layer 2 — see ADR-0001)
```

**2. Both figures are shown** — sticker tuition and cost after funding — so the student
sees what the funding actually changes.

**3. Scholarships stay fully deterministic. No ML.** `data-sourcing.md` calls
scholarship data "the hardest data of the lot". Providers publish eligibility rules but
essentially never publish award cutoffs or applicant volumes, so there is nothing to
train on, and a wrong answer costs a student real money.

**4. Wording stays "possibly eligible", never "guaranteed"**, per §6. Scholarship rules
are full of exceptions, and eligibility is not an award.

## Consequences

**Good**

- The product can actually surface a programme made affordable by funding, which is
  the thing it exists to do.
- Cost after funding becomes a first-class figure in the pipeline rather than a
  presentation detail bolted on at the end.
- Keeps the scholarship domain deterministic and explainable, consistent with ADR-0001.

**Bad / risky**

- Scholarship matching becomes a blocking step in the request path rather than an
  optional enrichment. It must be fast and it must not fail open.
- "Best-case cost after funding" is optimistic by construction — a student may be
  eligible for a scholarship and not receive it. The UI must not let a *possible*
  award read as a *secured* one, or the filter will admit programmes the student
  genuinely cannot afford. This is the mirror image of the bug being fixed and needs
  equal care.
- Requires numeric scholarship amounts. `scholarships.amount` is currently `TEXT`
  (`docs/schema.sql:57`) and `students.budget` is `VARCHAR(50)` (`docs/schema.sql:18`);
  both must become numeric before net cost can be computed at all.
