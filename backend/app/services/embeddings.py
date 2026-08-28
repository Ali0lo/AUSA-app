"""
OpenAI Vector Embedding Generation Service.
Generates 1536-dimensional embeddings for text documents and user search queries.
Uses OpenAI text-embedding-3-small API with a deterministic fallback for offline/test environments.
"""

import hashlib
import math
import os
from typing import List


def generate_fallback_embedding(text: str, dim: int = 1536) -> List[float]:
    """
    Generate a deterministic, unit-normalized float vector of length `dim` based on text hash.
    Used for offline testing or when OpenAI API key is unavailable.
    """
    seed_hash = hashlib.sha256(text.encode("utf-8")).digest()
    vec = []
    for i in range(dim):
        byte_val = seed_hash[i % len(seed_hash)]
        val = math.sin((i + 1) * (byte_val + 1))
        vec.append(val)

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        return [round(v / norm, 6) for v in vec]
    return [0.0] * dim


def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate a 1536-dimensional vector embedding for the input text.
    Calls OpenAI API using OPENAI_API_KEY environment variable.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() in ["", "your_openai_api_key_here", "sk-placeholder"]:
        return generate_fallback_embedding(text)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key.strip())
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except Exception:
        return generate_fallback_embedding(text)


async def get_embedding_async(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Asynchronously generate a 1536-dimensional vector embedding for the input text.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() in ["", "your_openai_api_key_here", "sk-placeholder"]:
        return generate_fallback_embedding(text)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key.strip())
        response = await client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except Exception:
        return generate_fallback_embedding(text)
