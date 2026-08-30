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
