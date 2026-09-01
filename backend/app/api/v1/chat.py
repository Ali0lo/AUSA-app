import io
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.agent.graph import application_agent
from app.services.agent.state import AgentState
from app.services.agent.tools import STUDENT_PROFILE_STORE, draft_motivation_letter, extract_and_update_profile
from app.services.embeddings import EmbeddingUnavailableError
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


class UpdatedStudentProfileInfo(BaseModel):
    """Updated student profile metrics returned after document extraction."""
    gpa: Optional[float] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    degree_level: Optional[str] = None


class AgentChatResponse(BaseModel):
    """Response payload from stateful application agent."""
    response: str = Field(..., description="Agent response message")
    student_id: str = Field(..., description="Student identifier")
    application_stage: str = Field(..., description="Current application dossier stage")
    missing_documents: List[str] = Field(default_factory=list, description="Updated list of missing documents")
    drafted_motivation_letter: Optional[str] = Field(None, description="Generated motivation letter text if drafted")
    updated_profile: Optional[UpdatedStudentProfileInfo] = Field(None, description="Updated student profile metrics if document was parsed")


class AgentStateResponse(BaseModel):
    """Response payload representing current agent workflow state."""
    student_id: str
    target_program_id: Optional[str] = None
    application_stage: str
    missing_documents: List[str]
    drafted_motivation_letter: Optional[str] = None
    student_profile: Optional[UpdatedStudentProfileInfo] = None


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract plain text content from uploaded PDF document bytes with fallback tools."""
    text = ""
    # 1. Try PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
        if text.strip():
            return text.strip()
    except Exception:
        pass

    # 2. Try pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        if text.strip():
            return text.strip()
    except Exception:
        pass

    # 3. Fallback: UTF-8 plain text decoder
    try:
        return file_bytes.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


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
    except EmbeddingUnavailableError as e:
        # The query cannot be embedded, so retrieval is impossible. Say so -- an
        # unretrieved answer would be ungrounded, which is worse than no answer.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search is unavailable: {str(e)}"
        )
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
    profile = STUDENT_PROFILE_STORE.get(student_id, {})
    
    return AgentStateResponse(
        student_id=student_id,
        target_program_id=target_program_id,
        application_stage="gathering_info",
        missing_documents=["passport_copy", "motivation_letter"],
        drafted_motivation_letter=letter,
        student_profile=UpdatedStudentProfileInfo(
            gpa=profile.get("gpa"),
            ielts=profile.get("ielts"),
            toefl=profile.get("toefl"),
            degree_level=profile.get("degree_level")
        )
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

        letter = None
        if "motivation" in payload.message.lower() or "draft" in payload.message.lower():
            letter = draft_motivation_letter.invoke({
                "student_id": payload.student_id,
                "program_id": payload.target_program_id or "prog_101"
            })

        stage = output_state.get("application_stage", "gathering_info")
        if letter or "draft" in payload.message.lower():
            stage = "drafting_documents"

        profile = STUDENT_PROFILE_STORE.get(payload.student_id, {})

        return AgentChatResponse(
            response=str(agent_reply),
            student_id=payload.student_id,
            application_stage=stage,
            missing_documents=output_state.get("missing_documents", ["passport_copy", "motivation_letter"]),
            drafted_motivation_letter=letter,
            updated_profile=UpdatedStudentProfileInfo(
                gpa=profile.get("gpa"),
                ielts=profile.get("ielts"),
                toefl=profile.get("toefl"),
                degree_level=profile.get("degree_level")
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing agent workflow: {str(e)}"
        )


@router.post(
    "/upload",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload Academic Document & Auto-Update Profile",
    description="Upload a transcript or certificate PDF file. Parses metrics (GPA, IELTS/TOEFL) and updates student profile."
)
async def upload_document_and_update_profile(
    file: UploadFile = File(...),
    message: Optional[str] = Form("I uploaded an academic document for profile extraction."),
    student_id: str = Form("std_demo"),
    target_program_id: Optional[str] = Form("prog_101")
) -> AgentChatResponse:
    """Accept multipart/form-data PDF upload, extract metrics, and update student profile."""
    try:
        file_bytes = await file.read()
        parsed_text = extract_text_from_pdf_bytes(file_bytes)

        if not parsed_text.strip():
            # Previously substituted "GPA 3.8, IELTS 7.5" here, which invented the student's
            # own qualifications and fed them into every subsequent eligibility check.
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"No text could be extracted from '{file.filename}'. It may be a scanned "
                    "image without an OCR layer, or an unsupported format. Please upload a "
                    "text-based PDF, or enter the scores manually."
                )
            )

        summary = extract_and_update_profile.invoke({
            "document_text": parsed_text,
            "student_id": student_id
        })

        agent_prompt = f"{message}\n\n[Uploaded Document Content]:\n{parsed_text[:500]}"
        initial_state: AgentState = {
            "messages": [HumanMessage(content=agent_prompt)],
            "student_id": student_id,
            "target_program_id": target_program_id,
            "missing_documents": [],
            "application_stage": "gathering_info",
        }

        try:
            output_state = await application_agent.ainvoke(initial_state)
            messages = output_state.get("messages", [])
            reply = messages[-1].content if messages else summary
        except Exception:
            reply = f"I have processed your document '{file.filename}'. {summary}"

        profile = STUDENT_PROFILE_STORE.get(student_id, {})

        return AgentChatResponse(
            response=str(reply),
            student_id=student_id,
            application_stage="gathering_info",
            missing_documents=["passport_copy", "motivation_letter"],
            drafted_motivation_letter=None,
            updated_profile=UpdatedStudentProfileInfo(
                gpa=profile.get("gpa"),
                ielts=profile.get("ielts"),
                toefl=profile.get("toefl"),
                degree_level=profile.get("degree_level")
            )
        )
    except HTTPException:
        # A deliberate 4xx (e.g. unreadable upload) must reach the client as itself,
        # not be relabelled a 500 by the handler below.
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading and parsing document: {str(e)}"
        )
