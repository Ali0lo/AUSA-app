"""The funding domain: what a scholarship's gate IS. Pure data, no I/O.

A funding programme is a route (spec §5.2), so this file is deliberately shaped like
`domain/routes.py` -- a frozen record carrying preconditions and a citation. What differs
is the preconditions themselves, and that difference is the whole reason this module
exists: **several of the gates that decide a scholarship have nothing to do with academic
merit.** SOCAR's is employment. Türkiye Bursları' is age. Chevening's is 2,800 documented
hours of work. Banach's is field of study. None of those appear on the award's marketing
page, and every one of them is checkable from a profile.

Until now this product modelled exactly one funder -- the Dövlət Proqramı -- because the DP
was the only one with a downloadable official catalogue. That is data-availability bias, not
a product decision: the general research brief's own advice is that a school-leaver should
prioritise Türkiye Bursları or the CSC over the DP, because the DP caps bachelor at 25% of
its quota. We had built the instrument the research says undergraduates should skip.

FOUR OUTCOMES, NOT THREE. A gate is met, missing, blocked, or UNKNOWN, and the fourth is
the one that matters. `GATE_UNKNOWN` means we could not check it -- the student did not give
us their age, or our two sources contradict each other. An unknown gate never contributes to
OPEN (see `services/scholarship_eligibility.py`), because ADR-0004's sharpest form is that
an unknown must never read as permission. A scholarship whose age gate we could not check is
reported as unlockable-pending-a-fact, never as one the student clears.

THE DÖVLƏT PROQRAMI IS NOT IN THIS CATALOGUE, deliberately. It has its own module
(`services/dp_eligibility.py`) with gates read from its own regulation, a funded-programme
catalogue of 4,121 rows, and a quota split this file has no way to express. Listing it here
too would create a second source of truth for the same award, and the two would diverge on
the first correction. The API returns both alongside each other; only one of them scores the
DP.
"""

from dataclasses import dataclass, field
from typing import Optional, Union

# The four things that can be true of one gate. `GATE_UNKNOWN` is not a soft `GATE_MET`:
# it is the outcome that keeps a fact we do not have from being read as a fact in the
# student's favour.
GATE_MET = "met"
# Not met, but obtainable -- sit the test, accrue the hours, get the certificate.
GATE_MISSING = "missing"
# Not met and not obtainable this cycle. Age limits and employment gates land here.
GATE_BLOCKED = "blocked"
# We could not check it at all. Never permission.
GATE_UNKNOWN = "unknown"

# Tier 1 is the Azerbaijani state, tier 2 a destination government, tier 3 the university
# itself (spec §5.2). The tier is not decoration: it says who owns the gate, and therefore
# who a student must satisfy and where an appeal would even go.
TIER_AZERBAIJANI_STATE = 1
TIER_DESTINATION_GOVERNMENT = 2
TIER_UNIVERSITY = 3


@dataclass(frozen=True)
class GateResult:
    outcome: str
    # Always written to be read by the student, not by a developer. A gate that says only
    # "age" tells them nothing; one that says "you are 22 and this award requires under 21
    # at bachelor level" tells them to stop looking at it.
    text: str


@dataclass(frozen=True)
class LevelGate:
    """The award exists only at these levels.

    The single highest-value gate in the catalogue: seven of the ten instruments are
    master's-only and only two reach bachelor, which means the honest answer to a
    school-leaver is that very few scholarships exist for them at all. That is a real
    finding (spec §2.3) and the product should say it rather than pad a list.
    """
    levels: tuple[str, ...]


@dataclass(frozen=True)
class AgeGate:
    """You must be UNDER `maximum_age` at application, at the levels named.

    Level-specific overrides apply where the source publishes different thresholds.
    Unlisted levels stay unknown instead of silently having no limit.
    """
    maximum_age: int
    applies_to_levels: tuple[str, ...]
    unverified_at_other_levels: str
    maximum_age_by_level: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class EmploymentGate:
    """Employment by a named organisation. SOCAR's programme is closed to everyone else.

    Nothing academic can open this. A student with a perfect record who does not work for
    the SOCAR group is not "competitive but unlikely" -- they are ineligible, and telling
    them so costs them nothing and saves them an application.
    """
    employer: str


@dataclass(frozen=True)
class WorkExperienceGate:
    """Documented professional hours. Chevening publishes 2,800, which is roughly two years.

    Missing rather than blocked: hours accrue. A 23-year-old short of the bar is being told
    when to apply, not that they never can.
    """
    minimum_hours: int
    description: str


@dataclass(frozen=True)
class LanguageGate:
    """A language bar the award sets itself, distinct from the university's own.

    Any one of the three satisfies it, which is why they sit in one gate rather than three.
    """
    minimum_certificate_level: str
    ielts: float
    toefl: int


@dataclass(frozen=True)
class UnresolvedGate:
    """A gate we know exists and cannot check, because our own sources contradict.

    This exists so a real requirement is never silently dropped for being inconvenient. It
    always returns UNKNOWN, which means a scholarship carrying one can never be reported
    OPEN -- correct, since we cannot say the student clears a bar we cannot state.
    """
    summary: str


Gate = Union[
    LevelGate,
    AgeGate,
    EmploymentGate,
    WorkExperienceGate,
    LanguageGate,
    UnresolvedGate,
]


@dataclass(frozen=True)
class Scholarship:
    key: str
    name: str
    provider: str
    tier: int
    # The country whose study this funds, as a route country code. None means the award is
    # not tied to one country -- Erasmus Mundus consortia span several. Used to check the
    # student can actually reach the place the money spends.
    country_code: Optional[str]
    # What it pays for, in words. Never a number we have not read: "full tuition and a
    # stipend" is what the source says; inventing an AZN figure would read as measured.
    coverage: str
    gates: tuple[Gate, ...]
    citation: str
    # What accepting it commits the student to. The DP's five-year return service is the
    # best-known example and the thing students are least often told; Chevening and
    # Fulbright carry their own. None means no obligation is RECORDED, never that none exists.
    obligation: Optional[str] = None
    # When the cycle runs, where we have read it. Same rule: None is "not recorded".
    window: Optional[str] = None
    # False means the award funds domestic study only. Listed deliberately rather than
    # omitted -- Prezident Təqaüdü is the most prestigious award in the country and students
    # will ask about it, so the product answers rather than staying silent.
    funds_study_abroad: bool = True
    # 'research-brief' is one rung below 'claude-extracted': taken from a Deep Research brief
    # whose primary pages this project has not opened. Nothing here is verified by loading.
    provenance: str = "research-brief"


@dataclass(frozen=True)
class ScholarshipAssessment:
    scholarship: Scholarship
    # OPEN / UNLOCKABLE / BLOCKED, the same three-valued vocabulary routes use.
    status: str
    gates_met: tuple[str, ...] = field(default_factory=tuple)
    gates_missing: tuple[str, ...] = field(default_factory=tuple)
    gates_blocked: tuple[str, ...] = field(default_factory=tuple)
    # Reported separately from `gates_missing` because the two ask different things of the
    # student: a missing gate is work to do, an unknown gate is a fact to tell us.
    gates_unknown: tuple[str, ...] = field(default_factory=tuple)
