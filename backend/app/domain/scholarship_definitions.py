"""The hand-written funding catalogue. Ten instruments, each carrying its real gate.

PROVENANCE. Every row here is `research-brief`: taken from spec §5.2 and the 2026-09-04
Deep Research briefs, whose primary pages this project has NOT opened. That rung sits one
below `claude-extracted` and well below `human-verified`. Each `citation` names both where
our figure came from and, where we hold one, the page a person must open to promote it.
Where we hold no URL at all, the citation says so rather than guessing one -- an invented
official URL is worse than an admitted gap, because it looks like a check that happened.

WHY THESE NINE AND NOT ONE. The product modelled the Dövlət Proqramı alone, and the reason
was that the DP publishes a downloadable catalogue while every other funder has to be
curated by hand. That is data-availability bias. Its cost is visible in the research brief's
own advice: because the DP caps bachelor funding at 25% of its quota, a school-leaver should
prioritise Türkiye Bursları or the CSC -- neither of which this product could see.

NOTICE WHAT THE `LevelGate`s SAY. Seven of the ten are master's-only, and exactly two --
Türkiye Bursları and the CSC -- reach bachelor at all. That is not a gap in this catalogue,
it is the finding (spec §2.3): **at bachelor level, scholarships barely exist**, and the
lever is affordability instead. A product that padded the bachelor list to look generous
would be lying about the thing that most changes a school-leaver's plan. It also explains
the research brief's advice, which this catalogue now makes actionable: a school-leaver
should apply to the two that exist rather than treating the DP as their funding plan.

THE DÖVLƏT PROQRAMI IS ABSENT ON PURPOSE. It is assessed by `services/dp_eligibility.py`
against its own regulation, with a 4,121-row funded catalogue and a quota split nothing here
could express. One award, one assessor.
"""

from app.domain.scholarships import (
    AgeGate,
    EmploymentGate,
    LanguageGate,
    LevelGate,
    Scholarship,
    TIER_AZERBAIJANI_STATE,
    TIER_DESTINATION_GOVERNMENT,
    UnresolvedGate,
    WorkExperienceGate,
)

SPEC_5_2 = "docs/superpowers/specs/2026-08-31-route-first-advisor-design.md §5.2"
GENERAL_BRIEF = "AUSA general research brief 2026-09-04, 'Study Abroad Guide for Azerbaijanis'"

# Chevening publishes its bar in HOURS, not years, and that is the unit used here. "Two
# years' experience" is the marketing phrasing; 2,800 documented hours is the requirement,
# and part-time or overlapping work counts differently under each reading.
CHEVENING_MINIMUM_WORK_HOURS = 2800

# "Under 21" at bachelor level -- a hard limit, verified at that level only.
TURKIYE_BURSLARI_BACHELOR_MAX_AGE = 21

SOCAR_MAX_AGE = 40
SOCAR_MAX_AGE_MBA = 45

# --- Tier 1: the Azerbaijani state --------------------------------------------------------

SOCAR_XARICI_TEQAUD = Scholarship(
    key="socar-xarici-teqaud",
    name="SOCAR Xarici Təqaüd Proqramı",
    provider="SOCAR",
    tier=TIER_AZERBAIJANI_STATE,
    country_code=None,
    coverage="Full funding for a master's degree abroad, for SOCAR group employees",
    gates=(
        LevelGate(levels=("master",)),
        # The gate that decides this award, and it is not academic. A student with a perfect
        # record who does not work for the SOCAR group is ineligible, not uncompetitive.
        EmploymentGate(employer="SOCAR"),
        AgeGate(
            maximum_age=SOCAR_MAX_AGE,
            applies_to_levels=("master",),
            unverified_at_other_levels=(
                "This programme funds master's study only, so no age limit is checked at "
                "other levels"
            ),
        ),
        LanguageGate(minimum_certificate_level="B2", ielts=6.0, toefl=80),
    ),
    citation=(
        f"{SPEC_5_2}: employment-gated to SOCAR group employees; age at most "
        f"{SOCAR_MAX_AGE} ({SOCAR_MAX_AGE_MBA} for an MBA); IELTS 6.0 / TOEFL 80 / B2. "
        "No official programme page has been identified by this project -- the age and "
        "language figures are unverified, and the MBA exception is NOT applied below "
        "because nothing in a profile tells us the degree is an MBA"
    ),
    window=None,
)

PREZIDENT_TEQAUDU = Scholarship(
    key="prezident-teqaudu",
    name="Prezident Təqaüdü",
    provider="Office of the President of Azerbaijan",
    tier=TIER_AZERBAIJANI_STATE,
    country_code="AZ",
    coverage="600-700 AZN a month, roughly 100-150 places a year, for study IN Azerbaijan",
    # No gates are listed, and none are checked. The award never reaches a gate for this
    # product's purposes: it does not fund study abroad, which settles it before eligibility
    # is even a question.
    gates=(),
    funds_study_abroad=False,
    citation=(
        f"{SPEC_5_2}: 600-700 AZN/month, ~100-150 places a year, domestic study only. "
        "Listed here precisely so the product does NOT offer it as a study-abroad option: "
        "it is the most prestigious domestic award and students will ask about it, so "
        "answering beats silence. No official page has been identified by this project"
    ),
)

# --- Tier 2: destination-country governments ----------------------------------------------

TURKIYE_BURSLARI = Scholarship(
    key="turkiye-burslari",
    name="Türkiye Bursları",
    provider="Government of Türkiye",
    tier=TIER_DESTINATION_GOVERNMENT,
    country_code="TR",
    coverage=(
        "Fully funded: tuition waiver, monthly stipend, university dormitory, health "
        "insurance, and a mandatory one-year Turkish language year (TÖMER)"
    ),
    gates=(
        LevelGate(levels=("bachelor", "master")),
        AgeGate(
            maximum_age=TURKIYE_BURSLARI_BACHELOR_MAX_AGE,
            applies_to_levels=("bachelor",),
            # The honest half of this gate. The programme plainly sets limits above bachelor
            # too and we have not read them, so master's gets UNKNOWN rather than a silent
            # pass that would read as "no age limit applies to you".
            unverified_at_other_levels=(
                "Türkiye Bursları sets age limits at master's level as well, and this "
                "project has not read them. No age check is applied here, which is not the "
                "same as there being no limit -- check before relying on it"
            ),
        ),
    ),
    citation=(
        f"{SPEC_5_2} and {GENERAL_BRIEF}: fully funded, under 21 at bachelor level, "
        "applications 10 January - 20 February. No official turkiyeburslari.gov.tr page has "
        "been opened by this project; the nearest source we hold is "
        "https://www.studyinturkiye.gov.tr/"
    ),
    window=(
        "Applications run 10 January to 20 February. The 2026 window has closed, so the "
        "next one opens in January 2027 -- that is the cycle to plan against"
    ),
)

CSC_CHINA = Scholarship(
    key="csc-china",
    name="Chinese Government Scholarship (CSC)",
    provider="China Scholarship Council",
    tier=TIER_DESTINATION_GOVERNMENT,
    country_code="CN",
    coverage="Tuition, accommodation and a stipend; Type A applies via the embassy, Type B via the university",
    gates=(
        LevelGate(levels=("bachelor", "master")),
        # The CSCA and HSK 4 bars are NOT repeated here. They sit on the `cn-bachelor-csc`
        # route in route_definitions.py, which is where the engine already checks them. Two
        # copies of one requirement diverge on the first correction.
        UnresolvedGate(
            summary=(
                "A CSC bachelor place must be taken in a CHINESE-taught programme -- "
                "English-taught study is open to graduate and non-degree students only -- "
                "and requires a CSCA score plus HSK 4. Those bars are checked on the China "
                "entry route rather than here. No age limit has been read from a CSC source "
                "by this project, and the programme is understood to set one"
            )
        ),
    ),
    citation=(
        f"{SPEC_5_2}, citing https://www.campuschina.org/. Bachelor is Chinese-taught with "
        "CSCA and HSK 4; English-taught master's needs IELTS 6.5 / TOEFL 80 or two years of "
        "prior English-medium study. Applications early January to early April. CUCAS is a "
        "third-party aggregator and is excluded as a source"
    ),
    window="Applications run from early January to early April via campuschina.org",
)

CHEVENING = Scholarship(
    key="chevening",
    name="Chevening Scholarship",
    provider="UK Foreign, Commonwealth & Development Office",
    tier=TIER_DESTINATION_GOVERNMENT,
    country_code="GB",
    coverage="Full tuition, a monthly stipend, return flights and visa fees for a one-year taught master's",
    gates=(
        LevelGate(levels=("master",)),
        WorkExperienceGate(
            minimum_hours=CHEVENING_MINIMUM_WORK_HOURS,
            description=(
                f"{CHEVENING_MINIMUM_WORK_HOURS:,} documented hours of work experience, "
                "which is roughly two years full-time. Chevening publishes the bar in hours, "
                "not years, and counts part-time and overlapping work against the hours"
            ),
        ),
    ),
    citation=(
        f"{GENERAL_BRIEF}, citing https://www.chevening.org/resource-hub/guidance/"
        f"eligibility/ and https://www.chevening.org/scholarships/guidance/courses/ -- "
        f"{CHEVENING_MINIMUM_WORK_HOURS:,} documented hours and four assessed essays on "
        "leadership, networking, choice of UK course, and career plan. Those pages have not "
        "been opened by this project"
    ),
    obligation=(
        "Chevening requires you to return to Azerbaijan for at least two years after "
        "graduating. It is a condition of the award, not a suggestion"
    ),
)

FULBRIGHT = Scholarship(
    key="fulbright-foreign-student",
    name="Fulbright Foreign Student Program",
    provider="U.S. Department of State, via the U.S. Embassy in Baku",
    tier=TIER_DESTINATION_GOVERNMENT,
    country_code="US",
    coverage="Full tuition, a monthly stipend, health insurance and J-1 visa sponsorship for a master's degree",
    gates=(
        LevelGate(levels=("master",)),
        UnresolvedGate(
            summary=(
                "Fulbright selects young professionals and weighs professional experience "
                "heavily, but this project has not read a published minimum. No hours bar is "
                "applied here, which is not the same as there being none"
            )
        ),
    ),
    citation=(
        f"{GENERAL_BRIEF}, citing https://az.usembassy.gov/fulbright-foreign-student-"
        "program/. That page has not been opened by this project"
    ),
    obligation=(
        "The J-1 visa carries a two-year home-country physical presence requirement: after "
        "the degree you must spend two years in Azerbaijan before you are eligible for "
        "certain US visas. This constrains what you can do next far beyond the degree itself"
    ),
)

DAAD = Scholarship(
    key="daad-individual-grants",
    name="DAAD individual scholarships",
    provider="Deutscher Akademischer Austauschdienst",
    tier=TIER_DESTINATION_GOVERNMENT,
    country_code="DE",
    coverage="Varies sharply by grant: most are a monthly stipend plus travel and insurance, not tuition (German public tuition is already near zero)",
    gates=(
        # "Overwhelmingly master's/PhD" is the spec's wording. Modelled as master's-only,
        # which is the conservative reading: it can produce a false BLOCKED for an unusual
        # bachelor grant, never a false OPEN.
        LevelGate(levels=("master",)),
        UnresolvedGate(
            summary=(
                "DAAD is not one scholarship but a database of hundreds, each with its own "
                "gate, and the gates are per-grant rather than programme-wide. This project "
                "cannot list them: DAAD's robots.txt explicitly disallows the scholarship "
                "database, so no automated collection of it is permitted and every grant has "
                "to be read by hand from a page that allows it"
            )
        ),
    ),
    citation=(
        f"{SPEC_5_2}: DAAD individual grants are overwhelmingly master's and PhD. DAAD's "
        "main host sets Crawl-delay: 2 and disallows /deutschland/foerderung/"
        "stipendiendatenbank/00462.*, so the database is off-limits to our collector. "
        "DAAD's terms of use have NOT been read and must be before any bulk fetch"
    ),
)

NAWA_BANACH = Scholarship(
    key="nawa-banach",
    name="Stefan Banach Scholarship Programme",
    provider="NAWA, the Polish National Agency for Academic Exchange",
    tier=TIER_DESTINATION_GOVERNMENT,
    country_code="PL",
    coverage="Fully funded master's study at a Polish public university",
    gates=(
        LevelGate(levels=("master",)),
        # Our two sources describe this restriction as exact opposites. Reported, not
        # resolved -- the same posture dp_eligibility takes on the C1-vs-TOEFL-80 conflict.
        # Picking one would produce a confident answer with a 50% chance of being backwards.
        UnresolvedGate(
            summary=(
                "Banach restricts which fields Azerbaijani applicants may study, and our two "
                "sources give opposite lists: spec §5.2 says humanities and social sciences "
                "only, while the general research brief says engineering, technical, "
                "agricultural and natural sciences. Those are complements, so one of them is "
                "wrong and we cannot tell which. Read nawa.gov.pl before relying on either"
            )
        ),
    ),
    citation=(
        f"{SPEC_5_2} (humanities/social sciences only for Azerbaijanis) CONTRADICTED BY "
        f"{GENERAL_BRIEF} (engineering, technical, agricultural and natural sciences). No "
        "nawa.gov.pl page has been opened by this project, and this conflict is the reason "
        "no field-of-study check is applied anywhere in the product yet"
    ),
)

ERASMUS_MUNDUS = Scholarship(
    key="erasmus-mundus",
    name="Erasmus Mundus Joint Masters",
    provider="European Commission",
    tier=TIER_DESTINATION_GOVERNMENT,
    # Not tied to one country: a joint master's is delivered by a consortium and the student
    # studies in at least two of them. None here means the destination check is skipped, not
    # that the award has no destination.
    country_code=None,
    coverage="Full tuition, travel and installation costs, and a monthly stipend, across a multi-country consortium",
    gates=(
        LevelGate(levels=("master",)),
        UnresolvedGate(
            summary=(
                "Each joint master's consortium sets its own admission requirements and its "
                "own deadline; there is no single Erasmus Mundus gate to check. Eligibility "
                "is decided by the specific programme you apply to"
            )
        ),
    ),
    citation=(
        f"{SPEC_5_2}: master's only. Erasmus+ mobility within a degree is a different "
        "instrument and is not a full-degree scholarship. No European Commission page has "
        "been opened by this project"
    ),
)

GREAT_SCHOLARSHIPS = Scholarship(
    key="great-scholarships",
    name="GREAT Scholarships",
    provider="British Council with participating UK universities",
    tier=TIER_DESTINATION_GOVERNMENT,
    country_code="GB",
    # Named as a reduction, not as funding. A GBP 10,000 cut against GBP 30,000+ of UK
    # master's tuition is real and is nowhere near a fully funded place; calling it a
    # scholarship without the number invites exactly the wrong plan.
    coverage=(
        "A single-year GBP 10,000 tuition REDUCTION -- not a full scholarship. UK master's "
        "tuition typically runs well above that, so this narrows a gap rather than closing it"
    ),
    gates=(
        LevelGate(levels=("master",)),
        UnresolvedGate(
            summary=(
                "GREAT awards are made by each participating university, so both the "
                "eligibility rules and the list of participating universities change year to "
                "year. This project has not read either"
            )
        ),
    ),
    citation=(
        f"{GENERAL_BRIEF}: jointly funded by the British Council and participating UK "
        "universities, GBP 10,000 for one year, master's students. No British Council page "
        "has been opened by this project"
    ),
)

ALL_SCHOLARSHIPS: tuple[Scholarship, ...] = (
    SOCAR_XARICI_TEQAUD,
    PREZIDENT_TEQAUDU,
    TURKIYE_BURSLARI,
    CSC_CHINA,
    CHEVENING,
    FULBRIGHT,
    DAAD,
    NAWA_BANACH,
    ERASMUS_MUNDUS,
    GREAT_SCHOLARSHIPS,
)
