"""Domain definitions and qualification evaluation engine for Global Scholarships.

Implements the official statutory criteria, eligibility gates, and funding benefits
for the primary international and bilateral scholarship programs accessible to Azerbaijani students:
1. State Programme 2022-2026 (Dövlət Proqramı) - Azerbaijan
2. Chevening Scholarships - United Kingdom
3. Fulbright Foreign Student Program - United States
4. Türkiye Bursları (YTB) - Turkey
5. Stipendium Hungaricum - Hungary
6. Italian Regional DSU / EDISU Scholarships - Italy
7. DAAD Master Studies Scholarships - Germany
8. Eiffel Excellence Scholarship Programme (Campus France) - France
9. Stefan Banach Scholarship Programme (NAWA) - Poland
10. Chinese Government Scholarship (CSC) - China
11. Erasmus Mundus Joint Masters - European Union
12. GREAT Scholarships (British Council) - United Kingdom
13. SOCAR Overseas Scholarship Program (SOCAR Xarici Təqaüd) - Azerbaijan
14. Baku Higher Oil School Full State Scholarship (BHOS) - Azerbaijan

Design adheres strictly to ADR-0001 & ADR-0008:
Discrete qualification gates (OPEN / UNLOCKABLE / BLOCKED) with honest gate diagnostics,
without synthetic weighted percentage scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class FundingTier(str, Enum):
    AZERBAIJANI_STATE = "azerbaijani_state"
    DESTINATION_GOVERNMENT = "destination_government"
    INTERNATIONAL_CONSORTIUM = "international_consortium"
    UNIVERSITY_MERIT = "university_merit"


class FundingType(str, Enum):
    FULLY_FUNDED = "fully_funded"        # 100% Tuition + Stipend + Living/Travel
    TUITION_AND_STIPEND = "tuition_and_stipend"
    TUITION_ONLY = "tuition_only"
    STIPEND_ONLY = "stipend_only"
    TUITION_REDUCTION = "tuition_reduction" # E.g. GREAT £10,000 reduction


class GateStatus(str, Enum):
    MET = "met"
    MISSING = "missing"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class ScholarshipStatus(str, Enum):
    OPEN = "open"
    UNLOCKABLE = "unlockable"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class GateEvaluation:
    gate_name: str
    status: GateStatus
    reason: str


@dataclass(frozen=True)
class GlobalScholarship:
    key: str
    name: str
    native_name: str
    provider: str
    tier: FundingTier
    country_code: Optional[str]  # e.g. "GB", "US", "DE", "IT", "HU", "TR", "FR", "PL", "CN", "AZ", None for multi-country
    country_name: str
    degree_levels: Tuple[str, ...]  # "bachelor", "master", "phd"
    funding_type: FundingType
    coverage_summary: str
    stipend_monthly_local: Optional[str]
    stipend_monthly_azn_approx: Optional[float]
    tuition_coverage_pct: float
    travel_covered: bool
    housing_covered: bool
    health_insurance_covered: bool
    return_service_obligation: Optional[str]
    min_gpa: Optional[float]
    min_gpa_scale: Optional[str]
    min_ielts: Optional[float]
    min_toefl: Optional[int]
    age_limit_bachelor: Optional[int]
    age_limit_master: Optional[int]
    work_experience_hours: Optional[int]
    financial_need_based: bool
    max_household_income_eur: Optional[float]
    application_window_start: str
    application_window_end: str
    official_portal_url: str
    official_guidelines_url: Optional[str]
    azerbaijan_quota_or_seats: Optional[str]
    eligibility_criteria: Tuple[str, ...]
    required_documents: Tuple[str, ...]
    selection_stages: Tuple[str, ...]
    citation: str
    provenance: str = "primary-verified"


@dataclass(frozen=True)
class GlobalScholarshipEvaluation:
    scholarship: GlobalScholarship
    status: ScholarshipStatus
    gates_met: Tuple[str, ...] = field(default_factory=tuple)
    gates_missing: Tuple[str, ...] = field(default_factory=tuple)
    gates_blocked: Tuple[str, ...] = field(default_factory=tuple)
    gates_unknown: Tuple[str, ...] = field(default_factory=tuple)
    summary_verdict: str = ""


# ==============================================================================
# CATALOGUE OF 14 GLOBAL SCHOLARSHIPS
# ==============================================================================

STATE_PROGRAM_AZ = GlobalScholarship(
    key="dp-azerbaijan",
    name="State Program on Foreign Education (2022–2026)",
    native_name="2022–2026-cı illər Dövlət Proqramı",
    provider="Ministry of Science and Education of the Republic of Azerbaijan",
    tier=FundingTier.AZERBAIJANI_STATE,
    country_code="AZ",
    country_name="Azerbaijan (for study abroad)",
    degree_levels=("bachelor", "master", "phd"),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="100% tuition, monthly living allowance (stipend), health insurance, visa costs, and round-trip flight tickets",
    stipend_monthly_local="Varies by country (e.g. £1,300/mo UK, €1,100/mo Germany, $1,500/mo USA)",
    stipend_monthly_azn_approx=2400.0,
    tuition_coverage_pct=100.0,
    travel_covered=True,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation="Mandatory 5-year work service commitment in the Republic of Azerbaijan following degree completion",
    min_gpa=3.0,
    min_gpa_scale="4.0",
    min_ielts=6.5,
    min_toefl=79,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="Early March",
    application_window_end="Mid June (annual call)",
    official_portal_url="https://dp.edu.az",
    official_guidelines_url="https://dp.edu.az/az/rules",
    azerbaijan_quota_or_seats="Up to 400 scholars per year (bachelor capped at max 20-25% of quota)",
    eligibility_criteria=(
        "Citizen of the Republic of Azerbaijan",
        "Unconditional admission offer from a target university and priority field approved in the 4,121-program catalogue",
        "Minimum 400 DİM entrance score for Group 1 specialties, or 550 for Groups 2-4 (or Olympiad medal)",
        "Language proficiency certificate satisfying host university unconditional admission",
    ),
    required_documents=(
        "Unconditional admission offer letter from approved target institution",
        "Academic diploma and official transcript of records",
        "DİM exam result certificate or Attestat score card",
        "Official language proficiency certificate (IELTS/TOEFL)",
        "Curriculum Vitae (CV) and Statement of Purpose",
        "Valid international biometric passport",
        "Medical certificate Form 086",
    ),
    selection_stages=(
        "Electronic document evaluation via portal.edu.az",
        "Interview panel by the Selection Commission of the State Program",
        "Final decree by the Ministry of Science and Education",
    ),
    citation="Presidential Decree No. 3163 of 28.02.2022; Ministry of Science and Education regulations.",
)

CHEVENING_UK = GlobalScholarship(
    key="chevening-uk",
    name="Chevening Scholarship",
    native_name="Chevening UK Government Scholarship",
    provider="UK Foreign, Commonwealth & Development Office (FCDO)",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="GB",
    country_name="United Kingdom",
    degree_levels=("master",),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="Full university tuition fees, a monthly living allowance, economy return flights to the UK, and arrival grants",
    stipend_monthly_local="£1,334/month in London, £1,023/month outside London",
    stipend_monthly_azn_approx=2600.0,
    tuition_coverage_pct=100.0,
    travel_covered=True,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation="Mandatory return to the country of citizenship for a minimum of two years following completion of the master's degree",
    min_gpa=2.8,
    min_gpa_scale="4.0",
    min_ielts=6.5,
    min_toefl=79,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=2800,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="Early August",
    application_window_end="Early November",
    official_portal_url="https://www.chevening.org/apply/",
    official_guidelines_url="https://www.chevening.org/guidance/eligibility/",
    azerbaijan_quota_or_seats="Approximately 10–15 fully funded Chevening scholars selected from Azerbaijan annually",
    eligibility_criteria=(
        "Citizen of a Chevening-eligible country (Azerbaijan)",
        "Completed an undergraduate degree equivalent to an upper second-class 2:1 honours UK degree",
        "Minimum of 2,800 hours of documented work experience (equivalent to roughly two years full-time)",
        "Apply to three different eligible UK university courses and hold at least one unconditional offer by July",
    ),
    required_documents=(
        "Undergraduate diploma and transcripts (translated & apostilled)",
        "Four Chevening essay answers (Leadership, Networking, Study in the UK, Career Plan)",
        "Two professional or academic recommendation letters",
        "Valid passport",
        "Unconditional offer from at least one chosen UK university course",
    ),
    selection_stages=(
        "Initial automated eligibility screening",
        "Independent academic reading committee assessment",
        "In-person interview at the British Embassy in Baku",
        "Final selection announcement by FCDO in June",
    ),
    citation="https://www.chevening.org/scholarships/who-can-apply/eligibility/ (Verified requirement: 2,800 work hours).",
)

FULBRIGHT_USA = GlobalScholarship(
    key="fulbright-usa",
    name="Fulbright Foreign Student Program",
    native_name="Fulbright Xarici Tələbə Proqramı",
    provider="U.S. Department of State (Bureau of Educational and Cultural Affairs)",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="US",
    country_name="United States",
    degree_levels=("master",),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="Full graduate tuition, monthly living stipend, books and supplies allowance, round-trip international airfare, and health benefit plan (ASPE)",
    stipend_monthly_local="$1,600 – $2,400/month depending on host US university location",
    stipend_monthly_azn_approx=3100.0,
    tuition_coverage_pct=100.0,
    travel_covered=True,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation="J-1 Exchange Visitor Visa Section 212(e): Mandatory two-year home-country physical presence requirement in Azerbaijan before immigrant/work visa eligibility in the US",
    min_gpa=3.0,
    min_gpa_scale="4.0",
    min_ielts=6.5,
    min_toefl=80,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="February",
    application_window_end="Late May",
    official_portal_url="https://az.usembassy.gov/education-culture/fulbright-foreign-student-program/",
    official_guidelines_url="https://foreign.fulbrightonline.org/",
    azerbaijan_quota_or_seats="5–8 Azerbaijani graduate scholars selected annually",
    eligibility_criteria=(
        "Citizen of Azerbaijan residing in Azerbaijan at time of application",
        "Completed undergraduate bachelor degree prior to scholarship commencement",
        "English proficiency with minimum TOEFL iBT 80 or IELTS 6.5",
        "Demonstrated leadership potential, academic excellence, and cross-cultural commitment",
    ),
    required_documents=(
        "Online Slate application dossier",
        "Personal Statement and Study/Research Objectives essays",
        "Three letters of recommendation",
        "Official university transcripts and degree diplomas",
        "TOEFL iBT or IELTS score report",
    ),
    selection_stages=(
        "Technical and substantive review by US Embassy Baku",
        "Bilingual interview with U.S. Embassy Selection Committee",
        "Final approval by the J. William Fulbright Foreign Scholarship Board (FFSB) in Washington D.C.",
        "University placement conducted by Institute of International Education (IIE)",
    ),
    citation="https://az.usembassy.gov/fulbright-foreign-student-program/ ; 8 CFR 212(e) home residency rule.",
)

TURKIYE_BURSLARI = GlobalScholarship(
    key="turkiye-burslari",
    name="Türkiye Bursları",
    native_name="Türkiye Bursları Tam Kapsamlı Burs Programı",
    provider="Presidency for Turks Abroad and Related Communities (YTB), Republic of Türkiye",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="TR",
    country_name="Turkey",
    degree_levels=("bachelor", "master", "phd"),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="University placement, 100% tuition waiver, monthly cash stipend, free state dormitory housing, 1-year Turkish language preparatory course (TÖMER), public health insurance, and round-trip flight tickets",
    stipend_monthly_local="3,500 TRY/mo (Bachelor), 5,000 TRY/mo (Master), 6,500 TRY/mo (PhD)",
    stipend_monthly_azn_approx=220.0,
    tuition_coverage_pct=100.0,
    travel_covered=True,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation=None,
    min_gpa=2.8,
    min_gpa_scale="4.0",
    min_ielts=None,
    min_toefl=None,
    age_limit_bachelor=21,
    age_limit_master=30,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="10 January",
    application_window_end="20 February",
    official_portal_url="https://www.turkiyeburslari.gov.tr",
    official_guidelines_url="https://www.turkiyeburslari.gov.tr/fulltimeprograms",
    azerbaijan_quota_or_seats="150–250 Azerbaijani students awarded scholarships annually across degree levels",
    eligibility_criteria=(
        "Citizens of all countries except citizens of the Republic of Türkiye or those who lost Turkish citizenship",
        "Minimum academic achievement: 70% for Bachelor, 75% for Master/PhD, 90% for Health Sciences (Medicine/Dentistry)",
        "Age limits: Under 21 for Bachelor, under 30 for Master, under 35 for PhD",
        "Cannot be currently enrolled in a Turkish university at the degree level applied for",
    ),
    required_documents=(
        "National ID card or valid international passport",
        "Recent photograph",
        "Graduation diploma or temporary graduation certificate",
        "Academic transcripts showing cumulative grade point average",
        "National or international exam scores (if any: DİM, SAT, GRE, GMAT)",
        "Letter of intent and research proposal (for graduate study)",
    ),
    selection_stages=(
        "Preliminary assessment of academic criteria and eligibility",
        "Expert committee scoring of academic and social achievements",
        "In-person interview in Baku (Yunus Emre Enstitüsü / Turkish Embassy)",
        "Final selection and university placement",
    ),
    citation="https://www.turkiyeburslari.gov.tr/about/whatisturkiyeburslari (Verified age and academic achievement rules).",
)

STIPENDIUM_HUNGARICUM = GlobalScholarship(
    key="stipendium-hungaricum",
    name="Stipendium Hungaricum Scholarship Programme",
    native_name="Stipendium Hungaricum Felsőoktatási Ösztöndíjprogram",
    provider="Tempus Public Foundation & Ministry of Science and Education of Azerbaijan",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="HU",
    country_name="Hungary",
    degree_levels=("bachelor", "master", "phd"),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="100% tuition exemption, monthly stipend (HUF 43,700 for bachelor/master, HUF 140,000 for PhD), free dormitory accommodation or HUF 40,000/month contribution, and medical insurance up to HUF 65,000/year",
    stipend_monthly_local="43,700 HUF/month (Bachelor/Master) or 140,000 HUF/month (PhD)",
    stipend_monthly_azn_approx=210.0,
    tuition_coverage_pct=100.0,
    travel_covered=False,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation=None,
    min_gpa=2.8,
    min_gpa_scale="4.0",
    min_ielts=5.5,
    min_toefl=65,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="15 November",
    application_window_end="15 January",
    official_portal_url="https://apply.stipendiumhungaricum.hu",
    official_guidelines_url="https://stipendiumhungaricum.hu/apply/",
    azerbaijan_quota_or_seats="200 scholarship quotas for Azerbaijani citizens annually under the bilateral memorandum",
    eligibility_criteria=(
        "Citizen of the Republic of Azerbaijan",
        "Must reach 18 years of age by 31 August of the admission year",
        "Must be nominated by the Ministry of Science and Education of the Republic of Azerbaijan",
        "Satisfy Hungarian host university minimum language and entrance examination requirements",
    ),
    required_documents=(
        "Online application on Tempus Public Foundation portal",
        "Parallel registration on Ministry portal.edu.az",
        "Motivation letter (minimum 1 page)",
        "Proof of language proficiency (IELTS/TOEFL or institutional test)",
        "School/bachelor diploma and certified transcript in English",
        "Medical certificate of satisfactory health condition",
        "Copy of passport identification page",
    ),
    selection_stages=(
        "Technical check by Tempus Public Foundation",
        "National nomination screening by Ministry of Science and Education of Azerbaijan",
        "Institutional entrance examinations and Skype interviews by Hungarian universities",
        "Final awarding decision by Tempus Board of Trustees in June",
    ),
    citation="Bilateral Educational Cooperation Workplan between Azerbaijan and Hungary 2024–2026; Tempus Public Foundation Call 2025/2026.",
)

ITALIAN_DSU_REGIONAL = GlobalScholarship(
    key="italian-dsu-regional",
    name="Italian Regional DSU Scholarships (EDISU / ER.GO / ALiSEO)",
    native_name="Borse di Studio per il Diritto allo Studio Universitario (DSU)",
    provider="Regional Education & Welfare Agencies (EDISU Piemonte, ER.GO, Disco Lazio, DSU Toscana)",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="IT",
    country_name="Italy",
    degree_levels=("bachelor", "master"),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="100% university tuition fee exemption, regional cash scholarship stipend up to €7,200/year (for non-resident students), free cafeteria meals, and subsidized student residence accommodation",
    stipend_monthly_local="Up to €600/month (€7,200/year) for non-resident (fuori sede) students",
    stipend_monthly_azn_approx=1100.0,
    tuition_coverage_pct=100.0,
    travel_covered=False,
    housing_covered=True,
    health_insurance_covered=False,
    return_service_obligation=None,
    min_gpa=None,
    min_gpa_scale=None,
    min_ielts=None,
    min_toefl=None,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=True,
    max_household_income_eur=25000.0,
    application_window_start="Early June",
    application_window_end="Late August to Early September",
    official_portal_url="https://www.edisu.piemonte.it ; https://www.er-go.it",
    official_guidelines_url="https://www.universitaly.it",
    azerbaijan_quota_or_seats="Needs-based welfare entitlement; all eligible international students below threshold receive grant or fee waiver",
    eligibility_criteria=(
        "Enrolled or matriculating into an accredited Italian public university",
        "Economic need requirement: Family ISEE Parificato indicator must not exceed €25,000",
        "Family asset (ISPE Parificato) indicator must not exceed €50,000",
        "Academic merit progression required for second year renewal (minimum 20 CFU university credits)",
    ),
    required_documents=(
        "Consular legalized family composition certificate from Azerbaijan",
        "Income certificate of all adult family members for the previous calendar year",
        "Property and real estate ownership documentation (showing square meters)",
        "Bank account balance statements of all household members as of 31 December",
        "Apostilled translations into Italian verified by the Italian Embassy in Baku",
        "Official ISEE Parificato certificate issued by an authorized Italian CAF",
    ),
    selection_stages=(
        "Online submission of economic declarations to regional agency (e.g. EDISU, ER.GO)",
        "Publication of provisional ranking list (graduatoria provvisoria) in October",
        "Submission of Italian residence permit (permesso di soggiorno) and finalized banking coordinates",
        "Payment of scholarship stipend in two installments (December and June)",
    ),
    citation="D.P.C.M. 159/2013 and Legislative Decree 68/2012 on Right to University Education (Diritto allo Studio).",
)

DAAD_GERMANY = GlobalScholarship(
    key="daad-germany",
    name="DAAD Master Studies Scholarships for All Academic Disciplines",
    native_name="DAAD Stipendien für Masterstudiengänge",
    provider="Deutscher Akademischer Austauschdienst (DAAD)",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="DE",
    country_name="Germany",
    degree_levels=("master",),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="Monthly scholarship payment of €934, travel allowance, one-off study allowance, health and accident insurance, and German language course funding",
    stipend_monthly_local="€934/month (€11,208/year)",
    stipend_monthly_azn_approx=1730.0,
    tuition_coverage_pct=100.0,
    travel_covered=True,
    housing_covered=False,
    health_insurance_covered=True,
    return_service_obligation=None,
    min_gpa=3.0,
    min_gpa_scale="4.0",
    min_ielts=6.5,
    min_toefl=80,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="Early September",
    application_window_end="Mid November",
    official_portal_url="https://www.daad.de/en/study-and-research-in-germany/scholarships/",
    official_guidelines_url="https://www.daad-azerbaijan.org/",
    azerbaijan_quota_or_seats="Competitive international selection; several individual grants awarded to Azerbaijani scholars yearly",
    eligibility_criteria=(
        "Completed Bachelor's degree (last degree completed typically not more than 6 years prior to application)",
        "Excellent academic record with strong academic references",
        "Admission to a state or state-recognized German higher education institution",
        "Study language proficiency (German DSH/TestDaF or English IELTS 6.5/TOEFL 80)",
    ),
    required_documents=(
        "Online DAAD portal application form",
        "Curriculum vitae in tabular form (Europass)",
        "Letter of motivation (1–3 pages explaining academic and personal reasons)",
        "Letter of acceptance from host German university (or proof of application)",
        "University degree certificate and transcripts with German/English translations",
        "One recent letter of recommendation from a university professor",
    ),
    selection_stages=(
        "Pre-selection by an independent selection committee in Germany",
        "Academic review of motivation, course choices, and academic trajectory",
        "Final awarding decision communicated in spring (April/May)",
    ),
    citation="DAAD Scholarship Database guidelines for Master Studies; DAAD Information Centre Baku.",
)

EIFFEL_EXCELLENCE_FRANCE = GlobalScholarship(
    key="eiffel-france",
    name="Eiffel Excellence Scholarship Programme (Bourses Eiffel)",
    native_name="Programme de bourses d'excellence Eiffel",
    provider="French Ministry for Europe and Foreign Affairs (managed by Campus France)",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="FR",
    country_name="France",
    degree_levels=("master", "phd"),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="Monthly allowance of €1,181 for Master students (€1,800 for PhD), international return airfare, domestic train transport to institution, Campus France health insurance coverage, and cultural activity subsidies",
    stipend_monthly_local="€1,181/month (Master) or €1,800/month (Doctoral)",
    stipend_monthly_azn_approx=2190.0,
    tuition_coverage_pct=100.0,
    travel_covered=True,
    housing_covered=False,
    health_insurance_covered=True,
    return_service_obligation=None,
    min_gpa=3.2,
    min_gpa_scale="4.0",
    min_ielts=6.5,
    min_toefl=80,
    age_limit_bachelor=None,
    age_limit_master=25,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="October",
    application_window_end="Early January",
    official_portal_url="https://www.campusfrance.org/en/the-eiffel-scholarship-program",
    official_guidelines_url="https://www.campusfrance.org/en/eiffel-program-call-for-applications",
    azerbaijan_quota_or_seats="Prestigious global competition; ~350 worldwide awards distributed across all eligible countries",
    eligibility_criteria=(
        "Non-French nationality (Azerbaijani citizens eligible)",
        "Maximum age: 25 years old at candidate evaluation date for Master's level (up to 30 for PhD)",
        "Applications must be submitted by a French higher education institution (direct applications by students are disqualified)",
        "Target fields: Science and Technology, Engineering, Economics and Management, Law and Political Science",
    ),
    required_documents=(
        "Completed institutional application file submitted by host French university",
        "Candidate's Curriculum Vitae in French or English",
        "Professional project and career roadmap statement",
        "Official transcripts and ranking certified by graduating university",
        "Language proficiency certificate corresponding to medium of instruction (French TCF/DALF or English IELTS)",
    ),
    selection_stages=(
        "Pre-selection and institutional ranking by French higher education institutions",
        "Submission of institutional dossiers to Campus France Paris",
        "Evaluation by specialized consultative committees composed of university professors",
        "Announcement of laureates in early April",
    ),
    citation="Campus France Eiffel Excellence Guidelines 2025/2026; Ministry for Europe and Foreign Affairs.",
)

NAWA_BANACH_POLAND = GlobalScholarship(
    key="nawa-banach-poland",
    name="Stefan Banach Scholarship Programme (NAWA Poland)",
    native_name="Program stypendialny im. Stefana Banacha",
    provider="Polish National Agency for Academic Exchange (NAWA) & Ministry of Foreign Affairs",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="PL",
    country_name="Poland",
    degree_levels=("master",),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="Full tuition fee exemption at Polish public universities and a monthly living allowance of PLN 2,500 during the academic year",
    stipend_monthly_local="2,500 PLN/month",
    stipend_monthly_azn_approx=1080.0,
    tuition_coverage_pct=100.0,
    travel_covered=False,
    housing_covered=False,
    health_insurance_covered=False,
    return_service_obligation=None,
    min_gpa=2.8,
    min_gpa_scale="4.0",
    min_ielts=6.0,
    min_toefl=75,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="March",
    application_window_end="Early May",
    official_portal_url="https://nawa.gov.pl/en/students/foreign-students/the-banach-scholarship-programme",
    official_guidelines_url="https://nawa.gov.pl/images/Banach/2026/Banach-2026---Call-for-applications-EN.pdf",
    azerbaijan_quota_or_seats="Azerbaijan is specifically listed as an eligible priority country in the European Neighbourhood group",
    eligibility_criteria=(
        "Citizen of Azerbaijan (and not holding Polish citizenship)",
        "Undergraduate degree completed no earlier than 2024 (or currently completing in application year)",
        "Applying for full-time second-cycle (Master's) studies conducted in Polish or English at participating Polish public universities",
        "Minimum language level B2 in the language of instruction",
    ),
    required_documents=(
        "Scan of passport page with photo and personal data",
        "Higher education diploma with transcript of grades and GPA calculation",
        "Language certificate at minimum B2 level (IELTS, TOEFL, or university certificate)",
        "Recommendation letter from academic referee or faculty dean",
    ),
    selection_stages=(
        "Formal eligibility check by NAWA agency officers",
        "Merit assessment by external evaluation experts",
        "Publication of results list by late July",
    ),
    citation="NAWA Banach Call for Applications; Polish Ministry of Foreign Affairs Official Journal.",
)

CSC_CHINA = GlobalScholarship(
    key="csc-china",
    name="Chinese Government Scholarship (CSC / Silk Road Program)",
    native_name="中国政府奖学金 (CSC)",
    provider="China Scholarship Council (CSC), Ministry of Education of the PRC",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="CN",
    country_name="China",
    degree_levels=("bachelor", "master", "phd"),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="Full tuition waiver, free on-campus university dormitory accommodation, comprehensive medical insurance, and monthly living stipend (CNY 2,500 for Bachelor, CNY 3,000 for Master, CNY 3,500 for PhD)",
    stipend_monthly_local="2,500 CNY/mo (Bachelor), 3,000 CNY/mo (Master), 3,500 CNY/mo (PhD)",
    stipend_monthly_azn_approx=600.0,
    tuition_coverage_pct=100.0,
    travel_covered=False,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation=None,
    min_gpa=2.8,
    min_gpa_scale="4.0",
    min_ielts=6.0,
    min_toefl=75,
    age_limit_bachelor=25,
    age_limit_master=35,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="Early January",
    application_window_end="Early April",
    official_portal_url="https://www.campuschina.org",
    official_guidelines_url="https://www.campuschina.org/content/details3_74776.html",
    azerbaijan_quota_or_seats="50+ scholarships awarded to Azerbaijani students under Type A (Embassy) and Type B (University) tracks",
    eligibility_criteria=(
        "Citizen of a country other than the People's Republic of China and in good health",
        "Age requirements: Under 25 for Bachelor, under 35 for Master, under 40 for PhD",
        "Language requirements: HSK 4 for Chinese-taught undergraduate programmes; IELTS 6.0/TOEFL 75 for English-taught graduate programmes",
    ),
    required_documents=(
        "Application Form for Chinese Government Scholarship (filled in Chinese or English online)",
        "Notarized copy of highest diploma and academic transcripts",
        "Foreigner Physical Examination Form (including blood test results)",
        "Two recommendation letters in Chinese or English from professors",
        "Study Plan or Research Proposal (minimum 800 words for graduate students)",
        "Certificate of Non-Criminal Record (police clearance)",
    ),
    selection_stages=(
        "Application review by Chinese Embassy in Baku (Type A) or host university (Type B)",
        "Issuance of Pre-admission Letter",
        "Review and approval by China Scholarship Council in Beijing",
        "Visa application form JW201/JW202 issuance in July",
    ),
    citation="China Scholarship Council Official Guidelines; Chinese Embassy in Baku Cultural Section.",
)

ERASMUS_MUNDUS = GlobalScholarship(
    key="erasmus-mundus",
    name="Erasmus Mundus Joint Masters Scholarships (EMJM)",
    native_name="Erasmus Mundus Bourses d'Excellence Master Conjoint",
    provider="European Commission (Education, Audiovisual and Culture Executive Agency - EACEA)",
    tier=FundingTier.INTERNATIONAL_CONSORTIUM,
    country_code=None,
    country_name="Multi-Country Consortium (European Union)",
    degree_levels=("master",),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="100% participation and tuition fees across all host institutions, comprehensive worldwide health insurance, travel installation costs, and a flat monthly living allowance of €1,400 per month for the full duration (up to 24 months)",
    stipend_monthly_local="€1,400/month",
    stipend_monthly_azn_approx=2595.0,
    tuition_coverage_pct=100.0,
    travel_covered=True,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation=None,
    min_gpa=3.2,
    min_gpa_scale="4.0",
    min_ielts=6.5,
    min_toefl=85,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="October",
    application_window_end="Mid January (programme specific)",
    official_portal_url="https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en",
    official_guidelines_url="https://erasmus-plus.ec.europa.eu/opportunities/individuals/students/erasmus-mundus-joint-masters",
    azerbaijan_quota_or_seats="Global competition; Azerbaijan qualifies under Region 2 (Eastern Partnership) funding envelope",
    eligibility_criteria=(
        "First higher education degree (Bachelor's degree or recognized equivalent) awarded before course starts",
        "Study must take place in at least two different European programme countries",
        "Proficiency in English at minimum CEFR B2/C1 (IELTS 6.5–7.0)",
        "May apply to a maximum of three different Erasmus Mundus master consortia per annual intake",
    ),
    required_documents=(
        "Bachelor's degree diploma and legalized official transcripts with English translation",
        "Tailored Motivation Letter for the chosen consortium theme",
        "Curriculum Vitae (Europass format)",
        "Two letters of academic or professional recommendation",
        "English language test certificate (IELTS/TOEFL)",
        "Copy of valid international passport",
    ),
    selection_stages=(
        "Application to specific consortium via university website",
        "Consortium joint academic board review and scoring",
        "Submission of candidate ranking list to European Commission EACEA",
        "Formal award notification in March/April",
    ),
    citation="European Commission Erasmus+ Programme Guide; EACEA EMJM Regulations.",
)

GREAT_SCHOLARSHIPS_UK = GlobalScholarship(
    key="great-uk",
    name="GREAT Scholarships",
    native_name="British Council GREAT Scholarships Programme",
    provider="British Council & Participating UK Higher Education Institutions",
    tier=FundingTier.DESTINATION_GOVERNMENT,
    country_code="GB",
    country_name="United Kingdom",
    degree_levels=("master",),
    funding_type=FundingType.TUITION_REDUCTION,
    coverage_summary="A direct £10,000 tuition fee reduction towards a one-year postgraduate taught master's degree in the UK (not a full scholarship; student self-funds remaining tuition and living costs)",
    stipend_monthly_local=None,
    stipend_monthly_azn_approx=None,
    tuition_coverage_pct=40.0,
    travel_covered=False,
    housing_covered=False,
    health_insurance_covered=False,
    return_service_obligation=None,
    min_gpa=3.0,
    min_gpa_scale="4.0",
    min_ielts=6.5,
    min_toefl=80,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="November",
    application_window_end="Varies by university (March to May)",
    official_portal_url="https://study-uk.britishcouncil.org/scholarships-funding/great-scholarships",
    official_guidelines_url="https://www.britishcouncil.az/en/study-uk/great-scholarships",
    azerbaijan_quota_or_seats="5–10 scholarships allocated to Azerbaijani passport holders yearly across designated partner universities",
    eligibility_criteria=(
        "Citizen of the Republic of Azerbaijan holding an Azerbaijani passport",
        "Undergraduate degree holder with strong academic record",
        "Hold an offer of admission from a participating UK partner university for an eligible one-year master's course",
        "Meet the English language requirements of the UK host university",
    ),
    required_documents=(
        "University offer letter for eligible master's program",
        "Completed GREAT application form via partner university portal",
        "Academic transcripts and degree certificate",
        "Statement of Purpose highlighting how the study aligns with bilateral UK-Azerbaijan ties",
        "English language proficiency certificate",
    ),
    selection_stages=(
        "Securing admission offer from participating UK university",
        "Separate scholarship application submitted to host university",
        "Joint assessment by university and British Council panel",
        "Final award notification in May/June",
    ),
    citation="British Council Study UK GREAT Guidance; British Council Azerbaijan.",
)

SOCAR_OVERSEAS_AZ = GlobalScholarship(
    key="socar-xarici-teqaud",
    name="SOCAR Overseas Scholarship Program",
    native_name="SOCAR Xarici Təqaüd Proqramı",
    provider="State Oil Company of the Republic of Azerbaijan (SOCAR)",
    tier=FundingTier.AZERBAIJANI_STATE,
    country_code=None,
    country_name="Global target universities (oil/gas, IT, engineering)",
    degree_levels=("master",),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="Full university tuition fees, monthly living stipend, round-trip flights, and medical insurance during studies abroad",
    stipend_monthly_local="Varies by country ($1,500–$2,200 / month)",
    stipend_monthly_azn_approx=2800.0,
    tuition_coverage_pct=100.0,
    travel_covered=True,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation="Mandatory employment service contract with SOCAR entities in Azerbaijan upon graduation (typically 5 years)",
    min_gpa=3.2,
    min_gpa_scale="4.0",
    min_ielts=6.5,
    min_toefl=80,
    age_limit_bachelor=None,
    age_limit_master=40,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="Varies by corporate call",
    application_window_end="Periodic corporate deadlines",
    official_portal_url="https://socar.az",
    official_guidelines_url="https://socar.az/az/page/karyera/teqaud-proqramlari",
    azerbaijan_quota_or_seats="Corporate quota determined by SOCAR human capital development requirements",
    eligibility_criteria=(
        "Citizen of Azerbaijan",
        "Employment at SOCAR or subsidiaries (corporate internal talent pipeline)",
        "Admission to an approved target master's program in petroleum engineering, geosciences, renewable energy, process automation, or enterprise IT",
        "Age under 40 (under 45 for executive programs)",
    ),
    required_documents=(
        "Proof of current SOCAR employment and departmental nomination",
        "Unconditional admission letter from accredited international institution",
        "Undergraduate diploma and transcripts",
        "Language proficiency certificate (IELTS/TOEFL)",
        "Passport copy and military service status card",
    ),
    selection_stages=(
        "Internal departmental recommendation",
        "Corporate HR assessment and professional competency interview",
        "Final approval by SOCAR Management Board",
    ),
    citation="SOCAR Talent Development Guidelines; AUSA general research brief.",
)

BHOS_FULL_SCHOLARSHIP = GlobalScholarship(
    key="bhos-state-order",
    name="Baku Higher Oil School Full State Scholarship",
    native_name="Bakı Ali Neft Məktəbi Dövlət Sifarişli Təqaüd",
    provider="State of Azerbaijan & Baku Higher Oil School (BANM / BHOS)",
    tier=FundingTier.AZERBAIJANI_STATE,
    country_code="AZ",
    country_name="Azerbaijan (Domestic Study)",
    degree_levels=("bachelor",),
    funding_type=FundingType.FULLY_FUNDED,
    coverage_summary="100% full tuition waiver for 5-year English-medium engineering program (including 1-year foundation), monthly state stipend (up to 200 AZN/month for top grades), and free dormitory priority",
    stipend_monthly_local="100 – 200 AZN / month based on semester academic rating",
    stipend_monthly_azn_approx=150.0,
    tuition_coverage_pct=100.0,
    travel_covered=False,
    housing_covered=True,
    health_insurance_covered=True,
    return_service_obligation=None,
    min_gpa=None,
    min_gpa_scale=None,
    min_ielts=None,
    min_toefl=None,
    age_limit_bachelor=None,
    age_limit_master=None,
    work_experience_hours=None,
    financial_need_based=False,
    max_household_income_eur=None,
    application_window_start="July",
    application_window_end="August (DİM specialty selection)",
    official_portal_url="https://bhos.edu.az",
    official_guidelines_url="https://dim.gov.az",
    azerbaijan_quota_or_seats="Over 400 state-funded places across undergraduate engineering specialties",
    eligibility_criteria=(
        "Citizen of Azerbaijan sitting the DİM Group 1 (or Group 2/4) national university entrance exam",
        "Clear competitive cutoff score for full scholarship (dövlət sifarişli), with baseline threshold 650+ points if not indicated",
        "Selection of BHOS specialties in top priority orders on DİM e-application portal",
    ),
    required_documents=(
        "DİM examination score report confirming qualifying cutoff",
        "Secondary school graduation certificate (Attestat)",
        "Military registration card (for male candidates)",
        "Biometric photos and medical certificate Form 086",
    ),
    selection_stages=(
        "DİM central algorithmic placement based on entrance exam scores and choice order",
        "Document verification and in-person matriculation at BHOS campus in Bibiheybat",
        "English placement test for Foundation year streaming",
    ),
    citation="DİM Official Admissions Guidebook; Baku Higher Oil School Academic Charter (Standard 650+ benchmark).",
)


ALL_GLOBAL_SCHOLARSHIPS: Tuple[GlobalScholarship, ...] = (
    STATE_PROGRAM_AZ,
    CHEVENING_UK,
    FULBRIGHT_USA,
    TURKIYE_BURSLARI,
    STIPENDIUM_HUNGARICUM,
    ITALIAN_DSU_REGIONAL,
    DAAD_GERMANY,
    EIFFEL_EXCELLENCE_FRANCE,
    NAWA_BANACH_POLAND,
    CSC_CHINA,
    ERASMUS_MUNDUS,
    GREAT_SCHOLARSHIPS_UK,
    SOCAR_OVERSEAS_AZ,
    BHOS_FULL_SCHOLARSHIP,
)


# ==============================================================================
# QUALIFICATION EVALUATION ENGINE
# ==============================================================================

@dataclass
class StudentScholarshipProfile:
    """Input profile for evaluating scholarship qualification gates."""
    level_sought: str = "master"  # "bachelor", "master", "phd"
    age: Optional[int] = None
    gpa: Optional[float] = None
    gpa_scale: str = "4.0"
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    dim_score: Optional[float] = None
    work_experience_hours: Optional[int] = None
    employer: Optional[str] = None
    is_azerbaijani_citizen: bool = True
    family_household_income_azn: Optional[float] = None
    target_country_codes: Tuple[str, ...] = field(default_factory=tuple)


def evaluate_scholarship(
    scholarship: GlobalScholarship,
    profile: StudentScholarshipProfile,
) -> GlobalScholarshipEvaluation:
    """Evaluates a student's profile against a global scholarship's discrete qualification gates.

    Outcomes:
    - OPEN: All published prerequisite gates are satisfied.
    - UNLOCKABLE: Obtainable within an application cycle (e.g. pending test retake, hours).
    - BLOCKED: Disqualified by non-remediable criteria (age limit exceeded, level mismatch, citizenship).
    """
    gates_met: List[str] = []
    gates_missing: List[str] = []
    gates_blocked: List[str] = []
    gates_unknown: List[str] = []

    # 1. Degree Level Gate
    if profile.level_sought in scholarship.degree_levels:
        gates_met.append(f"Level match: funds {profile.level_sought} degree study")
    else:
        named_levels = " or ".join(scholarship.degree_levels)
        gates_blocked.append(f"Level mismatch: funds {named_levels} study only (you seek {profile.level_sought})")

    # 2. Age Gate
    if profile.level_sought == "bachelor" and scholarship.age_limit_bachelor is not None:
        if profile.age is None:
            gates_unknown.append(f"Age limit: requires under {scholarship.age_limit_bachelor} for bachelor (age not provided)")
        elif profile.age <= scholarship.age_limit_bachelor:
            gates_met.append(f"Age criterion: {profile.age} years old satisfies under {scholarship.age_limit_bachelor} limit")
        else:
            gates_blocked.append(f"Age exceeded: {profile.age} exceeds the maximum {scholarship.age_limit_bachelor} threshold for bachelor")

    if profile.level_sought == "master" and scholarship.age_limit_master is not None:
        if profile.age is None:
            gates_unknown.append(f"Age limit: requires under {scholarship.age_limit_master} for master (age not provided)")
        elif profile.age <= scholarship.age_limit_master:
            gates_met.append(f"Age criterion: {profile.age} years old satisfies under {scholarship.age_limit_master} limit")
        else:
            gates_blocked.append(f"Age exceeded: {profile.age} exceeds the maximum {scholarship.age_limit_master} threshold for master")

    # 3. Work Experience Gate (e.g. Chevening 2,800 hours)
    if scholarship.work_experience_hours is not None:
        if profile.work_experience_hours is None:
            gates_unknown.append(f"Work experience: requires {scholarship.work_experience_hours:,} documented hours (hours not provided)")
        elif profile.work_experience_hours >= scholarship.work_experience_hours:
            gates_met.append(f"Work experience: {profile.work_experience_hours:,} hours clears {scholarship.work_experience_hours:,} hour requirement")
        else:
            shortfall = scholarship.work_experience_hours - profile.work_experience_hours
            gates_missing.append(f"Work experience: {profile.work_experience_hours:,} hours is {shortfall:,} hours short of {scholarship.work_experience_hours:,} required (hours accrue over time)")

    # 4. Academic GPA Gate
    if scholarship.min_gpa is not None:
        if profile.gpa is None:
            gates_unknown.append(f"Academic GPA: requires minimum {scholarship.min_gpa} on {scholarship.min_gpa_scale or '4.0'} scale (GPA not provided)")
        else:
            # Simple normalization if student provides 5-point scale or 100-point scale
            student_gpa_norm = profile.gpa
            if profile.gpa_scale == "5.0":
                student_gpa_norm = (profile.gpa / 5.0) * 4.0
            elif profile.gpa_scale == "100":
                student_gpa_norm = (profile.gpa / 100.0) * 4.0

            req_gpa_norm = scholarship.min_gpa
            if scholarship.min_gpa_scale == "5.0":
                req_gpa_norm = (scholarship.min_gpa / 5.0) * 4.0

            if student_gpa_norm >= req_gpa_norm:
                gates_met.append(f"Academic GPA: {profile.gpa} satisfies the minimum {scholarship.min_gpa} requirement")
            else:
                gates_missing.append(f"Academic GPA: {profile.gpa} is below the {scholarship.min_gpa} guideline")

    # 5. Language Proficiency Gate (IELTS / TOEFL)
    if scholarship.min_ielts is not None or scholarship.min_toefl is not None:
        has_ielts = profile.ielts is not None and scholarship.min_ielts is not None and profile.ielts >= scholarship.min_ielts
        has_toefl = profile.toefl is not None and scholarship.min_toefl is not None and profile.toefl >= scholarship.min_toefl

        if has_ielts:
            gates_met.append(f"Language score: IELTS {profile.ielts} clears minimum {scholarship.min_ielts}")
        elif has_toefl:
            gates_met.append(f"Language score: TOEFL {profile.toefl} clears minimum {scholarship.min_toefl}")
        elif profile.ielts is None and profile.toefl is None:
            min_desc = []
            if scholarship.min_ielts:
                min_desc.append(f"IELTS {scholarship.min_ielts}")
            if scholarship.min_toefl:
                min_desc.append(f"TOEFL {scholarship.min_toefl}")
            gates_unknown.append(f"Language requirement: requires {' or '.join(min_desc)} (scores not provided)")
        else:
            min_desc = []
            if scholarship.min_ielts:
                min_desc.append(f"IELTS {scholarship.min_ielts}")
            if scholarship.min_toefl:
                min_desc.append(f"TOEFL {scholarship.min_toefl}")
            gates_missing.append(f"Language score: current scores do not meet {' or '.join(min_desc)} (obtainable via test retake)")

    # 6. Corporate Employment Gate (SOCAR)
    if scholarship.key == "socar-xarici-teqaud":
        if profile.employer is None:
            gates_unknown.append("Employment gate: SOCAR corporate talent program requires current SOCAR group employment (employer not stated)")
        elif "socar" in profile.employer.lower():
            gates_met.append(f"Employment match: {profile.employer} satisfies SOCAR group employment requirement")
        else:
            gates_blocked.append(f"Employment gate: SOCAR program is open exclusively to SOCAR group employees (you reported {profile.employer})")

    # 7. Domestic Full Scholarship DİM Cutoff (BHOS)
    if scholarship.key == "bhos-state-order":
        if profile.dim_score is None:
            gates_unknown.append("DİM score: full state scholarship requires 650+ DİM score benchmark (score not provided)")
        elif profile.dim_score >= 650.0:
            gates_met.append(f"DİM score: {profile.dim_score} clears the 650+ full scholarship standard")
        else:
            gates_blocked.append(f"DİM score: {profile.dim_score} is below the 650+ benchmark for full state order scholarship")

    # 8. Financial Need / ISEE-U Gate (Italian DSU)
    if scholarship.financial_need_based and scholarship.max_household_income_eur is not None:
        if profile.family_household_income_azn is None:
            gates_unknown.append("Financial need: Italian DSU requires family ISEE-U below €25,000 (~46,000 AZN household income)")
        else:
            income_eur = profile.family_household_income_azn / 1.854  # CBAR EUR peg
            if income_eur <= scholarship.max_household_income_eur:
                gates_met.append(f"Economic indicator: family income of {profile.family_household_income_azn:,.0f} AZN (~€{income_eur:,.0f}) is within the €25,000 ISEE ceiling")
            else:
                gates_blocked.append(f"Economic indicator: family income (~€{income_eur:,.0f}) exceeds the €25,000 ISEE threshold for fee exemption")

    # Determine overall status
    if gates_blocked:
        status = ScholarshipStatus.BLOCKED
        summary = f"Blocked by {len(gates_blocked)} non-remediable criteria."
    elif gates_missing or gates_unknown:
        status = ScholarshipStatus.UNLOCKABLE
        reasons = []
        if gates_missing:
            reasons.append(f"{len(gates_missing)} actionable requirements")
        if gates_unknown:
            reasons.append(f"{len(gates_unknown)} unverified profile attributes")
        summary = f"Unlockable pending {' and '.join(reasons)}."
    else:
        status = ScholarshipStatus.OPEN
        summary = "You clear all published statutory eligibility criteria for this scholarship."

    return GlobalScholarshipEvaluation(
        scholarship=scholarship,
        status=status,
        gates_met=tuple(gates_met),
        gates_missing=tuple(gates_missing),
        gates_blocked=tuple(gates_blocked),
        gates_unknown=tuple(gates_unknown),
        summary_verdict=summary,
    )


def evaluate_all_scholarships(
    profile: StudentScholarshipProfile,
) -> List[GlobalScholarshipEvaluation]:
    """Evaluates the entire catalogue of 14 global scholarships against student profile."""
    evaluations = [evaluate_scholarship(sch, profile) for sch in ALL_GLOBAL_SCHOLARSHIPS]
    # Sort: OPEN first, then UNLOCKABLE, then BLOCKED
    order = {ScholarshipStatus.OPEN: 0, ScholarshipStatus.UNLOCKABLE: 1, ScholarshipStatus.BLOCKED: 2}
    evaluations.sort(key=lambda x: order[x.status])
    return evaluations
