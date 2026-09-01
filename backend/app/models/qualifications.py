from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, func,
)
from app.core.database import Base

# The qualification a student holds. This is the field that decides whether a route is
# open: an attestat opens Turkey and Poland directly but opens only the Studienkolleg in
# Germany, while a completed year of university study opens Germany and the UK both.
QUALIFICATION_ATTESTAT = "attestat"
QUALIFICATION_ONE_YEAR_UNIVERSITY = "one_year_university"
QUALIFICATION_A_LEVEL = "a_level"
QUALIFICATION_IB = "ib"
QUALIFICATION_FOUNDATION_YEAR = "foundation_year"
QUALIFICATION_FESTSTELLUNGSPRUEFUNG = "feststellungspruefung"
QUALIFICATION_BACHELOR_DEGREE = "bachelor_degree"


class StudentQualification(Base):
    """What a student holds and what they are aiming at. One row per student per level.

    Separate from `students` because a person can hold one profile and ask two different
    questions -- "where can I go for a bachelor's now" and "where could I go for a master's
    after that" -- and the answers share no requirements.
    """
    __tablename__ = "student_qualifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)

    # 'bachelor' | 'master'. Part of the key.
    level_sought = Column(String(20), nullable=False)
    # One of the QUALIFICATION_* constants above.
    qualification_held = Column(String(50), nullable=False)

    # Every score is nullable and stays nullable. "Did not sit the exam" and "scored zero"
    # are different facts, and a default would erase the difference.
    dim_score = Column(Float, nullable=True)
    ielts = Column(Float, nullable=True)
    toefl = Column(Integer, nullable=True)
    sat = Column(Integer, nullable=True)
    act = Column(Integer, nullable=True)
    # One column per exam. Sharing one would silently credit a student with an exam they
    # never sat -- an SAT score standing in for TestAS turns a blocked route into an open one.
    tr_yos = Column(Float, nullable=True)
    test_as = Column(Float, nullable=True)
    csca = Column(Float, nullable=True)
    hsk = Column(Integer, nullable=True)
    # CEFR level of the strongest language certificate held: 'B2', 'C1', 'C2'.
    language_certificate_level = Column(String(10), nullable=True)
    has_international_olympiad_medal = Column(Boolean, nullable=True)

    budget_azn_per_year = Column(Float, nullable=True)
    field_of_interest = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "level_sought", name="uq_student_qualification_level"),
    )


class ProgramRequirement(Base):
    """What one university asks of an international applicant, for one programme and level.

    The schema is spec §5.1 and is fixed before collection rather than discovered during
    it. Every row carries where it came from and when it was read.

    **A NULL means the requirement is unknown. It never means "not required."** Nothing
    may read a NULL here as permission: an unknown requirement must never let a route
    read OPEN, because "we could not find out" and "there is no such requirement" are
    different facts and conflating them produces confidently wrong advice (ADR-0004).
    The boolean columns can already carry the distinction -- NULL unknown, False known
    to be absent -- but the string and numeric columns cannot, and today nothing writes
    a confirmed absence into them. When curation needs to record one, it gets its own
    representation then, added by someone holding a real row to put in it; it must not
    be written as a NULL.
    """
    __tablename__ = "program_requirements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    university_name = Column(String(300), nullable=False, index=True)
    program_name = Column(String(500), nullable=False)
    # 'bachelor' | 'master'. Part of the key: the same university publishes different
    # requirements, fees and deadlines per level.
    level = Column(String(20), nullable=False, index=True)
    intake_year = Column(Integer, nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)

    # The field that decides whether a route is open. One of the QUALIFICATION_* constants.
    entry_qualification_accepted = Column(String(50), nullable=True)
    foundation_required = Column(Boolean, nullable=True)
    foundation_providers = Column(Text, nullable=True)

    language_test = Column(String(30), nullable=True)
    language_minimum_score = Column(Float, nullable=True)
    language_of_instruction = Column(String(50), nullable=True)

    entrance_exam = Column(String(30), nullable=True)
    entrance_exam_minimum = Column(Float, nullable=True)

    gpa_minimum = Column(Float, nullable=True)
    # The scale the minimum is expressed in -- '4.0', '5.0', '100'. A GPA without its
    # scale is not a number, and mixing scales silently is how a 3.0 becomes a rejection.
    gpa_scale = Column(String(10), nullable=True)

    # For INTERNATIONAL students. The domestic or EU figure is the wrong one and is
    # usually the more prominent number on the page (spec §5.1).
    tuition_per_year = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    living_cost_estimate_per_year = Column(Float, nullable=True)
    application_fee = Column(Float, nullable=True)

    application_deadline = Column(Date, nullable=True)
    application_portal = Column(String(60), nullable=True)
    documents_required = Column(Text, nullable=True)

    # 'seed' | 'claude-extracted' | 'human-verified' (ADR-0007 §5).
    # server_default as well as default: the ORM fills this before the row reaches the
    # database, so a model-only default leaves a raw-SQL insert with no value at all
    # while the SQLite suite still passes. The migration declares the same server_default.
    provenance = Column(
        String(30), nullable=False, default="claude-extracted",
        server_default="claude-extracted",
    )
    source_url = Column(Text, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=False)
    # Shown to the student. Honesty beats false confidence (spec §5.4).
    last_checked = Column(DateTime(timezone=True), nullable=True)
    # A fingerprint of the page this was read from, so a re-fetch can skip an unchanged
    # page without re-extracting it (spec §5.4).
    source_text_hash = Column(String(64), nullable=True)
    verified_by = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "university_name", "program_name", "level", "intake_year",
            name="uq_program_requirement_entry",
        ),
    )
