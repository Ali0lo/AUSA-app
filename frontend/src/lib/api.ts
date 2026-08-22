import {
  DocumentSourceInfo,
  MatchResult,
  ProgramRequirements,
  StudentProfile,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Send student profile and target program requirements to backend deterministic matching engine.
 */
export async function fetchMatchScore(
  student: StudentProfile,
  program: ProgramRequirements
): Promise<MatchResult> {
  const response = await fetch(`${API_BASE_URL}/matching/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
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
 */
export async function sendChatMessage(
  message: string,
  type: "rag" | "agent",
  studentId: string = "std_demo",
  programId?: string
): Promise<ChatMessageResponse> {
  if (type === "rag") {
    const response = await fetch(`${API_BASE_URL}/chat/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
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
      headers: {
        "Content-Type": "application/json",
      },
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
