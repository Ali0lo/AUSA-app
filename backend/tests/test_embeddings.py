import pytest
from app.services.embeddings import generate_fallback_embedding, get_embedding, get_embedding_async


def test_generate_fallback_embedding():
    text = "Technical University of Munich (TUM) M.Sc. Informatics guidelines"
    vec = generate_fallback_embedding(text)
    assert len(vec) == 1536
    assert isinstance(vec[0], float)


def test_get_embedding_sync():
    vec = get_embedding("DAAD Master Studies Scholarship")
    assert len(vec) == 1536
    assert isinstance(vec[0], float)


@pytest.mark.asyncio
async def test_get_embedding_async():
    vec = await get_embedding_async("ADA University Computer Science")
    assert len(vec) == 1536
    assert isinstance(vec[0], float)
