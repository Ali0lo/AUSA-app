# ADR-0001 — Cutoff prediction replaces weighted scoring

**Status:** Accepted
**Date:** 2026-08-23
**Supersedes:** the scoring design in `architecture-decisions.md` §4

---

## Context

The course requires a tree-based ML model in the matching and scoring path, replacing
hand-coded logic. The existing engine (`backend/app/services/matching/engine.py`) uses
three hand-set weights — academic 0.50, budget 0.30, language 0.20 — that nobody
calibrated against anything. `architecture-decisions.md` already listed the scoring
formula as an open question.

The obvious ML framing is a supervised classifier predicting `P(admitted | student,
program)`. **We rejected it, because the training labels do not exist.** There is no
public dataset of Azerbaijani students' admission outcomes; there is none for Turkish
students either. Erasmus+ publishes participant-level data but only for students who
were *already placed*, so it carries no label. The `admitted_profiles` table in
`docs/schema.sql` cannot supply one either — it stores admitted students only, with no
rejections and no outcome flag, and a classifier trained on positives alone learns
nothing.

The decisive finding came from the target country list. **The seven priority countries
do not share one admission mechanism:**

| Country | Mechanism |
|---|---|
| Germany | NC — a cutoff *grade*, defined as the Abiturnote of the last applicant admitted last round, refloated each intake. Most non-NC programmes admit anyone meeting formal requirements |
| Turkey | YÖS/YKS score, quota plus rank cutoff |
| Azerbaijan | DIM state exam, score cutoff |
| Poland | Recruitment-points threshold |
| UK | Offers on grades; UCAS publishes accepted-grade profiles and offer rates per course |
| USA | Holistic, but College Scorecard publishes admit rates and SAT/ACT percentile bands |
| China | Documents plus institutional discretion |

Five of seven admit by threshold. Modelling `P(admit)` would have modelled a mechanism
that does not exist in most of the portfolio — and for Germany and Azerbaijan,
deterministic rules are not a shortcut to be replaced by ML, they are an accurate
description of how admission actually works.

## Decision

**1. The model predicts the next intake's admission cutoff, not a student's admission
probability.** Target: a per-programme, per-intake cutoff value. Tree-based regression.

**2. The match score is headroom above the predicted cutoff** — the student's converted
score minus the predicted cutoff — replacing the 0.50/0.30/0.20 weights entirely.

**3. ML ranks; it never decides eligibility.** Hard filters (degree level, deadline
passed, language minimum, net cost over budget) stay deterministic SQL. A tree that
admits a student below a stated IELTS minimum because similar profiles got in is a
product-destroying bug, and `architecture-decisions.md` §1 is right that a student told
they qualify for something they don't will not come back.

**4. Programmes are classified by admission regime**, via a new `admission_type` column:

| `admission_type` | Reality | Ranked by |
|---|---|---|
| `open` | Meet requirements → admitted | Deterministic headroom above formal minimums; labelled "not competitive" |
| `cutoff` | NC / YÖS / DIM threshold | **The ML model** |
| `competitive` | Holistic review | Deferred; labelled honestly |

**5. Absolute admission probabilities are never displayed.** Bands and ordering only.
Two independent reasons: the training cohort is not Azerbaijani, and published cutoff
history is a forecast target rather than a calibrated probability.

## Consequences

**Good**

- The labelling problem disappears. Cutoff history is published by every priority
  market; no student outcome data is needed at all.
- Training data is recent, legally clean and free — Turkey's YÖK Atlas set is
  MIT-licensed; College Scorecard is US federal open data.
- The output is more useful than a percentage: *"last year's cutoff was 2.1, it has
  risen ~0.1/year, we forecast 1.9, your converted grade is 2.0 — borderline."*
- Explanations need no SHAP for students, because a cutoff is an intrinsically
  meaningful quantity (see ADR-0004).
- Ranking stays cheap and inference-free at request time (ADR-0004).

**Bad / risky**

- **Coverage risk.** Most German programmes are non-NC. If the curated catalogue skews
  toward tuition-free open-admission programmes — exactly what Azerbaijani students
  gravitate to — the model touches a minority of it and the course requirement is met
  only on paper. This must be measured in week one of curation (open question B3).
- `competitive` programmes get no model at all for now.
- `admitted_profiles` becomes obsolete and is replaced by `program_cutoff_history`.
- The USA source is institution-level and undergraduate-focused, not programme-level.

**Neutral**

- Hard filters remain rule-based. Confirmed acceptable for the course (open question C1).
