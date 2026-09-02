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
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
)


@dataclass(frozen=True)
class UniversityMatch:
    """One curated university row, with its unknowns named rather than left blank."""
    requirement: ProgramRequirement
    unknown_fields: tuple[str, ...]


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
    newest: dict[tuple[str, str], ProgramRequirement] = {}
    for row in rows:
        key = (row.university_name, row.program_name)
        if key not in newest or row.intake_year > newest[key].intake_year:
            newest[key] = row
    return sorted(newest.values(), key=lambda r: (r.university_name, r.program_name))


async def universities_accepting(
    session: AsyncSession,
    *,
    country_code: str,
    level: str,
    qualification: str,
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
        .where(ProgramRequirement.entry_qualification_accepted == qualification)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return [
        UniversityMatch(requirement=row, unknown_fields=_unknown_fields(row))
        for row in _latest_intake_only(rows)
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
        f"None of the {country_code} universities we have collected documents accepting "
        f"'{qualification}' for entry. That is what their own admissions pages state, so "
        f"it is a real finding rather than a gap -- but we hold only a few universities "
        f"per country, and others may accept it."
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
        "Not stated on the source page, so not recorded: "
        + ", ".join(field.replace("_", " ") for field in unknown_fields)
        + ". Unknown here means we could not find it, never that it is not required."
    )
