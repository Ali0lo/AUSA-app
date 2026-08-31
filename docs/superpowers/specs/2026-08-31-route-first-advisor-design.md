# AUSA — route-first advisor: design

**Date:** 2026-08-31
**Status:** approved — implementation plan next
**Supersedes in part:** [ADR-0007](../../adr/0007-three-number-model-and-honesty-tiers.md) §3, §4; [ADR-0008](../../adr/0008-selectivity-replaces-cutoff-prediction.md) §4 (country and level scope)
**Carries forward:** ADR-0007 §2 (the two modes) — see §6; `architecture-decisions.md` §3 (freshness) — see §5.4
**Deadline:** 15 September 2026

---

## 1. What changed, and why this document exists

The product was built on an assumption that turned out to be false: that an Azerbaijani
student is measured against a published admission cutoff. In every destination they are
not — published thresholds describe the *domestic* route, and our student enters through an
international one. ADR-0008 recorded that and re-aimed the model at selectivity.

Two days of research since then found something better than a correction. The Azerbaijani
state publishes, as open machine-readable data, **the exact list of universities and
programmes it will fully fund, with numeric eligibility rules**. That single source answers
"which universities are known and demanded", "what does the student need", and "what does it
cost" simultaneously — and no competitor is using it.

This design reorients the product around **routes** rather than university lists, because
the research established that for a school-leaver the binding question is not *where do I
qualify* but *which paths are even open to me*.

---

## 2. Verified findings this design rests on

Everything in this section was confirmed by fetching the source named. Nothing is inferred.

### 2.1 Two of six destinations are closed to a school-leaver

| Country | Attestat alone | Opens with |
|---|---|---|
| **Germany** | Studienkolleg / Feststellungsprüfung **only** | 1 year at a recognised Azerbaijani university → direct subject-restricted access |
| **UK** | *"not accepted for direct entry to undergraduate programmes"* | Foundation year, A-levels, IB, **or** 1 year at an Azerbaijani university |
| Poland | accepted with apostille | — direct |
| **Turkey** | **direct** — most private universities accept the diploma and grades with no YÖS at all; some public universities require TR-YÖS or SAT for competitive programmes | — |
| USA | 11-vs-12-year gap; SAT helps, many test-optional | varies |
| China | direct for DP-funded study; **CSC bachelor is Chinese-taught** (see §5.2) | — |

Turkey is the most open of the six and also the largest destination, which is consistent:
TR-YÖS is run by ÖSYM twice a year and can be sat in Turkish, German, Arabic, French,
English or Russian, and **Turkish language ability is not required to take it** — the
language bar is set by the receiving university, not the exam.

Source for Germany: anabin/KMK, *"eröffnet den Zugang zum Studienkolleg/Feststellungsprüfung"*,
with direct access conditional on one completed year of university study. Applies to
attestats from 2015 onward (11-year schooling); pre-2015 assessed differently.

**Both blocked countries share one escape hatch: a year at an Azerbaijani university.** This
is the mechanic the design is built around.

### 2.2 The State Programme is the catalogue spine

`Dövlət Proqramı` — Ministry of Science and Education, published on the national open-data
portal (CKAN) as CSV.

```
dp-bakalavr-2026.csv    1,214 rows   123 universities   15 countries
dp-master-2026.csv      2,907 rows   223 universities   33 countries
                        -----------
                        4,121 rows
Columns: Nömrə, Təhsil səviyyəsi, Ölkə, Universitet, Təhsil proqramı
```

Programmes in our six countries:

| | Bachelor | Master's |
|---|---|---|
| China | 307 | 538 |
| UK | 161 | 382 |
| USA | **0** | 289 |
| Turkey | 106 | 286 |
| Germany | 27 | 189 |
| Poland | **0** | 8 |

Eligibility rules, verified on `dp.edu.az`:

```
Language   C1 minimum (IELTS / TOEFL / DELE / DELF / HSK)
Bachelor   DİM 400–550 depending on field
           OR SAT/ACT at 75th percentile
           OR international Olympiad medal
Age        no limit
Covers     tuition, visa & registration, living, medical insurance,
           international transport, banking fees
Levels     bakalavr · magistratura · doktorantura
Timing     announced at least 6 months before semester start
```

**The DİM score is an input to studying abroad.** This closes a question that has been
reopened three times: the DİM corpus is neither a separate product nor mere calibration — it
is a direct input to the state's funding decision.

### 2.3 At bachelor level, scholarships barely exist

| Programme | Level |
|---|---|
| Chevening (UK) | Master's only |
| NAWA Banach (Poland) | Master's only; for Azerbaijanis, humanities/social sciences only |
| Erasmus Mundus Joint Masters | Master's only |
| DAAD individual grants | overwhelmingly Master's/PhD |
| Erasmus+ | exchange within a degree, not a full degree |
| **Türkiye Bursları** | **Bachelor** — fully funded, under 21, applications 10 Jan – 20 Feb |
| **Dövlət Proqramı** | **Bachelor + Master's + PhD** |

**Consequence: at bachelor level the lever is affordability, not scholarships.** Germany's
public universities charge no tuition; Turkey runs ~$1,000/semester — *cheaper than studying
in Azerbaijan*, which is why Turkey is the number-one destination; Poland ~€2,000/year. A
"fully funded" filter at bachelor level would return almost nothing and look broken while
being accurate. Ranking is therefore on **total cost to degree**, with scholarships as one
input.

### 2.4 Destination reality

```
~48,000 Azerbaijani students abroad   (18,000 in 2018 → 45,000+ in 2022)
Turkey  #1 by a wide margin — 15,546 by 2017-18, from 6,177 in 2013-14
Russia  #2 — out of scope
UK, USA, Germany  the non-regional destinations that rank
Poland  absent from top-destination rankings
```

---

## 3. Two segments, one engine

| | DP-funded | Self-funded |
|---|---|---|
| Size | ~400/year | the ~48,000 |
| Binding question | Does my DİM + C1 clear the bar, and which of the 223 are open? | What can I afford, and where do I qualify? |
| Data | **one official CSV, in hand** | per-university requirements — the extraction work |
| Ranking | by fit within the eligible list | by total cost to degree |

Both run through the same eligibility engine. The DP segment is small but its data is
authoritative and already available; the self-funded segment carries the volume and the
collection cost. Shipping the DP path first de-risks the deadline.

---

## 4. Domain model

### 4.1 Route

The primary object is a **Route**, not a university.

```
Route = qualification held → entry mechanism → country, at a level
```

| Field | Meaning |
|---|---|
| `level` | `bachelor` \| `master` — **part of the key, not a filter** (see below) |
| `preconditions` | qualification state required to start |
| `produces` | qualification state on completion |
| `time_cost_months` | 0 for direct, 12 for Studienkolleg / prep year |
| `money_cost_range` | AZN, low–high |
| `exams_required` | e.g. IELTS 6.0, TestAS, SAT, HSK, none |
| `provenance` | `seed` / `claude-extracted` / `human-verified` (ADR-0007 §5) |

**Level is a key, not a filter.** Every finding in §2 is level-specific and several invert
between the two: Germany and the UK are blocked to a school-leaver but **open to a bachelor
holder**, since a completed degree is an accepted entry qualification where an attestat is
not. Scholarships invert the other way — Chevening, Banach, Erasmus Mundus and most of DAAD
exist only at master's, while Türkiye Bursları' hard **under-21** limit exists only at
bachelor. The DP publishes two separate catalogues with different countries in them (USA and
Poland have **zero** bachelor programmes and 289 and 8 master's respectively).

A design that filtered a level-agnostic route set would therefore produce confident wrong
answers in both directions: Germany BLOCKED for a master's applicant it is open to, and DP
programmes offered in countries that fund none at that level. So the student's `level` is
asked in the first profile step alongside their qualification, and it selects which routes,
which requirement rows and which funding tiers exist at all.

Against a student's qualification state the engine classifies each route:

- **OPEN** — every precondition met
- **UNLOCKABLE** — met except for a named, obtainable set (with what and by when)
- **BLOCKED** — a precondition that cannot be obtained this cycle, with the reason

**Routes compose, capped at two hops.** "One year at an Azerbaijani university" is itself a
route whose `produces` satisfies Germany's and the UK's `preconditions`, which is what lets
the engine say:

> Germany is blocked today. Two ways to open it: Studienkolleg (12 months, TestAS) — or one
> year at a university here, which also keeps Poland and Turkey open.

The two-hop cap is deliberate. Deeper chains exist but do not help a 17-year-old, and
uncapped graph search turns a product into a research project.

Route definitions are **hand-written and human-verified with a citation each** — roughly 15
across six countries. They are the highest-value data in the product and none of it is
scraped.

### 4.2 The three numbers

| Number | Mechanism | Applies to |
|---|---|---|
| **Eligibility** | Deterministic rules | everything |
| **Admission chance / selectivity** | **ML** | see below |
| **Total cost to degree** | Arithmetic: tuition + living + prep-year − scholarship | everything |

**The ML has two homes, and the primary one is the prep-year route.**

*Primary — DİM cutoff prediction for the prep year.* Germany and the UK are blocked to a
school-leaver, and both unlock through **one year at an Azerbaijani university**. So the
question "which Azerbaijani programme can I get into next year?" is not a domestic
side-feature — it is **step one of two blocked routes**, and answering it is what makes those
routes actionable rather than merely named.

This is also the only place in the entire project where the honest claim is available. DİM
admission is mechanical: clearing the cutoff *is* admission, so `P(next year's cutoff ≤ your
score)` **is** the success rate rather than a proxy for it. Nowhere else survives that test —
which is precisely why every earlier attempt to state it elsewhere had to be withdrawn
(ADR-0008). Measured on real data: department-mean baseline 57.37 → HistGradientBoosting
**41.34, a 27.9% improvement**.

The DİM model also feeds two other surfaces: the DP eligibility band (400–550 by field, §2.2)
and the domestic baseline a student is implicitly comparing against.

*Honest limit, stated up front:* the Azerbaijani corpus has **three intake years**. Cold-start
prediction works and is measured; year-over-year forecasting is thin, and AZ forecasting was
skipped in the earlier evaluation for exactly this reason. The model therefore ships with an
uncertainty band, validated on the single held-out year available, and labelled as such. It
does not ship as a point estimate.

*Secondary — selectivity from College Scorecard.* 1,853 US institutions over nine years with
real admit-rate labels. Its product reach is narrow (US bachelor, where DP funds nothing), so
its role is to demonstrate the method **generalises to a second country** rather than to carry
the product.

Everywhere else — master's programmes, and non-US countries without published rates — gets
eligibility and cost with **no ML number at all**, following the "requirements only" pattern
of ADR-0007 §3. That is a deliberate, labelled absence, never filled by estimation.

---

## 5. Data sources

| Source | Status | Use |
|---|---|---|
| `dp-bakalavr-2026.csv`, `dp-master-2026.csv` | **verified, downloadable** | catalogue spine, funded-route eligibility |
| `dp.edu.az` rules | **verified** | DP eligibility thresholds |
| College Scorecard (`usa_cutoff_history.csv`) | **in repo** — 1,853 institutions × 9 years, admit rate on every row | selectivity model |
| DİM open-data API (`ws.dim.gov.az/wa_open_data/api/json/…`) | **found, unprofiled** | DİM scores; official, and *not* the forbidden qebulai.az |
| `ixtisas-istiqamətləri` (field taxonomy) | **found** | field labelling (ADR-0007 §9) |
| **DAAD International Programmes JSON API** | **verified 31 Aug** — 2,306 programmes | Germany: catalogue, tuition, deadlines |
| UCAS Courses Data Service | **ruled out** — commercial licence only | — UK stays manual |
| studyinturkiye.gov.tr (ÖSYM / TR-YÖS) | official, unprofiled | Turkey route + exam rules |
| campuschina.org (CSC) | official; CUCAS is a third-party aggregator and excluded | China funding |
| Per-university international requirements | **partly solved for Germany; the critical path elsewhere** | the remaining collection work |
| Scholarships (Türkiye Bursları, DP, Chevening, DAAD, NAWA, CSC) | **does not exist** | funding layer |
| AZ DİM cutoffs (2,576 rows), Turkish YKS (115,482 rows) | in repo | training corpora only; **no further investment** |

### 5.1 What we extract from a university's application page

This is the critical path and the largest uncertainty, so the target schema is fixed here
rather than discovered during collection. One row per (university, programme, **level**,
intake), and **every field carries `source_url`, `retrieved_at` and a provenance state.**

| Field | Notes |
|---|---|
| `level` | `bachelor` \| `master`. Part of the key — the same university publishes different requirements, fees and deadlines per level |
| `entry_qualification_accepted` | attestat / attestat+foundation / 1-year university / A-level / IB / bachelor degree. **The field that decides whether a route is open.** |
| `foundation_required` | boolean, and which providers if so |
| `language_requirement` | test, minimum score, and the language of instruction |
| `entrance_exam` | SAT / ACT / YÖS / TestAS / CSCA / GRE / GMAT / none, with minimum |
| `gpa_minimum` | in the source's own scale, plus the scale itself |
| `tuition_per_year` + `currency` | for **international** students — the domestic figure is the wrong one |
| `living_cost_estimate` | city-level where the university publishes one |
| `application_deadline` | per intake; multiple rows where a university runs several |
| `application_portal` | UCAS, uni-assist, Common App, IRK, campuschina, YÖS portal, direct |
| `application_fee` | often overlooked and a real barrier at UK/US volume |
| `documents_required` | apostille, translation, transcript, motivation letter, references |

`tuition_per_year` deserves emphasis: quoting a domestic or EU fee to a non-EU applicant is a
silent error of exactly the kind §8 warns about, and it is the single easiest field to get
wrong because it is usually the more prominent number on the page.

### 5.2 Funding: three tiers, all eligibility-gated

Funding is not one list. It has three distinct tiers with different owners and, critically,
**different gates — several of which have nothing to do with academic merit.**

**Tier 1 — Azerbaijani state (`təqaüd`)**

| Programme | Level | Gate |
|---|---|---|
| **Dövlət Proqramı** — financed by SOFAZ, run by the Ministry | bachelor · master · PhD | C1 + DİM 400–550 (or SAT/ACT p75, or Olympiad medal); **only the 223 listed universities** |
| **SOCAR Xarici Təqaüd Proqramı** | master's | **employment-gated — SOCAR group employees only**; age ≤40 (45 for MBA); IELTS 6.0 / TOEFL 80 / B2 |
| **Prezident Təqaüdü** | — | 600–700 AZN/month, ~100–150 places/year, **domestic study only — not for abroad** |

The Presidential scholarship is listed precisely so the product does *not* offer it as a
study-abroad option. It is the most prestigious domestic award and students will ask about it.

**Tier 2 — Destination-country government**

| Programme | Level | Verified detail |
|---|---|---|
| **Türkiye Bursları** | bachelor+ | fully funded; **under 21** for bachelor; applications 10 Jan – 20 Feb |
| **CSC** (China) | bachelor · master · PhD | **Bachelor recipients must register for Chinese-taught courses** — English-taught is open to graduate and non-degree students only. Bachelor also requires a **CSCA** score, an exam this project has never modelled. Master's English-taught needs IELTS 6.5 / TOEFL 80 or 2 years' prior English-medium study; Chinese-taught master's needs HSK 4 plus a year of Chinese. Applications early January to early April via campuschina.org; Type A (embassy) vs Type B (university) |
| **Chevening** (UK) | master's only | |
| **DAAD** (Germany) | overwhelmingly master's/PhD | |
| **NAWA Banach** (Poland) | master's only | for Azerbaijanis, humanities/social sciences only |
| **Erasmus Mundus** | master's only | |

**Tier 3 — University-level:** merit scholarships, tuition discounts, need-based aid. Turkish
private universities discount heavily, which is why they appear affordable in agency
marketing; the discount is real but is not a scholarship and is recorded as a discount.

**A funding programme IS a route.** The Dövlət Proqramı has preconditions (C1, DİM 400–550),
`produces` funded access, carries a time and money cost of zero, and gates a fixed list of
223 universities. That is exactly the Route shape in §4.1, and it is modelled as one rather
than as a parallel concept — so "Germany is blocked, and here are two ways to open it" and
"DP is available, and here is what it requires" run through a single engine and compose with
each other. A student can then be told that the prep year at an Azerbaijani university both
opens Germany *and* preserves DP eligibility, which neither concept could express alone.

**Scholarships therefore run through the same eligibility engine as programmes.** A scholarship the
student cannot win is a false inclusion, and the gates above show why: SOCAR's is employment,
Türkiye Bursları' is age, Chevening's and Banach's is degree level, DP's is a fixed university
list. None of those are visible from a scholarship's marketing page, and all of them are
checkable.

**Wording rule: "possibly eligible", never "you will get it".** Eligibility and award are
different events, and every programme here is competitive — the DP funds roughly 400 places
against a pool far larger, Chevening and Türkiye Bursları more sharply still. What the engine
checks is whether the student clears the *stated gates*; the selection that follows is a
committee decision no dataset in this project models. So the product's strongest permitted
claim is **"you meet the published requirements for this award"**, with the gate that was
checked shown beside it. "You qualify for a full scholarship" is prohibited output, in
generated text and in UI labels alike, and it is precisely the phrasing that makes agency
marketing untrustworthy. The absence of a probability here is deliberate and labelled, the
same as the missing second number in §4.2.

### 5.3 Source order — aggregator before scraper

`data-sourcing.md` (28 Aug) prescribes this order and it was not followed, which cost two days
on hochschulstart and per-university NC pages before anyone checked DAAD. It is now binding:

```
1. National aggregator / open dataset   DP CSVs · DAAD API · anabin · College Scorecard
2. Sitemap                              /sitemap.xml, filter /programmes/ /courses/
3. The catalogue's own JSON endpoint     DevTools -> Network -> XHR, before writing a parser
4. Manual curation                       30-50 records is 2-3 days, and beats a pipeline
5. LLM extraction at scale               only once the schema is proven by 1-4
```

**Checked at tier 1 on 31 August:**

| | Result |
|---|---|
| **DAAD** (Germany) | **Open.** JSON API found at tier 3: `www2.daad.de/…/api/solr/en/search.json`. **2,306 programmes** — 363 bachelor, 1,747 master, 171 PhD, **25 preparatory courses** (the Studienkolleg route). `academy`, `city`, `subject`, `tuitionFees`, `applicationDeadline`, `programmeDuration` and `link` are **100% populated** over a 100-record sample. Language levels are **not** in the list endpoint — they need the HTML detail pages, ~77 minutes at the site's own `Crawl-delay: 2` |
| **UCAS** (UK) | **Closed.** Courses Data Service is a paid 12-month licence with silver/gold tiers and no public API. The UK requires manual curation |

`tuitionFees` values are real and directly support §2.3: **53% "No tuition fees"**, 32%
"Tuition varies", the remainder actual figures. Deadlines are real dates
("Register by 15 July 2027").

**Terms not yet cleared.** `www2.daad.de/robots.txt` returns 404, so nothing is stated there;
the main host sets `Crawl-delay: 2`, carries no AI-specific rules and no TDM reservation, and
explicitly disallows the **scholarship** database (`/deutschland/foerderung/stipendiendatenbank/00462.*`)
— not the programmes one. That reads as permissible but DAAD's terms of use have not been
read. **Read them before any bulk fetch**, and honour `Crawl-delay: 2` regardless.

**Legal position unchanged:** qebulai.az remains excluded (robots.txt disallows ClaudeBot,
`Content-Signal: ai-train=no`, Article 4 EU 2019/790 reservation, and a direct competitor).
hochschulstart.de's PDFs sit under a `Disallow: /fileadmin/` path and are not to be crawled.
`nc-werte.info`, `studis-online.de` and `auswahlgrenzen.de` are aggregators — usable to
*discover* official URLs, never as sources.

### 5.4 Freshness

`architecture-decisions.md` §3 (28 Aug) settled this and it is carried forward unchanged,
because a deadline is the field most likely to be wrong and the most damaging when it is:

| Mechanism | Behaviour |
|---|---|
| **Text hash** | Fingerprint each page. Re-fetch, re-hash, compare. Identical → do nothing, no re-extraction cost. Different → re-extract the fields and refresh |
| **`last_checked`** | Stored per record and **shown to the student**. Honesty beats false confidence |
| **Tiered re-check** | Deadlines and fees checked often; descriptions rarely change |
| **Change guardrail** | Keep previous values rather than overwriting blindly. Implausible jumps — tuition triples — are flagged for human review, **not published** |

The guardrail is the same rule as ADR-0004 in a different costume: an implausible new value
is a suspected extraction failure, and the correct response is to hold the old value and
raise a flag, never to publish the new one because it arrived more recently.

---

## 6. What the student sees

ADR-0007 §2 defined two modes over one spine. They survive this redesign intact — the routes
change what each mode *says*, not that there are two — and step 9 of §10 builds them.

**Discovery.** One profile step: level, qualification held, exam scores, budget, destination
preference, field. Results refine live as fields are filled, and the page is never empty
before input — it opens on the most competitive or most popular programmes in the field.
**Destination is asked first and never excludes**: chosen countries fill the main results,
while a persistent *"your score goes further here"* section surfaces the strongest matches
from countries the student did not name. Gating on destination would be the steering
behaviour this product exists to refuse, implemented in software.

**Target.** The student names a university. They get a gap statement, a requirement
checklist, a process checklist, and alternatives that close the gap. A named university we
do not hold produces a plain *"we don't have this yet"* plus what we do hold for that
country — never a guessed cutoff, never a silent substitution.

**Target excludes a study plan.** *"You are 68 points short"* is supported by the data.
*"Retake DİM in March, target +70, focus on maths"* is not — nothing in any dataset links
effort to score change. The roadmap is a gap, a checklist, a deadline and alternatives.

**The walkthrough step 9 must complete**, for a profile of *attestat, DİM 520, IELTS 7.0,
bachelor, engineering, budget 8,000 AZN/year*:

```
1  Turkey and Poland OPEN — direct entry on the attestat.
   Germany and the UK BLOCKED — attestat opens Studienkolleg only.
2  Two unlocks named for Germany: Studienkolleg (12 months, TestAS)
   — or one year at an Azerbaijani university, which ALSO opens the UK
   and preserves DP eligibility. Both costed.
3  DP: DİM 520 clears the 400–550 band, IELTS 7.0 clears C1.
   The funded bachelor set for open countries is listed, with the band shown.
4  Everything ranked by total cost to degree, each row carrying its
   last_checked date and its source.
5  Student picks one. Roadmap: gap, requirement checklist, process
   checklist, deadlines — and every claim cited or absent.
```

Nothing in that sequence needs a number the project cannot honestly produce.

---

## 7. Scope

**Six countries:** Turkey, Germany, UK, USA, Poland, China.
**Two levels:** bachelor and master's. **PhD excluded** — supervisor-driven admission and
funded-position financing share no mechanics with the rest and would need data we cannot get.

**Coverage target**, weighted to where students actually go and consistent with the cut
order in §10 — Poland is not given a Turkey-sized budget when it is first to be cut:

```
Turkey    ~25    #1 destination, cheaper than home, 286 DP master's programmes
China     ~20    largest DP destination at both levels
Germany   ~20    free public tuition; the highest-value trade-off in the product
UK        ~15    382 DP master's programmes, but expensive self-funded
USA       ~10    289 DP master's, zero DP bachelor
Poland     ~5    3 DP universities total; direct entry is its only virtue
```

Counts are *total* per country, and the DP list already supplies most of them — 13 Turkish,
12 German, 19 UK, 23 US and 33 Chinese universities appear in it. Curation effort therefore
goes to institutions outside the DP list, chosen in three deliberate buckets:

1. **Where they go** — institutions carrying real Azerbaijani enrolment.
2. **What they aspire to** — Boğaziçi, METU, Bilkent, Koç, Sabancı, TUM, LMU, UCL, Warsaw.
3. **What agencies push** — commission-heavy privates (Istanbul Aydın, Bahçeşehir, Okan,
   Vistula). **Including these is the point**: showing them beside Boğaziçi with honest cost
   and selectivity is the anti-steering value an agency cannot offer.

The DP list supplies buckets 1 and 2 for free and authoritatively.

---

## 8. Where the LLM sits

Per ADR-0007 §6, the contract is by claim type, not by layer:

| Claim | Rule |
|---|---|
| Numbers | ML or arithmetic only; every numeral in generated text validated against the payload |
| University-specific qualitative | cite-or-drop |
| Country process steps | curated per-country library |
| Framing, tone, explanation | free |

The LLM's product job is the advisory layer the user named: interpreting "I'm interested in
X", explaining why a route is blocked, and narrating the gap. It also does bulk requirement
extraction offline, where its output is `claude-extracted` provenance and never
`human-verified`.

**Extraction failure is silent** — a wrong IELTS minimum sends a student to a university that
will reject them and nothing in the system notices. This is where ADR-0007's provenance
states and cite-or-drop rule matter most, and why unverified requirements filter but never
silently: every exclusion is shown with its reason and source.

---

## 9. How this lands on the existing codebase

This design has been written as though the repository were empty. It is not, and a spec that
does not say what happens to the running code is a spec that gets ignored the first time they
disagree. There is no rewrite here — the spine is sound and the additions are additive.

**Kept as-is.** FastAPI + SQLAlchemy 2.0 async + Alembic + Postgres/pgvector; the auth flow;
`students`, `programs`, `scholarships`, `applications`, `documents`; the migration chain
(`ca962f4261fb` → `a1b2c3d4e5f6`); the test setup (aiosqlite + `StaticPool`). New tables are
new migrations on that chain, never a reset.

**Added.** `routes`, `student_qualifications`, `program_requirements`, `funding_programmes` —
steps 1–4 of §10. `programs` gains `level`, and `program_cutoff_history` gains the 3-column
unique index `(country, source_program_code, intake_year)`, which is the key that was
verified duplicate-free; the 4-column version considered earlier covers 0.8% of rows because
`variant_index` is NULL on all 115,482 Turkey rows.

**Provenance reuses the existing review queue.** `admin.py` already has the flagged-programme
queue, the verify endpoint and `confidence_score` (now nullable, since 31 Aug). The three
provenance states of §4.1 map onto it rather than defining a parallel mechanism: a
`claude-extracted` row is a queued row, and `verified_by` is written only by the verify
endpoint — which means the endpoint must first be given authentication, per the table below.

**Re-aimed, not deleted.** `matching.py` computes a deterministic explainable match score —
that is the §4.2 eligibility number and it survives. What changes is what sits beside it: a
route classification instead of an implied admission probability. `chat.py` becomes the §8
advisory layer under the cite-or-drop contract. `embeddings.py` and pgvector keep their
`architecture-decisions.md` §2 role — filter in SQL, search in the same store.

**Blocking defects, found 31 August and now carried as step 0 of §10.** These are on the
path this spec writes through, and each ships bad data or worse:

| Defect | Why it blocks |
|---|---|
| `require_admin_user` returns `{"is_admin": True}` **unconditionally** | No authentication on the admin endpoints at all — anyone can call `/programs/{id}/verify` and publish unverified data to students. The single most serious item in the repo |
| `admin.py:252-271` — verify checks the demo store **before** the database | Reports "successfully verified and published" without writing anything |
| `export.py:40-56` invents a student (`gpa 3.65`, `ielts 7.0`) and a TUM programme on an empty payload | The same fabrication class fixed in `extraction.py` on 31 Aug, in a second location. Should be a 422 |
| `pdf_export.py:176-182` — three fabricated defaults behind truthiness guards | Dead today, live the moment a guard changes |
| Rows written by the deleted extraction fallback | Quarantine any `programs` row with `extraction_notes="Extracted via fallback parser."` or university `"Extracted University"` before the catalogue is trusted |
| `README.md` | Three broken ADR links, a false "admission probability" claim, deleted DAAD scrapers advertised, wrong venv path |

Budget **2 days** for this table. It is not optional cleanup: ADR-0004 is the project's
central promise, and three of the six rows are that promise being broken in code.

---

## 10. Build order, and what gets cut

Ordered so that each step ships something usable alone.

**This spec is larger than one implementation plan.** Step 0 plus steps 1–4 form the first
plan — they close the defects and deliver the DP path end to end, which is the
deadline-critical core. Steps 5–9 get their own plans; step 7 in particular is a collection
project whose size is not yet known, and scoping it as a task inside a larger plan would
hide that.

| # | Step | Days | Done when |
|---|---|---|---|
| 1 | **DP catalogue loader** — two CSVs, 4,121 rows | 1 | Both files load idempotently; a second run inserts 0 rows; counts match §2.2 exactly |
| 2 | **`student_qualifications` + `program_requirements`** — the §5.1 schema, keyed by level | 4 | A profile round-trips; requirements join to catalogue rows on (university, programme, level, intake); every row carries provenance and `source_url` |
| 3 | **Route definitions + engine** — ~15 hand-written, cited | 3 | Attestat-only profile returns Germany and UK **BLOCKED** with both unlocks named, and Turkey/Poland/China **OPEN**; two-hop composition produces the prep-year path |
| 4 | **DP eligibility as a route** | 2 | DİM 520 + IELTS 7.0 returns the funded programme set filtered by country and level, with the band that decided it shown |
| 5 | **DAAD import** — 2,306 programmes via the JSON API | 2 | Tuition and deadline populated for ≥95% of imported rows; `Crawl-delay: 2` honoured; terms read and recorded |
| 6 | **DİM cutoff model** — the primary ML | 2 | Beats the department-mean baseline on a held-out year (baseline 57.37); ships quantile bands, not a point estimate; refuses to predict where history < 2 years |
| 7 | **Manual curation** — 50 programmes for Turkey, UK, Poland, USA | 3 | 50 rows human-verified with sources; the schema survives contact with all four countries unchanged |
| 8 | **Scholarship layer** — DP, Türkiye Bursları, CSC, SOCAR, Chevening, DAAD, NAWA | 2 | Every scholarship carries its gate; an under-21 check and an employment check both demonstrably exclude |
| 9 | **Results UI + roadmap view** — Discovery and Target (§6) | 5 | The §6 walkthrough completes end to end for the profile named there |
| 0 | **Defect table (§9)** — admin auth, `export.py`, verify ordering, quarantine, README | 2 | No endpoint publishes without authentication; no code path fabricates a record; the six rows of §9 are closed |

**~26 person-days against 4 people × 15 days**, now including the §9 defects. Step 0 is
numbered last and sequenced first: it is the smallest item on the list and the only one that
is already shipping wrong behaviour.

**Step 7 must start immediately and in parallel.** It is the only item that cannot be
compressed by writing better code, and `data-sourcing.md` is right that 50 records is two to
three days of human work — but only once someone begins.

**Cut order if the schedule slips:** Poland first (8 DP master's programmes, zero bachelor,
absent from destination rankings), then the USA bachelor path (zero DP programmes), then
curation depth — reduce universities per country rather than dropping a country, so the
product stays consistent.

**Not cuttable:** the DP path (1, 3, 4). It is the only segment where the data is already
authoritative, and it is the clearest differentiator against every agency in the market.

---

## 11. Open questions

- The DİM open-data API is found but unprofiled. What does it actually expose, and does it
  cover cutoffs or only aggregate statistics?
- Do the DP CSVs exist for earlier years? Multi-year history would allow showing whether a
  programme's eligibility is stable.
- Türkiye Bursları' 2026 window (10 Jan – 20 Feb) has closed; next is January 2027. Does the
  product show closed cycles with their next opening, or hide them?
- China's **funding** mechanics are now verified (§5.2) but its **entry route** is not. The
  CSCA requirement for CSC bachelor applicants is a new exam we have never modelled, and
  whether an Azerbaijani attestat gives direct entry to Chinese universities outside CSC is
  unchecked — this is the same question that turned out to close Germany and the UK.
- SOFAZ reportedly supports 200+ master's students a year. Whether that is the funding
  mechanism *behind* the Dövlət Proqramı or a separate award with its own application is
  unresolved, and it matters: if separate, it is a Tier 1 entry we are missing.
- Türkiye Bursları' under-21 bachelor limit interacts with the prep-year routes. A student
  who spends a year at an Azerbaijani university to open Germany may age out of Türkiye
  Bursları in the process. The engine should surface that trade-off; whether it can is
  untested.
- Poland's 8 master's programmes may not justify its curation budget even before any cut.
