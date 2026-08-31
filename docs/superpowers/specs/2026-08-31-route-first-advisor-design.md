# AUSA — route-first advisor: design

**Date:** 2026-08-31
**Status:** proposed, awaiting review
**Supersedes in part:** [ADR-0007](../../adr/0007-three-number-model-and-honesty-tiers.md) §2, §3, §4; [ADR-0008](../../adr/0008-selectivity-replaces-cutoff-prediction.md) §4 (country and level scope)
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
| Turkey | international quota / YÖS / SAT | — direct |
| USA | 11-vs-12-year gap; SAT helps, many test-optional | varies |
| China | varies by institution; HSK or English-taught | — direct |

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
Route = qualification held → entry mechanism → country
```

| Field | Meaning |
|---|---|
| `preconditions` | qualification state required to start |
| `produces` | qualification state on completion |
| `time_cost_months` | 0 for direct, 12 for Studienkolleg / prep year |
| `money_cost_range` | AZN, low–high |
| `exams_required` | e.g. IELTS 6.0, TestAS, SAT, HSK, none |
| `provenance` | `seed` / `claude-extracted` / `human-verified` (ADR-0007 §5) |

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
| **Selectivity** | **ML** — trained on published admit rates | **US bachelor only** |
| **Total cost to degree** | Arithmetic: tuition + living + prep-year − scholarship | everything |

Selectivity is honest only where we hold real admit-rate labels: College Scorecard, which is
US and undergraduate. Master's programmes and non-US countries get eligibility and cost with
**no selectivity badge** — the "requirements only" pattern ADR-0007 §3 already established.
This is a deliberate, labelled absence, not a gap to be filled by estimation.

---

## 5. Data sources

| Source | Status | Use |
|---|---|---|
| `dp-bakalavr-2026.csv`, `dp-master-2026.csv` | **verified, downloadable** | catalogue spine, funded-route eligibility |
| `dp.edu.az` rules | **verified** | DP eligibility thresholds |
| College Scorecard (`usa_cutoff_history.csv`) | **in repo** — 1,853 institutions × 9 years, admit rate on every row | selectivity model |
| DİM open-data API (`ws.dim.gov.az/wa_open_data/api/json/…`) | **found, unprofiled** | DİM scores; official, and *not* the forbidden qebulai.az |
| `ixtisas-istiqamətləri` (field taxonomy) | **found** | field labelling (ADR-0007 §9) |
| Per-university international requirements | **does not exist** | the critical path |
| Scholarships (Türkiye Bursları, DP, Chevening, DAAD, NAWA, CSC) | **does not exist** | funding layer |
| AZ DİM cutoffs (2,576 rows), Turkish YKS (115,482 rows) | in repo | training corpora only; **no further investment** |

### 5.1 What we extract from a university's application page

This is the critical path and the largest uncertainty, so the target schema is fixed here
rather than discovered during collection. One row per (university, programme, intake), and
**every field carries `source_url`, `retrieved_at` and a provenance state.**

| Field | Notes |
|---|---|
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
silent error of exactly the kind §7 warns about, and it is the single easiest field to get
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
| **CSC** (China) | bachelor · master · PhD | English-taught needs **no HSK at application**; master's requires IELTS 6.5 / TOEFL 80 or 2 years' prior English-medium study; **bachelor requires a CSCA score**; Chinese-taught master's needs HSK 4 + a year of Chinese; deadlines Feb–late April via campuschina.org; Type A (embassy) vs Type B (university) |
| **Chevening** (UK) | master's only | |
| **DAAD** (Germany) | overwhelmingly master's/PhD | |
| **NAWA Banach** (Poland) | master's only | for Azerbaijanis, humanities/social sciences only |
| **Erasmus Mundus** | master's only | |

**Tier 3 — University-level:** merit scholarships, tuition discounts, need-based aid. Turkish
private universities discount heavily, which is why they appear affordable in agency
marketing; the discount is real but is not a scholarship and is recorded as a discount.

**Scholarships run through the same eligibility engine as programmes.** A scholarship the
student cannot win is a false inclusion, and the gates above show why: SOCAR's is employment,
Türkiye Bursları' is age, Chevening's and Banach's is degree level, DP's is a fixed university
list. None of those are visible from a scholarship's marketing page, and all of them are
checkable.

**Legal position unchanged:** qebulai.az remains excluded (robots.txt disallows ClaudeBot,
`Content-Signal: ai-train=no`, Article 4 EU 2019/790 reservation, and a direct competitor).
hochschulstart.de's PDFs sit under a `Disallow: /fileadmin/` path and are not to be crawled.
`nc-werte.info`, `studis-online.de` and `auswahlgrenzen.de` are aggregators — usable to
*discover* official URLs, never as sources.

---

## 6. Scope

**Six countries:** Turkey, Germany, UK, USA, Poland, China.
**Two levels:** bachelor and master's. **PhD excluded** — supervisor-driven admission and
funded-position financing share no mechanics with the rest and would need data we cannot get.

**Coverage target**, weighted to where students actually go and consistent with the cut
order in §8 — Poland is not given a Turkey-sized budget when it is first to be cut:

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

## 7. Where the LLM sits

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

## 8. Build order, and what gets cut

Ordered so that each step ships something usable alone.

**This spec is larger than one implementation plan.** Steps 1–4 form the first plan — they
deliver the DP path end to end and are the deadline-critical core. Steps 5–7 get their own
plans; step 6 in particular is a collection project whose size is not yet known, and
scoping it as a task inside a larger plan would hide that.

1. **DP catalogue loader** — two CSVs, 4,121 rows, official schema. Small, high value.
2. **`student_qualifications` + `program_requirements`** — Tasks 3–4 of the existing
   catalogue-join plan, largely intact; they gain a route dimension.
3. **Route definitions + engine** — ~15 hand-written routes, OPEN/UNLOCKABLE/BLOCKED.
4. **DP eligibility check** — DİM + C1 against the funded list. First end-to-end user value.
5. **Selectivity model** — College Scorecard, US bachelor. The ML deliverable.
6. **Requirement extraction** — the self-funded path; the largest and most uncertain task.
7. **Scholarship layer** — Türkiye Bursları, DP, and university-level discounts.

**Cut order if the schedule slips:** Poland first (8 DP master's programmes, zero bachelor,
absent from destination rankings), then the USA bachelor path (zero DP programmes), then
requirement extraction depth — reduce universities per country rather than dropping a
country, so the product stays consistent.

**Not cuttable:** the DP path (1, 3, 4). It is the only segment where the data is already
authoritative, and it is the clearest differentiator against every agency in the market.

---

## 9. Open questions

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
