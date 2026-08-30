# ADR-0007 — Three numbers, honesty tiers, and the LLM/ML contract

**Status:** **Accepted** (30 August 2026) — seventeen decisions taken in a grilling
session on 29–30 August.
**Date:** 2026-08-30
**Amends:** [ADR-0001](0001-cutoff-prediction-replaces-weighted-scoring.md),
[ADR-0004](0004-batch-serving-and-explainability.md),
[ADR-0006](0006-admission-routes.md)
**Supersedes:** nothing. Every decision here refines an existing ADR or covers ground
none of them reached. The reasoning in 0001 in particular must survive intact — without
it, a later reader re-proposes the `P(admit)` classifier that 0001 rejected.

---

## Context

Three things forced this ADR.

**1. Success rate and fit were being conflated.** ADR-0001 produces one number per
programme and the product treated it as the answer. It is not: a student can have a 100%
success rate at a hundred programmes, which tells them nothing about which to choose.

**2. The catalogue, not the model, is the bottleneck.** Verified in code on 29 August:
`programs` holds **7 hardcoded seed rows**, `program_cutoff_history` **does not exist as a
table**, and 127,000 rows of collected cutoff history live only as CSVs. `students` has
`gpa`, `ielts` and `toefl` and no entrance qualifications at all. We have cutoffs without
requirements and requirements without cutoffs, and **the two datasets do not join.** The
modelling is nearly finished; the catalogue barely exists.

**3. Real consultancies do this differently than we assumed.** A knowledge base on
Azerbaijani study-abroad agencies (`../reference/study-abroad-agencies-azerbaijan.md`)
describes a seven-stage workflow whose stage 1 is a **profile audit** — GPA, exam
certificates, budget and destination preference gathered *together* — and whose stage 2
stratifies into **Safety / Match / Reach.** Two findings from it shaped decisions below:
the industry already uses our band vocabulary, and five of its seven stages are document,
portal and visa work that no cutoff model produces.

The same document supplies the positioning. Agencies take 10–30% commission from partner
universities, and its §4 records the consequences: students steered toward fee-paying
private institutions and away from tuition-free public ones, and automatic international
discounts rebranded as "exclusive agency scholarships." **AUSA takes no commission.** That
is not a marketing line here — it is the reason several decisions below went the way they
did.

---

## Decision

### 1. Three numbers, three mechanisms

| # | Number | Mechanism | Honest about |
|---|---|---|---|
| **Eligibility** | Do you meet the stated requirements? | Deterministic, from curated requirements | Binary, never guessed |
| **Success rate / selectivity** | Can you get in? How hard is it? | **ML** — cutoff regression (ADR-0001) | Differs per country, see §3 |
| **Fit** | Does it match your goals? | **User-controlled** filters and sort | The student's preference, not our judgment |

**Fit must never become a system-weighted formula.** There are no preference labels to
learn from, and inventing weights re-creates precisely the hardcoded scoring ADR-0001
exists to remove. The course's ML requirement rests entirely on the second number.

**Default ordering: hardest-you-can-still-get first.** A student sorted safest-first sees
places they are overqualified for. Sorted by the most competitive option where they still
have a real chance, they see the actual decision in front of them.

### 2. Two modes over one spine

**Discovery.** One profile step — exam scores, GPA, budget, destination preference, field
— with results refining live as fields are filled. Mirrors the agencies' stage 1.

**Target (Mode B).** The student names a university and receives a gap statement, a
requirement checklist, a process checklist and alternatives that close the gap.

Neither mode is a wizard. One page, results always visible, and before any input the page
shows the most competitive or most popular programmes in the field so it is never empty.

**Destination is asked first and never excludes.** Asking it first matches what students
expect and what consultancies do. Gating on it does not: a filter that hides options is
the steering behaviour §4 of the reference criticises, implemented in software. Chosen
countries fill the main results; a persistent "your score goes further here" section
surfaces the strongest matches from countries the student did not name. That is the
renegotiation a human consultant performs, and it is the product's highest-value output.

**Mode B excludes a study plan.** "You are 68 points short" is supported by the data.
"Retake DIM in March, target +70, focus on maths" is not — nothing in any dataset links
effort to score change. The roadmap is a gap, a checklist, a deadline and alternatives.

### 3. Results group by what we can tell you, not by geography

The second number does not mean the same thing everywhere. Ranking a genuine success rate
against a selectivity percentile in one list is misleading, and sorting them against each
other is worse. Three blocks, three card types, one-to-one:

| Block | Countries | Second number | Why |
|---|---|---|---|
| **Your chances** | Azerbaijan, Germany, Poland | Genuine success rate | Admission is mechanical — clearing the cutoff *is* admission, so `P(next year's cutoff ≤ your score)` is not a proxy for the success rate, it **is** the success rate |
| **How hard it is** | Turkey | Selectivity only | Cutoffs are published for the domestic YKS route; Azerbaijani applicants enter by protocol, SAT or attestat, and those cutoffs are not published (ADR-0006) |
| **Requirements only** | USA, UK, **all scholarships** | None | USA admits holistically and publishes no field dimension; the UK publishes *stated* entry requirements, not realized cutoffs, so there is nothing to regress on; funded scholarships select by committee |

Each block header states its own limit. Country is a filter chip inside the blocks.

**The UK ships with no second number and says so.** That is a deliberate demonstration
that the design degrades honestly rather than an omission to hide.

### 4. Coverage

Six countries. Five carry a second number; the UK does not.

Requirements are extracted for **~90 universities**, split **~55 by destination** (where
Azerbaijani students actually enrol) and **~35 by aspiration** (the names students type
into Mode B — Boğaziçi, METU, TU Munich, LMU, Warsaw, UCL). The two lists barely overlap,
and per the reference's §4 that gap *is* the industry's problem: agencies profit from
where students end up, not from where they hoped to go. Both criteria are stated in the
report.

**A named university we do not hold produces a plain "we don't have this yet" and what we
do hold for that country.** Never a guessed cutoff, never a silent substitution of
something adjacent.

### 5. Provenance has three states

ADR-0004 rule 2 forbids silent fallbacks and implies two states: `verified_by` set, or
empty. Extraction at this scale needs three.

| State | Meaning |
|---|---|
| `seed` | Hand-entered during development. Not evidence of anything |
| `claude-extracted` | Pulled from a named source page by the extraction pipeline. Carries `source_url` and `fetched_at` |
| `human-verified` | A person opened the source and confirmed the row. Only a person can set this |

**An LLM's self-reported confidence never promotes a record.** Low confidence flags a row
for review sooner; it cannot move it toward verified.

**Unverified requirements filter, but never silently.** Every exclusion appears in a
collapsible *"filtered out (N)"* panel with the reason, the source URL and the provenance
badge. The asymmetry that forces this:

- A **false inclusion** — we say you qualify, you don't — is visible. The student sees the
  programme, checks it, finds we were wrong. Recoverable.
- A **false exclusion** — we say you don't qualify, you do — is **invisible**. The
  programme never appears, the student never learns it existed, and a mis-extracted
  "IELTS 7.0" that is really 6.0 quietly deletes their best option. Unrecoverable, and it
  is the exact harm ADR-0001 exists to prevent.

### 6. The LLM/ML contract is by claim type, not by layer

Not every requirement is a number. "A Studienkolleg year is required unless your attestat
is recognised" is a real, decision-changing requirement that no template can compose and
no gap statement can express. So the guarantee differs per claim:

| Claim type | Producer | Guarantee |
|---|---|---|
| **Numeric** | **ML model only** | Every numeral in generated output must appear in the structured payload. If one does not, the response is **rejected, not repaired** |
| **University-specific qualitative** | LLM, grounded in the extracted page | **Cite or drop.** Source URL shown to the student, provenance badge attached. Uncited sentences are stripped before display |
| **Country process** | LLM, from a curated per-country library | Written once per country from the reference's stages 3–7, reviewed, reused. Not generated per query |
| **Framing and explanation** | LLM, freely | Rephrases fields that are already on screen. No factual claims |

**No number reaches a student unless a model produced it.** An LLM asked "what is the
cutoff for Boğaziçi Computer Engineering?" will produce a fluent, confident, entirely
invented figure indistinguishable from a real one. The numeral check makes that
structurally impossible rather than discouraged.

A hallucinated *qualitative* requirement is no less harmful: telling a student they need a
foundation year they do not need can cost them a year and thousands of manat. Hence
cite-or-drop rather than a disclaimer.

### 7. One model, one stored number, read by both modes

Extends ADR-0004 rule 1. The batch job writes onto each programme row:

```
predicted_cutoff   p10  p25  p50  p75  p90   band_thresholds   model_run_id
```

`model_run_id` resolves to an entry in `models/metrics.json`, satisfying ADR-0004 rule 4.

Both modes read that row. Neither calls the model at request time — and not only for
latency. If discovery read a precomputed value while Mode B recomputed live, the two could
disagree about the same programme: "648" in the list, "651" on the detail page. That
inconsistency is visible, unexplainable, and fatal to a product whose entire claim is
honesty. It is also what the §6 numeral check validates against; a number computed
elsewhere has no stable payload to be checked against.

What differs between the modes is use, not model:

| | Discovery | Mode B |
|---|---|---|
| Prediction | sort key and band assignment | the headline sentence |
| Extra arithmetic | none | `gap = predicted_cutoff − student_score` |

### 8. CatBoost ships; bands ship; the percentage is gated on evidence

**CatBoost is the served model**, for point estimates and for the quantile ladder via
`MultiQuantile`. Measured on Turkish cold start over 7,324 unseen programmes:

```
department-mean baseline        38.96
HistGradientBoosting (codes)    18.93   +51.4%
CatBoost (native categoricals)  14.18   +63.6%   → +25.1% over HGB
```

The cause is not tuning. `.cat.codes` tells a tree that university #47 sits between #46
and #48, which is false; CatBoost's ordered target statistics handle high-cardinality
categoricals properly. With 733 Turkish department names and 29,293 programme identities,
that is most of the signal. Decision Tree, Random Forest and HistGradientBoosting remain
in the comparison against their honest baselines — this amends the C2 answer in
`../open-questions.md`, which specified the three sklearn models.

`MultiQuantile` also fits the quantiles jointly rather than as independent models, which
attacks quantile crossing at its source instead of only sorting afterwards.

**Display.** The band — Safety / Match / Reach, the industry's own vocabulary — is the
headline. The percentage appears only if, after recalibration, empirical coverage lands
within ~2 points of nominal on a held-out year. Measured before the fix:

```
nominal   empirical    error
   0.10       0.098   -0.002
   0.50       0.431   -0.069     ← systematically over-optimistic
   0.90       0.838   -0.062
```

The error direction is the dangerous one: it tells students they are *safer* than they
are, worst in the middle of the range where most students sit. A 6-point shift rarely
crosses a band boundary; it corrupts a percentage outright.

Two fixes, gating different things. **Monotone sorting is required for anything to ship**,
bands included, because the bands are read off the same quantile ladder that currently
produces `p10 = 378.3` alongside `p25 = 375.1`. **Nominal→empirical recalibration**, fitted
on the validation year and inverted at serving, is what gates the percentage specifically.

**Cold-start calibration is measured separately** before deciding whether it needs its own
treatment. A prediction for a programme with no history of its own is inferred from
similar programmes; in discovery a slightly wrong sort position is invisible, but in
Mode B it is the headline number a student acts on. Whether its calibration is materially
worse is an empirical question, and it is answered with a split calibration table rather
than assumed either way.

### 9. Field matching is a labelling problem, not a curation project

Distinct programme names, not programme rows:

```
Turkey      733    (29,293 programmes)
Azerbaijan  238    (1,028 programmes)
USA           0    — no department dimension exists
```

With Germany and Poland, roughly 1,200 strings. One offline LLM pass labels them into
~25 fields, stored as an indexed `field` column; the student's free text maps to a
taxonomy node once per query. Serving is plain SQL — deterministic, free, fast, auditable,
and independent of Azerbaijani being a low-resource language for embedding models.

**The USA has no field dimension at all**, so a field-filtered search returns programmes
elsewhere and *institutions* there. That is the second honest exception alongside the UK's
missing second number, and it is labelled in the card, not hidden.

### 10. Scholarships are a first-class entity

The reference draws a hard line between **partial university discounts** — automatic,
20–50%, granted to meet international quotas — and **fully-funded state programmes**:
100% tuition plus stipend, housing, insurance and flights, selected by independent
committees. Its §4 records the first being routinely sold as the second.

~15 funded programmes are matched by eligibility alongside programmes: Dövlət Proqramı,
Stipendium Hungaricum, DAAD, Türkiye Bursları, Chevening, Fulbright, Erasmus Mundus,
Deutschlandstipendium, Italy's DSU and similar. They publish no cutoffs and select by
committee, so they belong in the *requirements only* block with no new card type.

**This closes Hungary and Italy without their cutoff data** — the two countries recur in
the reference as major routes, and since scholarships carry no second number, listing
Stipendium Hungaricum requires no Hungarian cutoffs.

Partial discounts remain an attribute on the programme row and are **labelled a discount,
never a scholarship**. Where a state programme is free to apply for directly, the product
says so, which is the reference's §6 guidance and something only an unconflicted system
can afford to say.

### 11. Extraction: auto-discover, human-review, script the rest

Requirements are a **university**-level fact — language minimum, accepted foreign
qualifications, tuition tier, deadline and scholarship terms sit on one
international-admissions page covering all of a university's programmes. Only degree level
and field-specific prerequisites vary per programme, and those come from the cutoff data.

```
seeded universities
  → robots.txt (permission check; usually names the sitemap)
  → sitemap.xml → keyword-filtered candidate URLs
  → HUMAN REVIEW → urls.yaml, committed
  → fetch (static first; Playwright only when the response is a JS shell)
  ├─ raw text → chunk → embed → university_documents{content, embedding, source_url, fetched_at}
  │                                    └─ the retrievable source §6 cite-or-drop requires
  └─ LLM extract → strict schema → validate → requirement rows (claude-extracted)
```

**One fetch, two artifacts.** The same page yields the structured fields the filter needs
and the embedded chunks the roadmap cites.

Discovery proposes; a person reviews before any page is used. Auto-discovery across
heterogeneous university sites will confidently select an outdated or wrong page
somewhere, and a wrong page is a wrong requirement — the §5 harm.

**Absent means null, never a default.** If a page does not state an IELTS minimum, the
field is empty and the filter treats it as unknown — not 0, not 6.0. A page that fails to
fetch or parse yields **no row**, and the run reports what it could not get. A short
honest table beats a long invented one.

### 12. Cut order, agreed in advance

If the schedule slips: **Poland first, then the UK, then the gated percentage.** Poland is
the only country here with no data, no collector and no compensating role. Deciding this
now is cheaper than improvising it on 13 September.

---

## Consequences

**Good**

- The three numbers are separable, so each can be honest about a different thing. Nothing
  has to be blended into a single score that means nothing precisely.
- Grouping by epistemic class gives every honest limitation a place to be stated, and
  collapses three card types across six countries into three blocks.
- The numeral check makes fabricated numbers structurally impossible rather than
  discouraged by convention — which matters in a codebase where the fabricate-and-continue
  pattern has now been removed three times.
- Requirements being a university-level fact turns ~800 programme pages into ~90 university
  pages, which is what makes six-country coverage feasible at all.
- Scholarships cost ~15 rows and extend coverage to Hungary and Italy for free.
- The report gains genuine findings either way: a calibration table before and after
  correction, a split by cold start, and a four-model comparison with a clear winner.

**Bad / risky**

- **Three UI surfaces** — discovery, Mode B, scholarship results — plus a "filtered out"
  panel, in sixteen days. This is the largest remaining chunk of work and the most likely
  thing to slip.
- Two exceptions must be explained rather than hidden: the UK has no second number, the
  USA has no field dimension. Honest, but they cost design attention.
- The percentage may never ship. If recalibration does not reach ±2 points, bands are all
  the product shows, and the calibration work lives only in the report.
- Extraction is 2–3 days of Claude's time and cutoff collection for Germany and Poland
  another 1–2, against sixteen days total. If extraction is still running on day six, the
  cut order applies.
- `human-verified` may be empty at submission. The two-tier labelling makes that honest,
  but "nothing here has been checked by a person" is a weak claim, and the fix is hours of
  someone's attention rather than any amount of engineering.

## Open, deliberately not decided here

Two items in the codebase have no decided role and were left for a later session rather
than settled by default:

- **Motivation letter drafting.** `agent/tools.py` ships a hardcoded template producing a
  generic letter. The reference's §4 lists *"Generic & Recycled Motivation Letters"* as an
  industry red flag that admissions boards detect and reject, and its §6 says to advise
  students to write their own. A generator would put AUSA on the wrong side of the
  positioning in §2. A **critique** tool — the student writes, AUSA reviews against that
  programme's extracted criteria — solves the same need from the other side, and is the
  recommendation, not the decision.
- **Stateful application tracking.** `student_applications` exists as a model with no
  migration; stages, missing documents and dossier export exist as code. Whether tracking
  a student's live applications is in scope for 15 September was never decided.
