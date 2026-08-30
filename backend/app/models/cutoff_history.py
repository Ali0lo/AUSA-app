from sqlalchemy import Boolean, Column, Float, Index, Integer, String, Text
from app.core.database import Base


class ProgramCutoffHistory(Base):
    """One published admission cutoff, for one programme, for one intake year.

    This is collected source data, not a prediction. `cutoff_value` is the score of the
    last admitted applicant where the source publishes that (Azerbaijan's keçid balı,
    Turkey's final_score_012); the unit differs per country, so `cutoff_unit` and
    `lower_is_better` must be read before comparing any two rows.
    """

    __tablename__ = "program_cutoff_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    country = Column(String(2), nullable=False, index=True)
    source_program_code = Column(String(300), nullable=False, index=True)
    # sec.az publishes rows that are byte-identical except for their scores. They are
    # distinct competitions, so they are kept apart rather than merged -- merging would
    # interleave unrelated series and corrupt every lag feature built from them.
    variant_index = Column(Integer, nullable=True)
    variant_discriminator_known = Column(Boolean, nullable=True)

    intake_year = Column(Integer, nullable=False, index=True)
    cutoff_value = Column(Float, nullable=False)
    # e.g. "dim_score_700", "yks_score_012", "sat_total_1600". Units are NOT comparable
    # across countries; ADR-0002 keeps one model per country for this reason.
    cutoff_unit = Column(String(50), nullable=False)
    # True where the published figure is a rank (lower is better), False where it is a score.
    lower_is_better = Column(Boolean, nullable=False, default=False)

    university_name = Column(String(300), nullable=False)
    department_name = Column(String(300), nullable=True)
    score_type = Column(String(100), nullable=True)
    scholarship_type = Column(String(100), nullable=True)
    is_undergraduate = Column(Boolean, nullable=True)

    source_url = Column(Text, nullable=True)
    # Stays NULL until a person opens the source and confirms the row (ADR-0004 rule 2).
    verified_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index(
            "ix_cutoff_history_series",
            "country",
            "source_program_code",
            "variant_index",
            "intake_year",
        ),
    )
