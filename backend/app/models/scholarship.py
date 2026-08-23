from sqlalchemy import Column, Date, Float, Integer, String, Text, func
from app.core.database import Base


class Scholarship(Base):
    """SQLAlchemy ORM model for storing scholarship opportunities."""
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    provider = Column(String(200), nullable=True)
    country = Column(String(50), nullable=True)
    degree_level = Column(String(20), nullable=True)
    min_gpa = Column(Float, nullable=True)
    min_ielts = Column(Float, nullable=True)
    eligibility_text = Column(Text, nullable=True)
    amount = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True)
    source_url = Column(Text, nullable=True)
    last_updated = Column(Date, server_default=func.current_date())
