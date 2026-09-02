"""
OpenAI Vector Embedding Generation Service.
Generates 1536-dimensional embeddings for text documents and user search queries.

There is deliberately no offline fallback. A previous version returned a
deterministic sha256-derived vector whenever the API key was missing or any
exception was raised. That vector is not an embedding: two near-identical
strings hash to unrelated vectors, so cosine similarity becomes noise, every
retrieval returns arbitrary documents, and nothing anywhere raises. Callers
cannot distinguish it from a real result -- which is exactly the failure mode
ADR-0004 forbids. If an embedding cannot be produced, this module raises.
"""

import os
from typing import List

MODEL = "text-embedding-3-small"
DIMENSIONS = 1536

# Values that mean "nobody configured this yet" rather than a real key --
# .env.example ships one of these, so it will be copied at some point.
_PLACEHOLDER_KEYS = {
    "",
    "your_openai_api_key_here",
    "sk-placeholder",
    "sk-proj-your_openai_api_key_here",
}


class EmbeddingUnavailableError(RuntimeError):
    """Raised when an embedding cannot be produced. Never return a substitute vector."""


def _require_api_key() -> str:
    """Return the configured OpenAI key, or raise explaining what is missing."""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if api_key.lower() in _PLACEHOLDER_KEYS:
        raise EmbeddingUnavailableError(
            "OPENAI_API_KEY is unset or still holds the .env.example placeholder. "
            "Embeddings cannot be generated. Set a real key -- do not substitute a "
            "stand-in vector, which would silently corrupt every similarity search."
        )
    return api_key


def get_embedding(text: str, model: str = MODEL) -> List[float]:
    """
    Generate a 1536-dimensional vector embedding for the input text.

    Raises EmbeddingUnavailableError if no key is configured; API and network
    errors propagate unchanged so the caller sees the real cause.
    """
    from openai import OpenAI

    client = OpenAI(api_key=_require_api_key())
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding


async def get_embedding_async(text: str, model: str = MODEL) -> List[float]:
    """
    Asynchronously generate a 1536-dimensional vector embedding for the input text.

    Raises EmbeddingUnavailableError if no key is configured; API and network
    errors propagate unchanged so the caller sees the real cause.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=_require_api_key())
    response = await client.embeddings.create(input=text, model=model)
    return response.data[0].embedding
