# University Matching Platform — Design Notes

*Restructured notes from our voice conversation.*

---

## 1. Data Strategy: What Lives Where

The single most important decision early on is drawing a clear line between structured data, unstructured data, and data refresh. Each needs a different mechanism.

### Structured database — the source of truth

University requirements, deadlines, and scholarship information are structured and change relatively slowly. Store them in your own database.

**Why:** matching score calculation needs fast, reliable queries. Firing live requests per student is slow, and most universities don't expose a usable API anyway.

### RAG — for the unstructured parts

Use retrieval for program descriptions, application guides, and long document text. When a student asks *"am I a good fit for this program?"*, RAG pulls context from those texts.

> **Rule of thumb:** structured database for the matching score, RAG for explanation and guidance.

### Requests / scraping — refresh only

Scraping and live requests exist purely to keep the database fresh. Run them as periodic background jobs — never while a user is waiting.

---

## 2. Architecture: Layered

### Layer 1 — Structured database

**PostgreSQL** is an excellent choice: it holds relational data *and*, with `pgvector`, embeddings in the same place. No separate vector database needed at the start.

### Layer 2 — Matching engine (deterministic)

Do **not** let the AI compute the score. Calculate it with rules and weights — grades, language score, budget, and similar criteria, each weighted.

Two benefits:

- **Cheap** — no inference cost per match.
- **Explainable** — you can tell a student exactly *why* they got that score.

### Layer 3 — AI, in three specific places

| # | Use case | What it does |
|---|----------|--------------|
| 1 | **RAG Q&A** | Answers questions about program details |
| 2 | **Document generation** | Motivation letter drafts and similar |
| 3 | **Agentic layer** | Manages the application process: tracks deadlines, checks for missing documents |

**LangGraph** fits the third one well — it's a multi-step, stateful flow.

---

## 3. Cost Model

**Largest line item:** LLM API calls, especially document generation and RAG.

**How to keep it down:**

- Keep matching AI-free.
- Use a large model only where it's genuinely needed; small models everywhere else.
- Embeddings are cheap. The database is cheap.

**The hidden cost** is data collection and keeping it current — i.e. maintaining the scraping infrastructure. Budget for that, not just for tokens.

---

## 4. Data Sourcing

This is the part that makes or breaks the product: **your matching is only as good as your program data.**

### The four options, cleanest to messiest

| Option | Coverage | Quality | Trade-off |
|--------|----------|---------|-----------|
| **1. Official APIs & open datasets** | Limited | Highest | Cleanest, but not everywhere. Some countries run central databases — UCAS in the UK, DAAD in Germany |
| **2. Partnerships** (direct from universities/agencies) | Narrow at first | Highest | Can become a revenue path, but slow to set up |
| **3. Licensed aggregator data** | Broad | Good | Fast, but costs money |
| **4. Web scraping university sites** | Widest | Fragile | Most brittle, and a legal grey area to handle carefully |

Research options 1–3 first, before committing to scraping.

### Scraping, done intelligently

Do **not** write a separate scraper per university — maintenance becomes a nightmare.

Instead, use **LLM-assisted extraction**: fetch the page, hand the raw HTML to a model, and ask it to return the target fields as JSON — deadline, requirements, fees. This plays to your AI experience and survives site redesigns far better than selector-based scrapers.

### Human verification layer (critical)

**Never publish automatically extracted data directly.**

- Attach a confidence score to every extracted record.
- Route low-confidence records into a review queue for human approval.

If a student misses an application because of a wrong deadline, the product's reputation is gone.

### Freshness strategy

Stamp every record with a **last-updated** date and re-fetch stale entries on a schedule.

---

## 5. Core Domains

At the core there are three data domains:

1. **Student profile store**
2. **Program catalog** with structured requirements
3. **Matching engine** sitting between them

Keep the matching engine mostly **rule-based for hard filters** — budget, degree level, minimum scores — then layer a **scoring model on top for soft ranking**. Results stay explainable, and students trust that far more than a black box.

The **AI agent wraps around** this core. It handles:

- **Intake** — parsing a student's documents into a clean profile.
- **Explanation** — telling the student why a program ranks where it does.

---

## 6. MVP Recommendation

Don't try to cover the world.

Pick a narrow set — roughly **20–50 programs across two or three target countries** that Azerbaijani students actually apply to — and **hand-curate that data first**.

**Prove the matching works before investing in scaling the pipeline.**
