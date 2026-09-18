# AUSA — Final Project Report & Course Evaluation

**Date:** 5 September 2026  
**System Version:** AUSA v1.0 (Track D Complete)  
**Repository Branch:** \`main\`  

---

## 1. Executive Summary

The **AI University & Scholarship Advisor (AUSA)** answers one central question for an Azerbaijani student: **Where can you actually go, and who pays?**

Historically, higher education advisory tools and commissioned educational agencies offer illusory precision: computed "match percentages" (e.g. *"87% fit"*), speculative study schedules (e.g. *"study math 2 hours a day to raise score +70"*), or agency-steered destination funnels designed around commissions rather than applicant welfare.

AUSA departs fundamentally from these conventions. It operates as a deterministic, explainable **route planner and funding engine**. It models foreign university access as a sequence of formal qualification conversions (**routes** and **two-hop plans**) paired with verified university requirements and bilateral scholarship gates.

### The Three Pivots
1. **Deletion of Arbitrary Weighted Matching (ADR-0001):** The initial 0.50 academic / 0.30 budget / 0.20 language scoring model was eliminated because arbitrary weights cannot be defended mathematically or empirically.
2. **Rejection of Cutoff Prediction for Abroad Admissions (ADR-0008):** Attempting to predict admissions cutoffs for foreign universities using published score thresholds failed because published cutoffs (such as German Numerus Clausus or Turkish YKS) strictly apply to the domestic applicant pool, systematically excluding international applicants (*Bildungsausländer*).
3. **Adoption of Qualification Routes & Honest Grounding (Spec 2026-08-31):** The binding constraint for an Azerbaijani school-leaver holding an 11-year *attestat* is qualification recognition. Direct entry to Germany and the United Kingdom is closed on the secondary credential, not on grade points. A single preparatory year at an Azerbaijani university converts the credential into a recognised status, unlocking both destinations.

---

## 2. Architecture: Two Products in One Repository

AUSA explicitly maintains **two distinct products in one repository**, linked by a unified domain vocabulary and a conversational chatbot interface:

```
+-----------------------------------------------------------------------------+
|                           AUSA Chatbot & RAG Engine                         |
|           (LangGraph agent + pgvector embeddings + document parser)         |
+--------------------------------------++-------------------------------------+
                                       ||
            +--------------------------++--------------------------+
            |                                                     |
            v                                                     v
+--------------------------------------+  +-----------------------------------+
|     Abroad Routing & Funding         |  |      Azerbaijan DİM Predictor     |
|   (Deterministic Route Engine)       |  |   (HistGradientBoosting Models)   |
|                                      |  |                                   |
| - 16 routes across 6 destinations    |  | - Mechanical cutoff prediction    |
| - Two-hop route composition          |  | - 3 historical intake cycles      |
| - 4,121 State Programme allocations  |  | - Evaluates headroom against      |
| - 10 external scholarship gates      |  |   domestic university faculties   |
| - 12 curated university profiles     |  +-----------------------------------+
+--------------------------------------+
```

### The Data Boundary
The system enforces a strict separation regarding DİM examination data:
- **A DİM score entered by the student** is a verified personal credential. It is valid across the entire product, serving as an eligibility gate for the State Programme (requiring 400 or 550 minimums) and selecting academic tracks.
- **A DİM cutoff predicted by machine learning** belongs exclusively to the domestic Azerbaijan section. It is an internal projection regarding domestic universities and claims zero predictive validity over international admissions abroad.

---

## 3. Track D Implementation: Frontend & User Experience

Track D brings the frontend interface into full alignment with the backend domain engine across three major UX pillars and full documentation coverage:

### D1 · Discovery Flow
- **Level First:** The user selects degree level (*Bachelor* vs *Master*) as the initial input. Findings invert between levels: Germany and the UK are closed to *attestat* holders at bachelor level, but open directly to bachelor degree holders seeking master's degrees. Similarly, the State Programme funds 0 USA bachelor places but 289 master's places.
- **Dynamic Live Refining:** State updates instantaneously on user profile adjustments (qualification, GPA and scale selector, IELTS/TOEFL, DİM, SAT, age, annual budget, preferred destinations, and field of study).
- **Zero Empty Initial State:** The view initialises from verified baseline route fixtures, preventing blank or unhelpful landing states prior to user interaction.
- **Three Clear Status Groups:**
  1. `OPEN`: Routes where current credentials meet published entry gates.
  2. `UNLOCKABLE`: Routes accessible via intermediate steps (e.g. Studienkolleg, Foundation year, or 1 year of domestic higher education), accompanied by exact time and financial costs.
  3. `BLOCKED`: Routes closed due to absolute structural barriers, displaying the precise missing requirements.
- **Destination Ranking Without Exclusion:** Selected countries appear in primary results. To prevent agency steering, a persistent section entitled *"Your score goes further here"* displays reachable alternatives from unselected destinations.
- **Total Cost to Degree:** Ranks plans based on overall cost (living expenses + tuition) and study duration, explicitly flagging when tuition fees have not been published by institutions.

### D2 · Target Flow
- **University Search & Direct Evaluation:** Students can evaluate a specific target institution (e.g. Boğaziçi, TUM, Cambridge, Harvard).
- **Five-Part Roadmap:**
  1. *Objective Gap Statement:* Explains specifically whether credentials qualify for direct entry.
  2. *Requirement Checklist:* Compares applicant GPA, language exams, and entrance tests against published minima.
  3. *Process Checklist & Deadlines:* Outlines certified document translations, portal submissions, and key dates.
  4. *Alternative Routes:* Details pathways that bridge qualification deficits (e.g. Foundation courses).
  5. *Methodology Notice:* Explicitly repudiates ungrounded "study plans", adhering to the principle that effort cannot be arbitrarily mapped to score gains.
- **Honest Catalogue Gap Fallbacks:** For uncurated institutions, AUSA displays an explicit notice: *"We do not have curated admission requirements for this university yet"*, supplemented with verified country-level secondary schooling equivalence.

### D3 · Making Absence Visible
AUSA treats missing information as a first-class citizen, categorising absence into four distinct forms:
1. **Unstated vs Free (`unknown_fields` & `not_stated`):** Unstated tuition is never rendered as blank or 0 AZN (which misleads students into assuming zero tuition). Missing language requirements are marked as *not stated* rather than *none required*.
2. **Catalogue Gap vs Destination Rule (`universities_status`):** Distinguishes between lack of curated data in our database versus a structural finding that a destination's universities do not accept the applicant's qualification.
3. **Unknown vs Missing Gates (`gates_unknown` vs `gates_missing`):** Missing gates represent tasks the student must undertake (e.g. taking an exam); unknown gates represent missing user profile inputs.
4. **Provenance & Verification Stamps:** Every requirement displays its provenance (`seed`, `claude-extracted`, or `human-verified`) and `last_checked` date.
5. **Scale Approximation Warnings (`grade_exact: false`):** Highlights when GPA conversions across disparate educational grading systems are approximate screenings rather than certified conversions.

---

## 4. Verified System Limitations

In strict adherence to project honesty and scientific rigour, the system documentation and evaluation explicitly quote the following four verified limitations verbatim:

1. > **Published cutoffs describe the domestic route in every destination.** German NC tables are footnoted *"ohne Bildungsausländer\*innen"*. This is why the ML is Azerbaijan-only.
2. > **The ML rests on one country and three intake years.**
3. > **Every figure in the funding catalogue is `research-brief` provenance until Track A5 lands.**
4. > **`verified_by` is empty on the DİM training rows until Track A6 lands.**

---

## 5. Verification & Test Evidence

The implementation has been verified through comprehensive automated testing across both frontend and backend suites:

- **Backend Test Suite:** 352 passing unit, domain, and API contract tests (`pytest`, 3 skipped).
  - Verified route engine transitions and two-hop plan compositions.
  - Verified State Programme quota algorithms (4,121 catalogue rows).
  - Verified error handling and contract schemas.
- **Frontend Test Suite:** 72 passing tests across 13 test suites (`vitest`).
  - Verified Discovery Flow interactions and status groupings.
  - Verified Target Flow gap analysis and honest catalog gap fallbacks.
  - Verified absence visibility, provenance indicators, and scale flags.
  - Verified API payload contract conformance.
- **TypeScript Type Safety:** 0 errors under strict compilation (`tsc --noEmit`).
- **Production Build:** Successfully compiled Next.js 16 application bundle.

---

## 6. Conclusion

Track D successfully delivers an honest, grounded user interface and documentation standard for AUSA. By abandoning deceptive match formulas and commission-driven biases, AUSA provides Azerbaijani students with transparent, verifiable admission routes and actionable scholarship intelligence.
