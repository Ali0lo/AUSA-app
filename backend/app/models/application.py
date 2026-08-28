from sqlalchemy import Column, Date, DateTime, Integer, String, Text, func
from app.core.database import Base


class StudentApplication(Base):
    """SQLAlchemy ORM model for tracking student program applications and stage lifecycle."""
    __tablename__ = "student_applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(String(100), index=True, nullable=False, default="std_demo")
    program_id = Column(Integer, nullable=True)
    university_name = Column(String(200), nullable=False)
    program_name = Column(String(300), nullable=False)
    degree_level = Column(String(20), nullable=True)
    country = Column(String(50), nullable=True)
    deadline = Column(Date, nullable=True)
    stage = Column(String(50), nullable=False, default="shortlisted")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

