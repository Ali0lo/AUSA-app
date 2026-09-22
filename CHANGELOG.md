# Changelog

All notable changes to the **AUSA (AI University & Scholarship Advisor)** platform are documented in this file.
The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Conventional Commits](https://www.conventionalcommits.org/).

---

## [1.0.0] — 2026-09-22

### 🌟 Major Milestone Release — Complete Route-First Admissions Platform
The v1.0.0 release marks the complete delivery of all 7 core architectural phases, establishing AUSA as a production-grade, deterministic advisory platform with zero synthetic matching formulas and full statutory compliance.

### Added

#### Phase 1: Statutory Visa, Blocked Account & Living Cost Simulator
- Pure domain engine (`backend/app/domain/financial_calculator.py`) implementing statutory visa minimums:
  - Germany: § 16b AufenthG Sperrkonto (€11,904/yr).
  - United Kingdom: UKVI Appendix Student (£1,334/mo Inner London vs £1,023/mo Outer London with 28-day holding rule).
  - United States: Form I-20 Cost of Attendance (COA) estimates.
  - Italy: ISEE Parificato and DSU tuition waiver scales (€25,000 threshold).
- Real-time multi-currency converter against Central Bank of Azerbaijan (CBAR) reference rates (AZN, EUR, USD, GBP, TRY, PLN, HUF).
- Interactive glassmorphic simulator (`frontend/src/components/FinanceSimulator.tsx`) with route at `/finance`.
- Dedicated FastAPI endpoints (`backend/app/api/v1/finance.py`).

#### Phase 2: Comprehensive Global Scholarship Engine
- Evaluation engine (`backend/app/domain/global_scholarships.py`) covering 14 international and bilateral scholarship programs:
  - Türkiye Bursları (YTB), Chevening (2,800-hour work gate), Fulbright, Italian DSU/ER.GO, Stipendium Hungaricum, French Eiffel, Polish NAWA Banach, DAAD, and Baku Higher Oil School 650+ Full Scholarship.
- Discrete qualification gate evaluator (`OPEN`, `UNLOCKABLE`, `BLOCKED`) with actionable guidance.
- Interactive filtering portal (`frontend/src/components/ScholarshipExplorer.tsx`) with route at `/scholarships`.
- FastAPI endpoints (`backend/app/api/v1/scholarships.py`).

#### Phase 3: DİM Sub-Exam Score Calculator & Specialty Recommender
- Sub-test scoring engine (`backend/app/domain/dim_calculator.py`) for Azerbaijani university entrance exams:
  - Groups 1–4 breakdowns (Buraxılış 300 points + Blok 400 points).
  - 4-wrong-penalty rule for closed questions and partial credit scaling for open questions.
- Dynamic matching engine querying 2,578 historical DİM cutoff records (2023–2025) categorized into `SAFE`, `REALISTIC`, `TARGET`, and `REACH`.
- Enforced Baku Higher Oil School (BANM) 650+ full scholarship rule across all 10 BHOS specialties.
- Responsive calculator UI (`frontend/src/components/DimScoreSimulator.tsx`) with route at `/dim-calculator`.
- FastAPI endpoints (`backend/app/api/v1/dim.py`).

#### Phase 4: Statement of Purpose (SOP) & Academic CV Rubric Reviewer
- Natural language audit parser (`backend/app/domain/sop_analyzer.py`) evaluating 5 core narrative pillars:
  - Academic foundation, research intent, university fit, career trajectory, and State Programme repatriation/contribution.
- Heuristic cliché detector ("Ever since my childhood", "I have always been passionate", etc.) with actionable replacement suggestions.
- Passive voice density auditor and structural section checklist.
- Glassmorphic auditing UI (`frontend/src/components/SopChecker.tsx`) with route at `/sop-checker`.
- FastAPI endpoints (`backend/app/api/v1/sop.py`).

#### Phase 5: Admissions Timeline, Calendar & Milestone Tracker
- Cycle tracker (`backend/app/domain/timeline.py`) tracking 24+ verified intake deadlines for the 2026/2027 admissions cycle.
- Dynamic urgency categorizer (`CRITICAL`, `UPCOMING`, `OPEN`) with real-time countdown calculations.
- RFC 5545 compliant `.ics` calendar generator allowing one-click export to Google and Apple Calendar.
- Interactive calendar dashboard (`frontend/src/components/AdmissionsTimeline.tsx`) with route at `/timeline`.
- FastAPI endpoints (`backend/app/api/v1/timeline.py`).

#### Phase 6: Student Application Dashboard & Comparison Workbench
- Application lifecycle manager (`backend/app/domain/application_tracker.py`):
  - Stages: `DRAFT`, `DOCUMENT_GATHERING`, `SUBMITTED`, `UNDER_REVIEW`, `INTERVIEW_SCHEDULED`, `OFFER_RECEIVED`, `REJECTED`, `VISA_PROCESSING`.
  - Deterministic tier classifier: `DREAM`, `TARGET`, `SAFETY` based on verified QS ranks and GPA/IELTS thresholds.
- Dynamic country-specific prerequisite document generator (VPD, Sperrkonto, CAS, Denklik, ISEE Parificato, police clearances).
- Multi-university side-by-side comparison matrix evaluating tuition, living costs, blocked deposits, and post-study work visa durations.
- Full glassmorphic dashboard (`frontend/src/components/ApplicationDashboard.tsx`, `ComparisonMatrix.tsx`) with route at `/dashboard`.
- FastAPI endpoints (`backend/app/api/v1/applications.py`).

#### Phase 7: AUSA Developer CLI & Expanded Test Suites
- Unified developer command-line utility (`backend/cli/ausa_cli.py`) with executable wrapper `bin/ausa`.
- 8 high-utility subcommands: `dim-calc`, `finance`, `scholarships`, `timeline`, `compare`, `checklist`, `sop-check`, and `convert`.
- Full `--json` serialization for headless execution and CI/CD pipelines.
- Complete documentation manual in [`docs/CLI_REFERENCE.md`](docs/CLI_REFERENCE.md).
- Automated health verification script in [`scripts/verify_system_health.sh`](scripts/verify_system_health.sh).
- System architecture manual in [`docs/ARCHITECTURE_OVERVIEW.md`](docs/ARCHITECTURE_OVERVIEW.md).

### Changed & Improved
- **ADR-0008 Strict Compliance:** Eliminated all synthetic weighted matching percentages (`0.5*GPA + 0.3*IELTS + 0.2*EC`) across the codebase. All guidance is resolved via discrete qualification routes and statutory gates.
- **Pure Domain-Driven Isolation:** Every domain module is 100% pure Python with zero database or framework coupling.
- **Frontend Architecture:** Updated to Next.js 16.3 + React 19 with strict TypeScript typing and responsive midnight glassmorphic design system.

### Test & Quality Verification
- **Backend Test Suite:** 496 passing Pytest tests (3 skipped, 0 failed).
- **Frontend Test Suite:** 124 passing Vitest tests across 21 test files (0 failed).
- **Total Tests:** **620 automated tests passing (100% green)**.

---

### Lead Contributor
- **Ali0lo (Ali Iskandarli — `aliaze975@gmail.com`)**: Primary author and lead contributor across all 7 phases, contributing 98+ commits, +38,000 lines added, and +36,000 net lines of code.
