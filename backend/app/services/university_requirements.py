"""The universities a plan actually delivers a student to, and what each one asks of them.

This is the join that makes `program_requirements` worth collecting. The route engine
answers at the level of a country and a mechanism -- "Germany is reachable, via the
Studienkolleg" -- which is the right shape for planning and the wrong shape for acting on.
A student cannot apply to a mechanism. This module turns the plan into the named
universities that document accepting the qualification that plan ends holding.

The join key is one field, and it is the same field on both sides. `Route` is defined in
terms of the QUALIFICATION_* constants, and `ProgramRequirement.entry_qualification_accepted`
holds one of those same constants. So "which universities does this plan reach" reduces to
"which universities accept the qualification this plan produces", with no mapping table
between the two vocabularies and therefore no mapping table to fall out of step.

**A NULL column is never rendered as an absence of requirement here.** The table's own
docstring makes that binding, and this module is its first reader, so it is where the rule
either holds or is quietly lost. `unknown_fields` on every listing names the columns that
were NULL, so a missing IELTS score reaches the student as "this university's English
requirement is not recorded" and never as a silent blank that reads like "no English needed"
(ADR-0004).
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.grades import GradeCheck, check_grade
from app.models.qualifications import ProgramRequirement
from app.services.route_engine import RoutePlan
from app.domain.routes import StudentRouteProfile

# The three distinct facts an empty result can represent. As with the DP's funded
# programmes, a student must never be left to guess which one applies.
UNIS_STATUS_LISTED = "listed"
UNIS_STATUS_NONE_CURATED_FOR_COUNTRY = "no_requirements_collected_for_this_country_yet"
UNIS_STATUS_NONE_ACCEPT_QUALIFICATION = "collected_but_none_documents_this_qualification"

# Columns a student acts on, checked for NULL and reported by name. Deliberately not every
# nullable column: this is the set whose absence would change what a student does next.
REPORTED_FIELDS = (
    "language_test",
    "language_minimum_score",
    "entrance_exam",
    "entrance_exam_minimum",
    "gpa_minimum",
    "tuition_per_year",
    "application_deadline",
    "living_cost_estimate_per_year",
)


@dataclass(frozen=True)
class UniversityMatch:
    """One curated university row, with its unknowns named rather than left blank."""
    requirement: ProgramRequirement
    unknown_fields: tuple[str, ...]
    # Advisory only. A grade never changes a route's status -- see app/domain/grades.py.
    grade: GradeCheck
    checks: tuple[str, ...] = ()
    application_status: str = "needs_review"


def qualification_delivered(plan: RoutePlan, profile: StudentRouteProfile) -> str:
    """The qualification the student will be holding when they apply to the degree.

    A fold rather than an index into `hops`, so it is correct for a one-hop plan and a
    two-hop one without a length check. A hop that produces a qualification replaces what
    the student held; a hop that produces none (a direct entry route) leaves it untouched,
    which is right -- a direct route admits you *on* the qualification you walked in with.

    Worked through the case the product exists for: a school-leaver holds `attestat`, and
    the plan is AZ_PREP_YEAR then UK_BACHELOR_DIRECT. The first hop produces
    `one_year_university`; the second produces nothing. The fold returns
    `one_year_university`, which is exactly the value Manchester's and Cambridge's curated
    rows carry -- so the two UK universities that document accepting a completed first year
    are the two this plan surfaces.
    """
    held = profile.qualification_held
    for hop in plan.hops:
        if hop.produces_qualification is not None:
            held = hop.produces_qualification
    return held


def _unknown_fields(row: ProgramRequirement) -> tuple[str, ...]:
    return tuple(field for field in REPORTED_FIELDS if getattr(row, field) is None)


def _latest_intake_only(rows: list[ProgramRequirement]) -> list[ProgramRequirement]:
    """Keep one row per university and programme: the most recent intake year.

    `intake_year` is part of the table's natural key, so the same programme legitimately
    holds a row per year. Showing two of them side by side would put last year's tuition
    and last year's deadline in front of a student next to this year's, with nothing but a
    small integer distinguishing them -- which is how a stale fee gets acted on. Today
    every curated row is 2026 and this changes nothing; it is here so that the first time a
    second year is loaded, the read stays correct without anyone remembering to fix it.
    """
    newest = {}
    for row in rows:
        key = (row.country_code, row.university_name, row.program_name, row.level)
        newest[key] = max(newest.get(key, 0), row.intake_year)
    return sorted([
        row for row in rows if row.intake_year == newest[(row.country_code, row.university_name, row.program_name, row.level)]
    ], key=lambda r: (r.university_name, r.program_name, r.entry_qualification_accepted or ""))


def assess_requirement(row: ProgramRequirement, profile: Optional[StudentRouteProfile] = None,
                       student_gpa=None, student_gpa_scale=None, today=None) -> UniversityMatch:
    """Advisory checks of the recorded facts, never an admission decision.

    Language alternatives, subscores, document recognition and selection are not fully
    structured. Even passing all recorded numeric checks remains needs_review.
    """
    today = today or date.today()
    grade = check_grade(profile.gpa if profile else student_gpa,
                        profile.gpa_scale if profile else student_gpa_scale,
                        row.gpa_minimum, row.gpa_scale)
    checks = []
    status = "needs_review"
    if row.application_deadline and row.application_deadline < today:
        status = "deadline_passed"
        checks.append(f"The recorded deadline ({row.application_deadline.isoformat()}) has passed. Check the next intake.")
    if row.intake_year < today.year:
        status = "historical_intake"
        checks.append(f"These requirements describe the {row.intake_year} intake, not the current cycle.")
    if row.requirement_scope == "foundation":
        checks.append("These are foundation-entry requirements; degree progression and degree-level language requirements need separate confirmation.")
    if profile:
        if row.entry_qualification_accepted != profile.qualification_held:
            checks.append(f"This row describes entry with {row.entry_qualification_accepted or 'an unrecorded qualification'}; your current qualification differs.")
        score_fields = {"IELTS": "ielts", "TOEFL": "toefl", "SAT": "sat", "ACT": "act", "TR-YOS": "tr_yos", "TR-YÖS": "tr_yos", "TestAS": "test_as", "CSCA": "csca", "HSK": "hsk"}
        for label, minimum in ((row.language_test, row.language_minimum_score), (row.entrance_exam, row.entrance_exam_minimum)):
            if label in score_fields and minimum is not None:
                actual = getattr(profile, score_fields[label])
                if actual is None:
                    checks.append(f"{label} {minimum:g} is recorded; your {label} score is missing. Check accepted alternatives in the source.")
                elif actual < minimum:
                    checks.append(f"Your {label} {actual:g} is below the recorded {minimum:g}. Check accepted alternatives in the source.")
                else:
                    checks.append(f"Your {label} meets the recorded overall minimum; subscores, validity and exemptions still need checking.")
    if row.provenance != "human-verified":
        checks.append("The source has been collected but this row still awaits human review.")
    checks.append("A qualification match is a possible application pathway. Subject prerequisites, certificate recognition and selection remain the university's decision.")
    return UniversityMatch(row, _unknown_fields(row), grade, tuple(checks), status)


async def universities_accepting(
    session: AsyncSession,
    *,
    country_code: str,
    level: str,
    qualification: str,
    student_gpa: Optional[float] = None,
    student_gpa_scale: Optional[str] = None,
    profile: Optional[StudentRouteProfile] = None,
    language: Optional[str] = None,
) -> list[UniversityMatch]:
    """The curated universities in one country that document accepting one qualification.

    No `intake_year` filter. Pinning one here would mean a constant somewhere that goes
    stale in silence: the day the curated file moves to 2027, a hardcoded 2026 returns an
    empty list, and an empty list is indistinguishable from "no university accepts this"
    unless someone notices. `_latest_intake_only` picks the newest row per programme
    instead, which needs nothing updated to stay right.
    """
    stmt = (
        select(ProgramRequirement)
        .where(ProgramRequirement.country_code == country_code)
        .where(ProgramRequirement.level == level)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return [
        assess_requirement(row, profile, student_gpa, student_gpa_scale)
        for row in _latest_intake_only(rows)
        if row.entry_qualification_accepted == qualification
        and (language is None or (row.language_of_instruction or "").lower() == language.lower())
    ]


async def any_requirements_curated(
    session: AsyncSession, *, country_code: str, level: str
) -> bool:
    """Have we collected ANY requirements for this country at this level?

    An existence check only (`LIMIT 1`), and consulted only when
    `universities_accepting()` came back empty. It separates "we have not collected
    Poland yet" from "we have collected Germany, and none of the three German
    universities we hold documents direct entry on a completed year" -- the second is a
    finding about Germany, the first is a gap in our data, and reporting one as the other
    is exactly the confident wrongness this project refuses.
    """
    stmt = (
        select(ProgramRequirement.id)
        .where(ProgramRequirement.country_code == country_code)
        .where(ProgramRequirement.level == level)
        .limit(1)
    )
    return (await session.execute(stmt)).first() is not None


def describe_universities(
    matches: list[UniversityMatch],
    *,
    country_code: str,
    qualification: str,
    any_curated: bool,
) -> tuple[str, str]:
    """Explain what `universities_accepting()`'s result means. Returns (status, text).

    `any_curated` is read only when `matches` is empty; pass anything otherwise.
    """
    if matches:
        return UNIS_STATUS_LISTED, ""
    if not any_curated:
        return UNIS_STATUS_NONE_CURATED_FOR_COUNTRY, (
            f"We have not collected university requirements for {country_code} yet. This "
            f"is a gap in our data, not a statement that no university there accepts you. "
            f"The route itself is still open -- check the universities directly."
        )
    return UNIS_STATUS_NONE_ACCEPT_QUALIFICATION, (
        f"None of the collected {country_code} rows documents accepting '{qualification}' "
        f"for entry. Our coverage is incomplete: this is not evidence that a university "
        f"rejects this qualification. Ask its admissions office."
    )


def missing_requirement_note(unknown_fields: tuple[str, ...]) -> Optional[str]:
    """Sentence naming what this university's page did not state, or None if it stated all.

    The point of saying it out loud: a blank tuition on a page rendering a list of
    universities reads as free, and a blank language test reads as none required. Both are
    wrong, and both are wrong in the direction that costs a student an application.
    """
    if not unknown_fields:
        return None
    return (
        "Not recorded in this catalogue row: "
        + ", ".join(field.replace("_", " ") for field in unknown_fields)
        + ". Unknown here means we could not find it, never that it is not required."
    )
