/**
 * Application Tracker, Document Checklist & University Comparison Client API.
 * 
 * Provides:
 * - TypeScript interfaces for student application items, stages, tiers, and comparison matrices.
 * - Offline-first LocalStorage persistence for saving, editing, and checking off documents.
 * - Dynamic document checklist generator matching country requirements.
 * - Multi-university comparison engine for up to 5 universities.
 */

export type ApplicationStage =
  | "shortlisted"
  | "document_gathering"
  | "submitted"
  | "under_review"
  | "interview_scheduled"
  | "offer_received"
  | "offer_accepted"
  | "rejected"
  | "visa_processing";

export type AdmissionTier = "DREAM" | "TARGET" | "SAFETY";

export type DocumentCategory =
  | "ACADEMIC"
  | "LANGUAGE"
  | "FINANCIAL"
  | "LEGAL_IMMIGRATION"
  | "APPLICATION_ASSETS";

export interface DocumentItem {
  id: string;
  title: string;
  category: DocumentCategory;
  description: string;
  is_mandatory: boolean;
  issuing_authority: string;
  translation_required: boolean;
  apostille_required: boolean;
  estimated_processing_days: number;
  notes?: string;
}

export interface DocumentChecklistRequest {
  country_code: string;
  degree_level?: string;
  is_state_programme?: boolean;
  has_scholarship?: boolean;
}

export interface DocumentChecklistResult {
  country_code: string;
  country_name: string;
  degree_level: string;
  total_documents: number;
  mandatory_count: number;
  documents: DocumentItem[];
  country_specific_notes: string[];
}

export interface UniversityComparisonItem {
  id: string;
  university_name: string;
  country_code: string;
  country_name: string;
  flag: string;
  city: string;
  qs_rank?: number | null;
  program_name: string;
  degree_level: string;
  tuition_eur_annual: number;
  living_cost_eur_monthly: number;
  blocked_account_required_eur: number;
  total_first_year_eur: number;
  original_tuition: string;
  ielts_min: number;
  toefl_min: number;
  post_study_work_visa_duration_months: number;
  post_study_work_visa_name: string;
  post_study_work_visa_summary: string;
  state_programme_eligible: boolean;
  admission_tier: AdmissionTier;
  tier_rationale: string;
}

export interface ComparisonRequest {
  university_ids: string[];
  student_gpa?: number;
  student_ielts?: number;
  student_budget_eur_annual?: number;
}

export interface ComparisonResult {
  items: UniversityComparisonItem[];
  lowest_cost_university: string;
  longest_pswr_university: string;
  best_ranked_university?: string | null;
  average_first_year_cost_eur: number;
  comparison_summary_notes: string[];
}

export interface StudentApplicationItem {
  id: string;
  university_name: string;
  program_name: string;
  country_code: string;
  country_name: string;
  flag: string;
  city: string;
  degree_level: string;
  stage: ApplicationStage;
  tier: AdmissionTier;
  deadline?: string;
  tuition_eur_annual: number;
  living_cost_eur_monthly: number;
  completed_doc_ids: string[];
  notes?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";
const STORAGE_KEY = "ausa_saved_applications_v1";

// ==============================================================================
// Curated Benchmark University Database
// ==============================================================================

export const CURATED_BENCHMARKS: Record<string, UniversityComparisonItem> = {
  tum_cs: {
    id: "tum_cs",
    university_name: "Technical University of Munich (TUM)",
    country_code: "DE",
    country_name: "Almaniya",
    flag: "🇩🇪",
    city: "Münxen",
    qs_rank: 28,
    program_name: "MSc Informatics (Computer Science)",
    degree_level: "master",
    tuition_eur_annual: 12000.0,
    living_cost_eur_monthly: 1250.0,
    blocked_account_required_eur: 11904.0,
    total_first_year_eur: 27000.0,
    original_tuition: "€6,000 / semester (Non-EU)",
    ielts_min: 6.5,
    toefl_min: 88,
    post_study_work_visa_duration_months: 18,
    post_study_work_visa_name: "Almaniya Məzun İş Axtarma İcazəsi (§ 20 AufenthG)",
    post_study_work_visa_summary: "Məzuniyyətdən sonra 18 aylıq açıq iş vizası və 21-27 ay sonra EU Blue Card / daimi oturum hüququ.",
    state_programme_eligible: true,
    admission_tier: "DREAM",
    tier_rationale: "QS #28 pilləsindədir və Almaniyanın ən rəqabətli texnologiya fakültəsidir.",
  },
  oxford_cs: {
    id: "oxford_cs",
    university_name: "University of Oxford",
    country_code: "GB",
    country_name: "Böyük Britaniya",
    flag: "🇬🇧",
    city: "Oksford",
    qs_rank: 3,
    program_name: "MSc in Advanced Computer Science",
    degree_level: "master",
    tuition_eur_annual: 43500.0,
    living_cost_eur_monthly: 1500.0,
    blocked_account_required_eur: 12000.0,
    total_first_year_eur: 61500.0,
    original_tuition: "£37,500 / year",
    ielts_min: 7.5,
    toefl_min: 110,
    post_study_work_visa_duration_months: 24,
    post_study_work_visa_name: "UK Graduate Route Visa",
    post_study_work_visa_summary: "Böyük Britaniyada 2 illik sərbəst işləmək icazəsi və Skilled Worker vizasına birbaşa keçid.",
    state_programme_eligible: true,
    admission_tier: "DREAM",
    tier_rationale: "Dünya #3-cüsü; qəbul dərəcəsi 8-12% aralığındadır.",
  },
  rwth_engineering: {
    id: "rwth_engineering",
    university_name: "RWTH Aachen University",
    country_code: "DE",
    country_name: "Almaniya",
    flag: "🇩🇪",
    city: "Aaxen",
    qs_rank: 99,
    program_name: "MSc Mechanical Engineering",
    degree_level: "master",
    tuition_eur_annual: 0.0,
    living_cost_eur_monthly: 950.0,
    blocked_account_required_eur: 11904.0,
    total_first_year_eur: 11400.0,
    original_tuition: "€0 / il (Yalnız €320 semestr bilet rüsumu)",
    ielts_min: 6.5,
    toefl_min: 90,
    post_study_work_visa_duration_months: 18,
    post_study_work_visa_name: "Almaniya Məzun İş Axtarma İcazəsi",
    post_study_work_visa_summary: "18 aylıq Almaniya iş axtarışı vizası və sənaye klasterlərinə birbaşa çıxış.",
    state_programme_eligible: true,
    admission_tier: "TARGET",
    tier_rationale: "Profil göstəriciləri (GPA 3.4+) ilə güclü uyğunlaşma.",
  },
  polimi_cs: {
    id: "polimi_cs",
    university_name: "Politecnico di Milano",
    country_code: "IT",
    country_name: "İtaliya",
    flag: "🇮🇹",
    city: "Milan",
    qs_rank: 111,
    program_name: "MSc Computer Science and Engineering",
    degree_level: "master",
    tuition_eur_annual: 3900.0,
    living_cost_eur_monthly: 1050.0,
    blocked_account_required_eur: 6000.0,
    total_first_year_eur: 16500.0,
    original_tuition: "€3,900 / il (DSU ilə €160-a enir)",
    ielts_min: 6.0,
    toefl_min: 78,
    post_study_work_visa_duration_months: 12,
    post_study_work_visa_name: "Permesso di Soggiorno per Ricerca Lavoro",
    post_study_work_visa_summary: "12 aylıq məzun iş axtarış icazəsi və İtaliya əmək müqaviləsi ilə çevrilmə.",
    state_programme_eligible: true,
    admission_tier: "TARGET",
    tier_rationale: "DSU təqaüdü ilə tam pulsuz təhsil və €7,000 illik stipendiya imkanı.",
  },
  itu_engineering: {
    id: "itu_engineering",
    university_name: "Istanbul Technical University (İTÜ)",
    country_code: "TR",
    country_name: "Türkiyə",
    flag: "🇹🇷",
    city: "İstanbul",
    qs_rank: 404,
    program_name: "BSc Computer Engineering (English)",
    degree_level: "bachelor",
    tuition_eur_annual: 1800.0,
    living_cost_eur_monthly: 650.0,
    blocked_account_required_eur: 3000.0,
    total_first_year_eur: 9600.0,
    original_tuition: "₺65,000 / il",
    ielts_min: 6.5,
    toefl_min: 79,
    post_study_work_visa_duration_months: 12,
    post_study_work_visa_name: "Türkiyə Qısamüddətli İkamət İzni",
    post_study_work_visa_summary: "12 aylıq məzuniyyət sonrası texnopark və müdafiə sənayesi şirkətlərində iş imkanı.",
    state_programme_eligible: false,
    admission_tier: "SAFETY",
    tier_rationale: "GPA və SAT nəticələri ilə təminatlı və münasib seçim.",
  },
  bhos_chemical: {
    id: "bhos_chemical",
    university_name: "Baku Higher Oil School (BANM)",
    country_code: "AZ",
    country_name: "Azərbaycan",
    flag: "🇦🇿",
    city: "Bakı",
    qs_rank: null,
    program_name: "BSc Chemical Engineering (Heriot-Watt Dual)",
    degree_level: "bachelor",
    tuition_eur_annual: 0.0,
    living_cost_eur_monthly: 450.0,
    blocked_account_required_eur: 0.0,
    total_first_year_eur: 5400.0,
    original_tuition: "0 AZN (650+ DİM balı ilə 100% təqaüd)",
    ielts_min: 6.0,
    toefl_min: 75,
    post_study_work_visa_duration_months: 0,
    post_study_work_visa_name: "Yerli Sənaye Karyerası",
    post_study_work_visa_summary: "SOCAR, bp və beynəlxalq neft-qaz layihələrində birbaşa iş təminatı.",
    state_programme_eligible: false,
    admission_tier: "SAFETY",
    tier_rationale: "650+ DİM balı ilə 100% dövlət sifarişi və Heriot-Watt ikili diplomu.",
  },
  cmu_software: {
    id: "cmu_software",
    university_name: "Carnegie Mellon University",
    country_code: "US",
    country_name: "Amerika Birləşmiş Ştatları",
    flag: "🇺🇸",
    city: "Pittsburgh, PA",
    qs_rank: 52,
    program_name: "Master of Software Engineering",
    degree_level: "master",
    tuition_eur_annual: 55000.0,
    living_cost_eur_monthly: 1600.0,
    blocked_account_required_eur: 25000.0,
    total_first_year_eur: 74200.0,
    original_tuition: "$58,500 / year",
    ielts_min: 7.5,
    toefl_min: 102,
    post_study_work_visa_duration_months: 36,
    post_study_work_visa_name: "US F-1 STEM OPT (3 İl)",
    post_study_work_visa_summary: "12 ay standart OPT + 24 ay STEM uzadılması ilə ABŞ-da 3 illik tam iş icazəsi və H-1B müraciəti.",
    state_programme_eligible: true,
    admission_tier: "DREAM",
    tier_rationale: "Proqram təminatı mühəndisliyi üzrə dünya 1-cisi; yüksək rəqabətli qəbul.",
  },
};

// ==============================================================================
// Default Seed Applications (When Storage is Empty)
// ==============================================================================

export const DEFAULT_APPLICATIONS: StudentApplicationItem[] = [
  {
    id: "app_tum_cs",
    university_name: "Technical University of Munich (TUM)",
    program_name: "MSc Informatics (Computer Science)",
    country_code: "DE",
    country_name: "Almaniya",
    flag: "🇩🇪",
    city: "Münxen",
    degree_level: "master",
    stage: "document_gathering",
    tier: "DREAM",
    deadline: "2026-07-15",
    tuition_eur_annual: 12000.0,
    living_cost_eur_monthly: 1250.0,
    completed_doc_ids: ["doc_diploma_transcript", "doc_passport", "doc_cv"],
    notes: "Uni-Assist VPD sənədi üçün müraciət iyun ayında edilməlidir.",
  },
  {
    id: "app_polimi_cs",
    university_name: "Politecnico di Milano",
    program_name: "MSc Computer Science and Engineering",
    country_code: "IT",
    country_name: "İtaliya",
    flag: "🇮🇹",
    city: "Milan",
    degree_level: "master",
    stage: "shortlisted",
    tier: "TARGET",
    deadline: "2026-08-25",
    tuition_eur_annual: 3900.0,
    living_cost_eur_monthly: 1050.0,
    completed_doc_ids: ["doc_passport", "doc_cv"],
    notes: "DSU regional təqaüdü üçün ISEE Parificato sənədləri toplanır.",
  },
  {
    id: "app_itu_engineering",
    university_name: "Istanbul Technical University (İTÜ)",
    program_name: "BSc Computer Engineering",
    country_code: "TR",
    country_name: "Türkiyə",
    flag: "🇹🇷",
    city: "İstanbul",
    degree_level: "bachelor",
    stage: "submitted",
    tier: "SAFETY",
    deadline: "2026-06-30",
    tuition_eur_annual: 1800.0,
    living_cost_eur_monthly: 650.0,
    completed_doc_ids: ["doc_diploma_transcript", "doc_passport", "doc_cv", "doc_language_cert", "doc_recommendation_letters"],
    notes: "Denklik belgesi Bakı Türkiyə Səfirliyindən təsdiqlənib.",
  },
];

// ==============================================================================
// Local Storage Persistence Manager
// ==============================================================================

export function loadSavedApplications(): StudentApplicationItem[] {
  if (typeof window === "undefined") return DEFAULT_APPLICATIONS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_APPLICATIONS));
      return DEFAULT_APPLICATIONS;
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : DEFAULT_APPLICATIONS;
  } catch {
    return DEFAULT_APPLICATIONS;
  }
}

export function saveApplicationsToStorage(apps: StudentApplicationItem[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(apps));
  } catch (err) {
    console.error("Failed to save applications to storage:", err);
  }
}

// ==============================================================================
// Local Fallback Heuristics
// ==============================================================================

export function getLocalComparison(req: ComparisonRequest): ComparisonResult {
  const items: UniversityComparisonItem[] = [];
  const ids = req.university_ids.length > 0 ? req.university_ids : ["tum_cs", "oxford_cs", "rwth_engineering"];

  for (const uid of ids) {
    const b = CURATED_BENCHMARKS[uid];
    if (b) {
      items.push({ ...b });
    }
  }

  if (items.length === 0) {
    items.push(CURATED_BENCHMARKS.tum_cs, CURATED_BENCHMARKS.rwth_engineering, CURATED_BENCHMARKS.polimi_cs);
  }

  const sortedByCost = [...items].sort((a, b) => a.total_first_year_eur - b.total_first_year_eur);
  const lowestCost = sortedByCost[0].university_name;

  const sortedByVisa = [...items].sort((a, b) => b.post_study_work_visa_duration_months - a.post_study_work_visa_duration_months);
  const longestVisa = `${sortedByVisa[0].university_name} (${sortedByVisa[0].post_study_work_visa_duration_months} ay)`;

  const rankedItems = items.filter((x) => x.qs_rank != null);
  const bestRanked = rankedItems.length > 0 ? [...rankedItems].sort((a, b) => (a.qs_rank || 999) - (b.qs_rank || 999))[0].university_name : null;

  const avgCost = items.reduce((acc, x) => acc + x.total_first_year_eur, 0) / items.length;

  return {
    items,
    lowest_cost_university: lowestCost,
    longest_pswr_university: longestVisa,
    best_ranked_university: bestRanked,
    average_first_year_cost_eur: Math.round(avgCost),
    comparison_summary_notes: [
      `Ən sərfəli proqram: ${lowestCost} (ilk il təxmini: €${sortedByCost[0].total_first_year_eur.toLocaleString()}).`,
      `Ən uzun məzuniyyət iş vizası: ${longestVisa}.`,
      `Müqayisə edilən universitetlər üzrə orta illik xərc: €${Math.round(avgCost).toLocaleString()}.`,
    ],
  };
}

export function getLocalDocumentChecklist(req: DocumentChecklistRequest): DocumentChecklistResult {
  const country = (req.country_code || "DE").toUpperCase();

  const docs: DocumentItem[] = [
    {
      id: "doc_diploma_transcript",
      title: "Diplom və Akademik Transkript (Attestat / Bakalavr)",
      category: "ACADEMIC",
      description: "Bakalavr diplomu və əlavəsi və ya attestat. Cari tələbələr üçün rəsmi arayış və transkript.",
      is_mandatory: true,
      issuing_authority: "Universitet / Məktəb",
      translation_required: true,
      apostille_required: true,
      estimated_processing_days: 5,
    },
    {
      id: "doc_recommendation_letters",
      title: "2 Ədəd Akademik Tövsiyə Məktubu (LoR)",
      category: "APPLICATION_ASSETS",
      description: "Fənn müəllimləri və ya kafedra rəhbəri tərəfindən imzalanmış tövsiyə məktubları.",
      is_mandatory: true,
      issuing_authority: "Müəllimlər / Kafedra",
      translation_required: false,
      apostille_required: false,
      estimated_processing_days: 7,
    },
    {
      id: "doc_sop",
      title: "Statement of Purpose / Motivasiya Məktubu",
      category: "APPLICATION_ASSETS",
      description: "Akademik motivasiya və hədəfləri əks etdirən 500-1000 sözlük inşa.",
      is_mandatory: true,
      issuing_authority: "Müraciətçi",
      translation_required: false,
      apostille_required: false,
      estimated_processing_days: 3,
    },
    {
      id: "doc_cv",
      title: "Akademik CV / Resume",
      category: "APPLICATION_ASSETS",
      description: "Beynəlxalq standartlara uyğun akademik və iş təcrübəsi xülasəsi.",
      is_mandatory: true,
      issuing_authority: "Müraciətçi",
      translation_required: false,
      apostille_required: false,
      estimated_processing_days: 2,
    },
    {
      id: "doc_language_cert",
      title: "Beynəlxalq Dil Sertifikatı (IELTS / TOEFL)",
      category: "LANGUAGE",
      description: "Minimum IELTS 6.5 və ya TOEFL 80 nəticəsi.",
      is_mandatory: true,
      issuing_authority: "British Council / ETS",
      translation_required: false,
      apostille_required: false,
      estimated_processing_days: 14,
    },
    {
      id: "doc_passport",
      title: "Xarici Pasport",
      category: "LEGAL_IMMIGRATION",
      description: "Etibarlılıq müddəti ən azı 6 ay olan xarici pasport.",
      is_mandatory: true,
      issuing_authority: "ASAN Xidmət",
      translation_required: false,
      apostille_required: false,
      estimated_processing_days: 10,
    },
  ];

  if (country === "DE") {
    docs.push(
      {
        id: "doc_de_vpd",
        title: "Uni-Assist Vorprüfungsdokumentation (VPD)",
        category: "ACADEMIC",
        description: "Diplomun alman təhsil sisteminə ekvivalentlik rəsmi sertifikatı.",
        is_mandatory: true,
        issuing_authority: "Uni-Assist e.V.",
        translation_required: true,
        apostille_required: true,
        estimated_processing_days: 35,
      },
      {
        id: "doc_de_sperrkonto",
        title: "Sperrkonto (Almaniya Bloklanmış Bank Hesabı €11,904)",
        category: "FINANCIAL",
        description: "Tələbə vizası üçün illik €11,904 məbləğində bloklanmış bank hesabı.",
        is_mandatory: true,
        issuing_authority: "Fintiba / Expatrio / Coracle",
        translation_required: false,
        apostille_required: false,
        estimated_processing_days: 5,
      }
    );
  } else if (country === "GB") {
    docs.push(
      {
        id: "doc_gb_cas",
        title: "CAS (Confirmation of Acceptance for Studies)",
        category: "ACADEMIC",
        description: "UK universitetinin təqdim etdiyi rəsmi viza sponsorluq nömrəsi.",
        is_mandatory: true,
        issuing_authority: "UK Universiteti",
        translation_required: false,
        apostille_required: false,
        estimated_processing_days: 10,
      },
      {
        id: "doc_gb_maintenance_funds",
        title: "28 Günlük Bank Çıxarışı (UK Maintenance Proof)",
        category: "FINANCIAL",
        description: "Təhsil haqqı qalığı + 9 aylıq yaşayış xərclərinin hesabda 28 gün fasiləsiz qalması.",
        is_mandatory: true,
        issuing_authority: "Kommersiya Bankı",
        translation_required: true,
        apostille_required: false,
        estimated_processing_days: 28,
      }
    );
  } else if (country === "IT") {
    docs.push(
      {
        id: "doc_it_dov_cimea",
        title: "Declaration of Value (DOV) və ya CIMEA Sertifikatı",
        category: "ACADEMIC",
        description: "Diplomun İtaliya təhsilinə uyğunluq bəyannaməsi.",
        is_mandatory: true,
        issuing_authority: "İtaliya Səfirliyi / CIMEA",
        translation_required: true,
        apostille_required: true,
        estimated_processing_days: 30,
      },
      {
        id: "doc_it_isee_parificato",
        title: "ISEE Parificato (Ailə Gəlir Hesabatı)",
        category: "FINANCIAL",
        description: "DSU təqaüdü və universitet təhsil haqqı güzəşti üçün tələb olunan hesabat.",
        is_mandatory: true,
        issuing_authority: "İtaliya CAF Mərkəzi",
        translation_required: true,
        apostille_required: true,
        estimated_processing_days: 20,
      }
    );
  }

  if (req.is_state_programme) {
    docs.push(
      {
        id: "doc_sp_acceptance",
        title: "Dövlət Proqramı Təsdiq Edilmiş Universitetdən Qəbul",
        category: "ACADEMIC",
        description: "Top-500 xarici ali məktəbdən rəsmi qəbul məktubu.",
        is_mandatory: true,
        issuing_authority: "Xarici Universitet",
        translation_required: true,
        apostille_required: false,
        estimated_processing_days: 1,
      },
      {
        id: "doc_sp_motivation",
        title: "Dövlət Proqramı Esse (Azərbaycana Töhfə Maddəsi)",
        category: "APPLICATION_ASSETS",
        description: "Məzuniyyətdən sonra Azərbaycana qayıdış və töhfə planı.",
        is_mandatory: true,
        issuing_authority: "Müraciətçi",
        translation_required: false,
        apostille_required: false,
        estimated_processing_days: 3,
      }
    );
  }

  return {
    country_code: country,
    country_name: country === "DE" ? "Almaniya" : country === "GB" ? "Böyük Britaniya" : country === "IT" ? "İtaliya" : country,
    degree_level: req.degree_level || "master",
    total_documents: docs.length,
    mandatory_count: docs.filter((x) => x.is_mandatory).length,
    documents: docs,
    country_specific_notes: [
      `${country} üzrə təhsil və viza tələbləri yoxlanılmışdır.`,
    ],
  };
}

// ==============================================================================
// Remote API Client Methods
// ==============================================================================

export async function fetchComparison(req: ComparisonRequest): Promise<ComparisonResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/applications/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) return getLocalComparison(req);
    return await res.json();
  } catch {
    return getLocalComparison(req);
  }
}

export async function fetchChecklist(req: DocumentChecklistRequest): Promise<DocumentChecklistResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/applications/checklist`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok) return getLocalDocumentChecklist(req);
    return await res.json();
  } catch {
    return getLocalDocumentChecklist(req);
  }
}
