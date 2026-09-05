# Track D — Frontend and report

**Status: COMPLETED (5 September 2026)**
- [x] **D1: Discovery Flow** — Level first, live refining, baseline loaded so never empty, three status groups (OPEN, UNLOCKABLE, BLOCKED), destination ranking without exclusion ("Your score goes further here"), total cost to degree.
- [x] **D2: Target Flow** — Name university, objective gap statements, requirement checklist, process checklist, deadlines, alternatives closing gap, honest uncurated fallback, speculative study plan excluded.
- [x] **D3: Make Absence Visible** — `unknown_fields` + `not_stated`, distinguish catalogue gap vs country finding, separate `gates_unknown` vs `gates_missing`, `provenance` + `last_checked` on every row, warn on `grade_exact: false`.
- [x] **D4: Report & README Pass** — Update `README.md`, create `docs/PROJECT-REPORT.md` quoting the four verified limitations verbatim.

---

## What you are building on

Run this first — it prints the whole response shape a page has to render:

```bash
python demo_walkthrough.py
```

`frontend/src/test/fixtures/assess-routes.json` is a real captured response, and
`src/lib/assess-contract.test.ts` (17 tests) pins its shape. **Build against the fixture,
not against a hand-written mock** — a mock is where a UI starts rendering fields the backend
does not send.

---

## Steps, in order

### D1 · Discovery — 2 days

One profile step, results refining live, never empty before input.

1. **Level first**, because every finding in this product is level-specific and several
   *invert* between the two: Germany and the UK are blocked to a school-leaver and open to a
   bachelor holder; Türkiye Bursları' under-21 limit exists only at bachelor; the State
   Programme funds zero USA bachelor places and 289 at master's.
2. Qualification held, exam scores, **grade with its scale** (the selector, not a 4.0
   assumption), age, budget, destination preference, field.
3. Results in three groups, from `status`: **OPEN**, **UNLOCKABLE** (with what is missing and
   what it costs), **BLOCKED** (with the reason).
4. **Destination ranks, it never excludes.** Chosen countries fill the main results; a
   persistent *"your score goes further here"* section carries the strongest matches from
   countries the student did not name. Gating on destination is the steering behaviour this
   product exists to refuse, implemented in software.
5. Rank by **total cost to degree** — `total_cost_azn_low/high` plus `time_cost_months`. Note
   this only becomes meaningful once Track A fills tuition in; until then show the route cost
   and label what is missing rather than showing a total that omits tuition silently.

**Done when:** the spec's walkthrough profile — attestat, DİM 520, IELTS 7.0, bachelor,
8,000 AZN/year — renders Turkey and Poland OPEN, Germany and the UK BLOCKED with both
unlocks named and costed, and the funded programme set with the band that decided it.

### D2 · Target — 1.5 days

The student names a university and gets: a gap statement, a requirement checklist, a process
checklist, deadlines, and alternatives that close the gap.

**A university we do not hold produces a plain "we don't have this yet"** plus what we do
hold for that country. Never a guessed requirement, never a silent substitution.

**Target excludes a study plan.** *"You are 68 points short"* is supported by the data.
*"Retake DİM in March, target +70, focus on maths"* is not — nothing in any dataset links
effort to score change.

### D3 · Make absence visible — half a day

The response is built to distinguish four kinds of nothing, and a UI that renders them all as
blank throws that away. This is the smallest task with the largest honesty effect.

| Field | What the UI must do |
|---|---|
| `unknown_fields` + `not_stated` | Name what the source page did not state. **A blank tuition reads as free and a blank language test reads as none required** — both wrong in the direction that costs an application |
| `universities_status` | Distinguish *we have not collected this country* from *we collected it and none accepts this qualification*. One is our gap, the other is a finding about the country |
| `gates_unknown` vs `gates_missing` | Never merge them. Missing is work the student can do; unknown is a fact they can tell us. Neither counts as open |
| `provenance`, `last_checked` | On every row. `claude-extracted` is not `human-verified`, and the student should see which |
| `grade_exact: false` | The comparison crossed two scales and is a screening signal, not an official conversion. Rendering the verdict without the flag overstates what was checked |

### D4 · Report and README — 1 day

1. **README §"Honest status" is stale.** It says the frontend still shows demo programmes
   (fixed in `fdf230a`) and reports 186 / 233 tests (actually 277 backend + 47 frontend). The
   weighted matcher it describes is deleted.
2. **Say plainly that this is two products in one repository** — abroad routing and the
   Azerbaijan DİM predictor, tied by one chatbot. Two products in one repository is a
   defensible design; two products described as one is what a marker catches.
3. The report's limitations section quotes, rather than discovers:
   - Published cutoffs describe the **domestic** route in every destination. German NC tables
     are footnoted *"ohne Bildungsausländer\*innen"*. This is why the ML is Azerbaijan-only.
   - The ML rests on **one country and three intake years**.
   - Every figure in the funding catalogue is `research-brief` provenance until Track A5
     lands.
   - `verified_by` is empty on the DİM training rows until Track A6 lands.

---

## Files this track owns

```
frontend/src/app/          (except azerbaijan/, which is Track B)
frontend/src/components/
frontend/src/lib/
README.md
```

## Rules for this track specifically

- **Never render a number the API did not send.** No client-side percentage, no computed
  "fit score", no rounding that invents precision. The weighted score was deleted from the
  backend; do not rebuild it in TypeScript.
- **Never render `null` as a blank cell.** See D3.
- Say *"you meet the published requirements"*, never *"you qualify for a full scholarship"*.
  The second is prohibited output in UI labels as much as in generated text, and it is
  precisely the phrasing that makes agency marketing untrustworthy.
