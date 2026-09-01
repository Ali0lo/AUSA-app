"""The Dövlət Proqramı funding gate, modelled as a route.

The DP has preconditions (C1, and DİM 400-550 or SAT/ACT at the 75th percentile or an
international Olympiad medal), produces funded access, costs nothing in time or money, and
gates a fixed list of universities. That is the Route shape, which is why it composes with
the others: the prep year at an Azerbaijani university opens Germany AND preserves DP
eligibility, and only one engine can say both.

Neither function here reads `program_requirements`. That table is empty today -- nothing
populates it yet -- and its NULL columns mean "unknown", never "not required" (ADR-0004).
The DP's published gates below are hard-coded from dp.edu.az, not derived from that table,
so this module has nothing to get wrong by reading it; when a future task wires
program-level requirements into DP eligibility, it must treat "no row found" as unknown,
never as "no requirements", exactly as that table's docstring requires.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.routes import RouteStatus, StudentRouteProfile
from app.models.dp_catalogue import DPCatalogueEntry

# "DİM 400-550 depending on field" (dp.edu.az). The per-field table has NOT been verified,
# so the engine reports the band it checked and never a single threshold. Inventing the
# midpoint would be a number that looks measured.
DIM_BAND_LOW = 400.0
DIM_BAND_HIGH = 550.0
BAND_DESCRIPTION = f"DİM {DIM_BAND_LOW:.0f}-{DIM_BAND_HIGH:.0f}, the exact bar depending on field"

# spec §2.2's eligibility table -- the block marked "verified on dp.edu.az" -- names the
# DİM/SAT/Olympiad academic gate on a row labelled "Bachelor", separate from its "Language",
# "Age", "Covers" and "Levels" rows. §5.2's Tier-1 summary table puts the same gate against
# "bachelor · master · PhD" without qualification, so THE SPEC CONTRADICTS ITSELF here; §11
# records it as an open question for a person to settle against dp.edu.az. §2.2 most likely
# governs (verified, and more granular -- §5.2 appears to have merged the "Levels" row, what
# the DP covers, with the "Bachelor" row, what the gate requires), but that is a reading and
# not a check. So above bachelor the gate is UNKNOWN, which is not "no gate applies": per
# ADR-0004 an unknown must never read as permission, and it is reported as an unconfirmed
# gate -- never skipped as though clearing it were optional, and never answered with the
# bachelor band it did not check. That is safe under either reading of the conflict.
NO_ACADEMIC_GATE_PUBLISHED = (
    "no academic band is published for this level here -- only the bachelor row of the "
    "DP's eligibility table names DİM/SAT/Olympiad thresholds; only the language "
    "requirement above is checked"
)

ACCEPTED_LANGUAGE_LEVELS = ("C1", "C2")

# The three distinct facts an empty `funded_programmes` result can represent. A student must
# never be left to guess which one applies (see `describe_funded_programmes`).
FUNDED_STATUS_LISTED = "listed"
FUNDED_STATUS_NONE_AT_LEVEL = "no_dp_programmes_at_this_level"
FUNDED_STATUS_UNREACHABLE = "dp_programmes_exist_but_not_in_a_reachable_country"
FUNDED_STATUS_NO_ROUTES_REACHABLE = "no_route_reaches_any_country_at_this_level"


@dataclass(frozen=True)
class DPEligibility:
    status: RouteStatus
    band_checked: str
    gates_met: tuple[str, ...]
    gates_missing: tuple[str, ...]


def assess_dp_eligibility(profile: StudentRouteProfile) -> DPEligibility:
    """Check the published gates. Clearing them is 'possibly eligible', never an award.

    The DP funds roughly 400 places a year against a much larger pool. What is checkable
    is whether the student clears the stated gates; the selection that follows is a
    committee decision no dataset in this project models.

    Level is part of the key here, not a filter: the DİM/SAT/Olympiad academic gate is
    published for bachelor level only (spec §2.2). At any other level (master's today;
    PhD is out of product scope entirely) that gate is UNKNOWN, so it is reported as an
    unconfirmed requirement rather than either invented or silently skipped -- a master's
    applicant is never told they are missing a DİM score they have no reason to hold, and
    is never read as eligible on the strength of an academic gate nobody checked.
    """
    met: list[str] = []
    missing: list[str] = []

    if profile.language_certificate_level in ACCEPTED_LANGUAGE_LEVELS:
        met.append(f"Language certificate at {profile.language_certificate_level}")
    else:
        missing.append("A language certificate at C1 or above is required")

    if profile.level_sought != "bachelor":
        missing.append(
            f"The Dövlət Proqramı's academic gate for {profile.level_sought} level is not "
            "established in our data; only the language requirement above is checked here"
        )
        band_checked = NO_ACADEMIC_GATE_PUBLISHED
    else:
        band_checked = BAND_DESCRIPTION
        # Three alternative academic gates. Any one of them satisfies this half.
        if profile.has_international_olympiad_medal:
            met.append("International Olympiad medal")
        elif profile.dim_score is not None and profile.dim_score >= DIM_BAND_HIGH:
            met.append(f"DİM {profile.dim_score:.0f} clears the whole {BAND_DESCRIPTION}")
        elif profile.dim_score is not None and profile.dim_score >= DIM_BAND_LOW:
            met.append(f"DİM {profile.dim_score:.0f} is inside the band")
            missing.append(
                f"DİM {profile.dim_score:.0f} clears some fields but not all: the requirement is "
                f"{BAND_DESCRIPTION}, and the bar for your field has not been confirmed here"
            )
        elif profile.sat is not None:
            met.append(f"SAT {profile.sat} offered against the 75th-percentile alternative")
        else:
            missing.append(
                f"One of: {BAND_DESCRIPTION}; SAT/ACT at the 75th percentile; "
                "or an international Olympiad medal"
            )

    status = RouteStatus.OPEN if not missing else RouteStatus.UNLOCKABLE
    return DPEligibility(
        status=status,
        band_checked=band_checked,
        gates_met=tuple(met),
        gates_missing=tuple(missing),
    )


async def funded_programmes(
    session: AsyncSession,
    level: str,
    country_codes: tuple[str, ...],
) -> list[DPCatalogueEntry]:
    """The funded programmes for one level in the given countries.

    An empty list is a real answer -- the state funds zero bachelor programmes in the USA
    and Poland -- and is returned as one.

    `country_codes` is expected to come from the route engine's own country codes (TR, DE,
    GB, US, PL, CN, AZ), which are never NULL. SQL's `IN` never matches NULL, so a catalogue
    row from one of the 27 out-of-scope countries (`country_code IS NULL`) is excluded here
    as a side effect of that -- not filtered as "unavailable". Those rows are outside this
    product's six-country scope entirely; the route engine never proposes a plan that
    reaches them, so this function is never asked about them, and never reports on them one
    way or the other.
    """
    stmt = (
        select(DPCatalogueEntry)
        .where(DPCatalogueEntry.level == level)
        .where(DPCatalogueEntry.country_code.in_(country_codes))
        .order_by(DPCatalogueEntry.country_code, DPCatalogueEntry.university_name)
    )
    return list((await session.execute(stmt)).scalars().all())


async def any_funded_programmes_at_level(session: AsyncSession, level: str) -> bool:
    """Does the DP fund ANYTHING at this level, in any country (including the 27
    out-of-scope ones with `country_code IS NULL`)?

    An existence check only -- `LIMIT 1`, no `country_codes` filter, never a full fetch --
    used solely to tell "the DP funds zero programmes at this level" (a real answer) apart
    from "it funds some, just not anywhere this profile's routes currently reach" (a
    different answer) when `funded_programmes()` comes back empty. See
    `describe_funded_programmes`.
    """
    stmt = select(DPCatalogueEntry.id).where(DPCatalogueEntry.level == level).limit(1)
    return (await session.execute(stmt)).first() is not None


def describe_funded_programmes(
    programmes: list[DPCatalogueEntry],
    reachable: tuple[str, ...],
    any_at_level: bool,
) -> tuple[str, str]:
    """Explain what `funded_programmes()`'s result actually means. Returns (status, text).

    An empty list conflates three different facts if left unexplained, and a student must
    never be left to guess which one applies:

    (a) the DP funds zero programmes at this level at all -- a real answer, e.g. the USA's
        zero DP bachelor places;
    (b) the DP funds programmes at this level, but none of them are in a country this
        profile's routes can currently reach;
    (c) this profile's routes do not reach any country at all at this level, so no country
        was ever queried.

    Showing programmes from a country the student cannot enter would be the wrong fix in
    the other direction -- it would suggest an entry path they do not have -- so this names
    the reason instead of widening the list. `any_at_level` is only consulted when
    `programmes` is empty and `reachable` is non-empty (case (a) vs (b)); pass anything for
    it otherwise, it is not read.
    """
    if programmes:
        return FUNDED_STATUS_LISTED, ""
    if not reachable:
        return FUNDED_STATUS_NO_ROUTES_REACHABLE, (
            "Your profile does not currently reach any country in our route list at this "
            "level, so no funded programmes could be checked. This is not a statement "
            "that the Dövlət Proqramı funds nothing at this level -- only that none of "
            "your open or unlockable routes lead to a country it funds."
        )
    if not any_at_level:
        return FUNDED_STATUS_NONE_AT_LEVEL, (
            "The Dövlət Proqramı funds zero programmes at this level. That is a real "
            "answer, not a gap in our data."
        )
    return FUNDED_STATUS_UNREACHABLE, (
        "The Dövlət Proqramı funds programmes at this level, but not in a country your "
        "current profile can reach. This is not a statement that you are ineligible for "
        "the programme overall -- only that none of its funded placements fall within the "
        "countries your qualifications currently open."
    )
