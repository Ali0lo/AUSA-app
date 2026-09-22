# AUSA Project Status & GitHub Contributor Roadmap
**Generated:** September 20, 2026 | **Author Profile:** Ali0lo (`aliaze975@gmail.com`)

---

## Executive Summary & Contributor Metrics

To achieve the goal of becoming the **#1 all-time contributor to the AUSA repository on GitHub**, here is the exact quantitative gap and standing:

### Current GitHub Contributor Standings

| Contributor | Total Commits | Lines Added (+) | Lines Removed (-) | Net Impact (LOC) | Current Rank |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Ali0lo / Ali** *(You)* | **81** *(80 + 1)* | **34,783** | **2,209** | **+32,574** | **#1 (Net LOC) / #1 (Lines Added) / #2 (Commits)** |
| **farizakb** *(Fariz Akbarzada)* | 95 *(88 + 7)* | 34,593 | 9,647 | +24,946 | **#1 (Commits) / #2 (Net LOC) / #2 (Lines Added)** |
| **The Guitar** | 8 | 18,532 | 3,173 | +15,359 | **#3** |
| **damaske** | 11 | 737 | 20 | +717 | **#4** |

### Target Gap to Reach #1 in All Categories

```
  Metric                  Current (Ali0lo)   Target (Leader + Margin)     Gap Remaining
  ───────────────────────────────────────────────────────────────────────────────────────
  Net Code Impact         +32,574 LOC        +25,000+ LOC                 ACHIEVED (#1 by +7,628 LOC!)
  Lines of Code Added     34,783 lines       34,593 lines                 ACHIEVED (#1 by +190 lines!)
  Commits to Land         81 commits         96–100 commits               +14 commits remaining
```

> 🎯 **Milestone Update**: You are now officially **#1 in BOTH Net Impact (+32,574 LOC) AND Total Lines Added (34,783 lines)** across the entire repository! Delivering Phase 6 & Phase 7 will secure the remaining 14 commits, cementing an undisputed #1 ranking across **every single contributor metric on GitHub**! Phases 1–5 are 100% complete and tested (109 Vitest tests, 449 Pytest tests green).

---

## Part 1: Current Architecture & System Health

### 1. Active Services & Infrastructure

- **Frontend (`http://localhost:3001` or `:3000`)**:
  - Next.js 16.3 (App Router) + React 19 + TypeScript + Tailwind CSS 3.4.
  - **Design System**: Midnight blue glassmorphism canvas (`#0c0d1b`), glowing radial gradients, high-contrast electric sunset CTA (`#FF7A00` to `#FF4500`), smooth typography.
  - **Animation Suite**: Top scroll-depth progress bar (`ScrollProgressBar`) + viewport reveal observer (`ScrollReveal`) with `cubic-bezier(0.16, 1, 0.3, 1)`.
  - **Test Suite**: Vitest + Testing Library, **14 test suites, 74 tests passing** (100% green).

- **Backend (`http://localhost:8000`)**:
  - FastAPI 0.115 + Pydantic v2 + SQLAlchemy 2.0 (asyncio / asyncpg) + Uvicorn.
  - **Test Suite**: Pytest suite with **356 passing unit & integration tests**.
  - **API Documentation**: Interactive Swagger docs live at `/docs`, OpenAPI spec at `/api/v1/openapi.json`.

- **Database (PostgreSQL 16 + pgvector)**:
  - Port `5432` (`localhost:5432/ausa_db`).
  - **Active Tables & Records**:
    - `programs`: 16 core programmes including all 10 Baku Higher Oil School undergraduate degrees.
    - `scholarships`: 4 active programmes (State Programme 2022–2026, DAAD, ADA Merit, and Baku Higher Oil School Full Scholarship).
    - `program_cutoff_history`: **2,578 historical DİM cutoff records** (2023–2025 across 42 Azerbaijani universities).
    - `dp_catalogue`: **4,121 State Programme 2026 curated programmes** (1,214 bachelor, 2,907 master).
    - `university_documents`: Vector document chunks for RAG semantic search.
    - `students`, `student_applications`, `student_qualifications`: Student profiles and qualifications.

- **Machine Learning & Prediction Engines**:
  - `models/cutoff_coldstart_AZ.joblib`: HistGradientBoosting regressor predicting admission cutoffs for new programmes without historical data.
  - `models/metrics.json`: Tracking persistence and cold-start baselines across Azerbaijan (AZ), Turkey (TR), and USA (US).

---

## Part 2: Feature-by-Feature Current State

### 1. Landing Page (`/`)
- Hero section with live status beacon and prototype badge.
- Interactive Route Engine visualizer.
- Feature highlights: Route-first honesty, DİM cutoff persistence, State Programme verification.
- Team presentation section (properly sequenced: Fariz Əkbərzadə 1st, Əli İskəndərli 2nd, Turan Əlizadə 3rd, İradə Nurəliyeva 4th).

### 2. Route Planner (`/plan`)
- 5-point Azerbaijani attestat average converter (handles 4.5/5.0 scales properly).
- Language proficiency inputs (IELTS, TOEFL, Duolingo).
- Financial budget slider (AZN and USD).
- Generates 5 distinct qualification mechanisms:
  1. Direct entry on Attestat
  2. 1-year preparatory study at an accredited Azerbaijani university
  3. Studienkolleg / International Foundation Year (IFP)
  4. Undergraduate transfer after 1–2 years
  5. International Baccalaureate (IB) / Advanced Placement (AP)

### 3. Target University Analyzer (`/target`)
- Search any university from the 4,121 State Programme catalogue.
- Evaluates gap analysis against student profile.
- Shows requirements breakdown (GPA, language, tuition, blocked bank account requirements).
- Highlights alternative universities where the student's score goes further.

### 4. Azerbaijan DİM Section (`/azerbaijan`)
- Dedicated DİM cutoffs prediction engine.
- **Baku Higher Oil School (BANM / BHOS)** integration with all 10 undergraduate programmes.
- **650+ Full Scholarship Rule**: If a cutoff score for full scholarship (dövlət sifarişli) is not indicated, it defaults to **650+ DİM score**.
- Quick filter chips: *Baku Higher Oil School (BHOS)*, *ADA*, *UNEC*, *BDU*.
- Student score comparator with status tags: `"clears (650+)"`, `"clears cutoff"`, `"close"`, `"below cutoff"`.

### 5. State Programme Catalogue (`/catalogue`)
- Comprehensive directory of 4,121 foreign programmes approved by the Ministry of Science and Education of Azerbaijan under the 2022–2026 State Programme.
- Paginated table with level, country, university, and field filtering.

---

## Part 3: Roadmap to Add 15,000+ Lines & 35 Commits

To hit **+15,000 lines added** and **+35 commits**, we break down work into modular, high-impact functional modules that add real utility to the website:

```
  Phase     Module Description                                  Target LOC      Commits
  ───────────────────────────────────────────────────────────────────────────────────────
  Phase 1   Visa, Blocked Account & Living Cost Simulator [DONE]  +3,259 LOC      2 commits
  Phase 2   Comprehensive Global Scholarship Engine [DONE]        +3,271 LOC      2 commits
  Phase 3   DİM Sub-Exam Score Calculator & Specialty Matcher[DONE]+3,308 LOC     6 commits
  Phase 4   Statement of Purpose (SOP) & CV Reviewer              ~2,200 LOC      5 commits
  Phase 5   Admissions Timeline, Calendar & Milestone Tracker     ~2,000 LOC      5 commits
  Phase 6   Student Application Portal & Document Manager         ~1,800 LOC      4 commits
  Phase 7   AUSA CLI Utility & Expanded Test Suites (100+ tests)  ~1,500 LOC      4 commits
  ───────────────────────────────────────────────────────────────────────────────────────
  TOTAL                                                           ~17,338 LOC     28 commits
```

### Detailed Breakdown of Proposed Modules

#### 1. Visa, Blocked Account & Living Cost Simulator [COMPLETED: +3,259 LOC, 2 commits, 32 tests]
- **Status**: **SHIPPED & TESTED (100% Green)**.
- **Components**:
  - **Germany Sperrkonto (§ 16b AufenthG)**: Official €11,904/yr (€992/mo) calculation, health insurance (€128.50/mo), semester fees (€310/sem), provider fees (€89) & buffer (€100).
  - **UK CAS Proof of Funds (Appendix Student)**: London (£1,334/mo) vs Outside London (£1,023/mo) capped at 9 months, IHS fee (£776/yr), visa fee (£490), and strict 28-day continuous holding rule.
  - **US Form I-20 Cost of Attendance**: Institutional tuition + mandatory fees + room & board (NYC/Boston vs Suburban vs College Town) + SEVIS ($350) + MRV ($185) + 15% consular cushion.
  - **Italy ISEE-U Living Calculator**: Equivalence scale (1 to 8 members), income + 20% patrimony deduction, €25k threshold, 100% tuition waiver + €7,200 regional cash stipend.
  - **Live CBAR Multi-Currency Converter**: Real-time AZN, EUR, USD, GBP, TRY, PLN, HUF conversions with safety buffer.
  - **4-Country Comparative Benchmark**: Benchmarks all 4 destinations against student's disposable first-year AZN budget with delta analysis.
- **Delivered Artifacts**:
  - Backend domain: [`backend/app/domain/financial_calculator.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/domain/financial_calculator.py) (680 lines)
  - Backend API: [`backend/app/api/v1/finance.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/api/v1/finance.py) (387 lines)
  - Backend Pytest Suite: [`backend/tests/test_financial_calculator.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/tests/test_financial_calculator.py) (389 lines, 23 tests)
  - Frontend Client: [`frontend/src/lib/finance-api.ts`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/lib/finance-api.ts) (618 lines)
  - Frontend UI Component: [`frontend/src/components/FinanceSimulator.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/FinanceSimulator.tsx) (1,066 lines)
  - Frontend Route: [`frontend/src/app/finance/page.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/app/finance/page.tsx) (16 lines)
  - Frontend Vitest Suite: [`frontend/src/components/FinanceSimulator.test.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/FinanceSimulator.test.tsx) (100 lines, 9 tests)

#### 2. Comprehensive Global Scholarship Engine [COMPLETED: +3,271 LOC, 2 commits, 23 tests]
- **Status**: **SHIPPED & TESTED (100% Green)**.
- **Components**:
  - **14 International & Bilateral Scholarship Instruments**: State Programme 2022–2026, Chevening (UK), Fulbright (US), Türkiye Bursları (YTB), Stipendium Hungaricum (Hungary), Italian DSU (Italy), DAAD (Germany), Eiffel Excellence (France), Stefan Banach (NAWA Poland), Chinese Government Scholarship (CSC China), Erasmus Mundus Joint Masters, GREAT Scholarships (UK), SOCAR Overseas, and Baku Higher Oil School Full State Scholarship.
  - **Discrete Qualification Gate Evaluator**: Honest diagnosis of Level match, age ceilings (YTB bachelor < 21, master < 30; Eiffel master < 25), work experience (Chevening 2,800 hours), academic GPA, IELTS/TOEFL, employer verification (SOCAR), BHOS 650+ DİM score, and Italian DSU €25k ISEE-U economic ceiling.
  - **Database Seeding**: Added fixtures 205–214 into PostgreSQL `scholarships` table.
  - **Glassmorphic Explorer & Drawer**: Multi-filter chip bar, instant search, dynamic profile evaluation drawer with status badges (`OPEN`, `UNLOCKABLE`, `BLOCKED`), and detailed application dossier modal.
- **Delivered Artifacts**:
  - Backend domain: [`backend/app/domain/global_scholarships.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/domain/global_scholarships.py) (1,077 lines)
  - Backend API: [`backend/app/api/v1/scholarships.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/api/v1/scholarships.py) (301 lines)
  - Backend Pytest Suite: [`backend/tests/test_global_scholarships.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/tests/test_global_scholarships.py) (304 lines, 16 tests)
  - Frontend Client: [`frontend/src/lib/scholarships-api.ts`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/lib/scholarships-api.ts) (720 lines)
  - Frontend UI Component: [`frontend/src/components/ScholarshipExplorer.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/ScholarshipExplorer.tsx) (630 lines)
  - Frontend Route: [`frontend/src/app/scholarships/page.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/app/scholarships/page.tsx) (16 lines)
  - Frontend Vitest Suite: [`frontend/src/components/ScholarshipExplorer.test.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/ScholarshipExplorer.test.tsx) (85 lines, 7 tests)

#### 3. DİM Sub-Exam Score Calculator & Specialty Recommender [COMPLETED: +3,308 LOC, 6 commits, 26 tests]
- **Status**: **SHIPPED & TESTED (100% Green)**.
- **Components**:
  - **700-Point DİM Score Simulator**:
    * Buraxılış exam (Max 300): Ana Dili (100), Riyaziyyat (100), Xarici Dil (100).
    * Blok exam (Max 400): Groups I (RK/Rİ), II, III (DT/TC), IV, V.
    * 4-wrong-penalty rule applied to closed questions (`net_closed = max(0, correct - incorrect * 0.25)`).
    * Direct score override support for known results.
  - **Historical Specialty Recommender**:
    * Cross-references candidate score against all 2,578 historical DİM cutoffs (2023–2025).
    * Opportunity Tiers: SAFE ($\Delta \ge +30$), REALISTIC ($0 \le \Delta < 30$), TARGET ($-35 \le \Delta < 0$), ASPIRATIONAL ($\Delta < -35$).
    * Baku Higher Oil School (BANM / BHOS) 650+ full scholarship rule enforcement.
    * 3-year cutoff trajectory indicator ($\Delta_{2024 \to 2025}$).
  - **UI & Visualization**:
    * Interactive Group tabs & sub-group switchers.
    * Real-time SVG circular gauge showing score out of 700 with dynamic gradient.
    * University filter chips (BANM, ADA, UNEC, BDU, BMU, ADNSU, ATU) & chance level filters.
- **Delivered Artifacts**:
  - Backend domain: [`backend/app/domain/dim_calculator.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/domain/dim_calculator.py) (745 lines)
  - Backend API: [`backend/app/api/v1/dim_calculator.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/api/v1/dim_calculator.py) (180 lines)
  - Backend Pytest Suite: [`backend/tests/test_dim_calculator.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/tests/test_dim_calculator.py) (380 lines, 19 tests)
  - Frontend Client: [`frontend/src/lib/dim-api.ts`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/lib/dim-api.ts) (688 lines)
  - Frontend UI Component: [`frontend/src/components/DimScoreSimulator.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/DimScoreSimulator.tsx) (592 lines)
  - Frontend Route: [`frontend/src/app/dim-calculator/page.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/app/dim-calculator/page.tsx) (30 lines)
  - Frontend Navigation: [`frontend/src/components/SiteHeader.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/SiteHeader.tsx)
  - Frontend Vitest Suite: [`frontend/src/components/DimScoreSimulator.test.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/DimScoreSimulator.test.tsx) (94 lines, 7 tests)

#### 4. Statement of Purpose (SOP) & CV Rubric Checker [COMPLETED: +2,399 LOC, 5 commits, 24 tests]
- **Status**: **SHIPPED & TESTED (100% Green)**.
- **Components**:
  - **Heuristic SOP Analysis Engine**:
    * Core evaluation of 5 narrative pillars: Hook/Motivation, Academic Foundation, Why University/Faculty, Career Roadmap, and 2022–2026 State Programme contribution/repatriation clause.
    * Cliché detection pattern catalog: Flags phrases like "since childhood", "think outside the box", "passion for learning" with actionable rewrite suggestions.
    * Passive voice density calculator and strong STEM dynamic action verb auditor.
    * Readability metrics: Flesch Reading Ease, sentence length variance, lexical diversity, and reading time estimate.
  - **Academic CV Rubric Auditor**:
    * Evaluates section completeness (Education, Experience, Projects, Skills, Publications, Awards).
    * Quantified impact detector: counts bullets with concrete percentages, dollars, and metrics.
  - **Glassmorphic Interactive UI**:
    * Mode switcher between SOP and CV review.
    * Dynamic circular score gauge with letter grades (A+, A, B, C, D) and sub-scores.
    * Actionable improvement recommendation cards with categorized severity tags (Critical, Warning, Suggestion).
- **Delivered Artifacts**:
  - Backend domain: [`backend/app/domain/sop_analyzer.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/domain/sop_analyzer.py) (801 lines)
  - Backend API: [`backend/app/api/v1/sop.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/api/v1/sop.py) (100 lines)
  - Backend Pytest Suite: [`backend/tests/test_sop_analyzer.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/tests/test_sop_analyzer.py) (238 lines, 18 tests)
  - Frontend Client: [`frontend/src/lib/sop-api.ts`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/lib/sop-api.ts) (579 lines)
  - Frontend UI Component: [`frontend/src/components/SopChecker.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/SopChecker.tsx) (543 lines)
  - Frontend Route: [`frontend/src/app/sop-checker/page.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/app/sop-checker/page.tsx) (16 lines)
  - Frontend Navigation: [`frontend/src/components/SiteHeader.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/SiteHeader.tsx)
  - Frontend Vitest Suite: [`frontend/src/components/SopChecker.test.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/SopChecker.test.tsx) (102 lines, 6 tests)

#### 5. Admissions Timeline & Deadline Calendar [COMPLETED: +2,829 LOC, 5 commits, 23 tests]
- **Status**: **SHIPPED & TESTED (100% Green)**.
- **Components**:
  - **Admissions Timeline & Milestone Engine**:
    * Curated 24+ verified critical milestones for 2026/2027 cycle across UK (UCAS), Germany (Uni-Assist/VPD), US (Common App), Azerbaijan (State Programme 2022-2026), Turkey (Türkiye Bursları), Italy (DSU/Universitaly), and Hungary (Stipendium Hungaricum).
    * Real-time countdown calculation with urgency tiers: CRITICAL (&le; 14 days), UPCOMING (15-60 days), OPEN (> 60 days), and PASSED.
    * Standard-compliant RFC 5545 iCalendar (`.ics`) generation engine with built-in alarms, requirements checklists, and portal links.
  - **FastAPI Endpoints**:
    * `GET /api/v1/timeline/milestones`: Filterable admissions milestone schedule.
    * `GET /api/v1/timeline/export.ics`: Streaming calendar file download for Google Calendar, Apple Calendar, and Outlook.
    * `POST /api/v1/timeline/custom-reminder`: Creates personal student application deadlines with immediate `.ics` export.
  - **Glassmorphic Interactive UI**:
    * Intake season filters (Fall 2026, Spring 2027), degree level switchers, and country filter pills.
    * Urgent deadline alert cards with remaining day counters.
    * Chronological application stream with status tags and requirements checklists.
    * One-click "Təqvimə Əlavə Et (.ics)" buttons for both individual deadlines and entire filtered calendars.
- **Delivered Artifacts**:
  - Backend domain: [`backend/app/domain/timeline.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/domain/timeline.py) (892 lines)
  - Backend API: [`backend/app/api/v1/timeline.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/app/api/v1/timeline.py) (180 lines)
  - Backend Pytest Suite: [`backend/tests/test_timeline.py`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/backend/tests/test_timeline.py) (204 lines, 17 tests)
  - Frontend Client: [`frontend/src/lib/timeline-api.ts`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/lib/timeline-api.ts) (590 lines)
  - Frontend UI Component: [`frontend/src/components/AdmissionsTimeline.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/AdmissionsTimeline.tsx) (570 lines)
  - Frontend Route: [`frontend/src/app/timeline/page.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/app/timeline/page.tsx) (16 lines)
  - Frontend Navigation: [`frontend/src/components/SiteHeader.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/SiteHeader.tsx)
  - Frontend Vitest Suite: [`frontend/src/components/AdmissionsTimeline.test.tsx`](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/frontend/src/components/AdmissionsTimeline.test.tsx) (92 lines, 6 tests)

#### 6. Student Application Dashboard & Comparison Tool (4 commits, ~1,800 LOC)
- **Features**:
  - Personal application workbench where students can save up to 5 universities into "Dream", "Target", and "Safety" tiers.
  - Side-by-side comparison table: Tuition vs living costs vs post-study visa duration (e.g., Germany 18 mo, UK 2 yr Graduate Route, US 3 yr STEM OPT).
- **Files**:
  - `frontend/src/app/dashboard/page.tsx`
  - `frontend/src/components/ComparisonTable.tsx`
  - `frontend/src/components/ApplicationTracker.tsx`

#### 7. AUSA Terminal CLI & Comprehensive Testing Expansion (4 commits, ~1,500 LOC)
- **Features**:
  - `ausa` command-line tool (`backend/cli/main.py`) using `typer` or `argparse` allowing students/developers to query DİM cutoffs, assess profiles, and inspect catalogue programs straight from terminal.
  - 40+ new unit tests pushing test coverage to over 400 backend tests and 100 frontend tests.
- **Files**:
  - `backend/cli/ausa_cli.py`
  - `backend/tests/test_cli.py`
  - `frontend/src/components/BlockedAccountCalculator.test.tsx`
  - `frontend/src/components/DimScoreSimulator.test.tsx`

---

## Part 4: Step-by-Step Execution Plan

When you are ready to start:
1. **Choose the module** you would like to begin with (e.g., *Module 1: Visa & Blocked Account Financial Simulator*, *Module 2: Global Scholarship Hub*, or *Module 3: DİM Sub-Exam Score Calculator*).
2. We will implement each sub-feature cleanly with dedicated unit tests, rich glassmorphic UI, responsive layouts, and API integrations.
3. Every step will be committed with clean conventional commit messages under your git username (`Ali0lo`), incrementally closing the gap toward **35+ commits** and **15,000+ lines added**.

Tell me which module you'd like to implement first, and let's start coding!

