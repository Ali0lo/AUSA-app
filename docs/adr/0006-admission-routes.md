# ADR-0006 — Admission routes: programs accept several qualifications, not one

**Status:** **Accepted** (29 August 2026) — G1–G4 answered in
[`../open-questions.md`](../open-questions.md).
**Date:** 2026-08-28, accepted 2026-08-29
**Amends:** [ADR-0001](0001-cutoff-prediction-replaces-weighted-scoring.md), [ADR-0002](0002-per-country-models-and-normalization.md)

---

## Context

ADR-0001 models one cutoff per (program, intake) and defines the match score as the
student's converted score minus that cutoff. That assumes **each program admits on a
single entrance qualification.** Most do not.

A Turkish university may admit international applicants on **SAT ≥ 1200 *or* YÖS ≥ 60**.
A German program may accept a converted Abiturnote *or* a Studienkolleg
Feststellungsprüfung result. These are genuine alternatives, each with its own cutoff
and its own competitiveness.

### Two axes, and only one of them is a gap

**Axis A — entrance qualification.** DIM, YÖS, SAT, Abiturnote, UCAS tariff, IB.
Alternatives, **competitive**, each with a cutoff. *This is the gap.*

**Axis B — language proficiency.** IELTS *or* TOEFL *or* Duolingo *or* TestDaF *or* an
institutional test. Also alternatives, but these are **pass/fail thresholds, not
competitive cutoffs** — scoring IELTS 8.0 against a 6.5 requirement does not make an
applicant more admissible.

**Axis B is already handled correctly.** ADR-0001 put language in the deterministic
Layer 1 hard filter precisely because it is a constraint rather than a likelihood
signal. Supporting several accepted certificates only changes the filter from
`IELTS >= X` to *"satisfies any one of the accepted certificates"*. No ML involved,
no ADR change needed.

### Why this matters more for AUSA than for a general product

It is not an edge case here, it is the main case.

An Azerbaijani student applying to a Turkish university does **not** sit YKS. They
apply through **YÖS** or the **international quota**, and many Turkish universities
accept **SAT** from international applicants. Those cutoffs are entirely separate from
the domestic YKS figures.

This sharpens a caveat already recorded in `data-collection-plan.md`: the 115,482 rows
of YKS cutoff history we collected describe **a route our users will never take**. The
data remains valid as ML training material and as a program-selectivity signal, but the
product must never present a YKS cutoff to an Azerbaijani student as "the score you
need".

## Proposed decision

**1. An admission route becomes a first-class entity.** `program_cutoff_history`
already carries `cutoff_unit` (`yks_score_012`, `dim_score`, `sat_p25`, `abiturnote`),
so it is *already* keyed by qualification type — it simply does not permit more than
one row per (program, intake). The natural key becomes:

```
(program_id, intake_year, qualification_type)
```

Each row is then one route, with its own cutoff, its own history, and its own
`lower_is_better` polarity.

**2. The student profile holds several qualifications.** `students` currently has only
`gpa`, `ielts`, `toefl` — no SAT, DIM, YÖS, IB or A-levels. A student holds a *set* of
qualifications, and which routes are open to them follows from that set.

**3. Match score is the best headroom across routes the student is eligible for.** A
route the student holds no qualification for is not scored and not counted against them.

**4. The route is shown, not hidden.** The output becomes a genuinely useful answer:

> *"Your SAT 1350 clears this program's SAT route (predicted cutoff ~1200). Your DIM
> score would not qualify on the DIM route. Apply via SAT."*

Nobody presents route choice clearly today, and it is the question students actually
have.

**5. Routes with no published cutoff history fall back to the ADR-0001 taxonomy** —
`admission_type = open` or `competitive`, ranked deterministically and labelled
honestly. They are never given an invented cutoff.

## Consequences

**Good**

- Models how admission actually works for our users, rather than for domestic applicants.
- Route recommendation is a differentiating feature, not just a correctness patch.
- The schema change is small — the discriminator column already exists.
- Reinforces the ADR-0001 split: language stays a deterministic filter, entrance
  qualification stays the learned ranking signal.

**Bad / risky**

- **The route with the best data may be the one nobody uses.** YKS cutoffs are
  published in bulk; YÖS and SAT-route cutoffs for international quotas frequently are
  not published at all. This is the central tension and it does not have a clean answer.
- Student intake gets longer — capturing several qualifications is more form-filling,
  which conflicts with the deliberately minimal Phase 1 intake in
  `architecture-decisions.md` §5.
- More rows per program to curate and to human-verify.
- Per-route models fragment already-thin data.

**Consequence worth stating plainly**

The ML deliverable is likely to be trained on the data that exists (YKS, College
Scorecard — real, recent, defensible, gradeable), while the *product* serves routes we
may only be able to rank deterministically. That is an acceptable and honest split, but
it should be a **stated decision recorded here**, not something discovered while writing
the final report.

## Accepted scope (29 August 2026)

### The finding that shaped it

Research on 29 August established that **DIM has signed recognition protocols with
Turkish universities**: an Azerbaijani student can apply to some of them on their DIM
score alone, with no YÖS and no SAT. DIM is therefore not merely the home-market
qualification — it is also a Turkey route. That single fact makes DIM the best value
per unit of collection effort in the whole project, and it inverts the priority the
draft assumed.

### The route matrix

Routes are not one-per-country. A qualification opens routes in several destinations:

| Student holds | Azerbaijan | Turkey | Germany | USA |
|---|---|---|---|---|
| **DIM** (0–700) | native cutoff | **protocol universities** | — (→ Studienkolleg) | — |
| **Attestat GPA** | — | private universities | → Abiturnote, Bavarian formula | GPA |
| **SAT** | — | international quota | — | native |
| Language (IELTS / TOEFL / TÖMER / TestDaF) | pass/fail | pass/fail | pass/fail | pass/fail |

**Three routes are in scope: DIM, SAT, attestat GPA. YÖS is dropped** — its per-programme
cutoffs are rarely published, so collection cost is high and the resulting data thin.

### Two kinds of calculation, and they must not be blurred

1. **Conversion is arithmetic.** Attestat → Abiturnote uses the KMK-recognised Modified
   Bavarian formula, `(Nmax − Nd) / (Nmax − Nmin) × 3 + 1`, the same one uni-assist
   applies. ADR-0002 already forbids learning this: compute it.
2. **Cutoff prediction is ML.** What score actually clears the bar on that route.

A student's qualifications are evaluated against **every route they open**, across every
destination — but the conversion layer and the prediction layer stay separate.

### Intake (G2)

One optional "which of these do you have?" step: DIM, attestat GPA, SAT, plus language
certificates. A route the student holds no qualification for is **not scored and never
counted against them** — absent, not zero.

### Routes without published cutoffs (G3)

Shown as `admission_type = competitive`, labelled *"requirements known, competitiveness
unknown"*. Applies immediately to the Turkish international-quota SAT route. A cutoff is
never invented to fill the gap — the ADR-0004 no-fabrication rule, applied to the UI.

### Trained-on versus served (G4)

- **Trained on:** YKS (Turkey) and College Scorecard (USA); DIM once collected.
- **Served:** DIM, SAT, attestat GPA.
- **Trained only, never served:** YKS. **No product route uses it.**

YKS earns its place as a **selectivity signal** — how competitive a Turkish programme is
relative to its peers — which is what the selectivity index needs, and which transfers
across routes even though the raw score does not. This limitation is stated here so it
is quoted, not discovered, when the report is written.
