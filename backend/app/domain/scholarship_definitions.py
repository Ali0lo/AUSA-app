"""The hand-written funding catalogue. Ten instruments, each carrying its real gate.

PROVENANCE. Unreviewed rows remain `research-brief`, taken from spec §5.2 and the 2026-09-04
Deep Research briefs, whose primary pages had not been opened. Track A updates Türkiye Bursları, Chevening and
NAWA from primary pages read on 2026-09-15 as `claude-extracted`, never human-verified.
Research-brief claims remain below extracted primary evidence and human verification. Each `citation` names both where
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

# "Under 21" at bachelor level; the master gate separately uses under 30.
TURKIYE_BURSLARI_BACHELOR_MAX_AGE = 21

SOCAR_MAX_AGE = 40
SOCAR_MAX_AGE_MBA = 45

# --- Tier 1: the Azerbaijani state --------------------------------------------------------

SOCAR_XARICI_TEQAUD = Scholarship(
    key="socar-xarici-teqaud", name="SOCAR Xarici Təqaüd Proqramı", provider="SOCAR",
    tier=TIER_AZERBAIJANI_STATE, country_code=None,
    coverage="Research brief describes funding for SOCAR employees; current terms unconfirmed",
    gates=(LevelGate(levels=("master",)), EmploymentGate(employer="SOCAR"),
           UnresolvedGate(summary="The current official SOCAR call was not located. Age, MBA exceptions, language scores and employment conditions need source review; unverified age/language figures are not enforced as rejections.")),
    citation="Source search 2026-09-15 did not establish a current official call. Previous research-brief claims (age 40/45 and B2/IELTS 6/TOEFL 80) remain unverified; do not rely on them.",
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
    key="turkiye-burslari", name="Türkiye Bursları", provider="Government of Türkiye",
    tier=TIER_DESTINATION_GOVERNMENT, country_code="TR",
    coverage="Tuition, placement, stipend, accommodation, health insurance, Turkish language course and flights under the award's terms",
    gates=(
        LevelGate(levels=("bachelor", "master")),
        AgeGate(maximum_age=TURKIYE_BURSLARI_BACHELOR_MAX_AGE,
                applies_to_levels=("bachelor", "master"), maximum_age_by_level=(("master", 30),),
                unverified_at_other_levels="This planner covers bachelor and master study."),
        UnresolvedGate(summary="Additional criteria need review: academic achievement at least 70% for bachelor, 75% for graduate and 90% for health sciences; citizenship, graduation and current Turkish enrolment restrictions also apply. The profile cannot establish all of these. Graduate health-science funding is excluded."),
    ),
    citation="https://www.turkiyeburslari.gov.tr/scholarshipsprograms ; https://www.turkiyeburslari.gov.tr/fulltimeprograms . Primary pages read 2026-09-15; under 21 for bachelor and under 30 for master. Awaiting human review.",
    window="Published recurring window: 10 January–20 February. The 2026 round is closed; confirm the next call's dates before applying.",
    provenance="claude-extracted",
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
    key="chevening", name="Chevening Scholarship",
    provider="UK Foreign, Commonwealth & Development Office",
    tier=TIER_DESTINATION_GOVERNMENT, country_code="GB",
    coverage="Tuition and living/travel support for eligible UK master's study, subject to award terms and any course caps",
    gates=(
        LevelGate(levels=("master",)),
        WorkExperienceGate(minimum_hours=CHEVENING_MINIMUM_WORK_HOURS,
                           description="2,800 hours of work experience gained AFTER completing the undergraduate degree"),
        UnresolvedGate(summary="The profile records total work hours, not when they were gained. Confirm 2,800 post-degree hours, graduation at least two years before the deadline, three eligible course applications, an unconditional offer by the specified deadline and citizenship/residency conditions."),
    ),
    citation="https://www.chevening.org/resource-hub/guidance/eligibility/ . Primary page read 2026-09-15; total lifetime work hours alone do not establish eligibility. Awaiting human review.",
    obligation="Return to the country of citizenship for at least two years after the scholarship.",
    provenance="claude-extracted",
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
        "program/. Retrieval on 2026-09-15 returned HTTP 403; a published minimum could not be established."
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
    key="nawa-banach", name="Stefan Banach Scholarship Programme",
    provider="NAWA, the Polish National Agency for Academic Exchange",
    tier=TIER_DESTINATION_GOVERNMENT, country_code="PL",
    coverage="Public-university tuition exemption and PLN 2500 monthly scholarship under the programme's terms",
    gates=(
        LevelGate(levels=("master",)),
        UnresolvedGate(summary="The 2026 call permits full-time second-cycle courses at participating universities; neither earlier exclusive field list applies. Check eligible citizenship, degree country/date (normally 2024 onward), prior master's/NAWA awards, B2 study language or B1 Polish preparation, and university admission. The 2026 application round is closed."),
    ),
    citation="https://nawa.gov.pl/images/Banach/2026/Banach-2026---Call-for-applications-EN.pdf , sections 2.2–2.4; https://nawa.gov.pl/en/students/foreign-students/the-banach-scholarship-programme . Read 2026-09-15; replaces the conflicting research-brief field lists. Awaiting human review.",
    window="2026 deadline: 8 May at 15:00 Warsaw time, or earlier when the country-group submission cap was reached. Next call unconfirmed.",
    provenance="claude-extracted",
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
