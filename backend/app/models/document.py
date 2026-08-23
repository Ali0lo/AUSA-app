from sqlalchemy import Column, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class UniversityDocument(Base):
    """SQLAlchemy ORM model for storing university guideline document text chunks and vector embeddings."""
    __tablename__ = "university_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    university_id = Column(Integer, nullable=True, index=True)
    program_id = Column(Integer, nullable=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    doc_metadata = Column("metadata", JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
