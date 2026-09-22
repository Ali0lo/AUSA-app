# AUSA Developer & Admissions CLI Reference Manual

The **AUSA CLI** (`bin/ausa` or `python -m backend.cli.ausa_cli`) provides command-line utilities for students, admissions counselors, and engineers to evaluate application qualifications, simulate statutory visa funds, calculate DİM entrance exam scores, audit Statements of Purpose, and inspect upcoming admissions deadlines.

---

## 1. Installation & Quickstart

From repository root:
```bash
# Verify executable
./bin/ausa --version

# Display global help banner
./bin/ausa --help
```

All commands support `--json` for headless automation, scripting, and CI/CD pipelines.

---

## 2. Command Reference

### `dim-calc` — DİM 700-Point Score Simulator & Specialty Recommender
Calculates scaled scores for Azerbaijani university entrance exams across Groups 1–4 and matches candidates against 2,578 historical DİM cutoff records (2023–2025).

#### Flags:
- `--score <float>`: Direct total DİM score (0–700).
- `--group {1,2,3,4}`: Exam group (default: 1).
- `--sub-group {rk,ri,dt,tc}`: Sub-group specialization (default: `ri`).
- `--bur-closed <int>`: Correct closed questions on Buraxılış (graduation) exam.
- `--bur-open <int>`: Correct open / situational questions on Buraxılış.
- `--blok-closed <int>`: Correct closed questions on Blok (specialty) exam.
- `--blok-open <int>`: Correct open questions on Blok.
- `--university <string>`: Filter results by university (e.g. `BANM`, `ADA`, `UNEC`, `BDU`).
- `--limit <int>`: Maximum recommendation rows (default: 10).

#### Examples:
```bash
# Direct score calculation for Group 1 with Baku Higher Oil School filter
./bin/ausa dim-calc --score 665 --group 1 --university BANM

# Question-by-question calculation with JSON output
./bin/ausa --json dim-calc --group 1 --sub-group ri --bur-closed 60 --blok-closed 55
```

---

### `finance` — Statutory Visa, Blocked Account & Living Cost Simulator
Simulates statutory minimum proof-of-funds required by immigration authorities for study visas in Germany, the UK, the US, and Italy, converting amounts into Azerbaijani Manat (AZN).

#### Flags:
- `--country {DE,GB,US,IT}`: Target study destination (default: `DE`).
- `--tuition <float>`: Annual tuition in destination currency (EUR, GBP, USD).
- `--budget-azn <float>`: Disposable first-year budget in AZN (default: 25,000 AZN).
- `--london`: Enforce UKVI Inner London monthly allowance (£1,334/mo vs £1,023/mo outer).
- `--members <int>`: Household size for Italy ISEE-U equivalence scale (default: 4).
- `--iseeu-income <float>`: Annual household net income for Italy ISEE-U (default: 12,000 AZN).
- `--all`: Run a 4-country comparative benchmark across DE, GB, US, and IT.

#### Examples:
```bash
# German Sperrkonto (§ 16b AufenthG) calculation
./bin/ausa finance --country DE --tuition 0

# Comparative benchmark across all 4 destinations against 35,000 AZN budget
./bin/ausa finance --all --budget-azn 35000
```

---

### `scholarships` — Global Scholarship Qualification Evaluator
Evaluates student eligibility across 14 international and bilateral scholarship programs with discrete gates (`OPEN`, `UNLOCKABLE`, `BLOCKED`).

#### Flags:
- `--level {bachelor,master,phd}`: Target degree level (default: `master`).
- `--country <string>`: Filter scholarship by host country code (e.g. `TR`, `GB`, `DE`, `IT`).
- `--gpa <float>`: Academic GPA on 0–100 scale (default: 85.0).
- `--ielts <float>`: IELTS overall band score (default: 7.0).
- `--work-hours <int>`: Verified professional work experience hours (for Chevening: 2,800 hrs).
- `--age <int>`: Candidate age in years (default: 23).
- `--dim-score <int>`: DİM entrance exam score (for BHOS full state grant: 650+).

#### Examples:
```bash
# Master's degree evaluation with high GPA and IELTS
./bin/ausa scholarships --level master --gpa 92 --ielts 7.5

# Türkiye Bursları bachelor evaluation
./bin/ausa scholarships --country TR --level bachelor --age 19
```

---

### `timeline` — Admissions Calendar & Deadline Milestone Tracker
Displays verified application deadlines for the 2026/2027 admissions cycle with real-time countdowns and urgency status (`CRITICAL`, `UPCOMING`, `OPEN`).

#### Flags:
- `--country <string>`: Filter milestones by country code (`DE`, `GB`, `US`, `AZ`, `TR`, `IT`, `HU`).
- `--level {bachelor,master,phd}`: Filter by degree level.
- `--urgency {critical,upcoming,open}`: Filter by urgency category.
- `--limit <int>`: Maximum milestones to return (default: 15).

#### Examples:
```bash
# List all critical deadlines occurring within 14 days
./bin/ausa timeline --urgency critical

# Filter UK undergraduate deadlines in JSON
./bin/ausa --json timeline --country GB --level bachelor
```

---

### `compare` — Multi-University Side-by-Side Comparison Matrix
Generates multi-variable comparison tables across benchmark universities computing tuition, monthly living expenses, blocked account requirements, and post-study work visa rights.

#### Flags:
- `--universities <string>`: Comma-separated university IDs (e.g. `tum_cs,oxford_cs,rwth_engineering`).
- `--gpa <float>`: Candidate GPA for admissions tier categorization.
- `--ielts <float>`: Candidate IELTS score for qualification verification.

#### Examples:
```bash
./bin/ausa compare --universities tum_cs,oxford_cs,rwth_engineering
```

---

### `checklist` — Country-Specific Prerequisite Document Generator
Generates mandatory and supplementary prerequisite document checklists for foreign university admissions and student visas.

#### Flags:
- `--country <string>`: Destination country code (`DE`, `GB`, `IT`, `TR`, `US`).
- `--level <string>`: Degree level (`bachelor` or `master`).
- `--state-programme`: Include Azerbaijan 2022–2026 State Programme requirements.

#### Examples:
```bash
# Germany document checklist with Uni-Assist VPD and Sperrkonto
./bin/ausa checklist --country DE

# UK checklist including 2022-2026 State Programme contribution essay
./bin/ausa checklist --country GB --state-programme
```

---

### `sop-check` — Statement of Purpose & Academic CV Rubric Auditor
Audits Statement of Purpose (SOP) essays against 5 core narrative pillars, flags clichés and passive voice density, and scores overall readiness.

#### Flags:
- `--text <string>`: Raw text of the essay.
- `--file <path>`: Path to `.txt` or `.md` file containing the statement of purpose.
- `--country <string>`: Target destination country (default: `DE`).
- `--state-programme`: Audit for 2022–2026 State Programme repatriation/contribution clause.

#### Examples:
```bash
# Audit an essay file
./bin/ausa sop-check --file ./my_sop.txt --country DE --state-programme

# Audit text snippet directly with JSON output
./bin/ausa --json sop-check --text "Ever since childhood, I have had a passion for computer science..."
```

---

### `convert` — Multi-Currency Converter with CBAR Baseline Rates
Performs multi-currency conversions against the Central Bank of Azerbaijan (CBAR) reference rates with optional safety cushion buffers for exchange rate volatility.

#### Flags:
- `--amount <float>`: Amount to convert (default: 1,000.0).
- `--from <currency>`: Source currency: `AZN`, `EUR`, `USD`, `GBP`, `TRY`, `PLN`, `HUF` (default: `EUR`).
- `--to <currency>`: Target currency (default: `AZN`).
- `--buffer <float>`: Safety volatility buffer percentage (e.g. `2.5` for +2.5% cushion).

#### Examples:
```bash
# Convert 1,000 EUR to AZN with 2.5% volatility buffer
./bin/ausa convert --amount 1000 --from EUR --to AZN --buffer 2.5

# Convert 15,000 USD to AZN with JSON output
./bin/ausa --json convert --amount 15000 --from USD --to AZN
```

---

## 3. Scripting & Piping with `--json`

Use `jq` to parse structured outputs in shell scripts:
```bash
# Extract lowest cost university
./bin/ausa --json compare --universities tum_cs,oxford_cs | jq -r '.lowest_cost_university'

# Extract total first-year AZN cost for Germany
./bin/ausa --json finance --country DE | jq '.total_first_year_liquidity_azn'
```
