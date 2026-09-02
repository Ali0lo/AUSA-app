"""
Tests for the embedding service.

These assert that a missing or placeholder key *fails*. The previous tests
asserted `len(vec) == 1536` and passed whether or not an embedding had actually
been generated -- the sha256 fallback returned a correctly-shaped vector, so a
completely broken service looked green.
"""

import pytest

from app.services import embeddings
from app.services.embeddings import EmbeddingUnavailableError, get_embedding, get_embedding_async


def test_no_fallback_embedding_exists():
    """Regression guard: this fabrication has been reintroduced three times."""
    assert not hasattr(embeddings, "generate_fallback_embedding")


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(EmbeddingUnavailableError):
        get_embedding("ADA University Computer Science")


def test_placeholder_api_key_raises(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-YOUR_OPENAI_API_KEY_HERE")
    with pytest.raises(EmbeddingUnavailableError):
        get_embedding("DAAD Master Studies Scholarship")


@pytest.mark.asyncio
async def test_missing_api_key_raises_async(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(EmbeddingUnavailableError):
        await get_embedding_async("Technical University of Munich M.Sc. Informatics")


# -------------------------------------------------------------
# Index and query must embed with the same model
# -------------------------------------------------------------
# A vector store is only meaningful if the vectors in it and the vectors searched against
# it come from the same model. Embed the corpus with text-embedding-3-small and query with
# anything else and cosine similarity becomes noise -- retrieval returns confident,
# arbitrary documents, and nothing raises. It is the sha256-fallback failure again in a
# form no exception can catch, so it has to be caught structurally instead.
#
# Today this holds because seed_db.py (indexing) and rag/retriever.py (querying) both call
# get_embedding_async, and the model name exists in exactly one place. These tests fail if
# a future change gives either side its own model or its own dimension.

def test_one_model_constant_serves_both_indexing_and_querying():
    """The retriever must not carry a model of its own."""
    import inspect

    from app.services.rag import retriever

    assert retriever.get_embedding_async is get_embedding_async
    source = inspect.getsource(retriever)
    assert "text-embedding" not in source, (
        "The retriever names an embedding model directly. It must call "
        "app.services.embeddings.get_embedding_async so index and query cannot drift apart."
    )


def test_declared_dimension_matches_the_document_column():
    """DIMENSIONS and the pgvector column width are one fact written twice; keep them equal."""
    from app.models.document import UniversityDocument

    column_dim = UniversityDocument.__table__.c.embedding.type.dim
    assert column_dim == embeddings.DIMENSIONS == 1536, (
        f"embeddings.DIMENSIONS is {embeddings.DIMENSIONS} but university_documents.embedding "
        f"is Vector({column_dim}). Writing a vector of the wrong width fails at insert; "
        f"reading one silently ranks by a distance that means nothing."
    )


def test_the_embedding_model_is_pinned():
    """Changing this constant invalidates every stored vector, so it changes deliberately.

    If this assertion is updated, every row in university_documents must be re-embedded --
    a mixed-model store returns nonsense for whichever half does not match the query.
    """
    assert embeddings.MODEL == "text-embedding-3-small"
