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
}

export interface AgentStateData {
  student_id: string;
  target_program_id?: string;
  application_stage: string;
  missing_documents: string[];
  drafted_motivation_letter?: string;
}

export interface ChatMessageResponse {
  reply: string;
  sources?: DocumentSourceInfo[];
  applicationStage?: string;
  missingDocs?: string[];
  draftedLetter?: string;
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
