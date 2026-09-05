from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func
from app.core.database import Base


class Student(Base):
    """SQLAlchemy ORM model for storing student academic profile and authentication credentials."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    gpa = Column(Float, nullable=True)
    # Stored as a pair with `gpa`, never alone: an attestat 4.5 is excellent out of 5 and
    # impossible out of 4, and nothing but this column tells them apart. NULL means the
    # scale is unknown, which `domain.grades.check_grade` reports as not-comparable rather
    # than guessing one (ADR-0004).
    gpa_scale = Column(String(10), nullable=True)
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
