from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import UniversityDocument


async def get_query_embedding(query: str) -> List[float]:
    """
    Generate a 1536-dimensional vector embedding for the search query.
    Uses OpenAIEmbeddings if available, with fallback for offline environments.
    """
    try:
        from langchain_openai import OpenAIEmbeddings
        embeddings_model = OpenAIEmbeddings()
        return await embeddings_model.aembed_query(query)
    except Exception:
        # Fallback 1536-dim vector for testing and offline environments
        return [0.0] * 1536


async def retrieve_relevant_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None
) -> List[UniversityDocument]:
    """
    Perform a cosine similarity vector search against the UniversityDocument table using SQLAlchemy and pgvector.
    
    Args:
        db: SQLAlchemy AsyncSession instance.
        query: User search query string.
        top_k: Number of top relevant document chunks to retrieve (default: 5).
        filters: Optional filter dictionary (e.g. {"university_id": 1, "program_id": 5}).
        
    Returns:
        List of UniversityDocument instances ordered by cosine similarity.
    """
    # 1. Embed user query
    query_vector = await get_query_embedding(query)

    # 2. Build SQLAlchemy query using pgvector cosine distance
    stmt = select(UniversityDocument)

    # Apply metadata filtering criteria
    if filters:
        if "university_id" in filters and filters["university_id"] is not None:
            stmt = stmt.where(UniversityDocument.university_id == filters["university_id"])
        if "program_id" in filters and filters["program_id"] is not None:
            stmt = stmt.where(UniversityDocument.program_id == filters["program_id"])

    # Order by pgvector cosine_distance (<-> operator) and limit results
    stmt = stmt.order_by(UniversityDocument.embedding.cosine_distance(query_vector)).limit(top_k)

    # 3. Execute database query
    result = await db.execute(stmt)
    documents = result.scalars().all()

    return list(documents)
