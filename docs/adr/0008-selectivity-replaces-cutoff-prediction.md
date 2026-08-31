# ADR-0008 — The model predicts selectivity for the international route, not domestic cutoffs

**Status:** **Accepted** (31 August 2026)
**Date:** 2026-08-31
**Amends:** [ADR-0001](0001-cutoff-prediction-replaces-weighted-scoring.md), [ADR-0002](0002-per-country-models-and-normalization.md), [ADR-0007](0007-three-number-model-and-honesty-tiers.md)

---

## Context

ADR-0001 replaced hardcoded weighted scoring with cutoff prediction, and that reasoning
still holds: there are no labelled student-outcome data, so a `P(admit)` classifier would
have to be trained on invented labels. ADR-0007 §3 built on it, grouping results by whether
`P(next year's cutoff ≤ your score)` is available for a country.

**Both assumed the student is measured against the published cutoff. For our users, in
every one of our five destinations, they are not.**

Published thresholds describe the **domestic** admission route:

- **Turkey.** YKS cutoffs — 115,482 rows, the largest corpus in this project — rank Turkish
  students competing in the domestic pool. An Azerbaijani applicant enters through the
  international quota, YÖS, SAT or protocol, and is never ranked against a YKS score.
- **Germany.** Verified 31 August on Marburg's own Auswahlgrenzen page: the published tables
  carry the footnote *"Anzahl der gültigen Bewerbungen (ohne Bildungsausländer\*innen)"* —
  application counts **excluding** international applicants. Non-EU applicants are allocated
  from a separate quota, roughly 5–8% of places.
- **Poland.** `Próg punktowy` is the state-funded matura route. International admission is a
  separate, generally less competitive and often fee-paying track.

This is structural, not a coverage gap. Collecting more published cutoffs does not fix it,
because the number being collected describes a different population from the user.

**The corpus that does describe admission directly was misfiled as broken.**
`data/processed/usa_cutoff_history.csv` is US College Scorecard (Department of Education),
and it failed the Task 2 loader only because its schema is not the cutoff schema:

```
1,853 institutions × 9 years (2016–2024) = 14,798 rows
admission_rate      14,798 / 14,798 non-null   — a real published acceptance rate
SAT p25/p75/avg     10,288 rows carry both rate and SAT
1,417 institutions have the full 9-year panel
```

It has real admission labels, a nine-year panel, and SAT percentiles — the exam our students
actually sit.

**And German international-quota outcomes are published, at least sometimes.** The same
Marburg page carries a separate `Zulassungsverfahren der Ausländer*innen` section with its
own per-programme values (Humanbiologie 1.6 for WS 2025/26, 1.4 for WS 2024/25) and, for
many programmes, the outcome *"Es konnten alle Bewerbungen zugelassen werden"* — every
application admitted. How many universities publish this, and how far back, is unmeasured.

---

## Decision

### 1. The ML target becomes selectivity, not next year's cutoff

Trained on the College Scorecard panel, where `admission_rate` is a real label, and
generalised to institutions and countries that publish no rate — a cold-start problem, which
is where the existing CatBoost work already beat baselines by 63.6%.

Cutoff prediction is **retired as a user-facing number.** The infrastructure is not retired:
the CatBoost setup, `MultiQuantile` quantile fitting, year-based splitting, the calibration
harness and the `program_cutoff_history` schema all carry over unchanged. Admit rate is a
different target on the same panel shape.

### 2. Three numbers, and only the middle one is learned

| Number | Mechanism | Source |
|---|---|---|
| **Eligibility** | Deterministic rules | Your IELTS/SAT/GPA against stated minimums, tuition, deadline |
| **Selectivity** | **ML** | Trained on published admit rates; predicted where none is published |
| **Where you sit** | Arithmetic | Your SAT against the admitted p25–p75 band |

This preserves ADR-0007 §1's separation of mechanisms and its rule that fit never becomes a
system-weighted formula. What changes is only what the middle number *is*.

### 3. YKS data stays, relabelled

Turkey's 115,482 rows remain in the repository as a **competitiveness proxy for ranking**,
clearly labelled as the domestic route, and are never shown as a chance for an Azerbaijani
applicant. ADR-0007 §3's "How hard it is" block is the right home for it; the block's
justification changes from "cutoffs exist but not for your route" to the same fact stated
positively.

### 4. Five destinations. Azerbaijan becomes a separate future section

**Turkey, Germany, the UK, the USA, Poland.**

Azerbaijan and the DİM corpus are deferred to a **separate product surface** answering a
different question — "where can I go *here*" — and are not folded into the abroad flow. This
supersedes ADR-0007 §3's 30 August correction, which demoted Azerbaijan to "score
calibration" within the same flow. The corpus is valuable and is kept; it is simply not this
product. The `attestat → Abiturnote` conversion is unaffected: it takes the school-leaving
certificate, not the DİM score.

### 5. Scholarships are ranked, not merely listed

Results can be sorted and filtered funded-first. This follows from the data rather than from
preference: the College Scorecard admission-rate distribution is

```
mean 0.698   median 0.737   p25 0.579   p75 0.863
```

For most institutions an eligible applicant is admitted. **Admission is not the bottleneck;
funding and visa are.** A platform that matches students to affordable and funded options is
worth more than one that predicts admission probabilities for a decision that mostly is not
close. ADR-0005's scholarship-pass-before-budget-filter ordering already anticipated this and
is unchanged.

### 6. Collection re-aims at the international route

What we collect is what the student is measured against: **international-route requirements**
— IELTS/TOEFL and SAT minimums, GPA minimums, Studienkolleg or foundation-year needs,
tuition, deadlines — for Germany, Poland, Turkey and the UK.

The German survey's question changes accordingly. Not *"how deep is this university's NC
archive"* but **"does this university publish its international-quota outcome, and how far
back"**. `docs/reference/germany-nc-sources.md` is corrected to match.

---

## Consequences

**Good**

- The model is trained on labels that describe the population it serves. That was not
  previously true of any model in this project.
- Real supervised data exists today, in the repository, with a nine-year panel — no
  collection is on the critical path for the ML.
- "All applications admitted" is a fully honest answer, and now the design has somewhere to
  put it.
- The product matches what consultancies actually do: filter by eligibility, sort into
  reach/match/safety, then advise on money and documents.

**Bad**

- `admission_rate` is an **overall** rate, not an international one. Selective US
  institutions typically admit international applicants at a lower rate, and Scorecard does
  not break this out. Every US selectivity figure must be labelled as institution-wide.
- Scorecard is institution-level. There is no programme dimension, so US results answer at
  the institution and say so — the same honest exception ADR-0007 §9 already records.
- ADR-0007 §3's "Your chances" block, as written, no longer has a country that qualifies on
  its original terms. The block is redefined by decision 2 rather than filled.
- Some ML work aimed at cutoff forecasting is now scaffolding rather than product. The
  measured results stand and are still reportable — including that persistence beat CatBoost
  on Turkish forecasting at 13.77 MAE, which is itself a reason the point-prediction framing
  was weak.

**Open**

- How many German universities publish international-quota outcomes, and how deep. The
  survey answers this.
- Whether UK offer rates can be collected at programme level or only institution level.
- Whether "all admitted" outcomes are frequent enough across countries to become their own
  display state rather than a selectivity value of 1.0.
