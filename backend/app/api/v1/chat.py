from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.agent.graph import application_agent
from app.services.agent.state import AgentState
from app.services.agent.tools import draft_motivation_letter
from app.services.rag.generator import answer_student_question
from app.services.rag.retriever import retrieve_relevant_chunks

router = APIRouter(prefix="/chat", tags=["AI Advisor & RAG Chat"])


# -------------------------------------------------------------
# Schemas for RAG Q&A Endpoint (/chat/ask)
# -------------------------------------------------------------
class RAGQuestionRequest(BaseModel):
    """Request payload for RAG university guidelines Q&A."""
    question: str = Field(..., description="Student question regarding guidelines, requirements, or scholarships")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of vector document chunks to retrieve")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters like university_id or program_id")


class DocumentSourceInfo(BaseModel):
    """Source reference metadata for retrieved documents."""
    content_snippet: str = Field(..., description="Snippet of retrieved text chunk")
    source_url: Optional[str] = Field(None, description="Official source link")
    page: Optional[int] = Field(None, description="Page number in document")


class RAGQuestionResponse(BaseModel):
    """Grounded answer response from RAG system."""
    answer: str = Field(..., description="Grounded answer based strictly on retrieved context")
    sources: List[DocumentSourceInfo] = Field(default_factory=list, description="Source context references used")


# -------------------------------------------------------------
# Schemas for LangGraph Agent Endpoint (/chat/agent)
# -------------------------------------------------------------
class AgentChatRequest(BaseModel):
    """Request payload for stateful application agent conversation."""
    message: str = Field(..., description="User message to the application assistant")
    student_id: str = Field(..., description="Unique student identifier")
    target_program_id: Optional[str] = Field(None, description="Target program identifier")


class AgentChatResponse(BaseModel):
    """Response payload from stateful application agent."""
    response: str = Field(..., description="Agent response message")
    student_id: str = Field(..., description="Student identifier")
    application_stage: str = Field(..., description="Current application dossier stage")
    missing_documents: List[str] = Field(default_factory=list, description="Updated list of missing documents")
    drafted_motivation_letter: Optional[str] = Field(None, description="Generated motivation letter text if drafted")


class AgentStateResponse(BaseModel):
    """Response payload representing current agent workflow state."""
    student_id: str
    target_program_id: Optional[str] = None
    application_stage: str
    missing_documents: List[str]
    drafted_motivation_letter: Optional[str] = None


# -------------------------------------------------------------
# Route Handlers
# -------------------------------------------------------------
@router.post(
    "/ask",
    response_model=RAGQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask University Guidelines Q&A (RAG)",
    description=(
        "Retrieve relevant document chunks from PostgreSQL vector database (pgvector) "
        "and generate a strictly grounded answer. If the context does not contain the answer, "
        "returns 'I do not have this information.'"
    )
)
async def ask_university_guideline(
    payload: RAGQuestionRequest,
    db: AsyncSession = Depends(get_db)
) -> RAGQuestionResponse:
    """RAG endpoint querying vector store and generating grounded responses."""
    try:
        retrieved_docs = await retrieve_relevant_chunks(
            db=db,
            query=payload.question,
            top_k=payload.top_k,
            filters=payload.filters
        )

        answer = await answer_student_question(
            question=payload.question,
            retrieved_docs=retrieved_docs
        )

        sources = []
        for doc in retrieved_docs:
            meta = getattr(doc, "doc_metadata", {}) or {}
            sources.append(
                DocumentSourceInfo(
                    content_snippet=doc.content[:150] + "..." if len(doc.content) > 150 else doc.content,
                    source_url=meta.get("source_url"),
                    page=meta.get("page")
                )
            )

        return RAGQuestionResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}"
        )


@router.get(
    "/agent/state",
    response_model=AgentStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Agent Workflow State",
    description="Retrieve application stage, missing documents, and drafted motivation letter."
)
async def get_agent_state(
    student_id: str = "std_demo",
    target_program_id: Optional[str] = "prog_101"
) -> AgentStateResponse:
    """Retrieve agent workflow state."""
    letter = draft_motivation_letter.invoke({"student_id": student_id, "program_id": target_program_id or "prog_101"})
    return AgentStateResponse(
        student_id=student_id,
        target_program_id=target_program_id,
        application_stage="gathering_info",
        missing_documents=["official_transcript", "passport_copy", "motivation_letter"],
        drafted_motivation_letter=letter
    )


@router.post(
    "/agent",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Advisor Agent Conversation (LangGraph)",
    description=(
        "Interact with the stateful multi-step application preparation agent. "
        "Tracks application stage, checks missing documents, and assists with preparation."
    )
)
async def chat_with_application_agent(
    payload: AgentChatRequest
) -> AgentChatResponse:
    """Stateful Agent endpoint executing the LangGraph workflow."""
    try:
        initial_state: AgentState = {
            "messages": [HumanMessage(content=payload.message)],
            "student_id": payload.student_id,
            "target_program_id": payload.target_program_id,
            "missing_documents": [],
            "application_stage": "gathering_info",
        }

        output_state = await application_agent.ainvoke(initial_state)

        messages = output_state.get("messages", [])
        agent_reply = messages[-1].content if messages else "No response generated."

        # Generate motivation letter if requested
        letter = None
        if "motivation" in payload.message.lower() or "draft" in payload.message.lower():
            letter = draft_motivation_letter.invoke({
                "student_id": payload.student_id,
                "program_id": payload.target_program_id or "prog_101"
            })

        stage = output_state.get("application_stage", "gathering_info")
        if letter or "draft" in payload.message.lower():
            stage = "drafting_documents"

        return AgentChatResponse(
            response=str(agent_reply),
            student_id=payload.student_id,
            application_stage=stage,
            missing_documents=output_state.get("missing_documents", ["official_transcript", "passport_copy", "motivation_letter"]),
            drafted_motivation_letter=letter,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing agent workflow: {str(e)}"
        )
