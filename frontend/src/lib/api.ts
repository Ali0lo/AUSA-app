import type {
  AgentStateData,
  ChatMessageResponse,
  DocumentSourceInfo,
  FactorScoreDetail,
  FlaggedProgram,
  HealthResponse,
  MatchResult,
  ProgramRequirements,
  RegisterPayload,
  StudentAccountProfile,
  StudentProfile,
  TrackedApplication,
  VerifyProgramPayload
} from "@/types";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

export type ApiErrorKind = "offline" | "timeout" | "http" | "invalid-response";

export class ApiError extends Error {
  status?: number;
  kind: ApiErrorKind;

  constructor(message: string, kind: ApiErrorKind, status?: number) {
    super(message);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
  }
}

export interface UserFacingError {
  title: string;
  message: string;
}

const REQUEST_TIMEOUT_MS = 12000;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isOptionalNumber(value: unknown): value is number | null | undefined {
  return value === undefined || value === null || isNumber(value);
}

function isOptionalString(value: unknown): value is string | null | undefined {
  return value === undefined || value === null || typeof value === "string";
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isDegree(value: unknown): value is StudentProfile["degree_level"] {
  return value === "bachelor" || value === "master" || value === "phd";
}

function invalidResponse(feature: string): never {
  throw new ApiError(
    `The backend response for ${feature} did not match the documented API contract.`,
    "invalid-response"
  );
}

function validationDetail(value: unknown): string | null {
  if (typeof value === "string") return value;
  if (!Array.isArray(value)) return null;

  const messages = value
    .map((item) => {
      if (!isRecord(item) || typeof item.msg !== "string") return null;
      const location = Array.isArray(item.loc)
        ? item.loc.filter((part) => typeof part === "string" || typeof part === "number").join(" → ")
        : "request";
      return `${location}: ${item.msg}`;
    })
    .filter((message): message is string => Boolean(message));

  return messages.length ? messages.join("; ") : null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...options.headers
      }
    });

    const raw = await response.text();
    let data: unknown = null;

    if (raw) {
      try {
        data = JSON.parse(raw);
      } catch {
        if (response.ok) {
          throw new ApiError("The backend returned data that was not valid JSON.", "invalid-response", response.status);
        }
      }
    }

    if (!response.ok) {
      const detail = isRecord(data) ? validationDetail(data.detail) : null;
      throw new ApiError(detail || `The backend returned status ${response.status}.`, "http", response.status);
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The backend did not respond within 12 seconds.", "timeout");
    }
    throw new ApiError("The AUSA backend could not be reached.", "offline");
  } finally {
    clearTimeout(timeout);
  }
}

function authHeaders(token?: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function isFactor(value: unknown): value is FactorScoreDetail {
  return (
    isRecord(value) &&
    isNumber(value.score) &&
    isNumber(value.weight) &&
    isNumber(value.weighted_score) &&
    typeof value.passed_hard_filter === "boolean" &&
    typeof value.explanation === "string"
  );
}

function isSource(value: unknown): value is DocumentSourceInfo {
  return (
    isRecord(value) &&
    typeof value.content_snippet === "string" &&
    isOptionalString(value.source_url) &&
    isOptionalNumber(value.page)
  );
}

function assertHealth(data: unknown): asserts data is HealthResponse {
  if (
    !isRecord(data) ||
    typeof data.status !== "string" ||
    typeof data.service !== "string" ||
    typeof data.version !== "string" ||
    typeof data.environment !== "string"
  ) {
    invalidResponse("health check");
  }
}

function assertStudent(data: unknown): asserts data is StudentAccountProfile {
  if (
    !isRecord(data) ||
    !isNumber(data.id) ||
    typeof data.email !== "string" ||
    !isNumber(data.gpa) ||
    !isNumber(data.budget) ||
    !isDegree(data.degree_level) ||
    !isOptionalNumber(data.ielts) ||
    !isOptionalNumber(data.toefl) ||
    !isOptionalString(data.field_of_study) ||
    !isOptionalString(data.country)
  ) {
    invalidResponse("student profile");
  }
}

function assertToken(data: unknown): asserts data is { access_token: string; token_type: string } {
  if (!isRecord(data) || typeof data.access_token !== "string" || typeof data.token_type !== "string") {
    invalidResponse("account registration");
  }
}

function assertMatch(data: unknown): asserts data is MatchResult {
  if (
    !isRecord(data) ||
    typeof data.program_name !== "string" ||
    typeof data.university_name !== "string" ||
    !isNumber(data.overall_match_percentage) ||
    typeof data.is_eligible !== "boolean" ||
    !isStringArray(data.ineligibility_reasons) ||
    !isRecord(data.breakdown) ||
    !isFactor(data.breakdown.degree_level) ||
    !isFactor(data.breakdown.academic) ||
    !isFactor(data.breakdown.budget) ||
    !isFactor(data.breakdown.language)
  ) {
    invalidResponse("prototype matching");
  }
}

function assertAgentState(data: unknown): asserts data is AgentStateData {
  if (
    !isRecord(data) ||
    typeof data.student_id !== "string" ||
    !isOptionalString(data.target_program_id) ||
    typeof data.application_stage !== "string" ||
    !isStringArray(data.missing_documents) ||
    !isOptionalString(data.drafted_motivation_letter)
  ) {
    invalidResponse("application state");
  }
}

export function getUserFacingError(error: unknown, feature: string): UserFacingError {
  if (error instanceof ApiError) {
    if (error.kind === "offline") {
      return {
        title: "Backend unavailable",
        message: `The AUSA API could not be reached. ${feature} is disabled until the backend is running.`
      };
    }
    if (error.kind === "timeout") {
      return {
        title: "Request timed out",
        message: `${feature} took longer than expected. Check the backend and try again.`
      };
    }
    if (error.kind === "invalid-response") {
      return {
        title: "Unexpected backend response",
        message: error.message
      };
    }
    if (error.status === 401) {
      return {
        title: "Authentication required",
        message: "The backend rejected the current credentials or session. Sign in again and retry."
      };
    }
    if (error.status === 404 || error.status === 501) {
      return {
        title: "Feature unavailable",
        message: `${feature} is not implemented by the connected backend.`
      };
    }
    if (error.status === 422) {
      return {
        title: "Invalid request",
        message: error.message
      };
    }
    return {
      title: "Backend error",
      message: error.message
    };
  }

  return {
    title: "Unexpected error",
    message: `${feature} failed unexpectedly. Try again or check the browser console.`
  };
}

export async function fetchHealth(): Promise<HealthResponse> {
  const data = await request<unknown>("/health");
  assertHealth(data);
  return data;
}

export async function fetchCurrentStudentProfile(token: string): Promise<StudentAccountProfile> {
  const data = await request<unknown>("/auth/me", {
    headers: authHeaders(token)
  });
  assertStudent(data);
  return data;
}

export async function registerStudent(payload: RegisterPayload): Promise<{ access_token: string; token_type: string }> {
  const data = await request<unknown>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  assertToken(data);
  return data;
}

export async function fetchMatchScore(
  student: StudentProfile,
  program: ProgramRequirements,
  token?: string
): Promise<MatchResult> {
  const data = await request<unknown>("/matching/evaluate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token)
    },
    body: JSON.stringify({ student, program })
  });
  assertMatch(data);
  return data;
}

export async function fetchAgentState(
  studentId = "std_demo",
  programId = "prog_101",
  token?: string
): Promise<AgentStateData> {
  const query = new URLSearchParams({
    student_id: studentId,
    target_program_id: programId
  });
  const data = await request<unknown>(`/chat/agent/state?${query.toString()}`, {
    headers: authHeaders(token)
  });
  assertAgentState(data);
  return data;
}

export async function sendChatMessage(
  message: string,
  type: "rag" | "agent",
  studentId = "std_demo",
  programId?: string,
  token?: string
): Promise<ChatMessageResponse> {
  if (type === "rag") {
    const data = await request<unknown>("/chat/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(token)
      },
      body: JSON.stringify({ question: message, top_k: 5 })
    });

    if (
      !isRecord(data) ||
      typeof data.answer !== "string" ||
      !Array.isArray(data.sources) ||
      !data.sources.every(isSource)
    ) {
      invalidResponse("AI advisor");
    }

    return {
      reply: data.answer,
      sources: data.sources
    };
  }

  const data = await request<unknown>("/chat/agent", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token)
    },
    body: JSON.stringify({
      message,
      student_id: studentId,
      target_program_id: programId || "prog_demo"
    })
  });

  if (
    !isRecord(data) ||
    typeof data.response !== "string" ||
    typeof data.application_stage !== "string" ||
    !isStringArray(data.missing_documents) ||
    !isOptionalString(data.drafted_motivation_letter)
  ) {
    invalidResponse("application assistant");
  }

  let updatedProfile: Partial<StudentProfile> | undefined = undefined;
  if (isRecord(data.updated_profile)) {
    const prof = data.updated_profile;
    updatedProfile = {
      gpa: typeof prof.gpa === "number" ? prof.gpa : undefined,
      ielts: typeof prof.ielts === "number" ? prof.ielts : undefined,
      toefl: typeof prof.toefl === "number" ? prof.toefl : undefined,
      degree_level: (prof.degree_level === "bachelor" || prof.degree_level === "master" || prof.degree_level === "phd") ? prof.degree_level : undefined,
    };
  }

  return {
    reply: data.response,
    applicationStage: data.application_stage,
    missingDocs: data.missing_documents,
    draftedLetter: data.drafted_motivation_letter || undefined,
    updatedProfile,
  };
}

export async function uploadDocumentAndChat(
  file: File,
  message: string,
  studentId = "std_demo",
  programId = "prog_101",
  token?: string
): Promise<ChatMessageResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("message", message || "I uploaded an academic document for profile extraction.");
  formData.append("student_id", studentId);
  formData.append("target_program_id", programId);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);

  try {
    const response = await fetch(`${API_BASE_URL}/chat/upload`, {
      method: "POST",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...authHeaders(token)
      },
      body: formData
    });

    const raw = await response.text();
    let data: unknown = null;

    if (raw) {
      try {
        data = JSON.parse(raw);
      } catch {
        if (response.ok) {
          throw new ApiError("The backend returned data that was not valid JSON.", "invalid-response", response.status);
        }
      }
    }

    if (!response.ok) {
      const detail = isRecord(data) ? validationDetail(data.detail) : null;
      throw new ApiError(detail || `The backend returned status ${response.status}.`, "http", response.status);
    }

    if (
      !isRecord(data) ||
      typeof data.response !== "string" ||
      typeof data.application_stage !== "string" ||
      !isStringArray(data.missing_documents)
    ) {
      invalidResponse("document upload parsing");
    }

    let updatedProfile: Partial<StudentProfile> | undefined = undefined;
    if (isRecord(data.updated_profile)) {
      const prof = data.updated_profile;
      updatedProfile = {
        gpa: typeof prof.gpa === "number" ? prof.gpa : undefined,
        ielts: typeof prof.ielts === "number" ? prof.ielts : undefined,
        toefl: typeof prof.toefl === "number" ? prof.toefl : undefined,
        degree_level: (prof.degree_level === "bachelor" || prof.degree_level === "master" || prof.degree_level === "phd") ? prof.degree_level : undefined,
      };
    }

    return {
      reply: data.response,
      applicationStage: data.application_stage,
      missingDocs: data.missing_documents,
      draftedLetter: typeof data.drafted_motivation_letter === "string" ? data.drafted_motivation_letter : undefined,
      updatedProfile,
    };
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("The document upload timed out.", "timeout");
    }
    throw new ApiError("The AUSA backend could not be reached for document upload.", "offline");
  } finally {
    clearTimeout(timeout);
  }
}

export async function downloadApplicationDossierPdf(
  payload: {
    motivation_letter_text: string;
    student_id?: number;
    program_id?: number;
    student_data?: Record<string, unknown>;
    program_data?: Record<string, unknown>;
  },
  token?: string
): Promise<void> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  try {
    const response = await fetch(`${API_BASE_URL}/export/motivation-letter/pdf`, {
      method: "POST",
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/pdf",
        ...authHeaders(token)
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new ApiError(`PDF export failed with status ${response.status}.`, "http", response.status);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "AUSA_Application_Dossier.pdf";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("PDF export generation timed out.", "timeout");
    }
    throw new ApiError("The backend could not be reached to generate the PDF dossier.", "offline");
  } finally {
    clearTimeout(timeout);
  }
}

export async function fetchMyApplications(
  studentId = "std_demo",
  token?: string
): Promise<TrackedApplication[]> {
  const query = new URLSearchParams({ student_id: studentId });
  const data = await request<unknown>(`/applications/my-applications?${query.toString()}`, {
    headers: authHeaders(token)
  });

  if (!Array.isArray(data)) {
    invalidResponse("tracked applications query");
  }

  return (data as unknown) as TrackedApplication[];
}

export async function createTrackedApplication(
  payload: {
    university_name: string;
    program_name: string;
    student_id?: string;
    program_id?: number;
    degree_level?: string;
    country?: string;
    deadline?: string;
    stage?: string;
    notes?: string;
  },
  token?: string
): Promise<TrackedApplication> {
  const data = await request<unknown>("/applications/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token)
    },
    body: JSON.stringify(payload)
  });

  if (!isRecord(data) || typeof data.university_name !== "string") {
    invalidResponse("tracked application creation");
  }

  return (data as unknown) as TrackedApplication;
}

export async function updateTrackedApplicationStage(
  applicationId: number,
  stage: string,
  notes?: string,
  token?: string
): Promise<TrackedApplication> {
  const data = await request<unknown>(`/applications/${applicationId}/stage`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token)
    },
    body: JSON.stringify({ stage, notes })
  });

  if (!isRecord(data) || typeof data.stage !== "string") {
    invalidResponse("tracked application stage update");
  }

  return (data as unknown) as TrackedApplication;
}

export async function fetchFlaggedPrograms(token?: string): Promise<FlaggedProgram[]> {
  const data = await request<unknown>("/admin/programs/flagged", {
    headers: authHeaders(token)
  });

  if (!Array.isArray(data)) {
    invalidResponse("admin flagged programs query");
  }

  return data as FlaggedProgram[];
}

export async function verifyAndApproveProgram(
  programId: number,
  payload: VerifyProgramPayload,
  token?: string
): Promise<{ message: string; program_id: number; verification_status: string }> {
  const data = await request<unknown>(`/admin/programs/${programId}/verify`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token)
    },
    body: JSON.stringify(payload)
  });

  if (!isRecord(data) || typeof data.verification_status !== "string") {
    invalidResponse("admin program verification");
  }

  return data as { message: string; program_id: number; verification_status: string };
}
