import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.document import UniversityDocument
from app.services.embeddings import EmbeddingUnavailableError
from app.services.rag.generator import (
    NO_INFO_RESPONSE,
    answer_student_question,
    format_docs_context,
)
from app.services.rag.retriever import retrieve_relevant_chunks


def test_university_document_model():
    doc = UniversityDocument(
        id=1,
        university_id=10,
        program_id=100,
        content="Applicants must submit IELTS 6.5 minimum score.",
        doc_metadata={"source_url": "https://example.com/guidelines.pdf", "page": 4}
    )
    assert doc.id == 1
    assert doc.university_id == 10
    assert doc.program_id == 100
    assert "IELTS 6.5" in doc.content
    assert doc.doc_metadata["page"] == 4


def test_format_docs_context():
    doc1 = UniversityDocument(
        content="Tuition fee is 10,000 EUR per academic year.",
        doc_metadata={"source_url": "https://uni.edu/fees", "page": 2}
    )
    doc2 = UniversityDocument(
        content="Scholarship covers full tuition and accommodation.",
        doc_metadata={"source_url": "https://uni.edu/scholarship"}
    )
    
    context = format_docs_context([doc1, doc2])
    assert "Tuition fee is 10,000 EUR" in context
    assert "Scholarship covers full tuition" in context
    assert "[Page 2]" in context
    assert "Source: https://uni.edu/fees" in context


@pytest.mark.asyncio
async def test_answer_student_question_empty_docs():
    res = await answer_student_question("Is IELTS required?", [])
    assert res == NO_INFO_RESPONSE


@pytest.mark.asyncio
async def test_answer_student_question_grounded():
    doc = UniversityDocument(
        content="The deadline for international applicants is October 15, 2026.",
        doc_metadata={"source_url": "https://uni.edu/deadlines"}
    )
    res = await answer_student_question("What is the application deadline?", [doc])
    assert res != ""
    assert res != NO_INFO_RESPONSE or "deadline" in res.lower()


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_query_building():
    """Covers SQL construction only, so the embedding is stubbed rather than called.

    This previously relied on the real embedding path, which returned a sha256-derived
    vector when no API key was set -- so the test passed while retrieval was meaningless.
    """
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        UniversityDocument(id=1, content="Test content")
    ]
    mock_db.execute.return_value = mock_result

    with patch(
        "app.services.rag.retriever.get_embedding_async",
        new=AsyncMock(return_value=[0.1] * 1536),
    ):
        results = await retrieve_relevant_chunks(
            db=mock_db,
            query="What is the IELTS requirement?",
            top_k=3,
            filters={"university_id": 5}
        )

    assert len(results) == 1
    assert results[0].content == "Test content"
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_retrieve_raises_when_embeddings_unavailable(monkeypatch):
    """Retrieval must fail rather than search with a substitute vector."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(EmbeddingUnavailableError):
        await retrieve_relevant_chunks(db=AsyncMock(), query="What is the IELTS requirement?")
