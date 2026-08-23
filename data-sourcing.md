# Data Sourcing & Scraping Strategy

Companion to `architecture-decisions.md`. Covers where program data actually comes from and how to acquire it.

---

## 0. The MVP shortcut

**For 30–50 programs, do not build a scraper.** Copy-paste into a spreadsheet is two or three days of work. Building a pipeline before the schema is proven correct is the standard way to lose a month on infrastructure that then needs rewriting.

Build the pipeline when the manual work stops being feasible — not before.

---

## 1. Two problems, not one

Most people conflate these and suffer for it. Separate them from the start.

| Stage | Job | Why it's hard |
|---|---|---|
| **Fetch** | Get the page as clean text or markdown | JavaScript rendering, bot protection, layout noise |
| **Extract** | Turn that text into your fields | Every university words requirements differently |

Different tools, different failure modes, different costs.

---

## 2. Where the URLs come from

**There is no universal `/programs` path.** But there is a reliable hierarchy — always work top-down.

### Tier 1 — National aggregators (best source by far)

Most study destinations have an official database that has *already* normalized programs across every university in the country. One integration replaces a hundred scrapers.

- **Germany — DAAD "International Programmes in Germany"** — Bachelor's, Master's and PhD programs, filterable, English-language programs flagged. DAAD runs a **separate scholarship database** too, which addresses the hardest data problem in one place.
- Equivalent national bodies exist for most target countries — find each one before writing any code.

**Caution:** aggregators typically have *stricter* terms of use than individual universities, precisely because the data is their product. Read the terms before building on top of one. A partnership or licence may be both cheaper and safer than scraping.

### Tier 2 — Sitemaps (the correct way to go direct)

Every serious university site publishes `/sitemap.xml` or `/sitemap_index.xml`.

1. Fetch the sitemap
2. Filter URLs matching `/programmes/`, `/study/`, `/courses/`, `/degrees/`
3. That is your target list

This is polite, cheap, and stable — and it is what serious scrapers do instead of following links blindly. Some universities go further and publish machine-readable course feeds (e.g. Oxford's XCRI-CAP catalogue feeds), which skip parsing entirely.

### Tier 3 — The catalogue's own hidden API

Open the university's program finder, open browser DevTools, filter the Network tab to **XHR/Fetch**, then search or paginate.

Very often the page is calling a JSON endpoint behind the scenes. If it is, you get clean structured data and skip HTML parsing completely.

**Always check this before writing a parser.** It takes two minutes and can save days.

### Tier 4 — Search engines

Fallback only, for filling gaps in a list you already have. Never as a primary discovery method.

---

## 3. Fetching tools

| Option | Model | Trade-off |
|---|---|---|
| **Playwright / Puppeteer** | Self-hosted, free | Full control; you maintain browser infra and handle blocks yourself |
| **Firecrawl** | Managed API, ~$83–99/mo | Returns LLM-ready markdown; handles proxies, JS and anti-bot for you. Zero infrastructure |
| **Crawl4AI** | Open-source Python, self-hosted | No per-page fees; you carry server (~2GB+ RAM for Chromium) and proxy cost |
| **Apify / Bright Data** | Managed, enterprise | Only relevant at large scale |

**Recommendation for a solo founder: Firecrawl.** You should not be running browser infrastructure while you are still validating the product. Revisit once volume makes per-page fees hurt.

At scale, proxy infrastructure and anti-bot strategy matter more than the choice of scraper — plan for it in the architecture rather than bolting it on later.

---

## 4. Extraction

**This is where Claude belongs.** Feed the markdown in with a strict JSON schema; get structured fields back.

**Do not write CSS selectors per university.** They break every time a page changes, and you will be maintaining hundreds of them.

Practical notes:

- **Haiku is usually sufficient** for structured field extraction — no need for Opus here
- Cost is low: a program page is roughly 3–5k tokens in, a few hundred out. A few thousand pages lands in the low tens of dollars
- **Your real expense is fetching** (proxies, anti-bot), not the model
- **A human confirms every record before it goes live.** Extraction confidence is never high enough to publish blind on data students make financial decisions from

---

## 5. Claude subscription vs API

Two different things, and the distinction matters for budgeting.

| Use | Covered by | Notes |
|---|---|---|
| **Building the project** — writing the scraper, debugging the pipeline, managing the repo | ✅ Pro/Max subscription | Claude Code in the terminal is included alongside web and app access |
| **Running extraction in production** — your backend sending pages for field extraction | ❌ Needs an API key | A paid subscription does not include API or Console access. Programmatic calls are billed per token |

**Do not use OAuth-token workarounds** found on GitHub. That route was closed in January 2026, using subscription tokens with third-party tools violates the terms, and accounts have been banned over it.

**Suggested setup:** Claude Code (subscription) to build it → a separate API key with a **spend cap** for the extraction job → start with $5–10 of credit to measure real cost per program before scaling.

---

## 6. Legal position

Resolve this **early** — it is cheap to answer now and expensive to discover later.

- Check each source's **terms of service** and **robots.txt**
- Some sites explicitly forbid automated collection
- Aggregator terms are usually stricter than university terms
- **Reputational risk:** a startup that will later want partnerships with these same universities does not want to be discovered scraping them first

Where terms are restrictive, treat it as a prompt to approach for a partnership rather than a problem to route around.

---

## 7. Recommended order of work

1. Pick 2–3 target countries Azerbaijani students actually apply to
2. Find each country's **national database** — check terms, check for an export or API
3. For gaps, check individual universities for a **hidden JSON endpoint**
4. Fall back to **sitemaps** plus LLM extraction
5. Hand-verify everything before publishing
6. Only automate the loop once the manual process is proven and the schema is stable
