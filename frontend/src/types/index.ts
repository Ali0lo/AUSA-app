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
