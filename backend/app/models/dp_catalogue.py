from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from app.core.database import Base


class DPCatalogueEntry(Base):
    """One funded programme from the Dövlət Proqramı list.

    The state publishes exactly which universities and programmes it will pay for, per
    level, as open data. This table is that list and nothing else -- no requirements, no
    fees. Those live in program_requirements and join to this on (university, programme).
    """

    __tablename__ = "dp_catalogue"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # 'bachelor' | 'master'. Part of the key, never a filter: the state publishes two
    # separate lists with different countries in them -- the USA and Poland have zero
    # bachelor programmes against 289 and 8 master's.
    level = Column(String(20), nullable=False, index=True)
    # The country exactly as the source names it, in Azerbaijani. Kept verbatim so a row
    # can always be traced back to its line in the CSV.
    country_source = Column(String(120), nullable=False)
    # ISO-3166 alpha-2, and only for the six countries in scope. NULL for the other 27:
    # we have not checked how the ministry spells them and will not guess.
    country_code = Column(String(2), nullable=True, index=True)
    university_name = Column(String(300), nullable=False, index=True)
    program_name = Column(String(500), nullable=False)
    intake_year = Column(Integer, nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=False)
    # Stays NULL. Only a person who has opened the source may set it (ADR-0004 rule 2).
    verified_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "level", "country_source", "university_name", "program_name", "intake_year",
            name="uq_dp_catalogue_entry",
        ),
    )
