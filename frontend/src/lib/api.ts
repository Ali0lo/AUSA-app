import type {
  AgentStateData,
  AssessRoutesPayload,
  AssessRoutesResponse,
  ChatMessageResponse,
  DocumentSourceInfo,
  FlaggedProgram,
  HealthResponse,
  RegisterPayload,
  RoutePlan,
  RouteUniversity,
  Scholarship,
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

export interface CatalogueResult {
  status: string;
  total: number;
  items: RouteUniversity[];
}

function assertCatalogue(data: unknown): asserts data is CatalogueResult {
  if (!isRecord(data) || typeof data.status !== "string" || !isNumber(data.total) ||
      !Array.isArray(data.items) || !data.items.every(isUniversity)) invalidResponse("catalogue");
}

export async function fetchCatalogue(level: "bachelor" | "master"): Promise<CatalogueResult> {
  const items: RouteUniversity[] = [];
  let total = 0;
  do {
    const page = await request<unknown>(`/catalogue?level=${level}&limit=250&offset=${items.length}`);
    assertCatalogue(page);
    total = page.total;
    if (!page.items.length) break;
    items.push(...page.items);
  } while (items.length < total);
  return { status: items.length ? "listed" : "not_collected", total, items };
}

export async function assessCatalogue(university: string, payload: AssessRoutesPayload): Promise<CatalogueResult> {
  const data = await request<unknown>(`/catalogue/assess?university=${encodeURIComponent(university)}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
  });
  assertCatalogue(data);
  return data;
}

export interface CatalogueReview { revision: string; requirement: RouteUniversity }

export async function fetchCatalogueReview(level: "bachelor" | "master", token?: string): Promise<CatalogueReview[]> {
  const data = await request<unknown>(`/admin/catalogue?level=${level}&limit=250`, { headers: authHeaders(token) });
  if (!Array.isArray(data) || !data.every((row) => isRecord(row) && typeof row.revision === "string" && /^[a-f0-9]{64}$/.test(row.revision) && isUniversity(row.requirement) && isNumber(row.requirement.id))) invalidResponse("catalogue review");
  return data as CatalogueReview[];
}

export async function verifyCatalogueRow(id: number, revision: string, token?: string): Promise<void> {
  await request(`/admin/catalogue/${id}/verify`, {
    method: "PUT", headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ revision, source_checked: true })
  });
}

function authHeaders(token?: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
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

function isUniversity(value: unknown): value is RouteUniversity {
  return (
    isRecord(value) &&
    typeof value.university_name === "string" &&
    typeof value.program_name === "string" &&
    typeof value.country_code === "string" &&
    isNumber(value.intake_year) &&
    isOptionalString(value.entry_qualification_accepted) &&
    (value.foundation_required === null ||
      value.foundation_required === undefined ||
      typeof value.foundation_required === "boolean") &&
    isOptionalNumber(value.tuition_per_year) &&
    isOptionalString(value.application_deadline) &&
    isStringArray(value.unknown_fields) &&
    isOptionalString(value.not_stated) &&
    isOptionalNumber(value.id) &&
    isOptionalNumber(value.living_cost_estimate_per_year) &&
    isOptionalString(value.notes) &&
    isOptionalString(value.requirement_scope) &&
    isOptionalString(value.language_of_instruction) &&
    isOptionalString(value.application_status) &&
    (value.checks === undefined || isStringArray(value.checks)) &&
    (value.evidence === undefined || (Array.isArray(value.evidence) && value.evidence.every((item) =>
      isRecord(item) && typeof item.url === "string" && isStringArray(item.fields) &&
      typeof item.checked_at === "string" && typeof item.note === "string"))) &&
    // The three grade fields are required, not optional. A client that renders a
    // verdict without `grade_exact` reports a proportional cross-scale comparison
    // as though it were an exact one, so a response missing it is not a response
    // this client can render honestly.
    typeof value.grade_verdict === "string" &&
    typeof value.grade_exact === "boolean" &&
    typeof value.grade_explanation === "string" &&
    typeof value.provenance === "string" &&
    typeof value.source_url === "string"
  );
}

function isPlan(value: unknown): value is RoutePlan {
  return (
    isRecord(value) &&
    Array.isArray(value.hops) &&
    value.hops.every(
      (hop) =>
        isRecord(hop) &&
        typeof hop.key === "string" &&
        typeof hop.country_code === "string" &&
        typeof hop.mechanism === "string" &&
        isNumber(hop.time_cost_months) &&
        typeof hop.citation === "string" &&
        // Present and nullable, never absent. `null` is the backend saying "no
        // requirement recorded here"; a missing key would be indistinguishable
        // from an older backend that cannot report one at all, and this client
        // would then render Germany's EUR 11,904 deposit as though it did not exist.
        (hop.proof_of_funds === null || isRecord(hop.proof_of_funds))
    ) &&
    isNumber(value.total_months) &&
    isNumber(value.total_cost_azn_low) &&
    isNumber(value.total_cost_azn_high) &&
    typeof value.status === "string" &&
    isStringArray(value.missing) &&
    typeof value.destination_country === "string" &&
    typeof value.qualification_delivered === "string" &&
    Array.isArray(value.universities) &&
    value.universities.every(isUniversity) &&
    // Both are required. An empty `universities` list rendered without its status
    // is indistinguishable from "no university will take you", which is a claim
    // the backend never makes and this client must not make on its behalf.
    typeof value.universities_status === "string" &&
    typeof value.universities_explanation === "string"
  );
}

function isScholarship(value: unknown): value is Scholarship {
  return (
    isRecord(value) &&
    typeof value.key === "string" &&
    typeof value.name === "string" &&
    typeof value.provider === "string" &&
    isNumber(value.tier) &&
    isOptionalString(value.country_code) &&
    typeof value.coverage === "string" &&
    typeof value.status === "string" &&
    // All four are required and stay four separate arrays. `gates_unknown` is the one
    // that matters: it holds gates the backend could NOT check, and a client that
    // dropped it — or folded it into `gates_missing` — would render an award whose age
    // limit was never checked as though the student had cleared it.
    isStringArray(value.gates_met) &&
    isStringArray(value.gates_missing) &&
    isStringArray(value.gates_blocked) &&
    isStringArray(value.gates_unknown) &&
    isOptionalString(value.obligation) &&
    isOptionalString(value.window) &&
    typeof value.citation === "string" &&
    typeof value.provenance === "string"
  );
}

function assertAssessment(data: unknown): asserts data is AssessRoutesResponse {
  if (
    !isRecord(data) ||
    // Required, and required to be complete. The DP is only one of ten funders and is
    // the one every agency already names; the other nine are where the answer a student
    // cannot get elsewhere lives. An assessment without them is the old DP-only product.
    !Array.isArray(data.scholarships) ||
    !data.scholarships.every(isScholarship) ||
    typeof data.scholarships_note !== "string" ||
    // Present and nullable, never absent — same rule as proof_of_funds. `null` is the
    // backend saying this profile does not face the prep-year/Türkiye Bursları
    // trade-off; a missing key would be indistinguishable from a backend that cannot
    // detect it, and the warning would vanish silently for the students it is for.
    // Hence the explicit `in` check: isOptionalString alone accepts `undefined` and
    // would let an absent key pass as "no trade-off".
    !("prep_year_warning" in data) ||
    (data.prep_year_warning !== null && typeof data.prep_year_warning !== "string") ||
    !isStringArray(data.blocked) ||
    !Array.isArray(data.plans) ||
    !data.plans.every(isPlan) ||
    !isRecord(data.dp) ||
    typeof data.dp.status !== "string" ||
    typeof data.dp.band_checked !== "string" ||
    !isStringArray(data.dp.gates_met) ||
    !isStringArray(data.dp.gates_missing) ||
    typeof data.dp.note !== "string" ||
    // Required, all three. The quota tells a student how many places exist at their
    // level, the obligation tells them the money carries a 5-year return contract,
    // and the window tells them which academic year they are actually applying for.
    // A DP panel rendered without them presents a funding programme as if accepting
    // it were free of consequences and available right now, and neither is true.
    typeof data.dp.quota_note !== "string" ||
    typeof data.dp.obligation_note !== "string" ||
    typeof data.dp.window_note !== "string" ||
    !Array.isArray(data.dp.funded_programmes) ||
    typeof data.dp.funded_programmes_status !== "string" ||
    typeof data.dp.funded_programmes_explanation !== "string"
  ) {
    invalidResponse("route assessment");
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

/**
 * Assess which routes are open, unlockable or blocked for one profile.
 *
 * The payload IS the profile -- there is no student record to look up and
 * therefore no "row not found" case. Every score is optional, and an omitted
 * score is sent as absent rather than as 0: "did not sit the exam" and "scored
 * zero" are different facts and the backend keeps them apart.
 *
 * No token. Route assessment reads no student's stored data, so requiring a sign-in
 * to answer "where could I go" would gate the one question the product exists to
 * answer behind an account.
 */
export async function assessRoutes(payload: AssessRoutesPayload): Promise<AssessRoutesResponse> {
  const body: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(payload)) {
    if (value !== null && value !== undefined && value !== "") body[key] = value;
  }

  const data = await request<unknown>("/routes/assess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  assertAssessment(data);
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
