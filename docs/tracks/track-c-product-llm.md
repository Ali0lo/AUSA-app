# Track C — Product and the LLM

**One person. ~3.25 days.** C1, C2, C3 and C4 are **done** (C2.5 landed 16 September).
The only Track C item deliberately left undone is the motivation letter, which is a
decision rather than a task — see *Deliberately not in this track*.

---

## Done

| | Task | Commit |
|---|---|---|
| **C1** | `demo_walkthrough.py` runs end to end again, with a smoke test | `3bef1be` |
| **C3** | The weighted match score deleted front to back | `367b22a` |
| **C4** | `students.gpa` carries its scale; a 4.5/5 attestat can register | `e0dd0cd` |
| **C2.1** | Four tools over the route engine and the funding catalogue | `907e8b4` |
| **C2.2** | Free-text intake, plus `POST /routes/parse` | *this branch* |
| **C2.3** | The numeral guard | `907e8b4` |
| **C2.4** | System prompt rewritten around the contract and the DİM boundary | `907e8b4` |
| **C2.5** | The document process library, its agent tool and `GET /routes/{route_key}/process` | *this branch* |

C1 surfaced a finding now carried as Track A's first task: the prep-year path to Germany
resolves to **zero universities**, because all three curated German rows are
`feststellungspruefung`.

`services/agent/route_tools.py` does not reach the universities a plan lands on —
`university_requirements` needs a database session and those tools are deliberately sync
and I/O-free, so a caller that needs universities calls `POST /routes/assess`.

---

## C2 · Wire the LLM to the engine — 2 days

**The problem:** the chat layer retrieves documents from an empty index, and the agent's four
tools are `check_missing_documents`, `get_program_deadline`, `draft_motivation_letter` and
`extract_and_update_profile`. **None of them can see a route, a scholarship gate, or the
catalogue.** The LLM cannot answer the question the product exists to answer, while the
answer sits one function call away, already structured and already cited.

**The architecture:** one chatbot over both halves of the product — abroad routing and the
Azerbaijan DİM section — that explains *why*, not just *what*.

### The contract, by claim type

This is [the spec's §8](../superpowers/specs/2026-08-31-route-first-advisor-design.md) and it
is what makes one chatbot over two domains safe:

| Claim | Rule |
|---|---|
| **Numbers** | ML or arithmetic only. **Every numeral in generated text is validated against the payload** — by a check on the string, not by convention |
| **University-specific qualitative** | Cite or drop |
| **Country process steps** | From a curated per-country library |
| **Framing, tone, explanation** | Free |

Plus the boundary from [`README.md`](README.md): a number carries **which domain produced
it**. A predicted DİM cutoff must never appear in an answer about Germany.

### Steps

**1 · Tools over the route engine** ✅ — `backend/app/services/agent/route_tools.py`

Each tool calls the existing service and returns its structured result. None of them
computes anything new; that is the point.

| Tool | Wraps | Answers |
|---|---|---|
| `assess_student_routes` | `services/route_engine.assess_routes` + `compose_two_hop` | *"Where can I go?"* |
| `describe_route_requirements` | one `Route` in `domain/route_definitions` | *"Why is Germany closed to me?"* |
| `list_funding_options` | `services/scholarship_eligibility` + `services/dp_eligibility` | *"What can I get funded?"* |
| `explain_funding_gate` | one scholarship's `gates_missing` / `gates_blocked` / `gates_unknown` | *"Why not Chevening?"* |

A fifth, `universities_on_route` over `services/university_requirements`, is **not built**:
that service needs a database session and these tools are deliberately sync and I/O-free.
`POST /routes/assess` already returns the universities, so that is the call to make.

**Keep `gates_unknown` separate from `gates_missing` in every rendering.** A missing gate is
work the student can do; an unknown gate is a fact they can tell us or a source we have to
read. Merging them in prose is the same error as merging them in the API, and neither ever
counts as open.

**2 · Free-text intake** ✅ — `backend/app/services/agent/intake.py`, `POST /routes/parse`

Maps free text onto the `AssessRoutesPayload` fields. This is the "based on own interest"
half of the product: there is no field taxonomy a 17-year-old knows.

**Anything the student did not say stays `None`.** Not a default, not an inference from
context. This is the exact site where `extract_and_update_profile` used to invent GPA 3.8 and
IELTS 7.5 from an unparseable transcript and report success — so this is deliberately regular
expressions, not a model: **every value is anchored to a token naming its field.** `520`
becomes a DİM score because the word DİM is beside it, never because 520 looks like one, and
a message of bare numerals yields nothing.

Four places a helpful parser would lie, and what this one does instead:

| Input | It does not | It does |
|---|---|---|
| "robotics" | infer `dim_field_group=1` | carry `interest` as text and ask for the group |
| "IELTS 6.5 … then 7" | take the higher | report `conflicts`, set nothing |
| "my GPA is 4.5" | assume a 4.0 scale | note the missing scale and ask |
| "8000 AZN saved" | read it as a yearly budget | require "per year" beside it |

The subject → field group one is the load-bearing case: the Dövlət Proqramı threshold is 400
for Group 1 and 550 otherwise, so guessing the group from a word moves a real gate by 150
points.

`POST /routes/parse` exists so this is reachable with **no API key and no language model** —
which is what lets Track D ship a paste-a-paragraph entry instead of a form. It returns
`heard`, quoting the student's own words behind each value, so a misreading is correctable
before it is acted on.

**3 · The numeral guard** ✅ — `backend/app/services/agent/numerals.py`

Extracts every numeral from generated text and asserts the payload supports it. Normalises
both sides (`1,200` = `1200`, `7.0` = `7`) and mines citation strings, so quoting *"2,800
documented hours"* back passes. It does **no arithmetic of its own** on purpose: a total the
model computed correctly still trips it, because a total shown to a student should be
computed by the service and passed in.

Test-time and development assertion, never a runtime filter — silently dropping a sentence
would leave the student reading an explanation with a hole in it and no sign there was one.

**4 · Route explanation in the answer** ✅ *(the prompt half; the rendering is Track D)*

The engine already produces *"This route needs one of: one_year_university,
feststellungspruefung, a_level, ib. You hold: attestat."* The LLM's job is to turn that into
a sentence a 17-year-old reads, in Azerbaijani, **without adding a fact**. Rewriting a
computed reason cannot fabricate; that is why this is the first surface to build.

**5 · Application walkthrough** ✅ — `backend/app/domain/process_definitions.py`,
`services/agent/process_tools.py`, `GET /routes/{route_key}/process`

A curated library of what a student must do **to their Azerbaijani documents** to make them
usable in the destination. Curated, not generated: process steps are qualitative claims and
the contract says cite-or-drop.

**It is keyed on the route, not on the country.** The brief originally said "per-country",
and that is wrong in a way that would have shipped a confidently merged checklist. Germany
takes an attestat holder through a Studienkolleg and a prep-year holder through a transcript
of completed university study — same country, same level, different paperwork. `(country,
level)` would have flattened `de-bachelor-studienkolleg` and `de-bachelor-direct` into one
list, and one of the two students would have been handed a checklist missing the document
their route actually turns on.

**It owns one layer and points at the other three.** Three facts a walkthrough obviously
needs already have a home, and a fact with two homes drifts:

| Fact | Owner |
|---|---|
| The visa deposit (Sperrkonto) | `Route.proof_of_funds` |
| Portal, fee, document list, deadline | the catalogue row |
| A funder's application window | `Scholarship.window` |

The tool returns `see_also` naming the tool that holds each, and a test asserts the
Sperrkonto figure never appears in a step.

**Coverage, and the honest shape of it.** Seven routes curated from primary pages read on
16 September (three German, three Turkish, plus the prep year). The nine routes into the UK,
the USA, Poland and China are recorded `not_collected` — a named absence, never an empty
list that reads as "no documents needed". Filling a country later is a data-only change.

**What we could not reach is recorded, not worked around.** `scripts.check_sources_robots`
refused `denklik.meb.gov.tr` (DNS did not resolve) and `mfa.gov.az` (SSL verification
failed), and `studyinturkiye.gov.tr`'s deep paths answer HTTP 418 to an automated client.
So the Turkish *denklik* certificate and the Azerbaijani apostille are **not written as
steps**. They sit in `known_gaps`, which the prompt instructs the model to state as
something to ask the university about — never as a requirement. Both URLs are in
`sources.csv` marked `NOT READ`.

Notice what Germany does *not* require: uni-assist's own document pages mention neither an
apostille nor an APS certificate. That absence is deliberate. Adding an apostille step "to
be safe" would send a student to pay for a legalisation no page we read asks for.

### Done when

- A student can ask *"why can't I go to Germany?"* and get the engine's real reason in
  prose, with no number the engine did not produce.
- A free-text profile produces the same route assessment the form does, with every unstated
  field `None`.
- The numeral guard is a passing test with at least one recorded case that would fail
  without it.

---

## Deliberately not in this track

**Motivation letter generation.** `agent/tools.py` ships a hardcoded generic template. The
agency research this project rests on lists recycled motivation letters as an industry red
flag that admissions boards detect and reject, and advises students to write their own.

The recommendation on the table — **not yet a decision** — is to shift from *generation* to
**critique**: the student writes, AUSA reviews against that programme's extracted criteria.
Somebody should decide that before it is built either way.

## Files this track owns

```
backend/app/services/agent/
backend/app/api/v1/chat.py
backend/tests/test_agent.py
backend/tests/test_chat.py
```
