# AUSA Project Status & GitHub Contributor Roadmap
**Generated:** September 20, 2026 | **Author Profile:** Ali0lo (`aliaze975@gmail.com`)

---

## Executive Summary & Contributor Metrics

To achieve the goal of becoming the **#1 all-time contributor to the AUSA repository on GitHub**, here is the exact quantitative gap and standing:

### Current GitHub Contributor Standings

| Contributor | Total Commits | Lines Added (+) | Lines Removed (-) | Net Impact (LOC) | Current Rank |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **farizakb** *(Fariz Akbarzada)* | 95 *(88 + 7)* | 34,593 | 9,647 | +24,946 | **#1** |
| **Ali0lo / Ali** *(You)* | **59** *(58 + 1)* | **22,321** | **2,118** | **+20,203** | **#2** |
| **The Guitar** | 8 | 18,532 | 3,173 | +15,359 | **#3** |
| **damaske** | 11 | 737 | 20 | +717 | **#4** |

### Target Gap to Reach #1

```
  Metric                  Current (Ali0lo)   Target (Leader + Margin)     Gap Remaining
  ───────────────────────────────────────────────────────────────────────────────────────
  Commits to Land         59 commits         96–100 commits               +36 commits
  Lines of Code Added     22,321 lines       34,600+ lines                +12,272+ lines
  Net Code Impact         +20,203 LOC        +25,000+ LOC                 +4,797+ LOC
```

> 🎯 **Strategy**: Delivering 35–40 high-value, structured commits containing genuine, production-grade features, comprehensive dataset expansions, simulators, and tests will add **15,000+ lines** cleanly while making AUSA the most feature-complete study-abroad and domestic university advisory platform in Azerbaijan.

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
  Phase 2   Comprehensive Global Scholarship Engine (7 Grants)    ~3,200 LOC      7 commits
  Phase 3   DİM Sub-Exam Score Calculator & Specialty Matcher     ~2,600 LOC      6 commits
  Phase 4   Statement of Purpose (SOP) & CV Reviewer              ~2,200 LOC      5 commits
  Phase 5   Admissions Timeline, Calendar & Milestone Tracker     ~2,000 LOC      5 commits
  Phase 6   Student Application Portal & Document Manager         ~1,800 LOC      4 commits
  Phase 7   AUSA CLI Utility & Expanded Test Suites (100+ tests)  ~1,500 LOC      4 commits
  ───────────────────────────────────────────────────────────────────────────────────────
  TOTAL                                                           ~16,559 LOC     32 commits
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

#### 2. Comprehensive Global Scholarship Engine (7 commits, ~3,200 LOC)
- **Problem**: Currently only 4 scholarships exist in the database.
- **Expansions**:
  1. **Chevening Scholarship (UK)**: 100% tuition + stipend + flights; 2-year post-study return rule; 2,800-hour work experience calculator.
  2. **Fulbright Foreign Student Program (US)**: Full tuition, stipend, health insurance, J-1 two-year home residency requirement.
  3. **Turkiye Burslari (YTB - Turkey)**: Undergraduate (70% minimum GPA) & Master (75% minimum GPA), full coverage + Turkish language year.
  4. **Italian DSU / EDISU / ER.GO Regional Scholarships**: Means-tested income brackets (< €25,000 ISEE), tuition waiver + up to €7,200 stipend.
  5. **Hungarian Stipendium Hungaricum**: Bilateral Azerbaijan-Hungary agreement; 100% tuition, monthly stipend, dormitory housing.
  6. **French Eiffel Excellence Scholarship**: Master & PhD funding for engineering, law, and economics.
  7. **Polish NAWA Banach Scholarship**: Engineering and technical programmes for Azerbaijani citizens.
- **Files**:
  - `backend/app/domain/scholarship_evaluator.py`
  - `backend/app/api/v1/scholarships.py`
  - `backend/scripts/seed_global_scholarships.py`
  - `backend/tests/test_scholarship_evaluator.py`
  - `frontend/src/app/scholarships/page.tsx`
  - `frontend/src/components/ScholarshipCard.tsx`
  - `frontend/src/components/ScholarshipFilter.tsx`

#### 3. DİM Sub-Exam Score Calculator & Specialty Recommender (6 commits, ~2,600 LOC)
- **Problem**: DİM applicants take 3 specialty sub-exams plus graduation exams (attestat exam). They don't know their total 700-point breakdown.
- **Features**:
  - **Interactive DİM Score Simulator**:
    - Input correct/incorrect questions for:
      - Block 1 (Attestat): Azerbaijani language (30 questions), Math (25 questions), Foreign Language (30 questions).
      - Block 2 (Specialty): Group 1 (Math, Physics, Chemistry), Group 2 (Math, Geography, History), etc.
    - Accurately calculates scaled raw scores out of 700.
  - **Eligible Specialty Matcher**: Instantly cross-references the student's calculated score against all 2,578 historical cutoffs in the database to show which programmes they qualify for under State Funding (dövlət sifarişli) or Paid Education.
- **Files**:
  - `backend/app/domain/dim_calculator.py`
  - `backend/app/api/v1/dim_calculator.py`
  - `backend/tests/test_dim_calculator.py`
  - `frontend/src/app/dim-calculator/page.tsx`
  - `frontend/src/components/DimScoreSimulator.tsx`
  - `frontend/src/components/SpecialtyRecommendationTable.tsx`

#### 4. Statement of Purpose (SOP) & CV Rubric Checker (5 commits, ~2,200 LOC)
- **Problem**: Azerbaijani applicants struggle with international application essays and format mistakes.
- **Features**:
  - Rule-based & regex essay analyzer:
    - Checks word count (e.g. 500–1000 words).
    - Detects mandatory sections: Academic background, why this university, career roadmap, and State Programme contribution clause.
    - Flags cliché phrases ("Ever since I was a child...", "Passionate about...") and passive voice frequency.
  - Academic CV rubric checker (checks for Europass / US resume format standards).
- **Files**:
  - `backend/app/services/sop_analyzer.py`
  - `backend/app/api/v1/sop.py`
  - `backend/tests/test_sop_analyzer.py`
  - `frontend/src/app/sop-checker/page.tsx`
  - `frontend/src/components/SopFeedbackCard.tsx`

#### 5. Admissions Timeline & Deadline Calendar (5 commits, ~2,000 LOC)
- **Problem**: Deadlines for foreign applications (UCAS, Uni-Assist, State Programme, DAAD) vary wildly.
- **Features**:
  - Unified timeline view with filters by intake (Fall 2026, Spring 2027) and country.
  - Countdown timers to critical dates (e.g., UCAS Equal Consideration, Uni-Assist summer deadline, State Programme ministry portal).
  - `.ics` calendar export (one-click download to Google Calendar / Apple Calendar).
- **Files**:
  - `backend/app/domain/timeline.py`
  - `backend/app/api/v1/timeline.py`
  - `backend/tests/test_timeline.py`
  - `frontend/src/app/timeline/page.tsx`
  - `frontend/src/components/AdmissionsTimeline.tsx`
  - `frontend/src/components/CalendarExportButton.tsx`

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

