import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  fetchHealth,
  fetchMatchScore,
  getUserFacingError,
  registerStudent,
  sendChatMessage
} from "@/lib/api";
import { DEMO_PROGRAMS } from "@/lib/demo-programs";

const health = {
  status: "healthy",
  service: "AUSA",
  version: "0.1.0",
  environment: "test"
};

const match = {
  program_name: "MSc Computer Science",
  university_name: "Technical University of Munich (TU Munich)",
  overall_match_percentage: 88,
  is_eligible: true,
  ineligibility_reasons: [],
  breakdown: {
    degree_level: { score: 100, weight: 0.2, weighted_score: 20, passed_hard_filter: true, explanation: "Degree matches." },
    academic: { score: 90, weight: 0.3, weighted_score: 27, passed_hard_filter: true, explanation: "GPA meets the minimum." },
    budget: { score: 100, weight: 0.3, weighted_score: 30, passed_hard_filter: true, explanation: "Budget covers tuition." },
    language: { score: 80, weight: 0.2, weighted_score: 16, passed_hard_filter: true, explanation: "Language score meets the minimum." }
  }
};

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

describe("API compatibility layer", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("checks the documented health endpoint and validates its response", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(health));
    await expect(fetchHealth()).resolves.toEqual(health);
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8000/api/v1/health");
  });

  it("sends the original matching payload and accepts a complete result", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(match));
    const student = { gpa: 3.7, budget: 18000, ielts: 7, degree_level: "master" as const };

    await expect(fetchMatchScore(student, DEMO_PROGRAMS[0])).resolves.toEqual(match);

    const options = fetchMock.mock.calls[0][1];
    expect(options?.method).toBe("POST");
    expect(JSON.parse(String(options?.body))).toEqual({ student, program: DEMO_PROGRAMS[0] });
  });

  it("rejects malformed success responses before the interface renders them", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ overall_match_percentage: 88 }));

    await expect(
      fetchMatchScore({ gpa: 3.5, budget: 15000, degree_level: "master" }, DEMO_PROGRAMS[0])
    ).rejects.toMatchObject({
      name: "ApiError",
      kind: "invalid-response"
    });
  });

  it("retains backend validation detail in the user-facing error", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({
      detail: [{ loc: ["body", "gpa"], msg: "Input should be less than or equal to 4" }]
    }, 422));

    let failure: unknown;
    try {
      await registerStudent({
        email: "student@example.com",
        password: "secret1",
        gpa: 5,
        budget: 15000,
        degree_level: "master"
      });
    } catch (error) {
      failure = error;
    }

    expect(getUserFacingError(failure, "Account creation")).toEqual({
      title: "Invalid request",
      message: "body → gpa: Input should be less than or equal to 4"
    });
  });

  it("distinguishes an unreachable backend from an HTTP failure", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("fetch failed"));

    let failure: unknown;
    try {
      await fetchHealth();
    } catch (error) {
      failure = error;
    }

    expect(getUserFacingError(failure, "Health check")).toEqual({
      title: "Backend unavailable",
      message: "The AUSA API could not be reached. Health check is disabled until the backend is running."
    });
    expect(getUserFacingError(new ApiError("Maintenance", "http", 503), "Matching")).toEqual({
      title: "Backend error",
      message: "Maintenance"
    });
  });

  it("maps the RAG contract without manufacturing sources", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({
      answer: "The minimum IELTS result is 7.0.",
      sources: [{ content_snippet: "Applicants need IELTS 7.0.", source_url: "https://example.edu/rules", page: 4 }]
    }));

    await expect(sendChatMessage("What IELTS score is needed?", "rag")).resolves.toEqual({
      reply: "The minimum IELTS result is 7.0.",
      sources: [{ content_snippet: "Applicants need IELTS 7.0.", source_url: "https://example.edu/rules", page: 4 }]
    });
  });
});
