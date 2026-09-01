"""The hand-written routes. The highest-value data in the product, and none of it scraped.

Every route carries a citation. Provenance is 'seed' until a person opens that citation and
confirms it -- loading a route does not verify it (ADR-0004 rule 2).

Money ranges are annual, in AZN, and are order-of-magnitude figures for ranking, not
quotes. Where the spec verified a figure it is used; where it did not, the range is wide
rather than precise, because a narrow invented number reads as measured.
"""

from app.domain.routes import ExamRequirement, Route
from app.models.qualifications import (
    QUALIFICATION_A_LEVEL,
    QUALIFICATION_ATTESTAT,
    QUALIFICATION_BACHELOR_DEGREE,
    QUALIFICATION_FESTSTELLUNGSPRUEFUNG,
    QUALIFICATION_FOUNDATION_YEAR,
    QUALIFICATION_IB,
    QUALIFICATION_ONE_YEAR_UNIVERSITY,
)

ANABIN = "https://anabin.kmk.org/ -- attestat 'eröffnet den Zugang zum Studienkolleg/Feststellungsprüfung'"
UK_ENIC = "UK ENIC: an Azerbaijani attestat is 'not accepted for direct entry to undergraduate programmes'"
STUDY_IN_TURKIYE = "https://www.studyinturkiye.gov.tr/"
CAMPUS_CHINA = "https://www.campuschina.org/"
DP_RULES = "https://dp.edu.az/ -- Dövlət Proqramı eligibility rules"
SPEC_2_1 = "docs/superpowers/specs/2026-08-31-route-first-advisor-design.md §2.1"

# --- The unlock. Both blocked countries share this one escape hatch (spec §2.1). ---

AZ_PREP_YEAR = Route(
    key="az-prep-year",
    country_code="AZ",
    level="bachelor",
    mechanism="One year of study at a recognised Azerbaijani university",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    produces_qualification=QUALIFICATION_ONE_YEAR_UNIVERSITY,
    exams=(ExamRequirement("DİM", None, "dim_score"),),
    time_cost_months=12,
    money_cost_azn=(1000, 4000),
    citation=ANABIN,
)

# --- Bachelor, direct ---

TR_BACHELOR_DIRECT = Route(
    key="tr-bachelor-direct",
    country_code="TR",
    level="bachelor",
    mechanism="Direct application on the diploma and grades; most private universities require no YÖS",
    requires_qualification=(QUALIFICATION_ATTESTAT, QUALIFICATION_A_LEVEL, QUALIFICATION_IB),
    produces_qualification=None,
    exams=(),
    time_cost_months=0,
    money_cost_azn=(1700, 12000),
    citation=STUDY_IN_TURKIYE,
)

TR_BACHELOR_YOS = Route(
    key="tr-bachelor-yos",
    country_code="TR",
    level="bachelor",
    mechanism="TR-YÖS, required by some public universities for competitive programmes",
    requires_qualification=(QUALIFICATION_ATTESTAT, QUALIFICATION_A_LEVEL, QUALIFICATION_IB),
    produces_qualification=None,
    # Sat twice a year by ÖSYM, in six languages; Turkish is not required to take it.
    exams=(ExamRequirement("TR-YÖS", None, "tr_yos"),),
    time_cost_months=0,
    money_cost_azn=(1200, 6000),
    citation=STUDY_IN_TURKIYE,
)

PL_BACHELOR_DIRECT = Route(
    key="pl-bachelor-direct",
    country_code="PL",
    level="bachelor",
    mechanism="Direct application; the attestat is accepted with an apostille",
    requires_qualification=(QUALIFICATION_ATTESTAT, QUALIFICATION_A_LEVEL, QUALIFICATION_IB),
    produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.0, "ielts"),),
    time_cost_months=0,
    money_cost_azn=(3400, 8500),
    citation=SPEC_2_1,
)

US_BACHELOR_DIRECT = Route(
    key="us-bachelor-direct",
    country_code="US",
    level="bachelor",
    mechanism="Direct application; many institutions are test-optional, but the 11-vs-12-year gap is assessed per institution",
    requires_qualification=(QUALIFICATION_ATTESTAT, QUALIFICATION_A_LEVEL, QUALIFICATION_IB),
    produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0,
    money_cost_azn=(30000, 100000),
    citation=SPEC_2_1,
)

CN_BACHELOR_CSC = Route(
    key="cn-bachelor-csc",
    country_code="CN",
    level="bachelor",
    # CSC bachelor recipients must register for CHINESE-taught courses; English-taught is
    # open to graduate and non-degree students only (spec §5.2).
    mechanism="CSC-funded study, taught in Chinese, with a CSCA score",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    exams=(
        ExamRequirement("CSCA", None, "csca"),
        ExamRequirement("HSK", 4.0, "hsk"),
    ),
    produces_qualification=None,
    time_cost_months=0,
    money_cost_azn=(0, 0),
    citation=CAMPUS_CHINA,
)

# --- Bachelor, blocked-then-unlocked ---

DE_BACHELOR_STUDIENKOLLEG = Route(
    key="de-bachelor-studienkolleg",
    country_code="DE",
    level="bachelor",
    mechanism="Studienkolleg, ending in the Feststellungsprüfung",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    produces_qualification=QUALIFICATION_FESTSTELLUNGSPRUEFUNG,
    exams=(ExamRequirement("TestAS", None, "test_as"),),
    time_cost_months=12,
    money_cost_azn=(6000, 14000),
    citation=ANABIN,
)

DE_BACHELOR_DIRECT = Route(
    key="de-bachelor-direct",
    country_code="DE",
    level="bachelor",
    mechanism="Direct, subject-restricted entry",
    # An attestat alone does NOT appear here, and that is the whole point: it opens the
    # Studienkolleg and nothing else. Applies to attestats from 2015 onward.
    requires_qualification=(
        QUALIFICATION_ONE_YEAR_UNIVERSITY,
        QUALIFICATION_FESTSTELLUNGSPRUEFUNG,
        QUALIFICATION_A_LEVEL,
        QUALIFICATION_IB,
    ),
    produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0,
    money_cost_azn=(0, 1200),
    citation=ANABIN,
)

UK_BACHELOR_FOUNDATION = Route(
    key="uk-bachelor-foundation",
    country_code="GB",
    level="bachelor",
    mechanism="International foundation year",
    requires_qualification=(QUALIFICATION_ATTESTAT,),
    produces_qualification=QUALIFICATION_FOUNDATION_YEAR,
    exams=(ExamRequirement("IELTS", 5.5, "ielts"),),
    time_cost_months=12,
    money_cost_azn=(25000, 45000),
    citation=UK_ENIC,
)

UK_BACHELOR_DIRECT = Route(
    key="uk-bachelor-direct",
    country_code="GB",
    level="bachelor",
    mechanism="Direct entry via UCAS",
    requires_qualification=(
        QUALIFICATION_FOUNDATION_YEAR,
        QUALIFICATION_ONE_YEAR_UNIVERSITY,
        QUALIFICATION_A_LEVEL,
        QUALIFICATION_IB,
    ),
    produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0,
    money_cost_azn=(30000, 70000),
    citation=UK_ENIC,
)

# --- Master's. A completed bachelor's is an accepted entry qualification everywhere,
# which is why Germany and the UK invert from blocked to open at this level. ---

TR_MASTER_DIRECT = Route(
    key="tr-master-direct", country_code="TR", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.0, "ielts"),),
    time_cost_months=0, money_cost_azn=(1700, 12000), citation=STUDY_IN_TURKIYE,
)

DE_MASTER_DIRECT = Route(
    key="de-master-direct", country_code="DE", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0, money_cost_azn=(0, 1200), citation=SPEC_2_1,
)

UK_MASTER_DIRECT = Route(
    key="uk-master-direct", country_code="GB", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0, money_cost_azn=(35000, 80000), citation=SPEC_2_1,
)

US_MASTER_DIRECT = Route(
    key="us-master-direct", country_code="US", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0, money_cost_azn=(35000, 100000), citation=SPEC_2_1,
)

PL_MASTER_DIRECT = Route(
    key="pl-master-direct", country_code="PL", level="master",
    mechanism="Direct application with a completed bachelor's degree",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.0, "ielts"),),
    time_cost_months=0, money_cost_azn=(3400, 8500), citation=SPEC_2_1,
)

CN_MASTER_DIRECT = Route(
    key="cn-master-direct", country_code="CN", level="master",
    # English-taught master's: IELTS 6.5 / TOEFL 80, or two years of prior English-medium
    # study. Chinese-taught needs HSK 4 plus a year of Chinese (spec §5.2).
    mechanism="Direct application with a completed bachelor's degree; English-taught available",
    requires_qualification=(QUALIFICATION_BACHELOR_DEGREE,), produces_qualification=None,
    exams=(ExamRequirement("IELTS", 6.5, "ielts"),),
    time_cost_months=0, money_cost_azn=(0, 20000), citation=CAMPUS_CHINA,
)

ALL_ROUTES: tuple[Route, ...] = (
    AZ_PREP_YEAR,
    TR_BACHELOR_DIRECT, TR_BACHELOR_YOS, PL_BACHELOR_DIRECT, US_BACHELOR_DIRECT,
    CN_BACHELOR_CSC, DE_BACHELOR_STUDIENKOLLEG, DE_BACHELOR_DIRECT,
    UK_BACHELOR_FOUNDATION, UK_BACHELOR_DIRECT,
    TR_MASTER_DIRECT, DE_MASTER_DIRECT, UK_MASTER_DIRECT, US_MASTER_DIRECT,
    PL_MASTER_DIRECT, CN_MASTER_DIRECT,
)
