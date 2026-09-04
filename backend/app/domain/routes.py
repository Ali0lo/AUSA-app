"""The route domain: pure data and no I/O.

A Route is `qualification held -> entry mechanism -> country, at a level`. It is the
primary object in the product, because for a school-leaver the binding question is not
"where do I qualify" but "which paths are even open to me" (spec §4.1).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RouteStatus(str, Enum):
    # Every precondition met.
    OPEN = "open"
    # Met except for a named, obtainable set -- an exam not yet sat, a score not yet high
    # enough. The student can act on this within a cycle.
    UNLOCKABLE = "unlockable"
    # A precondition that cannot be obtained this cycle: the qualification itself is wrong.
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ExamRequirement:
    """One exam or score bar. `profile_field` names the StudentRouteProfile attribute."""
    name: str
    minimum: Optional[float]
    profile_field: str


@dataclass(frozen=True)
class Route:
    key: str
    country_code: str
    # 'bachelor' | 'master'. Part of the key, not a filter: Germany and the UK are blocked
    # to a school-leaver but open to a bachelor holder (spec §4.1).
    level: str
    mechanism: str
    # Any one of these qualifications satisfies the route.
    requires_qualification: tuple[str, ...]
    # What holding this route's completion gives you, for two-hop composition. None for a
    # route that terminates in a degree rather than in another qualification.
    produces_qualification: Optional[str]
    exams: tuple[ExamRequirement, ...]
    time_cost_months: int
    money_cost_azn: tuple[int, int]
    # Where this was read. Every route carries one; this is the highest-value data in the
    # product and none of it is scraped.
    citation: str
    # 'seed' until a person has opened the citation and confirmed it.
    provenance: str = "seed"


@dataclass(frozen=True)
class StudentRouteProfile:
    """What the engine needs from student_qualifications. Every score may be None."""
    level_sought: str
    qualification_held: str
    dim_score: Optional[float] = None
    ielts: Optional[float] = None
    toefl: Optional[int] = None
    sat: Optional[int] = None
    act: Optional[int] = None
    # One field per exam, never a shared one. Routing TestAS and TR-YÖS at the `sat` field
    # would mean a student who sat the SAT is silently credited with an exam they have
    # never taken -- and the route would come back OPEN when it is not.
    tr_yos: Optional[float] = None
    test_as: Optional[float] = None
    csca: Optional[float] = None
    hsk: Optional[int] = None
    language_certificate_level: Optional[str] = None
    has_international_olympiad_medal: Optional[bool] = None
    budget_azn_per_year: Optional[float] = None
    # The grade average OF THE QUALIFICATION NAMED IN `qualification_held` -- the attestat
    # for a school-leaver, the completed bachelor's degree for a master's applicant. One
    # field pair serves both levels because `qualification_held` already says which
    # qualification it belongs to, and master's admission abroad routinely turns on the
    # bachelor GPA against the same kind of published minimum.
    #
    # `gpa_scale` travels with it and is not optional in spirit: a grade without its scale
    # is not a number (see app/domain/grades.py). A grade supplied without one is reported
    # as not comparable rather than compared against an assumed scale -- assuming 4.0 is
    # what makes an Azerbaijani 4.5 out of 5 look like an impossible value.
    gpa: Optional[float] = None
    gpa_scale: Optional[str] = None


@dataclass(frozen=True)
class RouteAssessment:
    route: Route
    status: RouteStatus
    # Human-readable, one entry per unmet requirement. Empty when OPEN.
    missing: tuple[str, ...]
