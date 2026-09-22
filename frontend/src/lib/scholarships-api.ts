/**
 * Client API library and domain models for Global Scholarship Engine & Qualification Assessment.
 */

import { API_BASE_URL } from "@/lib/api";

export type FundingTier = "azerbaijani_state" | "destination_government" | "international_consortium" | "university_merit";

export type FundingType = "fully_funded" | "tuition_and_stipend" | "tuition_only" | "stipend_only" | "tuition_reduction";

export type ScholarshipStatus = "open" | "unlockable" | "blocked";

export interface ScholarshipBrief {
  key: string;
  name: string;
  native_name: string;
  provider: string;
  tier: FundingTier;
  country_code: string | null;
  country_name: string;
  degree_levels: string[];
  funding_type: FundingType;
  coverage_summary: string;
  stipend_monthly_local: string | null;
  stipend_monthly_azn_approx: number | null;
  tuition_coverage_pct: number;
  travel_covered: boolean;
  housing_covered: boolean;
  health_insurance_covered: boolean;
  return_service_obligation: string | null;
  min_gpa: number | null;
  min_ielts: number | null;
  min_toefl: number | null;
  age_limit_bachelor: number | null;
  age_limit_master: number | null;
  work_experience_hours: number | null;
  financial_need_based: boolean;
  application_window_start: string;
  application_window_end: string;
  official_portal_url: string;
  azerbaijan_quota_or_seats: string | null;
}

export interface ScholarshipDetail extends ScholarshipBrief {
  official_guidelines_url: string | null;
  min_gpa_scale: string | null;
  max_household_income_eur: number | null;
  eligibility_criteria: string[];
  required_documents: string[];
  selection_stages: string[];
  citation: string;
  provenance: string;
}

export interface ScholarshipListResponse {
  total_count: number;
  items: ScholarshipBrief[];
  available_countries: string[];
  available_degree_levels: string[];
  available_funding_types: string[];
}

export interface ScholarshipEvaluationRequest {
  level_sought: string;
  age?: number | null;
  gpa?: number | null;
  gpa_scale?: string;
  ielts?: number | null;
  toefl?: number | null;
  dim_score?: number | null;
  work_experience_hours?: number | null;
  employer?: string | null;
  is_azerbaijani_citizen?: boolean;
  family_household_income_azn?: number | null;
  target_country_codes?: string[];
}

export interface EvaluationItemResponse {
  scholarship: ScholarshipBrief;
  status: ScholarshipStatus;
  gates_met: string[];
  gates_missing: string[];
  gates_blocked: string[];
  gates_unknown: string[];
  summary_verdict: string;
}

export interface ScholarshipEvaluationResponse {
  profile_summary: Record<string, unknown>;
  total_evaluated: number;
  open_count: number;
  unlockable_count: number;
  blocked_count: number;
  results: EvaluationItemResponse[];
}

// ==============================================================================
// 14 FALLBACK SCHOLARSHIPS (Instant Zero-Latency Client Data)
// ==============================================================================

export const FALLBACK_SCHOLARSHIPS: ScholarshipDetail[] = [
  {
    key: "dp-azerbaijan",
    name: "State Program on Foreign Education (2022–2026)",
    native_name: "2022–2026-cı illər Dövlət Proqramı",
    provider: "Ministry of Science and Education of the Republic of Azerbaijan",
    tier: "azerbaijani_state",
    country_code: "AZ",
    country_name: "Azerbaijan (Foreign Study)",
    degree_levels: ["bachelor", "master", "phd"],
    funding_type: "fully_funded",
    coverage_summary: "100% tuition, monthly living allowance (stipend), health insurance, visa costs, and round-trip flight tickets",
    stipend_monthly_local: "£1,300/mo UK, €1,100/mo Germany, $1,500/mo USA",
    stipend_monthly_azn_approx: 2400.0,
    tuition_coverage_pct: 100.0,
    travel_covered: true,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: "Mandatory 5-year work service commitment in the Republic of Azerbaijan following degree completion",
    min_gpa: 3.0,
    min_gpa_scale: "4.0",
    min_ielts: 6.5,
    min_toefl: 79,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "Early March",
    application_window_end: "Mid June (annual call)",
    official_portal_url: "https://dp.edu.az",
    official_guidelines_url: "https://dp.edu.az/az/rules",
    azerbaijan_quota_or_seats: "Up to 400 scholars per year (bachelor capped at max 20-25% of quota)",
    eligibility_criteria: [
      "Citizen of the Republic of Azerbaijan",
      "Unconditional admission offer from target university in the 4,121-program catalogue",
      "Minimum 400 DİM score for Group 1 specialties, or 550 for Groups 2-4",
      "Language proficiency certificate satisfying university unconditional admission",
    ],
    required_documents: [
      "Unconditional admission offer letter from approved institution",
      "Academic diploma and official transcript of records",
      "DİM exam result certificate or Attestat score card",
      "Official language proficiency certificate (IELTS/TOEFL)",
      "Curriculum Vitae (CV) and Statement of Purpose",
      "Valid international biometric passport",
      "Medical certificate Form 086",
    ],
    selection_stages: [
      "Electronic document evaluation via portal.edu.az",
      "Interview panel by the Selection Commission of the State Program",
      "Final decree by the Ministry of Science and Education",
    ],
    citation: "Presidential Decree No. 3163 of 28.02.2022; Ministry regulations.",
    provenance: "primary-verified",
  },
  {
    key: "chevening-uk",
    name: "Chevening Scholarship",
    native_name: "Chevening UK Government Scholarship",
    provider: "UK Foreign, Commonwealth & Development Office (FCDO)",
    tier: "destination_government",
    country_code: "GB",
    country_name: "United Kingdom",
    degree_levels: ["master"],
    funding_type: "fully_funded",
    coverage_summary: "Full university tuition fees, monthly living allowance, economy return flights to the UK, and arrival grants",
    stipend_monthly_local: "£1,334/mo London, £1,023/mo outside London",
    stipend_monthly_azn_approx: 2600.0,
    tuition_coverage_pct: 100.0,
    travel_covered: true,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: "Mandatory return to the country of citizenship for a minimum of two years following master's degree",
    min_gpa: 2.8,
    min_gpa_scale: "4.0",
    min_ielts: 6.5,
    min_toefl: 79,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: 2800,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "Early August",
    application_window_end: "Early November",
    official_portal_url: "https://www.chevening.org/apply/",
    official_guidelines_url: "https://www.chevening.org/guidance/eligibility/",
    azerbaijan_quota_or_seats: "Approximately 10–15 fully funded Chevening scholars selected from Azerbaijan annually",
    eligibility_criteria: [
      "Citizen of Azerbaijan",
      "Undergraduate degree equivalent to an upper second-class 2:1 honours UK degree",
      "Minimum 2,800 hours of documented work experience",
      "Apply to three different eligible UK university courses and hold an unconditional offer by July",
    ],
    required_documents: [
      "Undergraduate diploma and transcripts (translated & apostilled)",
      "Four Chevening essay answers (Leadership, Networking, Study in the UK, Career Plan)",
      "Two professional or academic recommendation letters",
      "Valid passport",
      "Unconditional offer from at least one chosen UK university course",
    ],
    selection_stages: [
      "Automated eligibility screening",
      "Independent academic reading committee assessment",
      "In-person interview at the British Embassy in Baku",
      "Final selection announcement by FCDO in June",
    ],
    citation: "https://www.chevening.org/scholarships/who-can-apply/eligibility/",
    provenance: "primary-verified",
  },
  {
    key: "fulbright-usa",
    name: "Fulbright Foreign Student Program",
    native_name: "Fulbright Xarici Tələbə Proqramı",
    provider: "U.S. Department of State (Bureau of Educational and Cultural Affairs)",
    tier: "destination_government",
    country_code: "US",
    country_name: "United States",
    degree_levels: ["master"],
    funding_type: "fully_funded",
    coverage_summary: "Full graduate tuition, monthly living stipend, books allowance, round-trip international airfare, and ASPE health plan",
    stipend_monthly_local: "$1,600 – $2,400/month based on host US city",
    stipend_monthly_azn_approx: 3100.0,
    tuition_coverage_pct: 100.0,
    travel_covered: true,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: "J-1 Exchange Visitor Section 212(e): Mandatory two-year home-country presence requirement in Azerbaijan",
    min_gpa: 3.0,
    min_gpa_scale: "4.0",
    min_ielts: 6.5,
    min_toefl: 80,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "February",
    application_window_end: "Late May",
    official_portal_url: "https://az.usembassy.gov/education-culture/fulbright-foreign-student-program/",
    official_guidelines_url: "https://foreign.fulbrightonline.org/",
    azerbaijan_quota_or_seats: "5–8 Azerbaijani graduate scholars selected annually",
    eligibility_criteria: [
      "Citizen of Azerbaijan residing in Azerbaijan at application",
      "Completed undergraduate bachelor degree",
      "English proficiency with minimum TOEFL iBT 80 or IELTS 6.5",
      "Demonstrated leadership potential and academic excellence",
    ],
    required_documents: [
      "Online Slate application dossier",
      "Personal Statement and Study Objectives essays",
      "Three letters of recommendation",
      "Official university transcripts and diplomas",
      "TOEFL iBT or IELTS score report",
    ],
    selection_stages: [
      "Technical and substantive review by US Embassy Baku",
      "Bilingual interview with U.S. Embassy Selection Committee",
      "Approval by J. William Fulbright Foreign Scholarship Board (Washington D.C.)",
      "University placement via Institute of International Education (IIE)",
    ],
    citation: "https://az.usembassy.gov/fulbright-foreign-student-program/ ; 8 CFR 212(e).",
    provenance: "primary-verified",
  },
  {
    key: "turkiye-burslari",
    name: "Türkiye Bursları",
    native_name: "Türkiye Bursları Tam Kapsamlı Burs Programı",
    provider: "Presidency for Turks Abroad and Related Communities (YTB)",
    tier: "destination_government",
    country_code: "TR",
    country_name: "Turkey",
    degree_levels: ["bachelor", "master", "phd"],
    funding_type: "fully_funded",
    coverage_summary: "University placement, 100% tuition waiver, monthly stipend, free state dormitory, 1-year TÖMER language course, health insurance, and flights",
    stipend_monthly_local: "3,500 TRY/mo (Bachelor), 5,000 TRY/mo (Master)",
    stipend_monthly_azn_approx: 220.0,
    tuition_coverage_pct: 100.0,
    travel_covered: true,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: null,
    min_gpa: 2.8,
    min_gpa_scale: "4.0",
    min_ielts: null,
    min_toefl: null,
    age_limit_bachelor: 21,
    age_limit_master: 30,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "10 January",
    application_window_end: "20 February",
    official_portal_url: "https://www.turkiyeburslari.gov.tr",
    official_guidelines_url: "https://www.turkiyeburslari.gov.tr/fulltimeprograms",
    azerbaijan_quota_or_seats: "150–250 Azerbaijani students awarded scholarships annually",
    eligibility_criteria: [
      "Non-Turkish citizen (Azerbaijani citizens fully eligible)",
      "Minimum 70% GPA for Bachelor, 75% for Master/PhD",
      "Age under 21 for Bachelor, under 30 for Master, under 35 for PhD",
      "Not currently enrolled in a Turkish university at the degree level sought",
    ],
    required_documents: [
      "National ID card or passport",
      "Graduation diploma and academic transcripts",
      "National exam scores (DİM, SAT, if any)",
      "Letter of intent and research proposal (for graduate)",
    ],
    selection_stages: [
      "Preliminary eligibility screening",
      "Expert scoring of academic and social achievements",
      "In-person interview in Baku (Yunus Emre Enstitüsü)",
      "Final selection and placement decree",
    ],
    citation: "https://www.turkiyeburslari.gov.tr/about/whatisturkiyeburslari",
    provenance: "primary-verified",
  },
  {
    key: "stipendium-hungaricum",
    name: "Stipendium Hungaricum Scholarship Programme",
    native_name: "Stipendium Hungaricum Felsőoktatási Ösztöndíjprogram",
    provider: "Tempus Public Foundation & Ministry of Science and Education of Azerbaijan",
    tier: "destination_government",
    country_code: "HU",
    country_name: "Hungary",
    degree_levels: ["bachelor", "master", "phd"],
    funding_type: "fully_funded",
    coverage_summary: "100% tuition exemption, monthly living allowance (HUF 43,700), free dormitory accommodation, and medical insurance",
    stipend_monthly_local: "43,700 HUF/month (Bachelor/Master)",
    stipend_monthly_azn_approx: 210.0,
    tuition_coverage_pct: 100.0,
    travel_covered: false,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: null,
    min_gpa: 2.8,
    min_gpa_scale: "4.0",
    min_ielts: 5.5,
    min_toefl: 65,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "15 November",
    application_window_end: "15 January",
    official_portal_url: "https://apply.stipendiumhungaricum.hu",
    official_guidelines_url: "https://stipendiumhungaricum.hu/apply/",
    azerbaijan_quota_or_seats: "200 annual scholarship quotas for Azerbaijani citizens under bilateral agreement",
    eligibility_criteria: [
      "Citizen of Azerbaijan",
      "Minimum 18 years of age by 31 August of admission year",
      "Nominated by the Ministry of Science and Education of Azerbaijan (portal.edu.az)",
      "Satisfy Hungarian host university entrance exam requirements",
    ],
    required_documents: [
      "Application on Tempus Public Foundation portal",
      "Parallel registration on Ministry portal.edu.az",
      "Motivation letter and English proof",
      "School/bachelor diploma and certified transcript in English",
      "Medical certificate Form 086",
    ],
    selection_stages: [
      "Technical check by Tempus Public Foundation",
      "National nomination screening by Ministry of Science and Education",
      "Institutional entrance examinations/interviews by Hungarian universities",
      "Final awarding decision by Tempus Board in June",
    ],
    citation: "Bilateral Educational Cooperation Workplan between Azerbaijan and Hungary 2024–2026.",
    provenance: "primary-verified",
  },
  {
    key: "italian-dsu-regional",
    name: "Italian Regional DSU Scholarships (EDISU / ER.GO)",
    native_name: "Borse di Studio per il Diritto allo Studio Universitario (DSU)",
    provider: "Italian Regional Education & Welfare Agencies (EDISU Piemonte, ER.GO, Disco Lazio)",
    tier: "destination_government",
    country_code: "IT",
    country_name: "Italy",
    degree_levels: ["bachelor", "master"],
    funding_type: "fully_funded",
    coverage_summary: "100% university tuition fee exemption, regional cash scholarship stipend up to €7,200/year, free cafeteria meals, and subsidized student residence",
    stipend_monthly_local: "Up to €600/month (€7,200/year) for non-residents",
    stipend_monthly_azn_approx: 1100.0,
    tuition_coverage_pct: 100.0,
    travel_covered: false,
    housing_covered: true,
    health_insurance_covered: false,
    return_service_obligation: null,
    min_gpa: null,
    min_gpa_scale: null,
    min_ielts: null,
    min_toefl: null,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: true,
    max_household_income_eur: 25000.0,
    application_window_start: "Early June",
    application_window_end: "Late August / Early September",
    official_portal_url: "https://www.edisu.piemonte.it ; https://www.er-go.it",
    official_guidelines_url: "https://www.universitaly.it",
    azerbaijan_quota_or_seats: "Needs-based welfare entitlement; all eligible international students below threshold receive grant or fee waiver",
    eligibility_criteria: [
      "Enrolled or matriculating into an accredited Italian public university",
      "Family ISEE Parificato economic indicator must not exceed €25,000",
      "Family asset indicator (ISPE) under €50,000",
      "Minimum 20 CFU university credits required for second year renewal",
    ],
    required_documents: [
      "Consular legalized family composition certificate from Azerbaijan",
      "Income certificate of all adult household members for previous calendar year",
      "Property ownership documentation showing square meters",
      "Bank account statements as of 31 December",
      "Official ISEE Parificato certificate issued by an authorized Italian CAF",
    ],
    selection_stages: [
      "Online submission of economic declarations to regional agency",
      "Publication of provisional ranking list (graduatoria provvisoria) in October",
      "Submission of Italian residence permit and IBAN coordinates",
      "Stipend disbursement in two installments (December and June)",
    ],
    citation: "D.P.C.M. 159/2013 and Legislative Decree 68/2012 on Right to University Education.",
    provenance: "primary-verified",
  },
  {
    key: "daad-germany",
    name: "DAAD Master Studies Scholarships",
    native_name: "DAAD Stipendien für Masterstudiengänge",
    provider: "Deutscher Akademischer Austauschdienst (DAAD)",
    tier: "destination_government",
    country_code: "DE",
    country_name: "Germany",
    degree_levels: ["master"],
    funding_type: "fully_funded",
    coverage_summary: "Monthly scholarship payment of €934, travel allowance, study allowance, health and accident insurance, and German language course funding",
    stipend_monthly_local: "€934/month (€11,208/year)",
    stipend_monthly_azn_approx: 1730.0,
    tuition_coverage_pct: 100.0,
    travel_covered: true,
    housing_covered: false,
    health_insurance_covered: true,
    return_service_obligation: null,
    min_gpa: 3.0,
    min_gpa_scale: "4.0",
    min_ielts: 6.5,
    min_toefl: 80,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "Early September",
    application_window_end: "Mid November",
    official_portal_url: "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
    official_guidelines_url: "https://www.daad-azerbaijan.org/",
    azerbaijan_quota_or_seats: "Competitive international selection; individual grants awarded yearly",
    eligibility_criteria: [
      "Completed Bachelor's degree within last 6 years",
      "Excellent academic record with strong academic references",
      "Admission to a recognized German higher education institution",
      "German (TestDaF/DSH) or English (IELTS 6.5/TOEFL 80) proficiency",
    ],
    required_documents: [
      "Online DAAD portal application form",
      "Curriculum vitae (Europass)",
      "Letter of motivation (1–3 pages)",
      "University degree certificate and transcripts",
      "Letter of recommendation from university professor",
    ],
    selection_stages: [
      "Pre-selection by an independent selection committee in Germany",
      "Academic review of motivation and academic trajectory",
      "Final awarding decision in April/May",
    ],
    citation: "DAAD Scholarship Database guidelines; DAAD Information Centre Baku.",
    provenance: "primary-verified",
  },
  {
    key: "eiffel-france",
    name: "Eiffel Excellence Scholarship Programme (Bourses Eiffel)",
    native_name: "Programme de bourses d'excellence Eiffel",
    provider: "French Ministry for Europe and Foreign Affairs (Campus France)",
    tier: "destination_government",
    country_code: "FR",
    country_name: "France",
    degree_levels: ["master", "phd"],
    funding_type: "fully_funded",
    coverage_summary: "Monthly allowance of €1,181 for Master students (€1,800 for PhD), international airfare, domestic train transport, health insurance, and cultural subsidies",
    stipend_monthly_local: "€1,181/month (Master) or €1,800/month (PhD)",
    stipend_monthly_azn_approx: 2190.0,
    tuition_coverage_pct: 100.0,
    travel_covered: true,
    housing_covered: false,
    health_insurance_covered: true,
    return_service_obligation: null,
    min_gpa: 3.2,
    min_gpa_scale: "4.0",
    min_ielts: 6.5,
    min_toefl: 80,
    age_limit_bachelor: null,
    age_limit_master: 25,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "October",
    application_window_end: "Early January",
    official_portal_url: "https://www.campusfrance.org/en/the-eiffel-scholarship-program",
    official_guidelines_url: "https://www.campusfrance.org/en/eiffel-program-call-for-applications",
    azerbaijan_quota_or_seats: "Prestigious global competition; ~350 worldwide awards distributed annually",
    eligibility_criteria: [
      "Non-French nationality (Azerbaijani citizens fully eligible)",
      "Maximum age: 25 years old for Master's level (up to 30 for PhD)",
      "Application submitted exclusively by host French university (direct applications disqualified)",
      "Fields: Science, Engineering, Economics, Management, Law",
    ],
    required_documents: [
      "Institutional application file submitted by French university",
      "Curriculum Vitae in French or English",
      "Professional project and career roadmap statement",
      "Official academic transcripts and degree rankings",
    ],
    selection_stages: [
      "Pre-selection by French higher education institutions",
      "Submission to Campus France Paris",
      "Consultative committee expert scoring",
      "Announcement of laureates in early April",
    ],
    citation: "Campus France Eiffel Excellence Guidelines; Ministry for Europe and Foreign Affairs.",
    provenance: "primary-verified",
  },
  {
    key: "nawa-banach-poland",
    name: "Stefan Banach Scholarship Programme (NAWA Poland)",
    native_name: "Program stypendialny im. Stefana Banacha",
    provider: "Polish National Agency for Academic Exchange (NAWA)",
    tier: "destination_government",
    country_code: "PL",
    country_name: "Poland",
    degree_levels: ["master"],
    funding_type: "fully_funded",
    coverage_summary: "Full tuition fee exemption at Polish public universities and a monthly living allowance of PLN 2,500 during the academic year",
    stipend_monthly_local: "2,500 PLN/month",
    stipend_monthly_azn_approx: 1080.0,
    tuition_coverage_pct: 100.0,
    travel_covered: false,
    housing_covered: false,
    health_insurance_covered: false,
    return_service_obligation: null,
    min_gpa: 2.8,
    min_gpa_scale: "4.0",
    min_ielts: 6.0,
    min_toefl: 75,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "March",
    application_window_end: "Early May",
    official_portal_url: "https://nawa.gov.pl/en/students/foreign-students/the-banach-scholarship-programme",
    official_guidelines_url: "https://nawa.gov.pl/images/Banach/2026/Banach-2026---Call-for-applications-EN.pdf",
    azerbaijan_quota_or_seats: "Azerbaijan is specifically listed as an eligible priority country in the European Neighbourhood group",
    eligibility_criteria: [
      "Citizen of Azerbaijan",
      "Undergraduate degree completed no earlier than 2024 (or completing in application year)",
      "Full-time Master's study at participating Polish public universities",
      "Minimum language level B2 in Polish or English",
    ],
    required_documents: [
      "Passport scan and higher education diploma",
      "Transcript of grades and GPA calculation",
      "Language certificate at minimum B2 level",
      "Academic recommendation letter",
    ],
    selection_stages: [
      "Formal eligibility check by NAWA agency",
      "Merit assessment by external evaluation experts",
      "Publication of results list by late July",
    ],
    citation: "NAWA Banach Call for Applications; Polish Ministry of Foreign Affairs.",
    provenance: "primary-verified",
  },
  {
    key: "csc-china",
    name: "Chinese Government Scholarship (CSC / Silk Road)",
    native_name: "中国政府奖学金 (CSC)",
    provider: "China Scholarship Council (CSC)",
    tier: "destination_government",
    country_code: "CN",
    country_name: "China",
    degree_levels: ["bachelor", "master", "phd"],
    funding_type: "fully_funded",
    coverage_summary: "Full tuition waiver, free university dormitory, medical insurance, and monthly living stipend (CNY 2,500–3,500/month)",
    stipend_monthly_local: "2,500 CNY/mo (Bachelor), 3,000 CNY/mo (Master)",
    stipend_monthly_azn_approx: 600.0,
    tuition_coverage_pct: 100.0,
    travel_covered: false,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: null,
    min_gpa: 2.8,
    min_gpa_scale: "4.0",
    min_ielts: 6.0,
    min_toefl: 75,
    age_limit_bachelor: 25,
    age_limit_master: 35,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "Early January",
    application_window_end: "Early April",
    official_portal_url: "https://www.campuschina.org",
    official_guidelines_url: "https://www.campuschina.org/content/details3_74776.html",
    azerbaijan_quota_or_seats: "50+ scholarships awarded to Azerbaijani students under Type A (Embassy) and Type B (University) tracks",
    eligibility_criteria: [
      "Non-Chinese citizen in good health",
      "Age under 25 for Bachelor, under 35 for Master, under 40 for PhD",
      "HSK 4 for Chinese-taught undergraduate; IELTS 6.0/TOEFL 75 for English-taught graduate",
    ],
    required_documents: [
      "Application Form on CSC portal",
      "Notarized diploma and academic transcripts",
      "Foreigner Physical Examination Form",
      "Study Plan or Research Proposal",
      "Non-Criminal Record certificate",
    ],
    selection_stages: [
      "Review by Chinese Embassy or host university",
      "Pre-admission Letter issuance",
      "Review by China Scholarship Council in Beijing",
      "Visa form JW201 issuance in July",
    ],
    citation: "China Scholarship Council Official Guidelines; Chinese Embassy in Baku.",
    provenance: "primary-verified",
  },
  {
    key: "erasmus-mundus",
    name: "Erasmus Mundus Joint Masters Scholarships (EMJM)",
    native_name: "Erasmus Mundus Bourses d'Excellence Master Conjoint",
    provider: "European Commission (EACEA)",
    tier: "international_consortium",
    country_code: null,
    country_name: "Multi-Country Consortium (European Union)",
    degree_levels: ["master"],
    funding_type: "fully_funded",
    coverage_summary: "100% participation tuition fees, comprehensive worldwide health insurance, travel costs, and €1,400 per month living allowance",
    stipend_monthly_local: "€1,400/month",
    stipend_monthly_azn_approx: 2595.0,
    tuition_coverage_pct: 100.0,
    travel_covered: true,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: null,
    min_gpa: 3.2,
    min_gpa_scale: "4.0",
    min_ielts: 6.5,
    min_toefl: 85,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "October",
    application_window_end: "Mid January",
    official_portal_url: "https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en",
    official_guidelines_url: "https://erasmus-plus.ec.europa.eu/opportunities/individuals/students/erasmus-mundus-joint-masters",
    azerbaijan_quota_or_seats: "Global competition; Azerbaijan qualifies under Eastern Partnership funding envelope",
    eligibility_criteria: [
      "Bachelor's degree or recognized equivalent awarded before course start",
      "Study in at least two different European programme countries",
      "English proficiency at minimum B2/C1 (IELTS 6.5–7.0)",
    ],
    required_documents: [
      "Bachelor's diploma and legalized transcripts with English translation",
      "Tailored Motivation Letter",
      "Curriculum Vitae (Europass)",
      "Two letters of recommendation",
      "English test score report",
    ],
    selection_stages: [
      "Application to specific consortium portal",
      "Consortium joint academic board review",
      "EACEA ranking validation",
      "Award notification in March/April",
    ],
    citation: "European Commission Erasmus+ Programme Guide; EACEA EMJM Regulations.",
    provenance: "primary-verified",
  },
  {
    key: "great-uk",
    name: "GREAT Scholarships",
    native_name: "British Council GREAT Scholarships Programme",
    provider: "British Council & Participating UK Higher Education Institutions",
    tier: "destination_government",
    country_code: "GB",
    country_name: "United Kingdom",
    degree_levels: ["master"],
    funding_type: "tuition_reduction",
    coverage_summary: "Direct £10,000 tuition fee reduction towards a one-year postgraduate taught master's degree in the UK",
    stipend_monthly_local: null,
    stipend_monthly_azn_approx: null,
    tuition_coverage_pct: 40.0,
    travel_covered: false,
    housing_covered: false,
    health_insurance_covered: false,
    return_service_obligation: null,
    min_gpa: 3.0,
    min_gpa_scale: "4.0",
    min_ielts: 6.5,
    min_toefl: 80,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "November",
    application_window_end: "March to May (university specific)",
    official_portal_url: "https://study-uk.britishcouncil.org/scholarships-funding/great-scholarships",
    official_guidelines_url: "https://www.britishcouncil.az/en/study-uk/great-scholarships",
    azerbaijan_quota_or_seats: "5–10 scholarships allocated to Azerbaijani passport holders yearly",
    eligibility_criteria: [
      "Citizen of the Republic of Azerbaijan holding an Azerbaijani passport",
      "Undergraduate degree holder with strong academic record",
      "Offer of admission from a participating UK partner university for master's study",
    ],
    required_documents: [
      "University offer letter for eligible master's program",
      "Completed GREAT application form via partner university",
      "Academic transcripts and diploma",
      "Statement of Purpose",
    ],
    selection_stages: [
      "Admission offer from participating UK university",
      "Scholarship application submission to host university",
      "Joint assessment by university and British Council panel",
      "Award notification in May/June",
    ],
    citation: "British Council Study UK GREAT Guidance; British Council Azerbaijan.",
    provenance: "primary-verified",
  },
  {
    key: "socar-xarici-teqaud",
    name: "SOCAR Overseas Scholarship Program",
    native_name: "SOCAR Xarici Təqaüd Proqramı",
    provider: "State Oil Company of the Republic of Azerbaijan (SOCAR)",
    tier: "azerbaijani_state",
    country_code: null,
    country_name: "Global Target Universities (Energy & Tech)",
    degree_levels: ["master"],
    funding_type: "fully_funded",
    coverage_summary: "Full university tuition fees, monthly living stipend ($1,500–$2,200), round-trip flights, and medical insurance",
    stipend_monthly_local: "$1,500 – $2,200 / month",
    stipend_monthly_azn_approx: 2800.0,
    tuition_coverage_pct: 100.0,
    travel_covered: true,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: "Mandatory employment service contract with SOCAR in Azerbaijan upon graduation (typically 5 years)",
    min_gpa: 3.2,
    min_gpa_scale: "4.0",
    min_ielts: 6.5,
    min_toefl: 80,
    age_limit_bachelor: null,
    age_limit_master: 40,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "Varies by corporate call",
    application_window_end: "Periodic corporate deadlines",
    official_portal_url: "https://socar.az",
    official_guidelines_url: "https://socar.az/az/page/karyera/teqaud-proqramlari",
    azerbaijan_quota_or_seats: "Corporate quota determined by SOCAR human capital requirements",
    eligibility_criteria: [
      "Citizen of Azerbaijan",
      "Employment at SOCAR or subsidiaries (corporate internal talent pipeline)",
      "Admission to approved target master's program in petroleum, IT, or engineering",
      "Age under 40",
    ],
    required_documents: [
      "Proof of current SOCAR employment and departmental nomination",
      "Unconditional admission letter from accredited international institution",
      "Undergraduate diploma and transcripts",
      "Language proficiency certificate (IELTS/TOEFL)",
    ],
    selection_stages: [
      "Internal departmental recommendation",
      "Corporate HR assessment and competency interview",
      "Approval by SOCAR Management Board",
    ],
    citation: "SOCAR Talent Development Guidelines; AUSA general research brief.",
    provenance: "primary-verified",
  },
  {
    key: "bhos-state-order",
    name: "Baku Higher Oil School Full State Scholarship",
    native_name: "Bakı Ali Neft Məktəbi Dövlət Sifarişli Təqaüd",
    provider: "State of Azerbaijan & Baku Higher Oil School (BANM / BHOS)",
    tier: "azerbaijani_state",
    country_code: "AZ",
    country_name: "Azerbaijan (Domestic Study)",
    degree_levels: ["bachelor"],
    funding_type: "fully_funded",
    coverage_summary: "100% full tuition waiver for 5-year English-medium engineering program, monthly state stipend, and free dormitory priority",
    stipend_monthly_local: "100 – 200 AZN / month based on rating",
    stipend_monthly_azn_approx: 150.0,
    tuition_coverage_pct: 100.0,
    travel_covered: false,
    housing_covered: true,
    health_insurance_covered: true,
    return_service_obligation: null,
    min_gpa: null,
    min_gpa_scale: null,
    min_ielts: null,
    min_toefl: null,
    age_limit_bachelor: null,
    age_limit_master: null,
    work_experience_hours: null,
    financial_need_based: false,
    max_household_income_eur: null,
    application_window_start: "July",
    application_window_end: "August (DİM selection)",
    official_portal_url: "https://bhos.edu.az",
    official_guidelines_url: "https://dim.gov.az",
    azerbaijan_quota_or_seats: "Over 400 state-funded places across undergraduate engineering specialties",
    eligibility_criteria: [
      "Citizen of Azerbaijan sitting the DİM Group 1 (or Group 2/4) entrance exam",
      "Clear cutoff score for full scholarship (dövlət sifarişli), baseline 650+ points if not indicated",
      "Selection of BHOS in top priority choices on DİM portal",
    ],
    required_documents: [
      "DİM examination score report confirming qualifying cutoff",
      "Secondary school graduation certificate (Attestat)",
      "Military registration card and medical certificate Form 086",
    ],
    selection_stages: [
      "DİM central algorithmic placement based on entrance scores",
      "Document verification at BHOS campus in Bibiheybat",
      "English placement test for Foundation year streaming",
    ],
    citation: "DİM Official Admissions Guidebook; Baku Higher Oil School Charter.",
    provenance: "primary-verified",
  },
];

// ==============================================================================
// LOCAL EVALUATION LOGIC (Zero-latency fallback)
// ==============================================================================

export function evaluateScholarshipsLocal(req: ScholarshipEvaluationRequest): ScholarshipEvaluationResponse {
  const levelSought = req.level_sought || "master";
  const results: EvaluationItemResponse[] = [];
  let openCount = 0;
  let unlockableCount = 0;
  let blockedCount = 0;

  for (const s of FALLBACK_SCHOLARSHIPS) {
    const met: string[] = [];
    const missing: string[] = [];
    const blocked: string[] = [];
    const unknown: string[] = [];

    // 1. Level check
    if (s.degree_levels.includes(levelSought)) {
      met.push(`Level match: funds ${levelSought} degree study`);
    } else {
      blocked.push(`Level mismatch: funds ${s.degree_levels.join(" or ")} study only`);
    }

    // 2. Age check
    if (levelSought === "bachelor" && s.age_limit_bachelor) {
      if (req.age == null) {
        unknown.push(`Age limit: requires under ${s.age_limit_bachelor} for bachelor (not provided)`);
      } else if (req.age <= s.age_limit_bachelor) {
        met.push(`Age: ${req.age} satisfies under ${s.age_limit_bachelor} requirement`);
      } else {
        blocked.push(`Age: ${req.age} exceeds maximum ${s.age_limit_bachelor} limit for bachelor`);
      }
    }

    if (levelSought === "master" && s.age_limit_master) {
      if (req.age == null) {
        unknown.push(`Age limit: requires under ${s.age_limit_master} for master (not provided)`);
      } else if (req.age <= s.age_limit_master) {
        met.push(`Age: ${req.age} satisfies under ${s.age_limit_master} requirement`);
      } else {
        blocked.push(`Age: ${req.age} exceeds maximum ${s.age_limit_master} limit for master`);
      }
    }

    // 3. Work hours check
    if (s.work_experience_hours) {
      if (req.work_experience_hours == null) {
        unknown.push(`Work hours: requires ${s.work_experience_hours.toLocaleString()} documented hours (not provided)`);
      } else if (req.work_experience_hours >= s.work_experience_hours) {
        met.push(`Work hours: ${req.work_experience_hours.toLocaleString()} clears ${s.work_experience_hours.toLocaleString()} hour requirement`);
      } else {
        missing.push(`Work hours: ${req.work_experience_hours.toLocaleString()} is short of ${s.work_experience_hours.toLocaleString()} required`);
      }
    }

    // 4. GPA check
    if (s.min_gpa) {
      if (req.gpa == null) {
        unknown.push(`GPA: requires minimum ${s.min_gpa} (not provided)`);
      } else if (req.gpa >= s.min_gpa) {
        met.push(`GPA: ${req.gpa} satisfies minimum ${s.min_gpa} guideline`);
      } else {
        missing.push(`GPA: ${req.gpa} is below ${s.min_gpa} guideline`);
      }
    }

    // 5. Language check
    if (s.min_ielts || s.min_toefl) {
      const clearsIelts = req.ielts != null && s.min_ielts != null && req.ielts >= s.min_ielts;
      const clearsToefl = req.toefl != null && s.min_toefl != null && req.toefl >= s.min_toefl;
      if (clearsIelts) {
        met.push(`Language: IELTS ${req.ielts} clears minimum ${s.min_ielts}`);
      } else if (clearsToefl) {
        met.push(`Language: TOEFL ${req.toefl} clears minimum ${s.min_toefl}`);
      } else if (req.ielts == null && req.toefl == null) {
        unknown.push(`Language: requires IELTS ${s.min_ielts || "6.5"} or TOEFL ${s.min_toefl || "80"}`);
      } else {
        missing.push(`Language: current scores do not meet IELTS ${s.min_ielts || "6.5"} / TOEFL ${s.min_toefl || "80"}`);
      }
    }

    // 6. SOCAR check
    if (s.key === "socar-xarici-teqaud") {
      if (req.employer == null) {
        unknown.push("Employment: requires SOCAR group employment");
      } else if (req.employer.toLowerCase().includes("socar")) {
        met.push(`Employment: ${req.employer} satisfies SOCAR requirement`);
      } else {
        blocked.push(`Employment: open exclusively to SOCAR employees (reported ${req.employer})`);
      }
    }

    // 7. BHOS 650+ check
    if (s.key === "bhos-state-order") {
      if (req.dim_score == null) {
        unknown.push("DİM score: full scholarship requires 650+ DİM score");
      } else if (req.dim_score >= 650) {
        met.push(`DİM score: ${req.dim_score} clears 650+ full scholarship benchmark`);
      } else {
        blocked.push(`DİM score: ${req.dim_score} is below 650+ benchmark`);
      }
    }

    // 8. Financial need check
    if (s.financial_need_based && s.max_household_income_eur) {
      if (req.family_household_income_azn == null) {
        unknown.push("Financial need: requires family ISEE under €25,000 (~46,000 AZN)");
      } else {
        const eur = req.family_household_income_azn / 1.854;
        if (eur <= s.max_household_income_eur) {
          met.push(`Economic indicator: income €${Math.round(eur).toLocaleString()} is within €25,000 ceiling`);
        } else {
          blocked.push(`Economic indicator: income €${Math.round(eur).toLocaleString()} exceeds €25,000 ceiling`);
        }
      }
    }

    // Status decision
    let status: ScholarshipStatus;
    let verdict: string;

    if (blocked.length > 0) {
      status = "blocked";
      verdict = `Blocked by ${blocked.length} non-remediable criteria.`;
      blockedCount++;
    } else if (missing.length > 0 || unknown.length > 0) {
      status = "unlockable";
      verdict = `Unlockable pending ${missing.length} actionable requirements and ${unknown.length} unverified attributes.`;
      unlockableCount++;
    } else {
      status = "open";
      verdict = "You clear all published statutory eligibility criteria for this scholarship.";
      openCount++;
    }

    results.push({
      scholarship: s,
      status,
      gates_met: met,
      gates_missing: missing,
      gates_blocked: blocked,
      gates_unknown: unknown,
      summary_verdict: verdict,
    });
  }

  // Sort: open first, then unlockable, then blocked
  const order: Record<ScholarshipStatus, number> = { open: 0, unlockable: 1, blocked: 2 };
  results.sort((a, b) => order[a.status] - order[b.status]);

  return {
    profile_summary: {
      level_sought: req.level_sought,
      age: req.age,
      gpa: req.gpa ? `${req.gpa} (${req.gpa_scale || "4.0"})` : null,
      ielts: req.ielts,
      toefl: req.toefl,
      dim_score: req.dim_score,
      work_experience_hours: req.work_experience_hours,
      employer: req.employer,
    },
    total_evaluated: results.length,
    open_count: openCount,
    unlockable_count: unlockableCount,
    blocked_count: blockedCount,
    results,
  };
}

// ==============================================================================
// ASYNC API CLIENT FUNCTIONS (With Graceful Local Fallbacks)
// ==============================================================================

export async function fetchScholarships(params?: {
  country?: string;
  degree_level?: string;
  funding_type?: string;
  tier?: string;
  search?: string;
}): Promise<ScholarshipListResponse> {
  const query = new URLSearchParams();
  if (params?.country) query.set("country", params.country);
  if (params?.degree_level) query.set("degree_level", params.degree_level);
  if (params?.funding_type) query.set("funding_type", params.funding_type);
  if (params?.tier) query.set("tier", params.tier);
  if (params?.search) query.set("search", params.search);

  try {
    const res = await fetch(`${API_BASE_URL}/scholarships?${query.toString()}`);
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Local fallback
  }

  let filtered = [...FALLBACK_SCHOLARSHIPS];
  if (params?.country) {
    const c = params.country.toLowerCase();
    filtered = filtered.filter(
      (s) => (s.country_code && s.country_code.toLowerCase() === c) || s.country_name.toLowerCase().includes(c)
    );
  }
  if (params?.degree_level) {
    const l = params.degree_level.toLowerCase();
    filtered = filtered.filter((s) => s.degree_levels.includes(l));
  }
  if (params?.funding_type) {
    const ft = params.funding_type.toLowerCase();
    filtered = filtered.filter((s) => s.funding_type.toLowerCase() === ft);
  }
  if (params?.search) {
    const q = params.search.toLowerCase();
    filtered = filtered.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.native_name.toLowerCase().includes(q) ||
        s.provider.toLowerCase().includes(q) ||
        s.country_name.toLowerCase().includes(q)
    );
  }

  const countries = Array.from(new Set(FALLBACK_SCHOLARSHIPS.map((s) => s.country_name))).sort();

  return {
    total_count: filtered.length,
    items: filtered,
    available_countries: countries,
    available_degree_levels: ["bachelor", "master", "phd"],
    available_funding_types: ["fully_funded", "tuition_and_stipend", "tuition_only", "tuition_reduction"],
  };
}

export async function fetchScholarshipDetail(key: string): Promise<ScholarshipDetail | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/scholarships/${encodeURIComponent(key)}`);
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Local fallback
  }
  return FALLBACK_SCHOLARSHIPS.find((s) => s.key === key) || null;
}

export async function evaluateScholarshipsApi(
  req: ScholarshipEvaluationRequest
): Promise<ScholarshipEvaluationResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/scholarships/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Local fallback
  }
  return evaluateScholarshipsLocal(req);
}
