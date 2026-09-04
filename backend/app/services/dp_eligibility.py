"""The Dövlət Proqramı funding gate, modelled as a route.

The DP has preconditions, produces funded access, costs nothing in time or money, and gates
a fixed list of universities. That is the Route shape, which is why it composes with the
others: the prep year at an Azerbaijani university opens Germany AND preserves DP
eligibility, and only one engine can say both.

PROVENANCE OF THE GATES BELOW. Corrected on 2026-09-04 against a Deep Research brief that
quotes the DP's own regulation in Azerbaijani and cites dp.edu.az, edu.gov.az and
e-qanun.az. Those primary pages have NOT been opened by this project -- the brief has. So
every figure here is `research-brief` provenance, one rung below `claude-extracted`: better
evidenced than the spec text it replaces (which it contradicts in three places, see below),
and still not a primary read. `DP_SOURCES` names the pages a person must open to promote
any of this to verified. Nothing here is treated as verified by having been loaded.

WHAT THE BRIEF CORRECTED, and why each mattered:

1. The DİM "band" was never a band. spec §2.2 read "DİM 400-550 depending on field" as a
   continuum, so a 470 came back "inside the band, clears some fields but not all". The
   regulation is two discrete thresholds keyed on the applicant's ixtisas qrupu: at least
   400 for Group 1, at least 550 for every other field. A 470 is not partly qualifying --
   it clears Group 1 outright and fails everything else.
2. There is no SAT/ACT path. spec §2.2 listed "SAT/ACT at the 75th percentile" as an
   alternative to DİM. The regulation exempts one group of people from the DİM requirement
   and only one: international subject-olympiad medallists. The old code carried a gate for
   a route that does not exist -- and because ADR-0004 made it fail closed, it never once
   let a SAT score read as clearing it. That is the rule earning its keep.
3. The master's/PhD gate is published after all. The old code reported it UNKNOWN and
   recorded the spec's self-contradiction (§2.2 "Bachelor" row vs §5.2's "bachelor · master
   · PhD") as an open question. The brief settles it in §2.2's favour and names what does
   apply above bachelor: undergraduate CGPA plus an unconditional offer from an approved
   university in a priority field. DİM is explicitly excluded.

WHAT IT DID NOT SETTLE, and is therefore left alone: the language bar. spec §2.2 says C1;
the brief says TOEFL iBT 80 (20 per section) / Duolingo 110 / IELTS per the host offer,
and TOEFL 80 is nearer B2 than C1. Both cite dp.edu.az. `LANGUAGE_SOURCE_CONFLICT` reports
the disagreement instead of resolving it, and the C1 rule stands as the pass condition --
the stricter of the two, so the error stays a false negative rather than telling a student
they clear a bar nobody confirmed.

Neither function here reads `program_requirements`. That table is populated now (by
`scripts/load_program_requirements.py`) and read by `services/university_requirements.py`,
but its NULL columns mean "unknown", never "not required" (ADR-0004). The DP's published
gates below are hard-coded, not derived from that table, so this module has nothing to get
wrong by reading it; if DP eligibility is ever made to consult it, "no row found" must stay
unknown and never become "no requirements", exactly as that table's docstring requires.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.routes import RouteStatus, StudentRouteProfile
from app.models.dp_catalogue import DPCatalogueEntry

# The pages a person must open to promote anything in this module past `research-brief`.
DP_SOURCES = (
    # The regulation carrying the 400/550 thresholds and the olympiad exemption.
    "https://dp.edu.az/uploads/fileuploads/2022/12/bb6c86b54d0f4881a38cac1ae80b4a8f.pdf",
    # The 2026/2027 announcement carrying the 125/353/22 quota split.
    "https://dp.edu.az/az/news/5016",
    # The 2026/2027 document-intake announcement: master's and PhD gates.
    "https://dp.edu.az/az/news/4966",
    # The 5-year return-service obligation, stated by the programme's own management group.
    "https://www.dp.edu.az/az/news/4774",
    # Presidential Decree No. 3163 of 28 February 2022, establishing the 2022-2028 programme.
    "https://e-qanun.az/framework/49209",
)

# Two thresholds, not a band. Group 1 is the engineering and technology ixtisas qrupu; the
# regulation names Civil, Electronics and Electrical Engineering among its specialisations.
#
#   "yekun olaraq ən azı 400, digər sahələr üzrə ən azı 550 bal toplaması"
#   (a final score of at least 400, and at least 550 points for other fields)
#
# The distinction is the applicant's field group, which is why `dim_field_group` exists on
# the profile. Without it the two thresholds still decide the question at both extremes --
# see `_academic_gate_bachelor` -- and only a score in [400, 550) genuinely needs it.
DIM_GROUP_1_MINIMUM = 400.0
DIM_OTHER_MINIMUM = 550.0
DIM_GROUP_1 = 1
BAND_DESCRIPTION = (
    f"DİM at least {DIM_GROUP_1_MINIMUM:.0f} for Group 1 (engineering and technology), "
    f"at least {DIM_OTHER_MINIMUM:.0f} for every other field"
)

# Above bachelor level the DİM threshold does not apply at all -- not "is unknown", which is
# what this module used to say. What applies instead is a CGPA-and-offer gate with no
# published numeric minimum, so the GPA is reported and never compared against an invented
# bar, and the offer is a requirement this project cannot check from a profile.
MASTER_GATE_DESCRIPTION = (
    "Undergraduate CGPA and academic record, plus an unconditional offer from an approved "
    "university in one of the 15 priority fields. No numeric CGPA minimum is published, so "
    "no threshold is applied here"
)
DOCTORATE_GATE_DESCRIPTION = (
    "A recognised master's degree plus an unconditional offer from an approved doctoral "
    "programme. PhD study is outside this product's scope, so nothing further is checked"
)
UNCONDITIONAL_OFFER_GATE = (
    "An unconditional offer of admission from a university on the approved list, in a "
    "priority field. This is a document you obtain from the university, and nothing in a "
    "profile can show whether you hold one -- so it is always listed as outstanding here"
)

# There is no SAT/ACT route into the DP. The regulation exempts international subject-
# olympiad medallists from the DİM requirement and nobody else. A student who offers a SAT
# or ACT is told that plainly rather than having the field silently ignored -- silence would
# leave them assuming a strong score was counted.
def _no_sat_act_path(exam_name: str, score: object) -> str:
    return (
        f"{exam_name} {score} was offered, but the Dövlət Proqramı publishes no SAT or ACT "
        "route: the only exemption from the DİM requirement is an international subject-"
        "olympiad medal. Your SAT or ACT may still matter to the university itself"
    )


ACCEPTED_LANGUAGE_LEVELS = ("C1", "C2")

# The one gate the brief did NOT settle. Reported, not resolved -- see the module docstring.
DP_BRIEF_TOEFL_MINIMUM = 80
LANGUAGE_SOURCE_CONFLICT = (
    f"Our two sources disagree on this bar: one gives C1, the other gives TOEFL iBT "
    f"{DP_BRIEF_TOEFL_MINIMUM} with at least 20 per section (nearer B2), Duolingo 110, or "
    "whatever IELTS band your offer letter names. Both cite dp.edu.az. We apply the "
    "stricter reading until a person checks, so you may in fact clear this"
)

# The 2026/2027 allocation, published by the programme. 500 places, and the split is the
# single most decision-relevant fact about the DP: bachelor sits at the 25% statutory cap
# while master's takes the majority. A student choosing a level is choosing a queue.
ANNUAL_QUOTA_TOTAL = 500
QUOTA_2026_2027 = {"bachelor": 125, "master": 353, "doctorate": 22}

# Not a gate -- an obligation, and the one a student is least likely to have been told.
RETURN_SERVICE_YEARS = 5
RETURN_SERVICE_NOTE = (
    f"Accepting this funding is a contract. Graduates must return to Azerbaijan and work "
    f"here for {RETURN_SERVICE_YEARS} years; failing to return, failing to complete the "
    "degree, or breaking the service period requires repaying everything the state spent, "
    "with interest and contractual penalties"
)

# The window opens in Q1 and closes between April and June. No exact date is published per
# cycle in anything we hold, so none is stated -- the month is enough to tell a student
# which academic year they are actually applying for.
WINDOW_CLOSING_MONTH = 6

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
    # Not gates. Facts a student needs in order to decide whether to want this at all, and
    # which the product used to render nowhere: how many places exist at their level, what
    # accepting the money commits them to, and which academic year they are applying for.
    quota_note: str
    obligation_note: str
    window_note: str


def quota_note(level: str) -> str:
    """How many funded places exist at this level, against the 500 total.

    A level the programme does not fund at all is a real answer and is said plainly; it is
    never softened into silence, and no count is invented for a level we have no figure for.
    """
    places = QUOTA_2026_2027.get(level)
    if places is None:
        return (
            f"No published figure for {level} places in the 2026/2027 allocation is "
            f"recorded here, out of {ANNUAL_QUOTA_TOTAL} places in total"
        )
    share = 100.0 * places / ANNUAL_QUOTA_TOTAL
    return (
        f"{places} of the {ANNUAL_QUOTA_TOTAL} funded places in the 2026/2027 cycle are "
        f"for {level} study ({share:.0f}%). That is the size of the queue, not your odds "
        "in it: selection among applicants who clear the gates is a committee decision"
    )


def application_window_note(today: Optional[date] = None) -> str:
    """Which cycle an application started today would actually be for.

    Applications open in the first quarter and close between April and June. No exact date
    is published in anything this project holds, so none is stated -- saying "closed on 15
    June" would be a precise-looking invention. The month is enough to keep a student from
    assuming the current academic year is still available.
    """
    today = today or date.today()
    if today.month <= WINDOW_CLOSING_MONTH:
        return (
            f"Applications open in the first quarter and close between April and June. In "
            f"{today.strftime('%B %Y')} the window for the coming academic year may still "
            "be open, but the exact dates are published per cycle on dp.edu.az and are not "
            "recorded here -- check them before relying on this"
        )
    return (
        f"Applications open in the first quarter and close between April and June, so by "
        f"{today.strftime('%B %Y')} the window for the {today.year}/{today.year + 1} "
        f"academic year has closed. An application made now would be for "
        f"{today.year + 1}/{today.year + 2}, which is the year to plan against"
    )


def _academic_gate_bachelor(
    profile: StudentRouteProfile, met: list[str], missing: list[str]
) -> None:
    """The bachelor academic gate: a DİM score against the threshold for the student's
    field group, or an international subject-olympiad medal. Appends to `met`/`missing`.

    The field group matters only in the middle. A score at or above 550 clears the harder
    of the two thresholds and is therefore decisive whichever group the student is in; a
    score below 400 clears neither and is decisive the same way. Only [400, 550) genuinely
    depends on the group, and there the answer is withheld rather than guessed -- picking
    either threshold would be a coin flip presented as a check (ADR-0004).
    """
    if profile.has_international_olympiad_medal:
        met.append(
            "An international subject-olympiad medal, which is the only published "
            "exemption from the DİM requirement"
        )
        return

    score = profile.dim_score
    group = profile.dim_field_group

    if score is None:
        missing.append(
            f"A DİM score is required: {BAND_DESCRIPTION}. The alternative is an "
            "international subject-olympiad medal"
        )
        return

    if group is not None:
        threshold = DIM_GROUP_1_MINIMUM if group == DIM_GROUP_1 else DIM_OTHER_MINIMUM
        which = (
            "Group 1 (engineering and technology)" if group == DIM_GROUP_1
            else f"group {group}, which is not Group 1"
        )
        if score >= threshold:
            met.append(f"DİM {score:.0f} clears the {threshold:.0f} required for {which}")
        else:
            missing.append(
                f"DİM {score:.0f} is below the {threshold:.0f} required for {which}"
            )
        return

    # No field group given. Answer anyway wherever the thresholds agree.
    if score >= DIM_OTHER_MINIMUM:
        met.append(
            f"DİM {score:.0f} clears both thresholds ({DIM_GROUP_1_MINIMUM:.0f} for Group "
            f"1, {DIM_OTHER_MINIMUM:.0f} for other fields), so your field group does not "
            "change the answer"
        )
    elif score < DIM_GROUP_1_MINIMUM:
        missing.append(
            f"DİM {score:.0f} is below both thresholds ({DIM_GROUP_1_MINIMUM:.0f} for "
            f"Group 1, {DIM_OTHER_MINIMUM:.0f} for other fields), so your field group does "
            "not change the answer"
        )
    else:
        missing.append(
            f"DİM {score:.0f} clears the {DIM_GROUP_1_MINIMUM:.0f} required for Group 1 "
            f"(engineering and technology) but not the {DIM_OTHER_MINIMUM:.0f} required "
            "for every other field. Tell us your ixtisas qrupu and this becomes a "
            "definite answer either way"
        )


def assess_dp_eligibility(profile: StudentRouteProfile) -> DPEligibility:
    """Check the published gates. Clearing them is 'possibly eligible', never an award.

    The DP funds 500 places a year against a much larger pool. What is checkable is whether
    the student clears the stated gates; the selection that follows is a committee decision
    no dataset in this project models.

    Level is part of the key here, not a filter, and the gates genuinely differ by level.
    The DİM threshold is a bachelor gate and is explicitly excluded above that level, so a
    master's applicant is never told they are missing a school-leaving exam they have no
    reason to hold. What replaces it -- CGPA plus an unconditional offer -- is a real
    published gate rather than the UNKNOWN this module used to report.
    """
    met: list[str] = []
    missing: list[str] = []

    if profile.language_certificate_level in ACCEPTED_LANGUAGE_LEVELS:
        met.append(f"Language certificate at {profile.language_certificate_level}")
    else:
        note = "A language certificate at C1 or above is required"
        if profile.toefl is not None and profile.toefl >= DP_BRIEF_TOEFL_MINIMUM:
            note = f"{note}. {LANGUAGE_SOURCE_CONFLICT} -- you hold TOEFL {profile.toefl}"
        missing.append(note)

    if profile.level_sought == "bachelor":
        band_checked = BAND_DESCRIPTION
        _academic_gate_bachelor(profile, met, missing)
    elif profile.level_sought == "master":
        band_checked = MASTER_GATE_DESCRIPTION
        if profile.gpa is not None:
            scale = profile.gpa_scale or "an unstated scale"
            met.append(
                f"An undergraduate grade average of {profile.gpa:g} on {scale} is recorded "
                "and will be assessed. No published minimum exists to compare it against, "
                "so no threshold is claimed here"
            )
        else:
            missing.append(
                "Your undergraduate grade average, which is what this level is assessed "
                "on. No numeric minimum is published, but the figure itself is required"
            )
        missing.append(UNCONDITIONAL_OFFER_GATE)
    else:
        band_checked = DOCTORATE_GATE_DESCRIPTION
        missing.append(
            f"{profile.level_sought} study is outside this product's scope, so its "
            "Dövlət Proqramı gates are not checked here"
        )

    # The DP publishes no SAT or ACT route at any level. Reported wherever one is offered,
    # so the score is visibly considered and visibly not counted, rather than dropped.
    if profile.sat is not None:
        missing.append(_no_sat_act_path("SAT", profile.sat))
    if profile.act is not None:
        missing.append(_no_sat_act_path("ACT", profile.act))

    status = RouteStatus.OPEN if not missing else RouteStatus.UNLOCKABLE
    return DPEligibility(
        status=status,
        band_checked=band_checked,
        gates_met=tuple(met),
        gates_missing=tuple(missing),
        quota_note=quota_note(profile.level_sought),
        obligation_note=RETURN_SERVICE_NOTE,
        window_note=application_window_note(),
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
