from sqlalchemy import Boolean, Column, Date, Float, Integer, String, Text, func
from app.core.database import Base


class Program(Base):
    """SQLAlchemy ORM model for storing university program requirements."""
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    university_name = Column(String(200), nullable=False)
    program_name = Column(String(300), nullable=False)
    degree_level = Column(String(20), nullable=True)
    field = Column(String(100), nullable=True)
    country = Column(String(50), nullable=True)
    min_gpa = Column(Float, nullable=True)
    min_ielts = Column(Float, nullable=True)
    min_toefl = Column(Integer, nullable=True)
    tuition_fee = Column(Float, nullable=True)
    currency = Column(String(10), default="EUR")
    deadline = Column(Date, nullable=True)
    requirements_text = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    last_updated = Column(Date, server_default=func.current_date())
    is_active = Column(Boolean, default=True)
