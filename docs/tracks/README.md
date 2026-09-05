# Tracks — who does what, and how

**Written 5 September 2026. Deadline 15 September — 10 days.**

Four tracks, split so that two people working at the same time do not touch the same files.
Pick one, put your name on it in the table below, and work through its steps in order. Each
track's file names the exact files it owns.

Current status of the whole project is in [`../PROJECT-STATE.md`](../PROJECT-STATE.md). The
product spec is the
[route-first design](../superpowers/specs/2026-08-31-route-first-advisor-design.md).

| Track | What it is | Owner | Files it owns |
|---|---|---|---|
| **[A — Catalogue](track-a-catalogue.md)** | The university requirement rows. **The critical path.** | *two people, unclaimed* | `data/curation/*.csv` |
| **[B — ML](track-b-ml.md)** | The Azerbaijan DİM section | *unclaimed* | `backend/scripts/train_cutoff_models.py`, `backend/app/services/prediction/`, `notebooks/` |
| **[C — Product & LLM](track-c-product-llm.md)** | Wiring the chatbot to the engine | *Fariz + Claude* | `backend/app/services/agent/`, `backend/app/api/v1/chat.py` |
| **[D — Frontend](track-d-frontend.md)** | Discovery and Target flows | *unclaimed* | `frontend/src/` |

---

## The two products in this repository

Say this out loud once, because getting it wrong produces confident wrong answers and
several documents have already had to be corrected for it.

**AUSA is two things sharing a codebase, tied together by one chatbot.**

| | Abroad routing | Azerbaijan DİM |
|---|---|---|
| Question | *Where can I go, and who pays?* | *Which Azerbaijani programme can I get into?* |
| Countries | TR · DE · GB · US · PL · CN | AZ |
| Method | Deterministic routes, curated requirements, funding gates | Machine learning |
| Tracks | A, C, D | B |

### The boundary rule, stated precisely

An earlier draft of this said *"a DİM number must never appear in an abroad answer"*, and
that is **wrong** — it would move the State Programme into the wrong half of the product.
The boundary is not on the DİM scale. It is on **who produced the number**:

| Number | Where it belongs |
|---|---|
| **A DİM score the student tells us** | **Anywhere.** It is a fact about them. It gates the State Programme (400/550), it decides the prep year, and both of those are abroad features |
| **A DİM cutoff the model predicted** | **The Azerbaijan section only.** It is a number *we* produced, about Azerbaijani universities, and it says nothing about admission abroad |

So: **the Dövlət Proqramı belongs in the abroad universities part**, beside the other nine
funders, even though its academic gate reads a DİM score. It funds study *abroad*, at
foreign universities, and putting it in the Azerbaijan section because its gate mentions
DİM would file it by the shape of its input instead of by what it does for the student.

---

## Rules that bind every track

These are not style preferences. Each one exists because this project already shipped its
opposite and had to reverse out.

1. **An unknown must never read as permission.** A blank requirement means *nobody checked*,
   never *not required*. A blank tuition renders as free; a blank language test renders as
   none required. Both are wrong in the direction that costs a student an application.
   ([ADR-0004](../adr/0004-batch-serving-and-explainability.md))

2. **No `except Exception` → substitute plausible data → continue.** This produced the
   authentication bypass, the fabricated transcript profile, and three deleted collectors.
   A failure returns an error and says what failed.

3. **Every number a student sees came from a model, from arithmetic, or from a cited page.**
   Never from a formula someone invented. The weighted match score was deleted for exactly
   this.

4. **A grade without its scale is not a number.** 4.5 is an excellent attestat out of 5 and
   an impossible GPA out of 4. Always store and send the pair.

5. **`human-verified` means a named person opened the source page.** It cannot be set from a
   CSV or by an LLM's confidence in itself.

6. **Say "possibly eligible", never "you will get it."** Meeting an award's published gates
   is not the award. Every funder here is competitive and selection is a committee decision
   no dataset in this project models.

---

## Before you start

```bash
python -m venv .venv
.venv\Scripts\activate                    # Windows
pip install -r backend/requirements.txt

python demo_walkthrough.py                # see what the product does, ~15s, no database
cd backend && python -m pytest -q         # 277 tests, all should pass
cd frontend && npm install && npx vitest run   # 47 tests
```

If `demo_walkthrough.py` does not run to the end, stop and fix that first — it is the
fastest way to see whether your environment is the problem or your change is.

## Before you push

- Your track's tests pass, **and** the whole suite still passes.
- No new blank-means-permission path. Grep your diff for `except Exception`.
- One commit per idea, with a message that says *why*, not just what.
