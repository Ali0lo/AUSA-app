"""
Admissions Timeline, Calendar & Milestone Engine for AUSA.

Provides:
- Domain schemas for application milestones, admissions cycles, and urgency tiers.
- A curated database of 24+ verified international & domestic application gates
  (UK UCAS, Germany Uni-Assist/VPD, US Common App, Azerbaijan State Programme 2022-2026,
  Türkiye Bursları, Stipendium Hungaricum, Chevening, Italian DSU/Universitaly, etc.).
- Real-time countdown calculator with urgency classification.
- RFC 5545 compliant iCalendar (.ics) generation engine for export to Google/Apple/Outlook calendars.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MilestoneType(str, Enum):
    PORTAL_OPEN = "PORTAL_OPEN"
    EARLY_DEADLINE = "EARLY_DEADLINE"
    EQUAL_CONSIDERATION = "EQUAL_CONSIDERATION"
    REGULAR_DEADLINE = "REGULAR_DEADLINE"
    SCHOLARSHIP_DEADLINE = "SCHOLARSHIP_DEADLINE"
    DECISION_RELEASE = "DECISION_RELEASE"
    VISA_WINDOW = "VISA_WINDOW"
    DOCUMENT_SUBMISSION = "DOCUMENT_SUBMISSION"


class IntakeSeason(str, Enum):
    SPRING_2026 = "spring_2026"
    FALL_2026 = "fall_2026"
    WINTER_2026 = "winter_2026"
    SPRING_2027 = "spring_2027"
    FALL_2027 = "fall_2027"
    ROLLING = "rolling"


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"    # <= 14 days
    UPCOMING = "UPCOMING"    # 15 - 60 days
    OPEN = "OPEN"            # > 60 days
    PASSED = "PASSED"        # Already past deadline


class DegreeLevel(str, Enum):
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    ALL = "all"


class CountryCode(str, Enum):
    GB = "GB"
    DE = "DE"
    US = "US"
    AZ = "AZ"
    TR = "TR"
    IT = "IT"
    HU = "HU"
    FR = "FR"
    PL = "PL"
    GLOBAL = "GLOBAL"


class MilestoneItem(BaseModel):
    id: str
    title: str
    portal_name: str
    country_code: CountryCode
    country_name: str
    flag: str
    degree_level: DegreeLevel
    intake: IntakeSeason
    milestone_type: MilestoneType
    target_date: date
    deadline_time: str = "23:59 Local Time"
    description: str
    official_portal_url: str
    requirements_summary: List[str] = Field(default_factory=list)
    is_hard_deadline: bool = True
    days_remaining: int = 0
    urgency: UrgencyLevel = UrgencyLevel.OPEN
    is_state_programme_eligible: bool = True


class MilestoneFilter(BaseModel):
    country_code: Optional[CountryCode] = None
    degree_level: Optional[DegreeLevel] = None
    intake: Optional[IntakeSeason] = None
    urgency: Optional[UrgencyLevel] = None
    milestone_type: Optional[MilestoneType] = None
    is_state_programme_eligible: Optional[bool] = None
    search_query: Optional[str] = None


class TimelineSchedule(BaseModel):
    total_milestones: int
    critical_count: int
    upcoming_count: int
    open_count: int
    passed_count: int
    milestones: List[MilestoneItem]
    generated_at: datetime


class CustomReminderRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    target_date: date
    country_name: str = "International"
    description: Optional[str] = ""
    portal_url: Optional[str] = ""
    reminder_days_before: int = Field(default=3, ge=1, le=30)


# ==============================================================================
# Verified Global & Bilateral Admissions Milestones (2026/2027 Cycle)
# ==============================================================================

RAW_MILESTONES: List[dict] = [
    {
        "id": "gb_ucas_oxbridge_2026",
        "title": "UCAS Oxbridge, Medicine & Dentistry Early Deadline",
        "portal_name": "UCAS (Universities and Colleges Admissions Service)",
        "country_code": CountryCode.GB,
        "country_name": "United Kingdom",
        "flag": "🇬🇧",
        "degree_level": DegreeLevel.BACHELOR,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.EARLY_DEADLINE,
        "target_date": date(2026, 10, 15),
        "deadline_time": "18:00 (UK Time)",
        "description": "Strict deadline for all Oxford, Cambridge, and UK medicine, dentistry, and veterinary courses.",
        "official_portal_url": "https://www.ucas.com",
        "requirements_summary": [
            "UCAS Personal Statement (4,000 chars)",
            "Predicted A-Level / IB / Attestat grades",
            "Academic reference letter",
            "University admissions test registration (UCAT, ESAT, TMUA)",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "chevening_global_2026",
        "title": "UK Chevening Master's Scholarship Deadline",
        "portal_name": "Chevening OAS Portal",
        "country_code": CountryCode.GB,
        "country_name": "United Kingdom",
        "flag": "🇬🇧",
        "degree_level": DegreeLevel.MASTER,
        "intake": IntakeSeason.FALL_2027,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2026, 11, 3),
        "deadline_time": "12:00 (GMT)",
        "description": "Prestigious UK Foreign, Commonwealth & Development Office full master's scholarship for future Azerbaijani leaders.",
        "official_portal_url": "https://www.chevening.org/scholarship/azerbaijan/",
        "requirements_summary": [
            "4 Core Essays (Leadership, Networking, Study in UK, Career Plan)",
            "Minimum 2,800 hours of documented work experience",
            "Undergraduate degree diploma & transcript (GPA 3.0+/4.0)",
            "Three eligible UK Master's course selections",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": False,
    },
    {
        "id": "us_common_app_ed1_2026",
        "title": "US Common App Early Action & Early Decision I (EA/ED1)",
        "portal_name": "Common Application",
        "country_code": CountryCode.US,
        "country_name": "United States",
        "flag": "🇺🇸",
        "degree_level": DegreeLevel.BACHELOR,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.EARLY_DEADLINE,
        "target_date": date(2026, 11, 1),
        "deadline_time": "23:59 (Applicant Local Time)",
        "description": "Binding (ED) and non-binding (EA) early admission round for top US universities (MIT, Harvard, Stanford, Columbia).",
        "official_portal_url": "https://www.commonapp.org",
        "requirements_summary": [
            "Common App Personal Essay (650 words)",
            "Supplemental university-specific essays",
            "High School Official Transcript with school profile",
            "Counselor recommendation + 2 teacher evaluations",
            "SAT/ACT score report or test-optional declaration",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "us_grad_priority_2026",
        "title": "US Graduate School Priority Fellowship & PhD Deadline",
        "portal_name": "University Graduate Admissions Portals",
        "country_code": CountryCode.US,
        "country_name": "United States",
        "flag": "🇺🇸",
        "degree_level": DegreeLevel.MASTER,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2026, 12, 1),
        "deadline_time": "23:59 (EST)",
        "description": "First priority round for graduate institutional assistantships (TA/RA), fellowships, and STEM PhD programs.",
        "official_portal_url": "https://grad.gatech.edu",
        "requirements_summary": [
            "Statement of Purpose (SOP)",
            "3 Academic letters of recommendation",
            "Official Bachelor's transcripts (WES evaluation if required)",
            "GRE General score report (where required)",
            "TOEFL iBT (100+) or IELTS Academic (7.5+)",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "us_common_app_rd_2027",
        "title": "US Regular Decision (RD) & ED II Deadline",
        "portal_name": "Common Application",
        "country_code": CountryCode.US,
        "country_name": "United States",
        "flag": "🇺🇸",
        "degree_level": DegreeLevel.BACHELOR,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.REGULAR_DEADLINE,
        "target_date": date(2027, 1, 5),
        "deadline_time": "23:59 (Applicant Local Time)",
        "description": "Standard admissions window for major US undergraduate universities.",
        "official_portal_url": "https://www.commonapp.org",
        "requirements_summary": [
            "Complete Common App dossier",
            "Mid-year senior year grades report",
            "Financial certification (ISFAA / CSS Profile)",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "france_eiffel_2027",
        "title": "France Excellence Eiffel Scholarship Institution Deadline",
        "portal_name": "Campus France",
        "country_code": CountryCode.FR,
        "country_name": "France",
        "flag": "🇫🇷",
        "degree_level": DegreeLevel.MASTER,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2027, 1, 8),
        "deadline_time": "18:00 (Paris Time)",
        "description": "Pre-selection of candidates by French higher education institutions for the Eiffel excellence grant (€1,181/mo).",
        "official_portal_url": "https://www.campusfrance.org/en/the-eiffel-scholarship-program",
        "requirements_summary": [
            "Formal acceptance or pre-admission endorsement from French university",
            "Top 10% academic class standing",
            "Project proposal & CV",
            "Language certificate (English C1 or French B2)",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "stipendium_hungaricum_2027",
        "title": "Stipendium Hungaricum Online Portal Deadline",
        "portal_name": "Tempus Public Foundation DreamApply",
        "country_code": CountryCode.HU,
        "country_name": "Hungary",
        "flag": "🇭🇺",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2027, 1, 15),
        "deadline_time": "14:00 (CET)",
        "description": "Full bilateral government scholarship covering 200 Azerbaijani students annually (tuition, stipend, dorm, insurance).",
        "official_portal_url": "https://apply.stipendiumhungaricum.hu",
        "requirements_summary": [
            "DreamApply online submission (2 chosen degree programs)",
            "Motivational letter (min 1 page)",
            "Medical certificate & proof of foreign language proficiency",
            "Ministry of Science and Education of Azerbaijan bilateral nomination clearance",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": False,
    },
    {
        "id": "de_summer_uniassist_2027",
        "title": "Germany Summer Intake (Sommersemester) Uni-Assist Deadline",
        "portal_name": "Uni-Assist e.V.",
        "country_code": CountryCode.DE,
        "country_name": "Germany",
        "flag": "🇩🇪",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.SPRING_2027,
        "milestone_type": MilestoneType.REGULAR_DEADLINE,
        "target_date": date(2027, 1, 15),
        "deadline_time": "23:59 (CET)",
        "description": "Cutoff for Summer semester applications at public universities across Germany.",
        "official_portal_url": "https://www.uni-assist.de",
        "requirements_summary": [
            "Certified German or English translation of Bachelor/Attestat",
            "Vorprüfungsdokumentation (VPD) if required by target university",
            "TestDaF (4x4) or IELTS (6.5+) depending on language of instruction",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "gb_ucas_equal_consideration_2027",
        "title": "UCAS Undergraduate Equal Consideration Deadline",
        "portal_name": "UCAS",
        "country_code": CountryCode.GB,
        "country_name": "United Kingdom",
        "flag": "🇬🇧",
        "degree_level": DegreeLevel.BACHELOR,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.EQUAL_CONSIDERATION,
        "target_date": date(2027, 1, 29),
        "deadline_time": "18:00 (UK Time)",
        "description": "Standard UK national deadline guaranteeing equal evaluation for all undergraduate degree choices.",
        "official_portal_url": "https://www.ucas.com",
        "requirements_summary": [
            "Up to 5 UK course choices",
            "Completed UCAS application form and paid fee (£28.50)",
            "Verified teacher/counselor recommendation",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "turkiye_burslari_2027",
        "title": "Türkiye Bursları Government Scholarship Deadline",
        "portal_name": "TBBS (Türkiye Bursları Başvuru Sistemi)",
        "country_code": CountryCode.TR,
        "country_name": "Turkey",
        "flag": "🇹🇷",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2027, 2, 20),
        "deadline_time": "23:59 (Istanbul Time)",
        "description": "Full Turkish government grant covering tuition, monthly stipend, flights, accommodation, and 1-year TÖMER preparatory.",
        "official_portal_url": "https://turkiyeburslari.gov.tr",
        "requirements_summary": [
            "Attestat / Bachelor's Diploma with minimum 75% GPA (80% for engineering, 90% for medicine)",
            "Letter of Intent (Niyet Mektubu) explaining why Turkey",
            "Academic CV and extracurricular certificates",
            "Passport copy and biometric photo",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": False,
    },
    {
        "id": "pl_nawa_banach_2027",
        "title": "Poland NAWA Stefan Banach Scholarship Application",
        "portal_name": "NAWA ICT System",
        "country_code": CountryCode.PL,
        "country_name": "Poland",
        "flag": "🇵🇱",
        "degree_level": DegreeLevel.MASTER,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2027, 3, 31),
        "deadline_time": "15:00 (Warsaw Time)",
        "description": "Polish National Agency for Academic Exchange full tuition waiver + 1,700 PLN monthly stipend for engineering & science master's.",
        "official_portal_url": "https://nawa.gov.pl/en/students/foreign-students/the-banach-scholarship-programme",
        "requirements_summary": [
            "BSc Diploma in STEM or Social Sciences",
            "Minimum B2 English certificate or Polish B1",
            "Graduation within last 2 calendar years",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": False,
    },
    {
        "id": "aze_dp_portal_open_2026",
        "title": "State Programme 2022–2026 (DP) Portal Opens for Submissions",
        "portal_name": "Müasir Təhsil Portalı (portal.edu.az)",
        "country_code": CountryCode.AZ,
        "country_name": "Azerbaijan",
        "flag": "🇦🇿",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.PORTAL_OPEN,
        "target_date": date(2026, 4, 1),
        "deadline_time": "10:00 (Baku Time)",
        "description": "Ministry of Science and Education of Azerbaijan opens electronic submissions for 2022-2026 State Programme funding.",
        "official_portal_url": "https://dp.edu.az",
        "requirements_summary": [
            "Unconditional or Conditional Acceptance letter from approved Top-500 university",
            "Attestat / Bachelor's Diploma and official transcript",
            "State Programme Motivation Letter with Repatriation / Economic Contribution clause",
            "Two signed recommendation letters",
        ],
        "is_hard_deadline": False,
        "is_state_programme_eligible": True,
    },
    {
        "id": "it_universitaly_open_2026",
        "title": "Italy Universitaly Pre-Enrollment & Visa Window Opens",
        "portal_name": "Universitaly Portal",
        "country_code": CountryCode.IT,
        "country_name": "Italy",
        "flag": "🇮🇹",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.DOCUMENT_SUBMISSION,
        "target_date": date(2026, 4, 15),
        "deadline_time": "23:59 (Rome Time)",
        "description": "Mandatory Italian Ministry of Foreign Affairs pre-enrollment platform for non-EU students to obtain official visa summary.",
        "official_portal_url": "https://www.universitaly.it",
        "requirements_summary": [
            "University admission letter",
            "Declaration of Value (DOV) or CIMEA Statement of Comparability",
            "Language certificate (English B2/C1 or Italian B2)",
        ],
        "is_hard_deadline": False,
        "is_state_programme_eligible": True,
    },
    {
        "id": "us_fulbright_azerbaijan_2026",
        "title": "US Embassy Baku Fulbright Foreign Student Program",
        "portal_name": "IIE Fulbright Portal",
        "country_code": CountryCode.US,
        "country_name": "United States",
        "flag": "🇺🇸",
        "degree_level": DegreeLevel.MASTER,
        "intake": IntakeSeason.FALL_2027,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2026, 6, 1),
        "deadline_time": "18:00 (Baku Time)",
        "description": "Full bilateral US Government grant for Azerbaijani graduates pursuing a two-year Master's degree in the USA.",
        "official_portal_url": "https://az.usembassy.gov/education-culture/educational-programs/fulbright-foreign-student-program/",
        "requirements_summary": [
            "Azerbaijani citizenship and Bachelor's degree by time of departure",
            "TOEFL iBT (minimum 80) or IELTS (6.5+)",
            "Study/Research Objective and Personal Statement",
            "Commitment to return to Azerbaijan for at least two years (J-1 visa two-year rule)",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": False,
    },
    {
        "id": "aze_dp_deadline_2026",
        "title": "State Programme 2022–2026 Final Application Deadline",
        "portal_name": "portal.edu.az / dp.edu.az",
        "country_code": CountryCode.AZ,
        "country_name": "Azerbaijan",
        "flag": "🇦🇿",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.REGULAR_DEADLINE,
        "target_date": date(2026, 6, 15),
        "deadline_time": "18:00 (Baku Time)",
        "description": "Hard cutoff for all documents under the 2022–2026 State Programme for Youth Study Abroad.",
        "official_portal_url": "https://dp.edu.az",
        "requirements_summary": [
            "Uploaded university unconditional or conditional offer",
            "Medical health certificate Form 086",
            "No criminal record certificate (ASAN Xidmət)",
            "Complete military service status / postponement document",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "de_winter_uniassist_2026",
        "title": "Germany Winter Semester (Wintersemester) Uni-Assist & Direct Deadline",
        "portal_name": "Uni-Assist / Hochschulstart",
        "country_code": CountryCode.DE,
        "country_name": "Germany",
        "flag": "🇩🇪",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.REGULAR_DEADLINE,
        "target_date": date(2026, 7, 15),
        "deadline_time": "23:59 (CET)",
        "description": "Crucial national deadline for public university admissions across Germany (TUM, LMU, RWTH Aachen, Heidelberg).",
        "official_portal_url": "https://www.uni-assist.de",
        "requirements_summary": [
            "APS Certificate (if applicable) or VPD certificate issued by Uni-Assist",
            "Verified certified copies of educational transcripts",
            "Proof of Sperrkonto (€11,904) blocked account or DAAD grant",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "it_dsu_regional_2026",
        "title": "Italy Regional DSU / ER.GO Scholarship Deadline",
        "portal_name": "Azienda DSU / ER.GO / Disco Lazio",
        "country_code": CountryCode.IT,
        "country_name": "Italy",
        "flag": "🇮🇹",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2026, 8, 25),
        "deadline_time": "13:00 (Italian Time)",
        "description": "Need-based regional scholarship covering 100% tuition waiver, free dining hall meals, and up to €7,000 yearly stipend.",
        "official_portal_url": "https://www.dsu.toscana.it",
        "requirements_summary": [
            "ISEE Parificato (ISEE-U) income calculation certificate under €27,000",
            "Apostilled family income and property documents translated to Italian",
            "Enrollment matriculation number at an Italian public university",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "de_daad_epos_2026",
        "title": "Germany DAAD EPOS Development Postgraduate Deadline",
        "portal_name": "DAAD Portal",
        "country_code": CountryCode.DE,
        "country_name": "Germany",
        "flag": "🇩🇪",
        "degree_level": DegreeLevel.MASTER,
        "intake": IntakeSeason.FALL_2027,
        "milestone_type": MilestoneType.SCHOLARSHIP_DEADLINE,
        "target_date": date(2026, 9, 30),
        "deadline_time": "23:59 (CET)",
        "description": "DAAD full funding (€934/mo, health insurance, flights) for development-related postgraduate courses in Germany.",
        "official_portal_url": "https://www.daad.de/en/information-services-for-higher-education-institutions/further-information-on-daad-programmes/epos/",
        "requirements_summary": [
            "DAAD Application Form & Europass CV",
            "Hand-signed letter of motivation with development relevance",
            "Two years of professional work experience in relevant sector",
            "Letter of recommendation from current employer",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "uk_visa_cas_window_2026",
        "title": "UK Student Visa Application & CAS Confirmation Window",
        "portal_name": "UK Visas and Immigration (GOV.UK)",
        "country_code": CountryCode.GB,
        "country_name": "United Kingdom",
        "flag": "🇬🇧",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.VISA_WINDOW,
        "target_date": date(2026, 8, 10),
        "deadline_time": "23:59 (UK Time)",
        "description": "Critical visa filing window ensuring arrival in the UK before September term commencement.",
        "official_portal_url": "https://www.gov.uk/student-visa",
        "requirements_summary": [
            "Official CAS (Confirmation of Acceptance for Studies) number",
            "Proof of 28 consecutive days maintenance funds (£1,334/mo London, £1,023/mo outer London)",
            "IHS (Immigration Health Surcharge) payment (£776/yr)",
            "TB test certificate from IOM Baku",
        ],
        "is_hard_deadline": False,
        "is_state_programme_eligible": True,
    },
    {
        "id": "de_vpd_window_winter_2026",
        "title": "Germany Uni-Assist VPD (Preliminary Review) Recommended Submission",
        "portal_name": "Uni-Assist e.V.",
        "country_code": CountryCode.DE,
        "country_name": "Germany",
        "flag": "🇩🇪",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.DOCUMENT_SUBMISSION,
        "target_date": date(2026, 6, 1),
        "deadline_time": "23:59 (CET)",
        "description": "Uni-Assist takes 4-6 weeks to process VPD certificates. Submitting by June 1 ensures timely delivery before the July 15 university cutoff.",
        "official_portal_url": "https://www.uni-assist.de/en/how-to-apply/plan-your-application/vpd/",
        "requirements_summary": [
            "Scanned notarized and translated school leaving certificates",
            "Proof of online fee payment (€75 first university, €30 each additional)",
        ],
        "is_hard_deadline": False,
        "is_state_programme_eligible": True,
    },
    {
        "id": "aze_dp_interview_results_2026",
        "title": "State Programme 2022–2026 Committee Interviews & Results",
        "portal_name": "Ministry of Science and Education (dp.edu.az)",
        "country_code": CountryCode.AZ,
        "country_name": "Azerbaijan",
        "flag": "🇦🇿",
        "degree_level": DegreeLevel.ALL,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.DECISION_RELEASE,
        "target_date": date(2026, 7, 10),
        "deadline_time": "18:00 (Baku Time)",
        "description": "Shortlisted applicants participate in interview rounds covering academic motivation and Azerbaijani economic contribution.",
        "official_portal_url": "https://dp.edu.az",
        "requirements_summary": [
            "In-person or video panel interview with expert commission",
            "Presentation of study trajectory and repatriation commitment",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": True,
    },
    {
        "id": "uk_ucas_clearing_2026",
        "title": "UK UCAS Clearing & Late Undergraduate Direct Placements Open",
        "portal_name": "UCAS Clearing Portal",
        "country_code": CountryCode.GB,
        "country_name": "United Kingdom",
        "flag": "🇬🇧",
        "degree_level": DegreeLevel.BACHELOR,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.PORTAL_OPEN,
        "target_date": date(2026, 7, 5),
        "deadline_time": "08:00 (UK Time)",
        "description": "Alternative pathway for applicants without existing offers or those achieving higher than expected exam results.",
        "official_portal_url": "https://www.ucas.com/clearing",
        "requirements_summary": [
            "Official final high school exam marks / Attestat grades",
            "Valid English proficiency certificate (IELTS UKVI)",
            "Direct telephone/online interview with university admissions tutors",
        ],
        "is_hard_deadline": False,
        "is_state_programme_eligible": True,
    },
    {
        "id": "tr_tryos_exam_deadline_2026",
        "title": "Turkey TR-YÖS Central Foreign Student Exam Registration",
        "portal_name": "ÖSYM (Ölçme, Seçme ve Yerleştirme Merkezi)",
        "country_code": CountryCode.TR,
        "country_name": "Turkey",
        "flag": "🇹🇷",
        "degree_level": DegreeLevel.BACHELOR,
        "intake": IntakeSeason.FALL_2026,
        "milestone_type": MilestoneType.EARLY_DEADLINE,
        "target_date": date(2026, 3, 28),
        "deadline_time": "23:59 (Istanbul Time)",
        "description": "Official Turkish exam for international students applying directly to Turkish state and foundation universities.",
        "official_portal_url": "https://www.osym.gov.tr",
        "requirements_summary": [
            "Biometric photo and valid foreign passport",
            "Exam registration fee paid via ÖSYM e-İşlemler",
        ],
        "is_hard_deadline": True,
        "is_state_programme_eligible": False,
    },
    {
        "id": "us_css_profile_open_2026",
        "title": "US College Board CSS Profile Financial Aid Portal Opens",
        "portal_name": "College Board CSS Profile",
        "country_code": CountryCode.US,
        "country_name": "United States",
        "flag": "🇺🇸",
        "degree_level": DegreeLevel.BACHELOR,
        "intake": IntakeSeason.FALL_2027,
        "milestone_type": MilestoneType.PORTAL_OPEN,
        "target_date": date(2026, 10, 1),
        "deadline_time": "00:01 (EST)",
        "description": "Financial aid portal used by top private US colleges to award institutional need-based grants to international students.",
        "official_portal_url": "https://cssprofile.collegeboard.org",
        "requirements_summary": [
            "Tax records and official family earnings documentation",
            "Bank balance certifications and real estate equity disclosures",
        ],
        "is_hard_deadline": False,
        "is_state_programme_eligible": True,
    }
]


# ==============================================================================
# Domain Calculation & Engine Logic
# ==============================================================================

def calculate_milestone_status(target_date: date, reference_date: Optional[date] = None) -> tuple[int, UrgencyLevel]:
    """Calculates days remaining from reference_date to target_date and assigns urgency tier."""
    ref = reference_date or date.today()
    delta = (target_date - ref).days

    if delta < 0:
        return delta, UrgencyLevel.PASSED
    elif delta <= 14:
        return delta, UrgencyLevel.CRITICAL
    elif delta <= 60:
        return delta, UrgencyLevel.UPCOMING
    else:
        return delta, UrgencyLevel.OPEN


def build_milestone_item(raw: dict, reference_date: Optional[date] = None) -> MilestoneItem:
    """Builds a hydrated MilestoneItem with real-time countdown calculations."""
    target_dt = raw["target_date"]
    days_left, urgency = calculate_milestone_status(target_dt, reference_date)

    return MilestoneItem(
        id=raw["id"],
        title=raw["title"],
        portal_name=raw["portal_name"],
        country_code=raw["country_code"],
        country_name=raw["country_name"],
        flag=raw["flag"],
        degree_level=raw["degree_level"],
        intake=raw["intake"],
        milestone_type=raw["milestone_type"],
        target_date=target_dt,
        deadline_time=raw.get("deadline_time", "23:59 Local Time"),
        description=raw["description"],
        official_portal_url=raw["official_portal_url"],
        requirements_summary=raw.get("requirements_summary", []),
        is_hard_deadline=raw.get("is_hard_deadline", True),
        days_remaining=days_left,
        urgency=urgency,
        is_state_programme_eligible=raw.get("is_state_programme_eligible", True),
    )


def filter_milestones(
    milestones: List[MilestoneItem],
    filters: Optional[MilestoneFilter] = None,
) -> List[MilestoneItem]:
    """Filters milestones according to user criteria and sorts by target date."""
    if not filters:
        return sorted(milestones, key=lambda m: m.target_date)

    filtered = []
    for m in milestones:
        if filters.country_code and m.country_code != filters.country_code:
            continue
        if filters.degree_level and filters.degree_level != DegreeLevel.ALL:
            if m.degree_level != DegreeLevel.ALL and m.degree_level != filters.degree_level:
                continue
        if filters.intake and m.intake != filters.intake:
            continue
        if filters.urgency and m.urgency != filters.urgency:
            continue
        if filters.milestone_type and m.milestone_type != filters.milestone_type:
            continue
        if filters.is_state_programme_eligible is not None:
            if m.is_state_programme_eligible != filters.is_state_programme_eligible:
                continue
        if filters.search_query:
            query = filters.search_query.lower()
            reqs = " ".join(m.requirements_summary)
            text_corpus = f"{m.title} {m.description} {m.portal_name} {m.country_name} {m.deadline_time} {reqs}".lower()
            if query not in text_corpus:
                continue

        filtered.append(m)

    return sorted(filtered, key=lambda m: m.target_date)


def get_timeline_schedule(
    filters: Optional[MilestoneFilter] = None,
    reference_date: Optional[date] = None,
) -> TimelineSchedule:
    """Generates the full timeline schedule summary with statistics."""
    ref = reference_date or date.today()
    hydrated = [build_milestone_item(raw, ref) for raw in RAW_MILESTONES]
    filtered = filter_milestones(hydrated, filters)

    crit = sum(1 for m in filtered if m.urgency == UrgencyLevel.CRITICAL)
    upc = sum(1 for m in filtered if m.urgency == UrgencyLevel.UPCOMING)
    opn = sum(1 for m in filtered if m.urgency == UrgencyLevel.OPEN)
    psd = sum(1 for m in filtered if m.urgency == UrgencyLevel.PASSED)

    return TimelineSchedule(
        total_milestones=len(filtered),
        critical_count=crit,
        upcoming_count=upc,
        open_count=opn,
        passed_count=psd,
        milestones=filtered,
        generated_at=datetime.now(timezone.utc),
    )


# ==============================================================================
# RFC 5545 iCalendar (.ics) Generator Engine
# ==============================================================================

def _escape_ics_text(text: str) -> str:
    """Escapes special characters in accordance with RFC 5545 section 3.3.11."""
    if not text:
        return ""
    clean = text.replace("\\", "\\\\")
    clean = clean.replace(";", "\\;")
    clean = clean.replace(",", "\\,")
    clean = clean.replace("\r\n", "\\n").replace("\n", "\\n")
    return clean


def generate_single_vevent(m: MilestoneItem, now_str: str) -> str:
    """Generates a RFC 5545 VEVENT string for a single milestone."""
    dtstart = m.target_date.strftime("%Y%m%d")
    title_escaped = _escape_ics_text(f"{m.flag} {m.title}")
    
    desc_lines = [
        f"Portal: {m.portal_name}",
        f"Deadline Time: {m.deadline_time}",
        f"Description: {m.description}",
        f"Official URL: {m.official_portal_url}",
    ]
    if m.requirements_summary:
        desc_lines.append("Key Requirements:")
        for req in m.requirements_summary:
            desc_lines.append(f" - {req}")

    desc_escaped = _escape_ics_text("\n".join(desc_lines))
    url_escaped = _escape_ics_text(m.official_portal_url)

    lines = [
        "BEGIN:VEVENT",
        f"UID:{m.id}@ausa.edu.az",
        f"DTSTAMP:{now_str}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"SUMMARY:{title_escaped}",
        f"DESCRIPTION:{desc_escaped}",
        f"URL:{url_escaped}",
        "STATUS:CONFIRMED",
        "CLASS:PUBLIC",
        "TRANSP:TRANSPARENT",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {title_escaped}",
        "TRIGGER:-P3D",
        "END:VALARM",
        "END:VEVENT",
    ]
    return "\r\n".join(lines)


def generate_icalendar_content(
    milestones: List[MilestoneItem],
    calendar_name: str = "AUSA Admissions Deadlines 2026/2027",
) -> str:
    """
    Generates a full RFC 5545 compliant iCalendar string.
    Works natively across Google Calendar, Apple Calendar, and Microsoft Outlook.
    """
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    escaped_cal_name = _escape_ics_text(calendar_name)

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AUSA//Admissions Timeline Engine v1.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escaped_cal_name}",
        "X-WR-TIMEZONE:Asia/Baku",
    ]

    for m in milestones:
        lines.append(generate_single_vevent(m, now_str))

    lines.append("END:VCALENDAR\r\n")
    return "\r\n".join(lines)


def create_custom_event_ics(req: CustomReminderRequest) -> str:
    """Generates an RFC 5545 event for a user-submitted deadline reminder."""
    clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", req.title.lower())[:30]
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dtstart = req.target_date.strftime("%Y%m%d")

    title_escaped = _escape_ics_text(f"📌 {req.title}")
    desc_lines = [f"Destination / Portal: {req.country_name}"]
    if req.description:
        desc_lines.append(f"Notes: {req.description}")
    if req.portal_url:
        desc_lines.append(f"Portal: {req.portal_url}")
    desc_escaped = _escape_ics_text("\n".join(desc_lines))

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AUSA//Admissions Custom Reminder//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:AUSA Personal Deadline",
        "BEGIN:VEVENT",
        f"UID:custom_{clean_id}_{dtstart}@ausa.edu.az",
        f"DTSTAMP:{now_str}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"SUMMARY:{title_escaped}",
        f"DESCRIPTION:{desc_escaped}",
        f"URL:{_escape_ics_text(req.portal_url or '')}",
        "STATUS:CONFIRMED",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {title_escaped}",
        f"TRIGGER:-P{req.reminder_days_before}D",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR\r\n",
    ]
    return "\r\n".join(lines)
