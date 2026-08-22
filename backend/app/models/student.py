from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func
from app.core.database import Base


class Student(Base):
    """SQLAlchemy ORM model for storing student academic profile."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gpa = Column(Float, nullable=True)
    ielts = Column(Float, nullable=True)
    toefl = Column(Integer, nullable=True)
    degree_level = Column(String(20), nullable=True)
    field_of_study = Column(String(100), nullable=True)
    country = Column(String(50), nullable=True)
    research_experience = Column(Boolean, default=False)
    projects = Column(Text, nullable=True)
    budget = Column(String(50), nullable=True)
    goals = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
