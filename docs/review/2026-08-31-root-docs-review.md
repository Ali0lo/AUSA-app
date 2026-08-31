# Review: the four root-level documents, against where the project actually is

**Date:** 2026-08-31
**Reviewed:** `architecture-decisions.md`, `data-sourcing.md`, `university-matching-platform-notes.md`, `README.md` — all dated 28 August, all predating ADR-0006 onward.

**Summary:** the three design notes are better than their age suggests and contain material
the current spec is missing. The README is the opposite — it describes a system that does not
exist, and three of its links are broken.

---

## 1. What the root docs already solved that I re-derived this week

These are not "nice ideas we could adopt". They are answers to questions I spent days on.

### 1.1 DAAD's programme database — the biggest miss

`data-sourcing.md` §2 names **DAAD "International Programmes in Germany"** as a Tier-1
national aggregator: bachelor/master/PhD programmes across every German university,
filterable, English-taught flagged — plus **a separate DAAD scholarship database**.

I spent two days on hochschulstart.de and individual university NC pages, concluded German
collection was hard and uneven, and wrote `docs/reference/germany-nc-sources.md` about it.
**I never checked DAAD.** The document telling me to check national aggregators *first* was
sitting in the repository root the whole time.

`university-matching-platform-notes.md` §4 names **UCAS** the same way for the UK. Also
unchecked.

**Action:** before any German or UK requirement extraction, check DAAD and UCAS for an
export, an API, or terms permitting use. This may collapse the largest task in the spec.

### 1.2 "Cost after funding" was written on 28 August

`architecture-decisions.md` §6:

> "The differentiating number is **cost after funding**, not sticker tuition. That is the
> figure students actually care about and almost nobody presents clearly."

I presented "total cost to degree" as a finding on 31 August. It was already decided. The
research since then adds *why* it is true at bachelor level (the scholarships are all
master's-only) but the design conclusion was not new.

### 1.3 Scholarships as a second deterministic pass

`architecture-decisions.md` §6 already puts scholarships in their own table, matched by
rule-based eligibility on nationality, degree level, field, grades and deadline, and insists
on the wording **"possibly eligible", never "guaranteed"**.

My spec §5.2 says scholarships run through the same eligibility engine — the same idea. The
root doc's "possibly eligible" wording rule is stricter than anything in the spec and should
be adopted verbatim.

### 1.4 The answer to "how do we bound the extraction task"

`data-sourcing.md` §0:

> "For 30–50 programs, **do not build a scraper**. Copy-paste into a spreadsheet is two or
> three days of work. Building a pipeline before the schema is proven correct is the standard
> way to lose a month."

I flagged extraction sizing as an unresolved weakness of the spec. This is the answer, and it
was written three days earlier. With 15 days left it is almost certainly correct.

### 1.5 A freshness design the spec does not have

`architecture-decisions.md` §3 specifies: page **text hash** to skip unchanged pages and
avoid re-embedding cost; **`last_checked` shown to the student**; **tiered re-check** with
deadlines and fees checked more often than descriptions; and a **change guardrail** that
keeps previous values and flags implausible jumps (tuition tripling) for human review rather
than publishing them.

My spec has `retrieved_at` and nothing else. This is a complete gap, and the guardrail in
particular is the same class of protection as ADR-0004's no-silent-fallback rule.

### 1.6 Discovery techniques worth using as method, not luck

`data-sourcing.md` §2 Tier 3: open the programme finder, DevTools → Network → XHR, and look
for the JSON endpoint behind the page. "Always check this before writing a parser."

I found the DİM open-data API and the CKAN dataset endpoints by chance this week. Tier 2
(sitemaps) and Tier 3 (hidden JSON) are the systematic version of what I did ad hoc.

---

## 2. Where the root docs are genuinely superseded

Not everything old is right. These were correctly overtaken and should not be reinstated:

| Root doc says | Superseded by | Why |
|---|---|---|
| Scoring weights — tuition 0.3, language 0.2, country 0.1 — in a config file | ADR-0001 | Hand-set weights are exactly the hardcoded scoring the project exists to remove; there are no preference labels to calibrate them against |
| "at home and abroad", incl. Azerbaijani universities as destinations | ADR-0008 §4 | Scope is abroad; domestic study is a separate future surface |
| All three levels including PhD | Spec §6 | PhD admission is supervisor-driven and funding is a paid position — no shared mechanics |
| MVP of 2–3 countries | Spec §6 | Six countries, but with per-country coverage weighted, not equal |

The `architecture-decisions.md` open-questions list is also fully superseded by
`docs/open-questions.md`, which answers all six.

---

## 3. The README is wrong, and it is the public face

`README.md` is on GitHub with CI badges. It is what an examiner reads first. It currently
describes a system that does not exist.

**Broken links — verified:**

```
docs/adr/0001-ml-predictive-cutoff-layer.md          MISSING
docs/adr/0002-data-science-training-pipeline.md      MISSING
docs/adr/0005-scholarship-first-net-cost-evaluation.md  MISSING
```

The real filenames are `0001-cutoff-prediction-replaces-weighted-scoring.md`,
`0002-per-country-models-and-normalization.md`, `0005-scholarship-pass-precedes-budget-filter.md`.

**False capability claims:**

| README claims | Reality |
|---|---|
| "Random Forest models predict admission cutoff scores **and success probabilities**"; "infer **admission probability**" | ADR-0001 rejects P(admit) outright — there are no labelled student outcomes. This is the one claim the whole project is built on *not* making |
| "Random Forest" | Superseded by CatBoost / HistGradientBoosting |
| "Custom asyncio scrapers ingest program directories from **DAAD/Uni-Assist**" | `collect_germany.py` was **deleted on 30 August** — its three target URLs were invented and its only working path was a mock-HTML fallback. No German scraper exists |
| "local Azerbaijani higher education institutions" as a target | Contradicts the abroad-only scope (ADR-0008 §4) |
| "€11,208 blocked account" | The blocked-account figure changes annually and is unverified here |
| `./backend/.venv/bin/python` in the test command | The venv is at the repo root, and this is Windows — `Scripts`, not `bin` |

**The admin dashboard claim is true.** `backend/app/api/v1/admin.py`, `backend/tests/test_admin.py`
and `frontend/src/app/admin/page.tsx` all exist. It is the review queue
`university-matching-platform-notes.md` §4 asks for, and the spec's provenance states should
connect to it rather than reinvent it.

**But the number it gates on is fabricated — see §3.1.**

---

## 3.1 🔴 A live fabrication path in the extraction pipeline

`backend/app/data_pipeline/extraction.py:81` — found while verifying the admin claim above.
This is the same defect class deleted on 30 August, still in place, and it feeds the
`programs` table that the matching engine reads.

```python
    except Exception:
        # Fallback heuristic extractor when live LLM API is unavailable
```

A bare `except Exception` around the LLM call catches everything — missing API key, network
error, rate limit, malformed response, import failure — and silently substitutes a regex
heuristic that then **invents data**:

| Line | Fabrication |
|---|---|
| 117–118 | `university_name="Extracted University"`, `program_name="Extracted Program"` — literal placeholder strings written as if they were real values |
| 128 | `blocked_account_eur=11208.0` — a hardcoded constant presented as extracted from the page. The real figure changes annually |
| 126 | `requires_studienkolleg` set by mere substring presence, so a page that only *mentions* Studienkolleg gets flagged as requiring it |
| 112–114 | Country inferred by substring — any page containing "baku" becomes Azerbaijan |
| 94 | The confidence score itself |

**The confidence score is the worst of it**, because the human-in-the-loop safeguard depends
on it:

```python
calc_confidence = round(min(100.0, max(40.0, (found_count / 3.0) * 100.0)), 1) if found_count > 0 else 50.0
```

It measures how many of five regexes matched, not how reliable the extraction is. Three
matches gives `(3/3)*100 = 100.0` — **a perfect confidence score from a fallback parser that
also just invented the university name.** At 100.0 it clears the README's 85% threshold and
is published without human review. And when nothing at all is found, the score is `50.0`
rather than `0` — "we extracted nothing" is scored as a middling result.

There is also a testing consequence: in CI with no `OPENAI_API_KEY`, the `try` block always
raises, so `test_data_pipeline.py` exercises the fallback rather than the extractor. The
tests are green on the fabricated path.

**This is the highest-priority defect in the repository** — higher than anything in the spec,
because it silently writes invented values into the table students' decisions are read from,
and it defeats the one safeguard designed to catch that. It should be fixed before any new
extraction work begins, since the spec's entire critical path writes through this module.

---

## 4. What this means for the spec

Concrete changes to `docs/superpowers/specs/2026-08-31-route-first-advisor-design.md`:

1. **Add a data-source tier order** before extraction: national aggregators (DAAD, UCAS,
   the DP CSVs we already have) → sitemaps → hidden JSON → manual. Check DAAD and UCAS
   before committing to per-university extraction at all.
2. **Adopt hand-curation for the first 30–50 programmes.** It answers the sizing gap, and it
   matches the deadline.
3. **Add the freshness design** — text hash, `last_checked` displayed, tiered re-check,
   change guardrail on implausible jumps.
4. **Adopt "possibly eligible, never guaranteed"** as the scholarship wording rule.
5. **Connect provenance to the existing admin review queue** rather than defining a parallel
   mechanism — after confirming what actually exists in the code.

And separately from the spec: **rewrite the README.** It is the cheapest high-value fix
available — broken links and a false ML claim in the public-facing document of a graded
project.

---

## 5. Open

- How many rows currently in `programs` came through the fallback path in §3.1? Anything
  with `extraction_notes="Extracted via fallback parser."` or a university named
  "Extracted University" is suspect and needs quarantining, not just a code fix.
- Do DAAD's and UCAS's terms permit programmatic use, and do they expose an export?
- Should the three root design docs move into `docs/` and be marked superseded-where-noted,
  or stay at root as the origin record? They currently read as current guidance while being
  partly overtaken, which is how the DAAD lead got missed for three days.
