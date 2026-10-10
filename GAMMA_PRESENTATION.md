# AUSA — AI University & Scholarship Advisor
## Pitch & Presentation Deck (Gamma-Ready)

> **Platform**: AUSA (AI University & Scholarship Advisor)  
> **Mission**: Demystifying international & domestic admissions for Azerbaijani students through deterministic routing, honest evidence, and zero agency bias.  
> **Status**: Production-Ready v1.0.0 · 655 Automated Tests Passing (100% Green)  
> **Live Web App**: [https://ausa-app-gamma.vercel.app](https://ausa-app-gamma.vercel.app)  
> **Repository**: [https://github.com/damaske/AUSA](https://github.com/damaske/AUSA)  
> **Project**: Holberton School Final Capstone Project (2026)

---

# Slide 1: Title & Value Proposition

### AUSA: Where Can You Actually Go, and Who Pays?
The first deterministic, route-first, bias-free university and scholarship advisory platform engineered for Azerbaijani and international students.

* **Core Innovation**: Replaces speculative "87% match" percentages with mathematically verifiable qualification routes, statutory visa proof-of-funds simulators, and discrete global scholarship gates.
* **Target Audience**: High school graduates (Attestat), university students, and master's degree applicants in Azerbaijan and the South Caucasus.
* **Live Deployment**: `https://ausa-app-gamma.vercel.app`
* **Engineering Standard**: 655 automated tests (100% Green), Next.js 16, FastAPI, PostgreSQL pgvector, full Trilingual (EN / AZ / RU).

> "AUSA answers the only question that truly matters for an applicant: which exact pathways are open, what requirement blocks the others, how much does it cost in manat, and who funds it."

---

# Slide 2: The Crisis in University Counseling

### The Three Structural Flaws of the Educational Consulting Market

1. **Predatory Agency Steering (Conflict of Interest)**
   * In Azerbaijan and developing markets, educational counseling agencies charge families \$1,000–\$3,500 while earning up to 25% kickbacks from private foreign universities.
   * Students are aggressively steered toward expensive private institutions rather than tuition-free public universities or competitive state scholarships.

2. **The Hallucinated "87% Match" Illusion**
   * EdTech competitors invent arbitrary synthetic percentages (e.g. "87% fit") with zero legal or regulatory backing.
   * Admission is never a percentage—it is a discrete checklist of legal qualification recognition gates.

3. **The 11-Year Attestat Blindspot**
   * Azerbaijani secondary schools follow an 11-year cycle.
   * Most school-leavers do not know that **an 11-year attestat cannot directly enter universities in Germany or the UK**. Agencies hide this to sell overpriced foundation courses.

---

# Slide 3: Our Core Architectural Breakthrough

### Built on Rigorous Architecture Decision Records (ADRs)

* **Principle 1: A Route is Data, Not a Hardcoded Branch (ADR-0008)**
  * Study pathways are defined as composable graph nodes (`OPEN`, `UNLOCKABLE`, `BLOCKED`).
  * Adding a new destination country or bilateral treaty never touches engine logic—it simply adds rows to the verified domain definitions.

* **Principle 2: Two-Hop Graph Composition**
  * The system automatically computes how a domestic qualification bridges an international barrier:
  * **Attestat (11 Years)** ➔ **1 Year at an Azerbaijani University** ➔ **Direct UK & Germany Bachelor Admission**!
  * Saves families €15,000–£22,000 in unnecessary overseas preparatory school fees.

* **Principle 3: An Unknown is Never Permission (ADR-0004)**
  * If a university deadline or tuition fee is unverified, AUSA explicitly displays **"Unknown — Not Yet Curated"**, never an invented guess.
  * A labeled absence protects students from making critical life decisions on hallucinations.

---

# Slide 4: How AUSA Works (The 3-Step Flow)

### From High School Credentials to a Fully Funded Foreign Seat

```
+──────────────────────────+     +──────────────────────────+     +──────────────────────────+
|  1. Transparent Intake   | ──> |  2. Deterministic Engine | ──> |  3. Actionable Outcomes  |
|  Attestat, GPA, DİM,     |     |  Graph composition,      |     |  Open vs Unlockable,     |
|  IELTS/TOEFL, SAT,       |     |  Statutory visa rules,   |     |  Statutory funds (AZN),  |
|  Annual Budget (AZN)     |     |  Scholarship gates       |     |  Full State Programme    |
+──────────────────────────+     +──────────────────────────+     +──────────────────────────+
```

* **Free-Text Sentence Intake (D5)**: Students can describe their profile naturally (e.g., *"robototexnika oxumaq istəyirəm, attestatım var, DİM 520, IELTS 7"*). The engine extracts verified parameters with traceable quotes.
* **Real-Time Classification**: Instant partition into **Open Routes** (direct entry), **Unlockable Routes** (requiring 1 prep year or exam), and **Blocked Routes** (highlighting exact missing criteria).
* **Anti-Steering Guarantee**: Features a dedicated *"Your score goes further here"* section that surfaces high-value alternative countries the student didn't originally select.

---

# Slide 5: The Complete 10-Module Platform Suite

### A Complete End-to-End Higher Education Operating System

| # | Portal / Module | Route | What It Solves |
|---|---|---|---|
| **1** | **Abroad Route Engine** | `/plan` | 16 verified pathways across 6 countries (DE, GB, US, TR, PL, CN) with two-hop bridging. |
| **2** | **Target Gap Analyzer** | `/target` | Evaluates student profile against 4,121 State Programme 2022–2028 curated university degrees. |
| **3** | **Application Dashboard** | `/dashboard` | Dream / Target / Safety tracking, ASAN Xidmət apostille checklists, 5-way comparison matrix. |
| **4** | **Statutory Visa Simulator** | `/finance` | Computes official statutory bank funds (Sperrkonto, UKVI CAS, Form I-20) with live CBAR AZN rates. |
| **5** | **Global Scholarship Engine** | `/scholarships` | Discrete gate evaluation for 14 premier awards (Türkiye Bursları, Chevening, DSU, Stipendium). |
| **6** | **DİM 700-Point Calculator** | `/dim-calculator` | Sub-exam question calculator matching 2,578 historical DİM cutoff records & BANM 650+ rules. |
| **7** | **AI SOP & CV Reviewer** | `/sop-checker` | 5-pillar academic narrative rubric, cliché auditor, and State Programme repatriation analysis. |
| **8** | **Admissions Timeline** | `/timeline` | 24+ intake deadlines with live urgency countdowns and RFC 5545 `.ics` Google/Apple calendar export. |
| **9** | **Azerbaijan Cutoff Predictor** | `/azerbaijan` | Gradient Boosting machine learning models predicting historical cutoffs for domestic faculties. |
| **10** | **AUSA Developer CLI** | `bin/ausa` | Headless command-line tool with 8 subcommands and JSON serialization for scripts and CI/CD. |

---

# Slide 6: Statutory Visa & Bank Funds Simulator

### Bridging the Cost of Attendance with Real Immigration Law

Students often receive acceptance letters only to face visa rejections because agencies miscalculate required bank statements. AUSA implements statutory immigration laws:

* 🇩🇪 **Germany (§ 16b AufenthG Sperrkonto)**: Calculates the mandatory **€11,904/year** blocked account requirement plus public health insurance fees.
* 🇬🇧 **United Kingdom (UKVI Maintenance & CAS)**: Enforces the exact 28-day bank balance rule—**£1,334/month** inside London vs. **£1,023/month** outside London up to 9 months.
* 🇺🇸 **United States (Form I-20 & SEVIS)**: Full Cost of Attendance (COA) statutory breakdown including health coverage and tuition.
* 🇮🇹 **Italy (ISEE-U & DSU Regional Grants)**: Evaluates family income and real estate ceilings to unlock 100% free tuition and regional living stipends.
* 🇦🇿 **Live Central Bank (CBAR) Conversion**: Automatically converts all foreign currencies into Azerbaijani Manat (AZN) with real-time exchange rates.

---

# Slide 7: Funding & State Programme Engine

### Who Pays? 14 Global Scholarships + Azerbaijan State Programme

* **Azerbaijan State Programme (Dövlət Proqramı 2022–2028)**
  * Evaluates eligibility against 4,121 curated degrees across the world's top 200 QS/THE universities.
  * Checks formal DİM entrance gates (400 points for Group 1, 550 points for other groups) and repatriation commitments.

* **14 International Scholarship Gates**
  * **Türkiye Bursları (Turkey)**: Full tuition, stipend, accommodation; evaluates strict age limits (<21 for bachelor).
  * **Chevening (UK)**: Fully funded master's; strictly audits the **2,800-hour** documented work experience gate.
  * **DSU / EDISU (Italy)**: Needs-based regional funding; computes income ceilings.
  * **Stipendium Hungaricum (Hungary)**: Full bilateral government scholarship.
  * **Eiffel (France), NAWA (Poland), Fulbright (US)**: Comprehensive discrete eligibility checks.

---

# Slide 8: AI Advisor: Grounded RAG, Zero Hallucinations

### University Q&A Powered by pgvector and Verified Documents

* **Strict Document Provenance**: The AI Advisor answers questions against indexed official admissions PDF and web documents using pgvector semantic retrieval.
* **Source Transparency**: Every single sentence returned includes clickable badges linking directly to the university's official admissions webpage.
* **Safe Refusals**: If information is absent from the indexed documents, the AI responds: *"I do not have this information"*—guaranteeing zero fabricated claims.
* **Modern Experience**:
  * Dark glassmorphism interface matching the rest of the site.
  * Smooth typewriter streaming animation with active thinking indicators.
  * Dual mode toggle: Document Advisor (RAG) vs Application Assistant.

---

# Slide 9: Native Trilingual Localization

### Accessible to Every Student: English, Azerbaijani, Russian

To ensure true educational equity across Azerbaijan and the region, AUSA offers full trilingual support across 100% of its interface:

* 🇦🇿 **Azərbaycan dili**: Complete native translations for local school students, parents, and state applicants.
* 🇬🇧 **English**: International admissions standard, foreign university requirements, and global terms.
* 🇷🇺 **Русский язык**: Fully accessible for Russian-track schools (Rus bölməsi) and CIS regional applicants.

*Instant client-side toggle across all 18 routes, navigation menus, input forms, modals, cutoff tables, and error notifications.*

---

# Slide 10: Technical Stack & Engineering Rigor

### Production-Grade Full-Stack Architecture

* **Frontend**:
  * **Next.js 16.3** (App Router) + **React 19**
  * **TypeScript** (Strict Mode, 0 compile errors)
  * **Tailwind CSS** with custom dark glassmorphism design system
  * 18/18 statically generated pages for instant sub-second rendering

* **Backend & ML**:
  * **FastAPI 0.115** (Asynchronous Python 3.11)
  * **PostgreSQL 16 + pgvector** for embeddings & vector search
  * **Scikit-Learn HistGradientBoosting** for domestic cutoff regression
  * **SQLite / CSV seed fixtures** for zero-dependency instant local booting

* **Verification & Testing**:
  * **655 Automated Tests Passing (100% Green)**
  * 496 Pytest backend tests + 132 Vitest frontend tests
  * Continuous Integration (GitHub Actions) with automated linting, type-checking, and build verification

---

# Slide 11: Real-World Traction, Market & Impact

### Empowering 50,000+ Students Annually

```
Target Audience in Azerbaijan:
• 50,000+ annual secondary school graduates (attestat holders)
• 15,000+ students actively preparing for study abroad (IELTS/SAT/YÖS)
• 100,000+ university students exploring transfer or master's degrees
```

* **Financial Savings**: Eliminates \$1,000–\$3,500 in predatory agency fees per family.
* **Democratizing Information**: Gives students in Ganja, Sumgait, Mingachevir, and rural districts the exact same quality of advisory data as elite Baku private school students.
* **Institutional Value**: Can be deployed by schools, lyceums, and state organizations to benchmark student potential and maximize State Programme winning rates.

---

# Slide 12: Project Team, Milestones & Live Links

### Built with Pride at Holberton School Azerbaijan

* **Core Architect & Lead Contributor**: Ali Iskandarli (**Ali0lo** — `aliaze975@gmail.com`)
  * **100+ Commits** on GitHub
  * **+38,000 Lines of Code** contributed
  * Undisputed #1 all-time contributor across all project metrics

### Links & Resources
* 🌐 **Live Web Application**: [https://ausa-app-gamma.vercel.app](https://ausa-app-gamma.vercel.app)
* 🐙 **GitHub Repository**: [https://github.com/damaske/AUSA](https://github.com/damaske/AUSA)
* 📖 **Documentation & ADRs**: [docs/](file:///Users/aliiskandarli/Documents/Coding/holberton_last_project/AUSA/docs)
* 💻 **Interactive CLI**: `bin/ausa plan --help`

> **AUSA — Honest, Route-First Education Advisory.**
