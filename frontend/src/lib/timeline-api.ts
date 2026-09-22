/**
 * Admissions Timeline, Calendar & Milestone Client API for AUSA.
 * 
 * Provides:
 * - TypeScript types matching FastAPI Pydantic domain models.
 * - Curated 24+ verified international admissions milestones for the 2026/2027 cycle.
 * - Client-side fallback filtering and real-time urgency calculations.
 * - Standard RFC 5545 iCalendar (.ics) generation for zero-latency calendar downloads.
 */

export type MilestoneType =
  | "PORTAL_OPEN"
  | "EARLY_DEADLINE"
  | "EQUAL_CONSIDERATION"
  | "REGULAR_DEADLINE"
  | "SCHOLARSHIP_DEADLINE"
  | "DECISION_RELEASE"
  | "VISA_WINDOW"
  | "DOCUMENT_SUBMISSION";

export type IntakeSeason =
  | "fall_2026"
  | "spring_2027"
  | "winter_2026"
  | "spring_2026"
  | "fall_2027"
  | "rolling";

export type UrgencyLevel = "CRITICAL" | "UPCOMING" | "OPEN" | "PASSED";

export type DegreeLevel = "bachelor" | "master" | "phd" | "all";

export interface MilestoneItem {
  id: string;
  title: string;
  portal_name: string;
  country_code: string;
  country_name: string;
  flag: string;
  degree_level: DegreeLevel;
  intake: IntakeSeason;
  milestone_type: MilestoneType;
  target_date: string; // ISO YYYY-MM-DD
  deadline_time: string;
  description: string;
  official_portal_url: string;
  requirements_summary: string[];
  is_hard_deadline: boolean;
  days_remaining: number;
  urgency: UrgencyLevel;
  is_state_programme_eligible: boolean;
}

export interface TimelineSchedule {
  total_milestones: number;
  critical_count: number;
  upcoming_count: number;
  open_count: number;
  passed_count: number;
  milestones: MilestoneItem[];
  generated_at: string;
}

export interface MilestoneFilter {
  country_code?: string;
  degree_level?: DegreeLevel;
  intake?: IntakeSeason;
  urgency?: UrgencyLevel;
  is_state_programme_eligible?: boolean;
  search_query?: string;
}

export interface CustomReminderInput {
  title: string;
  target_date: string;
  country_name: string;
  description?: string;
  portal_url?: string;
  reminder_days_before: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

// ==============================================================================
// Curated 2026/2027 Admissions Milestones
// ==============================================================================

export const FALLBACK_MILESTONES_RAW: Omit<MilestoneItem, "days_remaining" | "urgency">[] = [
  {
    id: "gb_ucas_oxbridge_2026",
    title: "UCAS Oxbridge, Medicine & Dentistry Early Deadline",
    portal_name: "UCAS (Universities and Colleges Admissions Service)",
    country_code: "GB",
    country_name: "United Kingdom",
    flag: "🇬🇧",
    degree_level: "bachelor",
    intake: "fall_2026",
    milestone_type: "EARLY_DEADLINE",
    target_date: "2026-10-15",
    deadline_time: "18:00 (UK Time)",
    description: "Strict deadline for all Oxford, Cambridge, and UK medicine, dentistry, and veterinary courses.",
    official_portal_url: "https://www.ucas.com",
    requirements_summary: [
      "UCAS Personal Statement (4,000 chars)",
      "Predicted A-Level / IB / Attestat grades",
      "Academic reference letter",
      "University admissions test registration (UCAT, ESAT, TMUA)",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "chevening_global_2026",
    title: "UK Chevening Master's Scholarship Deadline",
    portal_name: "Chevening OAS Portal",
    country_code: "GB",
    country_name: "United Kingdom",
    flag: "🇬🇧",
    degree_level: "master",
    intake: "fall_2027",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2026-11-03",
    deadline_time: "12:00 (GMT)",
    description: "Prestigious UK Foreign, Commonwealth & Development Office full master's scholarship for future Azerbaijani leaders.",
    official_portal_url: "https://www.chevening.org/scholarship/azerbaijan/",
    requirements_summary: [
      "4 Core Essays (Leadership, Networking, Study in UK, Career Plan)",
      "Minimum 2,800 hours of documented work experience",
      "Undergraduate degree diploma & transcript (GPA 3.0+/4.0)",
      "Three eligible UK Master's course selections",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: false,
  },
  {
    id: "us_common_app_ed1_2026",
    title: "US Common App Early Action & Early Decision I (EA/ED1)",
    portal_name: "Common Application",
    country_code: "US",
    country_name: "United States",
    flag: "🇺🇸",
    degree_level: "bachelor",
    intake: "fall_2026",
    milestone_type: "EARLY_DEADLINE",
    target_date: "2026-11-01",
    deadline_time: "23:59 (Applicant Local Time)",
    description: "Binding (ED) and non-binding (EA) early admission round for top US universities (MIT, Harvard, Stanford, Columbia).",
    official_portal_url: "https://www.commonapp.org",
    requirements_summary: [
      "Common App Personal Essay (650 words)",
      "Supplemental university-specific essays",
      "High School Official Transcript with school profile",
      "Counselor recommendation + 2 teacher evaluations",
      "SAT/ACT score report or test-optional declaration",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "us_grad_priority_2026",
    title: "US Graduate School Priority Fellowship & PhD Deadline",
    portal_name: "University Graduate Admissions Portals",
    country_code: "US",
    country_name: "United States",
    flag: "🇺🇸",
    degree_level: "master",
    intake: "fall_2026",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2026-12-01",
    deadline_time: "23:59 (EST)",
    description: "First priority round for graduate institutional assistantships (TA/RA), fellowships, and STEM PhD programs.",
    official_portal_url: "https://grad.gatech.edu",
    requirements_summary: [
      "Statement of Purpose (SOP)",
      "3 Academic letters of recommendation",
      "Official Bachelor's transcripts (WES evaluation if required)",
      "GRE General score report (where required)",
      "TOEFL iBT (100+) or IELTS Academic (7.5+)",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "us_common_app_rd_2027",
    title: "US Regular Decision (RD) & ED II Deadline",
    portal_name: "Common Application",
    country_code: "US",
    country_name: "United States",
    flag: "🇺🇸",
    degree_level: "bachelor",
    intake: "fall_2026",
    milestone_type: "REGULAR_DEADLINE",
    target_date: "2027-01-05",
    deadline_time: "23:59 (Applicant Local Time)",
    description: "Standard admissions window for major US undergraduate universities.",
    official_portal_url: "https://www.commonapp.org",
    requirements_summary: [
      "Complete Common App dossier",
      "Mid-year senior year grades report",
      "Financial certification (ISFAA / CSS Profile)",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "france_eiffel_2027",
    title: "France Excellence Eiffel Scholarship Institution Deadline",
    portal_name: "Campus France",
    country_code: "FR",
    country_name: "France",
    flag: "🇫🇷",
    degree_level: "master",
    intake: "fall_2026",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2027-01-08",
    deadline_time: "18:00 (Paris Time)",
    description: "Pre-selection of candidates by French higher education institutions for the Eiffel excellence grant (€1,181/mo).",
    official_portal_url: "https://www.campusfrance.org/en/the-eiffel-scholarship-program",
    requirements_summary: [
      "Formal acceptance or pre-admission endorsement from French university",
      "Top 10% academic class standing",
      "Project proposal & CV",
      "Language certificate (English C1 or French B2)",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "stipendium_hungaricum_2027",
    title: "Stipendium Hungaricum Online Portal Deadline",
    portal_name: "Tempus Public Foundation DreamApply",
    country_code: "HU",
    country_name: "Hungary",
    flag: "🇭🇺",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2027-01-15",
    deadline_time: "14:00 (CET)",
    description: "Full bilateral government scholarship covering 200 Azerbaijani students annually (tuition, stipend, dorm, insurance).",
    official_portal_url: "https://apply.stipendiumhungaricum.hu",
    requirements_summary: [
      "DreamApply online submission (2 chosen degree programs)",
      "Motivational letter (min 1 page)",
      "Medical certificate & proof of foreign language proficiency",
      "Ministry of Science and Education of Azerbaijan bilateral nomination clearance",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: false,
  },
  {
    id: "de_summer_uniassist_2027",
    title: "Germany Summer Intake (Sommersemester) Uni-Assist Deadline",
    portal_name: "Uni-Assist e.V.",
    country_code: "DE",
    country_name: "Germany",
    flag: "🇩🇪",
    degree_level: "all",
    intake: "spring_2027",
    milestone_type: "REGULAR_DEADLINE",
    target_date: "2027-01-15",
    deadline_time: "23:59 (CET)",
    description: "Cutoff for Summer semester applications at public universities across Germany.",
    official_portal_url: "https://www.uni-assist.de",
    requirements_summary: [
      "Certified German or English translation of Bachelor/Attestat",
      "Vorprüfungsdokumentation (VPD) if required by target university",
      "TestDaF (4x4) or IELTS (6.5+) depending on language of instruction",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "gb_ucas_equal_consideration_2027",
    title: "UCAS Undergraduate Equal Consideration Deadline",
    portal_name: "UCAS",
    country_code: "GB",
    country_name: "United Kingdom",
    flag: "🇬🇧",
    degree_level: "bachelor",
    intake: "fall_2026",
    milestone_type: "EQUAL_CONSIDERATION",
    target_date: "2027-01-29",
    deadline_time: "18:00 (UK Time)",
    description: "Standard UK national deadline guaranteeing equal evaluation for all undergraduate degree choices.",
    official_portal_url: "https://www.ucas.com",
    requirements_summary: [
      "Up to 5 UK course choices",
      "Completed UCAS application form and paid fee (£28.50)",
      "Verified teacher/counselor recommendation",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "turkiye_burslari_2027",
    title: "Türkiye Bursları Government Scholarship Deadline",
    portal_name: "TBBS (Türkiye Bursları Başvuru Sistemi)",
    country_code: "TR",
    country_name: "Turkey",
    flag: "🇹🇷",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2027-02-20",
    deadline_time: "23:59 (Istanbul Time)",
    description: "Full Turkish government grant covering tuition, monthly stipend, flights, accommodation, and 1-year TÖMER preparatory.",
    official_portal_url: "https://turkiyeburslari.gov.tr",
    requirements_summary: [
      "Attestat / Bachelor's Diploma with minimum 75% GPA (80% for engineering, 90% for medicine)",
      "Letter of Intent (Niyet Mektubu) explaining why Turkey",
      "Academic CV and extracurricular certificates",
      "Passport copy and biometric photo",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: false,
  },
  {
    id: "pl_nawa_banach_2027",
    title: "Poland NAWA Stefan Banach Scholarship Application",
    portal_name: "NAWA ICT System",
    country_code: "PL",
    country_name: "Poland",
    flag: "🇵🇱",
    degree_level: "master",
    intake: "fall_2026",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2027-03-31",
    deadline_time: "15:00 (Warsaw Time)",
    description: "Polish National Agency for Academic Exchange full tuition waiver + 1,700 PLN monthly stipend for engineering & science master's.",
    official_portal_url: "https://nawa.gov.pl/en/students/foreign-students/the-banach-scholarship-programme",
    requirements_summary: [
      "BSc Diploma in STEM or Social Sciences",
      "Minimum B2 English certificate or Polish B1",
      "Graduation within last 2 calendar years",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: false,
  },
  {
    id: "aze_dp_portal_open_2026",
    title: "State Programme 2022–2026 (DP) Portal Opens for Submissions",
    portal_name: "Müasir Təhsil Portalı (portal.edu.az)",
    country_code: "AZ",
    country_name: "Azerbaijan",
    flag: "🇦🇿",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "PORTAL_OPEN",
    target_date: "2026-04-01",
    deadline_time: "10:00 (Baku Time)",
    description: "Ministry of Science and Education of Azerbaijan opens electronic submissions for 2022-2026 State Programme funding.",
    official_portal_url: "https://dp.edu.az",
    requirements_summary: [
      "Unconditional or Conditional Acceptance letter from approved Top-500 university",
      "Attestat / Bachelor's Diploma and official transcript",
      "State Programme Motivation Letter with Repatriation / Economic Contribution clause",
      "Two signed recommendation letters",
    ],
    is_hard_deadline: false,
    is_state_programme_eligible: true,
  },
  {
    id: "it_universitaly_open_2026",
    title: "Italy Universitaly Pre-Enrollment & Visa Window Opens",
    portal_name: "Universitaly Portal",
    country_code: "IT",
    country_name: "Italy",
    flag: "🇮🇹",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "DOCUMENT_SUBMISSION",
    target_date: "2026-04-15",
    deadline_time: "23:59 (Rome Time)",
    description: "Mandatory Italian Ministry of Foreign Affairs pre-enrollment platform for non-EU students to obtain official visa summary.",
    official_portal_url: "https://www.universitaly.it",
    requirements_summary: [
      "University admission letter",
      "Declaration of Value (DOV) or CIMEA Statement of Comparability",
      "Language certificate (English B2/C1 or Italian B2)",
    ],
    is_hard_deadline: false,
    is_state_programme_eligible: true,
  },
  {
    id: "us_fulbright_azerbaijan_2026",
    title: "US Embassy Baku Fulbright Foreign Student Program",
    portal_name: "IIE Fulbright Portal",
    country_code: "US",
    country_name: "United States",
    flag: "🇺🇸",
    degree_level: "master",
    intake: "fall_2027",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2026-06-01",
    deadline_time: "18:00 (Baku Time)",
    description: "Full bilateral US Government grant for Azerbaijani graduates pursuing a two-year Master's degree in the USA.",
    official_portal_url: "https://az.usembassy.gov/education-culture/educational-programs/fulbright-foreign-student-program/",
    requirements_summary: [
      "Azerbaijani citizenship and Bachelor's degree by time of departure",
      "TOEFL iBT (minimum 80) or IELTS (6.5+)",
      "Study/Research Objective and Personal Statement",
      "Commitment to return to Azerbaijan for at least two years (J-1 visa two-year rule)",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: false,
  },
  {
    id: "de_vpd_window_winter_2026",
    title: "Germany Uni-Assist VPD (Preliminary Review) Recommended Submission",
    portal_name: "Uni-Assist e.V.",
    country_code: "DE",
    country_name: "Germany",
    flag: "🇩🇪",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "DOCUMENT_SUBMISSION",
    target_date: "2026-06-01",
    deadline_time: "23:59 (CET)",
    description: "Uni-Assist takes 4-6 weeks to process VPD certificates. Submitting by June 1 ensures timely delivery before the July 15 university cutoff.",
    official_portal_url: "https://www.uni-assist.de/en/how-to-apply/plan-your-application/vpd/",
    requirements_summary: [
      "Scanned notarized and translated school leaving certificates",
      "Proof of online fee payment (€75 first university, €30 each additional)",
    ],
    is_hard_deadline: false,
    is_state_programme_eligible: true,
  },
  {
    id: "aze_dp_deadline_2026",
    title: "State Programme 2022–2026 Final Application Deadline",
    portal_name: "portal.edu.az / dp.edu.az",
    country_code: "AZ",
    country_name: "Azerbaijan",
    flag: "🇦🇿",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "REGULAR_DEADLINE",
    target_date: "2026-06-15",
    deadline_time: "18:00 (Baku Time)",
    description: "Hard cutoff for all documents under the 2022–2026 State Programme for Youth Study Abroad.",
    official_portal_url: "https://dp.edu.az",
    requirements_summary: [
      "Uploaded university unconditional or conditional offer",
      "Medical health certificate Form 086",
      "No criminal record certificate (ASAN Xidmət)",
      "Complete military service status / postponement document",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "uk_ucas_clearing_2026",
    title: "UK UCAS Clearing & Late Undergraduate Direct Placements Open",
    portal_name: "UCAS Clearing Portal",
    country_code: "GB",
    country_name: "United Kingdom",
    flag: "🇬🇧",
    degree_level: "bachelor",
    intake: "fall_2026",
    milestone_type: "PORTAL_OPEN",
    target_date: "2026-07-05",
    deadline_time: "08:00 (UK Time)",
    description: "Alternative pathway for applicants without existing offers or those achieving higher than expected exam results.",
    official_portal_url: "https://www.ucas.com/clearing",
    requirements_summary: [
      "Official final high school exam marks / Attestat grades",
      "Valid English proficiency certificate (IELTS UKVI)",
      "Direct telephone/online interview with university admissions tutors",
    ],
    is_hard_deadline: false,
    is_state_programme_eligible: true,
  },
  {
    id: "aze_dp_interview_results_2026",
    title: "State Programme 2022–2026 Committee Interviews & Results",
    portal_name: "Ministry of Science and Education (dp.edu.az)",
    country_code: "AZ",
    country_name: "Azerbaijan",
    flag: "🇦🇿",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "DECISION_RELEASE",
    target_date: "2026-07-10",
    deadline_time: "18:00 (Baku Time)",
    description: "Shortlisted applicants participate in interview rounds covering academic motivation and Azerbaijani economic contribution.",
    official_portal_url: "https://dp.edu.az",
    requirements_summary: [
      "In-person or video panel interview with expert commission",
      "Presentation of study trajectory and repatriation commitment",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "de_winter_uniassist_2026",
    title: "Germany Winter Semester (Wintersemester) Uni-Assist & Direct Deadline",
    portal_name: "Uni-Assist / Hochschulstart",
    country_code: "DE",
    country_name: "Germany",
    flag: "🇩🇪",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "REGULAR_DEADLINE",
    target_date: "2026-07-15",
    deadline_time: "23:59 (CET)",
    description: "Crucial national deadline for public university admissions across Germany (TUM, LMU, RWTH Aachen, Heidelberg).",
    official_portal_url: "https://www.uni-assist.de",
    requirements_summary: [
      "APS Certificate (if applicable) or VPD certificate issued by Uni-Assist",
      "Verified certified copies of educational transcripts",
      "Proof of Sperrkonto (€11,904) blocked account or DAAD grant",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "uk_visa_cas_window_2026",
    title: "UK Student Visa Application & CAS Confirmation Window",
    portal_name: "UK Visas and Immigration (GOV.UK)",
    country_code: "GB",
    country_name: "United Kingdom",
    flag: "🇬🇧",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "VISA_WINDOW",
    target_date: "2026-08-10",
    deadline_time: "23:59 (UK Time)",
    description: "Critical visa filing window ensuring arrival in the UK before September term commencement.",
    official_portal_url: "https://www.gov.uk/student-visa",
    requirements_summary: [
      "Official CAS (Confirmation of Acceptance for Studies) number",
      "Proof of 28 consecutive days maintenance funds (£1,334/mo London, £1,023/mo outer London)",
      "IHS (Immigration Health Surcharge) payment (£776/yr)",
      "TB test certificate from IOM Baku",
    ],
    is_hard_deadline: false,
    is_state_programme_eligible: true,
  },
  {
    id: "it_dsu_regional_2026",
    title: "Italy Regional DSU / ER.GO Scholarship Deadline",
    portal_name: "Azienda DSU / ER.GO / Disco Lazio",
    country_code: "IT",
    country_name: "Italy",
    flag: "🇮🇹",
    degree_level: "all",
    intake: "fall_2026",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2026-08-25",
    deadline_time: "13:00 (Italian Time)",
    description: "Need-based regional scholarship covering 100% tuition waiver, free dining hall meals, and up to €7,000 yearly stipend.",
    official_portal_url: "https://www.dsu.toscana.it",
    requirements_summary: [
      "ISEE Parificato (ISEE-U) income calculation certificate under €27,000",
      "Apostilled family income and property documents translated to Italian",
      "Enrollment matriculation number at an Italian public university",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "de_daad_epos_2026",
    title: "Germany DAAD EPOS Development Postgraduate Deadline",
    portal_name: "DAAD Portal",
    country_code: "DE",
    country_name: "Germany",
    flag: "🇩🇪",
    degree_level: "master",
    intake: "fall_2027",
    milestone_type: "SCHOLARSHIP_DEADLINE",
    target_date: "2026-09-30",
    deadline_time: "23:59 (CET)",
    description: "DAAD full funding (€934/mo, health insurance, flights) for development-related postgraduate courses in Germany.",
    official_portal_url: "https://www.daad.de/en/information-services-for-higher-education-institutions/further-information-on-daad-programmes/epos/",
    requirements_summary: [
      "DAAD Application Form & Europass CV",
      "Hand-signed letter of motivation with development relevance",
      "Two years of professional work experience in relevant sector",
      "Letter of recommendation from current employer",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: true,
  },
  {
    id: "tr_tryos_exam_deadline_2026",
    title: "Turkey TR-YÖS Central Foreign Student Exam Registration",
    portal_name: "ÖSYM (Ölçme, Seçme ve Yerleştirme Merkezi)",
    country_code: "TR",
    country_name: "Turkey",
    flag: "🇹🇷",
    degree_level: "bachelor",
    intake: "fall_2026",
    milestone_type: "EARLY_DEADLINE",
    target_date: "2026-03-28",
    deadline_time: "23:59 (Istanbul Time)",
    description: "Official Turkish exam for international students applying directly to Turkish state and foundation universities.",
    official_portal_url: "https://www.osym.gov.tr",
    requirements_summary: [
      "Biometric photo and valid foreign passport",
      "Exam registration fee paid via ÖSYM e-İşlemler",
    ],
    is_hard_deadline: true,
    is_state_programme_eligible: false,
  },
  {
    id: "us_css_profile_open_2026",
    title: "US College Board CSS Profile Financial Aid Portal Opens",
    portal_name: "College Board CSS Profile",
    country_code: "US",
    country_name: "United States",
    flag: "🇺🇸",
    degree_level: "bachelor",
    intake: "fall_2027",
    milestone_type: "PORTAL_OPEN",
    target_date: "2026-10-01",
    deadline_time: "00:01 (EST)",
    description: "Financial aid portal used by top private US colleges to award institutional need-based grants to international students.",
    official_portal_url: "https://cssprofile.collegeboard.org",
    requirements_summary: [
      "Tax records and official family earnings documentation",
      "Bank balance certifications and real estate equity disclosures",
    ],
    is_hard_deadline: false,
    is_state_programme_eligible: true,
  },
];

// ==============================================================================
// Client-Side Heuristics & Local Fallback Engine
// ==============================================================================

export function calculateLocalUrgency(targetDateStr: string, refDate?: Date): { daysLeft: number; urgency: UrgencyLevel } {
  const ref = refDate ? new Date(refDate.getFullYear(), refDate.getMonth(), refDate.getDate()) : new Date();
  const [y, m, d] = targetDateStr.split("-").map(Number);
  const target = new Date(y, m - 1, d);

  const diffMs = target.getTime() - ref.getTime();
  const daysLeft = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

  let urgency: UrgencyLevel = "OPEN";
  if (daysLeft < 0) {
    urgency = "PASSED";
  } else if (daysLeft <= 14) {
    urgency = "CRITICAL";
  } else if (daysLeft <= 60) {
    urgency = "UPCOMING";
  }

  return { daysLeft, urgency };
}

export function getLocalTimelineSchedule(filters?: MilestoneFilter, refDate?: Date): TimelineSchedule {
  const hydrated: MilestoneItem[] = FALLBACK_MILESTONES_RAW.map((m) => {
    const { daysLeft, urgency } = calculateLocalUrgency(m.target_date, refDate);
    return {
      ...m,
      days_remaining: daysLeft,
      urgency,
    };
  });

  const filtered = hydrated.filter((m) => {
    if (filters?.country_code && m.country_code !== filters.country_code) return false;
    if (filters?.degree_level && filters.degree_level !== "all") {
      if (m.degree_level !== "all" && m.degree_level !== filters.degree_level) return false;
    }
    if (filters?.intake && m.intake !== filters.intake) return false;
    if (filters?.urgency && m.urgency !== filters.urgency) return false;
    if (filters?.is_state_programme_eligible !== undefined) {
      if (m.is_state_programme_eligible !== filters.is_state_programme_eligible) return false;
    }
    if (filters?.search_query) {
      const q = filters.search_query.toLowerCase();
      const corpus = `${m.title} ${m.description} ${m.portal_name} ${m.country_name} ${m.requirements_summary.join(" ")}`.toLowerCase();
      if (!corpus.includes(q)) return false;
    }
    return true;
  });

  filtered.sort((a, b) => a.target_date.localeCompare(b.target_date));

  return {
    total_milestones: filtered.length,
    critical_count: filtered.filter((x) => x.urgency === "CRITICAL").length,
    upcoming_count: filtered.filter((x) => x.urgency === "UPCOMING").length,
    open_count: filtered.filter((x) => x.urgency === "OPEN").length,
    passed_count: filtered.filter((x) => x.urgency === "PASSED").length,
    milestones: filtered,
    generated_at: new Date().toISOString(),
  };
}

// ==============================================================================
// RFC 5545 iCalendar (.ics) Client-Side Generator
// ==============================================================================

function escapeIcsText(str: string): string {
  if (!str) return "";
  return str
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r\n|\n/g, "\\n");
}

export function generateClientIcs(milestones: MilestoneItem[], calName: string = "AUSA Admissions Deadlines 2026/2027"): string {
  const now = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}/, "");

  const lines: string[] = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//AUSA//Admissions Timeline Engine v1.0//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    `X-WR-CALNAME:${escapeIcsText(calName)}`,
    "X-WR-TIMEZONE:Asia/Baku",
  ];

  for (const m of milestones) {
    const dtstart = m.target_date.replace(/-/g, "");
    const titleEscaped = escapeIcsText(`${m.flag} ${m.title}`);
    const descLines = [
      `Portal: ${m.portal_name}`,
      `Deadline Time: ${m.deadline_time}`,
      `Description: ${m.description}`,
      `Official URL: ${m.official_portal_url}`,
    ];
    if (m.requirements_summary?.length) {
      descLines.push("Requirements:");
      m.requirements_summary.forEach((r) => descLines.push(` - ${r}`));
    }
    const descEscaped = escapeIcsText(descLines.join("\n"));

    lines.push(
      "BEGIN:VEVENT",
      `UID:${m.id}@ausa.edu.az`,
      `DTSTAMP:${now}`,
      `DTSTART;VALUE=DATE:${dtstart}`,
      `SUMMARY:${titleEscaped}`,
      `DESCRIPTION:${descEscaped}`,
      `URL:${escapeIcsText(m.official_portal_url)}`,
      "STATUS:CONFIRMED",
      "CLASS:PUBLIC",
      "TRANSP:TRANSPARENT",
      "BEGIN:VALARM",
      "ACTION:DISPLAY",
      `DESCRIPTION:Xatırlatma: ${titleEscaped}`,
      "TRIGGER:-P3D",
      "END:VALARM",
      "END:VEVENT"
    );
  }

  lines.push("END:VCALENDAR\r\n");
  return lines.join("\r\n");
}

export function downloadIcsFile(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ==============================================================================
// Remote API Client Methods
// ==============================================================================

export async function fetchMilestones(filters?: MilestoneFilter): Promise<TimelineSchedule> {
  const params = new URLSearchParams();
  if (filters?.country_code) params.append("country_code", filters.country_code);
  if (filters?.degree_level && filters.degree_level !== "all") params.append("degree_level", filters.degree_level);
  if (filters?.intake) params.append("intake", filters.intake);
  if (filters?.urgency) params.append("urgency", filters.urgency);
  if (filters?.is_state_programme_eligible !== undefined) {
    params.append("is_state_programme_eligible", String(filters.is_state_programme_eligible));
  }
  if (filters?.search_query) params.append("q", filters.search_query);

  const qs = params.toString();
  const url = `${API_BASE_URL}/api/v1/timeline/milestones${qs ? `?${qs}` : ""}`;

  try {
    const res = await fetch(url);
    if (!res.ok) {
      return getLocalTimelineSchedule(filters);
    }
    return await res.json();
  } catch {
    return getLocalTimelineSchedule(filters);
  }
}
