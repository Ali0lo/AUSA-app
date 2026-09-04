export type DegreeLevel = "bachelor" | "master" | "phd";

export type FeatureState = "available" | "demo" | "experimental" | "unavailable" | "offline";

export interface StudentProfile {
  gpa: number;
  budget: number;
  ielts?: number;
  toefl?: number;
  degree_level: DegreeLevel;
  field_of_study?: string;
  preferred_countries?: string[];
  research_experience?: boolean;
}

export interface StudentAccountProfile extends StudentProfile {
  id: number;
  email: string;
  country?: string;
}

export interface ProgramRequirements {
  program_id?: number;
  university_name: string;
  program_name: string;
  degree_level: DegreeLevel;
  field?: string;
  country?: string;
  min_gpa?: number;
  tuition_fee: number;
  currency: string;
  min_ielts?: number;
  min_toefl?: number;
}

export interface FactorScoreDetail {
  score: number;
  weight: number;
  weighted_score: number;
  passed_hard_filter: boolean;
  explanation: string;
}

export interface MatchBreakdown {
  degree_level: FactorScoreDetail;
  academic: FactorScoreDetail;
  budget: FactorScoreDetail;
  language: FactorScoreDetail;
}

export interface MatchResult {
  program_name: string;
  university_name: string;
  overall_match_percentage: number;
  is_eligible: boolean;
  ineligibility_reasons: string[];
  breakdown: MatchBreakdown;
  original_tuition?: number;
  scholarship_applied?: boolean;
  scholarship_name?: string | null;
  scholarship_amount?: number;
  net_cost?: number;
  admission_probability?: number | null;
  admission_prediction_rationale?: string | null;
}

export interface DocumentSourceInfo {
  content_snippet: string;
  source_url?: string | null;
  page?: number | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: DocumentSourceInfo[];
  application_stage?: string;
  missing_documents?: string[];
  attachment_name?: string;
}

export interface AgentStateData {
  student_id: string;
  target_program_id?: string;
  application_stage: string;
  missing_documents: string[];
  drafted_motivation_letter?: string;
  student_profile?: Partial<StudentProfile>;
}

export interface ChatMessageResponse {
  reply: string;
  sources?: DocumentSourceInfo[];
  applicationStage?: string;
  missingDocs?: string[];
  draftedLetter?: string;
  updatedProfile?: Partial<StudentProfile>;
}

export interface FlaggedProgram {
  id: number;
  university_name: string;
  program_name: string;
  degree_level?: string;
  field?: string;
  country?: string;
  min_gpa?: number;
  min_ielts?: number;
  tuition_fee?: number;
  currency: string;
  confidence_score: number;
  verification_status: string;
  extraction_notes?: string;
  source_url?: string;
  dim_score_required?: number;
  blocked_account_eur?: number;
  requires_studienkolleg?: boolean;
}

export interface VerifyProgramPayload {
  university_name?: string;
  program_name?: string;
  degree_level?: string;
  field?: string;
  country?: string;
  min_gpa?: number;
  min_ielts?: number;
  tuition_fee?: number;
  currency?: string;
  dim_score_required?: number;
  blocked_account_eur?: number;
  requires_studienkolleg?: boolean;
  verified_by?: string;
}

export interface TrackedApplication {
  id: number;
  student_id: string;
  program_id?: number | null;
  university_name: string;
  program_name: string;
  degree_level?: string | null;
  country?: string | null;
  deadline?: string | null;
  stage: "shortlisted" | "preparing_documents" | "submitted" | "accepted" | "rejected" | string;
  days_remaining: number;
  is_urgent: boolean;
  notes?: string | null;
}

export interface RegisterPayload extends StudentProfile {
  email: string;
  password: string;
  country?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

/* ---------------------------------------------------------------------------
 * Route planning: POST /routes/assess
 *
 * Every requirement below is nullable and stays nullable. A null means the
 * university's page did not state it -- never that the requirement does not
 * exist. `unknown_fields` names which ones came back null, so the interface can
 * show the gap rather than render an empty cell that reads as "not required".
 * ------------------------------------------------------------------------- */

export type RouteQualification =
  | "attestat"
  | "one_year_university"
  | "foundation_year"
  | "feststellungspruefung"
  | "a_level"
  | "ib"
  | "bachelor_degree";

export type GradeScaleKey = "5.0" | "100" | "4.0" | "german";

export type GradeVerdict =
  | "meets"
  | "below"
  | "no_grade_given"
  | "no_minimum_published"
  | "scales_not_comparable";

export interface AssessRoutesPayload {
  level_sought: "bachelor" | "master";
  qualification_held: RouteQualification;
  dim_score?: number | null;
  ielts?: number | null;
  toefl?: number | null;
  sat?: number | null;
  act?: number | null;
  tr_yos?: number | null;
  test_as?: number | null;
  csca?: number | null;
  hsk?: number | null;
  language_certificate_level?: string | null;
  has_international_olympiad_medal?: boolean | null;
  // DİM ixtisas qrupu, 1–4. The Dövlət Proqramı's threshold is 400 for Group 1
  // (engineering and technology) and 550 for every other field, so a score between the
  // two is only decidable with this.
  dim_field_group?: number | null;
  budget_azn_per_year?: number | null;
  gpa?: number | null;
  gpa_scale?: GradeScaleKey | null;
}

// Cash that must sit in an account before a visa is issued. Deliberately NOT part of
// money_cost_azn: the money stays the student's own, so adding it to the cost would
// overstate the price, and omitting it entirely — which this product did until now —
// showed Germany as the cheapest destination on the page when its deposit is the
// largest financial barrier of the six.
export interface ProofOfFunds {
  amount: number;
  currency: string;
  period: string;
  mechanism: string;
  citation: string;
}

export interface RouteHop {
  key: string;
  country_code: string;
  mechanism: string;
  time_cost_months: number;
  money_cost_azn_low: number;
  money_cost_azn_high: number;
  citation: string;
  provenance: string;
  // null means "no requirement recorded for this hop", which is NOT "this country
  // requires none". The UI must say which of the two it is.
  proof_of_funds: ProofOfFunds | null;
}

export interface RouteUniversity {
  university_name: string;
  program_name: string;
  country_code: string;
  intake_year: number;
  entry_qualification_accepted: string | null;
  foundation_required: boolean | null;
  foundation_providers: string | null;
  language_test: string | null;
  language_minimum_score: number | null;
  entrance_exam: string | null;
  entrance_exam_minimum: number | null;
  gpa_minimum: number | null;
  gpa_scale: string | null;
  tuition_per_year: number | null;
  currency: string | null;
  application_fee: number | null;
  application_deadline: string | null;
  application_portal: string | null;
  notes: string | null;
  unknown_fields: string[];
  not_stated: string | null;
  grade_verdict: GradeVerdict | string;
  // False when the grade comparison crossed two different scales. Rendering the
  // verdict without this flag overstates what was actually checked.
  grade_exact: boolean;
  grade_explanation: string;
  provenance: string;
  source_url: string;
  last_checked: string | null;
}

export interface RoutePlan {
  hops: RouteHop[];
  total_months: number;
  total_cost_azn_low: number;
  total_cost_azn_high: number;
  status: "open" | "unlockable" | string;
  missing: string[];
  destination_country: string;
  qualification_delivered: string;
  universities: RouteUniversity[];
  // Distinguishes "we have not collected this country" from "we collected it and
  // none of those universities accepts this qualification". An empty list must
  // never be shown without one of these.
  universities_status: string;
  universities_explanation: string;
}

export interface FundedProgramme {
  country_code: string | null;
  university_name: string;
  program_name: string;
  source_url: string;
}

export interface DPEligibility {
  status: string;
  band_checked: string;
  gates_met: string[];
  gates_missing: string[];
  note: string;
  // Not gates. What the student needs in order to decide whether to want this at all:
  // how many places exist at their level, the 5-year return-service contract the money
  // carries, and which academic year an application started today would be for.
  quota_note: string;
  obligation_note: string;
  window_note: string;
  funded_programmes: FundedProgramme[];
  funded_programmes_status: string;
  funded_programmes_explanation: string;
}

export interface AssessRoutesResponse {
  blocked: string[];
  plans: RoutePlan[];
  dp: DPEligibility;
}
