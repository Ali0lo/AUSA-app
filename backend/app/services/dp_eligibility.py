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

ACCEPTED_LANGUAGE_LEVELS = ("C1", "C2")


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
    """
    met: list[str] = []
    missing: list[str] = []

    if profile.language_certificate_level in ACCEPTED_LANGUAGE_LEVELS:
        met.append(f"Language certificate at {profile.language_certificate_level}")
    else:
        missing.append("A language certificate at C1 or above is required")

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
        band_checked=BAND_DESCRIPTION,
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
