# Program Matching Platform — Architecture Decisions

**Purpose:** Help Azerbaijani students find bachelor's, master's and PhD programs — at home and abroad — with real costs and scholarship opportunities surfaced clearly.

**Status:** Pre-MVP. Decisions below are agreed; open questions are listed at the end.

---

## 1. Guiding principle

**Eligibility is deterministic. The LLM only explains and assists.**

A student who is told they qualify for something they don't will not come back. Everything that decides *who gets in* is plain SQL and scoring code — reproducible, debuggable, and switch-off-able. The language model sits on top as a conversation layer and can be removed without breaking the product.

---

## 2. Storage

**One Postgres database with the `pgvector` extension.** No separate vector database.

Each program is a single row holding both:

- **Structured facts** — tuition, minimum IELTS, minimum GPA, deadline, country, city, degree level, field of study, language of instruction
- **An embedding column** — the program's descriptive text turned into a vector

Facts and meaning live side by side, so a single query can filter and rank together:

```sql
SELECT * FROM programs
WHERE tuition < :budget
  AND min_ielts <= :student_ielts
  AND deadline > CURRENT_DATE
ORDER BY embedding <=> :interest_vector
LIMIT 20;
```

**Why this matters:** with a separate vector store you would search first, then filter in application code — and lose valid results in the process. Nothing to keep in sync, fewer moving parts.

---

## 3. Ingestion and freshness

**Scraping produces two things per page:** raw descriptive text, and extracted hard facts.

Freshness is a first-class concern — stale data is worse than no data.

| Mechanism | Behaviour |
|---|---|
| **Text hash** | Store a fingerprint of each page. Re-fetch, re-hash, compare. Identical → do nothing, no re-embedding cost. Different → re-extract fields and refresh the vector. |
| **`last_checked` date** | Stored per record and **shown to the student**. Honesty beats false confidence. |
| **Tiered re-check** | Fast-moving fields (deadlines, fees) checked more often. Descriptions rarely change. |
| **Change guardrail** | Keep previous values rather than overwriting blindly. Implausible jumps (tuition triples) are flagged for human review, not published. |

---

## 4. Matching

Two layers, in strict order.

**Layer 1 — Hard filters (elimination only).**
Plain SQL. Fast. No cleverness. Removes anything the student cannot get into: tuition over budget, IELTS below minimum, deadline passed, wrong degree level.

**Layer 2 — Ranking (what survived).**
Two contributions combined:

- **Numeric score** — headroom above minimum requirements, cost, country preference, deadline proximity
- **Vector similarity** — the student's stated interests against program description text

Vector similarity **only reorders programs the student already qualifies for.** It can never admit or exclude anyone.

### Scoring weights

Weights (tuition 0.3, language score 0.2, country preference 0.1, etc.) live in **one settings file or a small config table — never scattered through code.** Tuning becomes editing numbers rather than touching logic. Later, per-country weight sets can move into the database.

---

## 5. Student input

Deliberately split by data type:

- **Hard numbers → proper form fields.** IELTS, GPA, budget, degree level as dropdowns and number inputs. These drive the filters and must be exact; free text here only invites mistakes.
- **Interests and goals → free text.** "I want to work on renewable energy storage." This is what vectors are good at.

**Phase 1 exception:** before any LLM exists, interests are captured as **tags and checkboxes** (field of study, subject areas, city preference) so the entire system remains deterministic.

---

## 6. Scholarships

The hardest data of the lot, and treated separately.

Scholarships do **not** belong as a column on the program — they come from universities, governments and foundations independently. They get **their own table**, linked to programs by rule-based eligibility: nationality, degree level, field, minimum grades, deadline. This is a second deterministic matching pass.

**Presentation:** same program card, its own section underneath. Each scholarship named, with amount and deadline.

**The differentiating number is cost after funding**, not sticker tuition. That is the figure students actually care about and almost nobody presents clearly.

**Always worded as "possibly eligible", never "guaranteed"** — scholarship rules are full of exceptions.

---

## 7. Results presentation

Every result shows **why** it matched, in plain language, straight from the deterministic filters:

- Meets IELTS requirement
- Tuition within budget
- Deadline in three months

Beyond the result list: a student workspace with saved programs, side-by-side comparison, and tracked deadlines.

---

## 8. Where the LLM enters — in this order

| Order | Capability | Risk |
|---|---|---|
| 1 | **Explanation layer.** Same ranking; the agent articulates why each program suits the student, grounded in program pages with sources cited (RAG). | Lowest — decides nothing |
| 2 | **Intake.** Student uploads CV or transcript; the model fills the form fields, **which the student then confirms.** | Low — human-verified |
| 3 | **Free-text interest matching.** Natural-language goals embedded and compared against program descriptions. | Moderate — reorders only |

The pattern throughout: the LLM never decides eligibility.

---

## 9. Phasing

**Phase 1 — Matching and ranking.** Curated program set, fully deterministic. Prove the matching works before investing in a scaling pipeline.

**Phase 2 — Application *preparation*, not submission.** Pre-filled forms, document checklists, tailored motivation-letter drafts, deadline reminders. Most of the value, almost none of the risk.

**Why preparation first:** every university has a different portal; some require posted documents or paid fees. There is no standard to build against. Preparing applications teaches you exactly what each university requires, document by document — and *that* accumulated knowledge is what makes real submission possible later. It is also a moat that is slow to copy.

**Phase 3 — True submission**, only where a portal permits it properly.

---

## 10. Data sourcing options

Ranked cleanest to messiest:

1. **Official APIs and open datasets** — cleanest, limited coverage
2. **Partnerships** with universities or agencies — highest quality, potential revenue path, slow to establish
3. **Licensed aggregator data** — fast, costs money
4. **Web scraping** — widest coverage, most fragile, legal grey area requiring care

**MVP recommendation:** do not try to cover the world. Hand-curate 30–50 programs across 2–3 countries Azerbaijani students actually apply to. Prove the matching first.

---

## Open questions

| # | Question | Why it blocks |
|---|---|---|
| 1 | Which target countries, and how many programs for the MVP? | Determines curation effort and scraping scope |
| 2 | Primary data source — scraping, partnerships, or licensed data? | Shapes the entire ingestion pipeline and cost base |
| 3 | Exact scoring formula and starting weights? | Cannot rank without it; needs real student input to calibrate |
| 4 | Web or mobile first? | Affects stack, timeline and the workspace design |
| 5 | Do students need accounts from day one? | Determines whether saved programs and tracking ship in Phase 1 |
| 6 | Legal position on scraping — terms of service, robots.txt, jurisdiction? | Risk to the whole business if handled late |

Worth adding to this list as you go: how you validate that a match is actually *good* (outcome logging), and whether the scholarship data can realistically be maintained at the same cadence as program data.
