import {
  DocumentSourceInfo,
  MatchResult,
  ProgramRequirements,
  StudentProfile,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Fetch authenticated student profile from /api/v1/auth/me.
 */
export async function fetchCurrentStudentProfile(
  token: string
): Promise<StudentProfile & { id: number; email: string }> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Profile fetch failed with status ${response.status}`
    );
  }

  return response.json();
}

/**
 * Send student profile and target program requirements to backend deterministic matching engine.
 * Automatically attaches Bearer JWT authorization token if available.
 */
export async function fetchMatchScore(
  student: StudentProfile,
  program: ProgramRequirements,
  token?: string
): Promise<MatchResult> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}/matching/evaluate`, {
    method: "POST",
    headers,
    body: JSON.stringify({ student, program }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Matching request failed with status ${response.status}`
    );
  }

  return response.json();
}

export interface ChatMessageResponse {
  reply: string;
  sources?: DocumentSourceInfo[];
  applicationStage?: string;
  missingDocs?: string[];
}

/**
 * Send chat message to backend (RAG guidelines Q&A or LangGraph stateful application agent).
 * Automatically attaches Bearer JWT authorization token if available.
 */
export async function sendChatMessage(
  message: string,
  type: "rag" | "agent",
  studentId: string = "std_demo",
  programId?: string,
  token?: string
): Promise<ChatMessageResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (type === "rag") {
    const response = await fetch(`${API_BASE_URL}/chat/ask`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        question: message,
        top_k: 5,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `RAG Q&A request failed with status ${response.status}`
      );
    }

    const data = await response.json();
    return {
      reply: data.answer,
      sources: data.sources || [],
    };
  } else {
    // Agent endpoint
    const response = await fetch(`${API_BASE_URL}/chat/agent`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        message,
        student_id: studentId,
        target_program_id: programId || "prog_demo",
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `Agent request failed with status ${response.status}`
      );
    }

    const data = await response.json();
    return {
      reply: data.response,
      applicationStage: data.application_stage,
      missingDocs: data.missing_documents || [],
    };
  }
}
