"""
Student Application Dashboard & Comparison Workbench Domain Engine.

Provides:
- Application lifecycle stages and Dream / Target / Safety tier classification.
- Dynamic country-specific prerequisite document checklist generator.
- Multi-university comparison matrix engine (tuition, living costs, blocked accounts,
  post-study work visa rights, and language score baselines).
- Strictly ADR-0008 compliant: Zero synthetic 0.5/0.3/0.2 percentage weights.
  All tiering is determined via discrete route criteria, academic thresholds, and acceptance selectivity.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ApplicationStage(str, Enum):
    SHORTLISTED = "shortlisted"
    DOCUMENT_GATHERING = "document_gathering"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER_RECEIVED = "offer_received"
    OFFER_ACCEPTED = "offer_accepted"
    REJECTED = "rejected"
    VISA_PROCESSING = "visa_processing"


class AdmissionTier(str, Enum):
    DREAM = "DREAM"      # Reach: Acceptance rate < 15%, QS Top 50, or strict GPA/GMAT cutoff
    TARGET = "TARGET"    # Realistic: Candidate matches all prerequisite requirements
    SAFETY = "SAFETY"    # High Probability: Candidate substantially exceeds academic & language thresholds


class DocumentCategory(str, Enum):
    ACADEMIC = "ACADEMIC"
    LANGUAGE = "LANGUAGE"
    FINANCIAL = "FINANCIAL"
    LEGAL_IMMIGRATION = "LEGAL_IMMIGRATION"
    APPLICATION_ASSETS = "APPLICATION_ASSETS"


class DocumentItem(BaseModel):
    id: str
    title: str
    category: DocumentCategory
    description: str
    is_mandatory: bool = True
    issuing_authority: str
    translation_required: bool = False
    apostille_required: bool = False
    estimated_processing_days: int = 7
    notes: Optional[str] = None


class DocumentChecklistRequest(BaseModel):
    country_code: str = Field(..., description="ISO 2-letter country code (GB, DE, US, IT, TR, HU, AZ, etc.)")
    degree_level: str = Field(default="master", description="bachelor or master")
    is_state_programme: bool = Field(default=False, description="Applying under 2022-2026 State Programme")
    has_scholarship: bool = Field(default=False, description="Has external or university funding")


class DocumentChecklistResult(BaseModel):
    country_code: str
    country_name: str
    degree_level: str
    total_documents: int
    mandatory_count: int
    documents: List[DocumentItem]
    country_specific_notes: List[str]


class UniversityComparisonItem(BaseModel):
    id: str
    university_name: str
    country_code: str
    country_name: str
    flag: str
    city: str
    qs_rank: Optional[int] = None
    program_name: str
    degree_level: str = "master"
    
    # Financial metrics (EUR)
    tuition_eur_annual: float
    living_cost_eur_monthly: float
    blocked_account_required_eur: float
    total_first_year_eur: float
    
    # Currency details
    original_tuition: str
    
    # Language thresholds
    ielts_min: float = 6.5
    toefl_min: int = 80
    
    # Post-Study Work Visa (PSWR)
    post_study_work_visa_duration_months: int
    post_study_work_visa_name: str
    post_study_work_visa_summary: str
    
    # Route & State Programme
    state_programme_eligible: bool = True
    admission_tier: AdmissionTier = AdmissionTier.TARGET
    tier_rationale: str = ""


class ComparisonRequest(BaseModel):
    university_ids: List[str] = Field(..., min_length=1, max_length=5, description="1 to 5 university identifiers to compare")
    student_gpa: Optional[float] = Field(None, ge=2.0, le=5.0, description="Student Attestat (max 5) or University GPA (max 4)")
    student_ielts: Optional[float] = Field(None, ge=4.0, le=9.0)
    student_budget_eur_annual: Optional[float] = Field(None, ge=0)


class ComparisonResult(BaseModel):
    items: List[UniversityComparisonItem]
    lowest_cost_university: str
    longest_pswr_university: str
    best_ranked_university: Optional[str] = None
    average_first_year_cost_eur: float
    comparison_summary_notes: List[str]


class TierClassificationRequest(BaseModel):
    university_name: str
    country_code: str
    qs_rank: Optional[int] = None
    program_field: str = "stem"
    student_gpa: float = Field(..., ge=2.0, le=5.0)
    student_gpa_max: float = Field(default=4.0)
    student_ielts: Optional[float] = Field(None, ge=4.0, le=9.0)
    has_relevant_experience: bool = True
    is_state_programme_target: bool = False


class TierClassificationResult(BaseModel):
    tier: AdmissionTier
    badge_label: str
    rationale: str
    qualification_factors: List[str]
    risk_factors: List[str]
    action_recommendations: List[str]


# ==============================================================================
# Verified Document Catalogs by Destination Country
# ==============================================================================

BASE_ACADEMIC_DOCS = [
    DocumentItem(
        id="doc_diploma_transcript",
        title="Diplom və Akademik Transkript (Attestat / Bakalavr)",
        category=DocumentCategory.ACADEMIC,
        description="Bakalavr diplomu və əlavəsi və ya məktəb attestatı. Cari tələbələr üçün rəsmi arayış və transkript.",
        is_mandatory=True,
        issuing_authority="Təhsil Müəssisəsi / Universitet",
        translation_required=True,
        apostille_required=True,
        estimated_processing_days=5,
    ),
    DocumentItem(
        id="doc_recommendation_letters",
        title="2 Ədəd Akademik / Peşəkar Tövsiyə Məktubu (LoR)",
        category=DocumentCategory.APPLICATION_ASSETS,
        description="Fənn müəllimləri və ya kafedra rəhbəri tərəfindən imzalanmış və universitet blankında hazırlanmış tövsiyə məktubları.",
        is_mandatory=True,
        issuing_authority="Fənn Müəllimləri / Tədqiqat Rəhbəri",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=7,
    ),
    DocumentItem(
        id="doc_sop",
        title="Statement of Purpose / Motivasiya Məktubu",
        category=DocumentCategory.APPLICATION_ASSETS,
        description="Akademik baza, tədqiqat maraqları, universitet seçimi və karyera hədəflərini əhatə edən 500-1000 sözlük inşa.",
        is_mandatory=True,
        issuing_authority="Müraciətçi",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=3,
    ),
    DocumentItem(
        id="doc_cv",
        title="Akademik CV / Resume",
        category=DocumentCategory.APPLICATION_ASSETS,
        description="Beynəlxalq standartlara uyğun (Europass və ya 1-səhifəlik US formatı) akademik və layihə təcrübəsi xülasəsi.",
        is_mandatory=True,
        issuing_authority="Müraciətçi",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=2,
    ),
    DocumentItem(
        id="doc_language_cert",
        title="Beynəlxalq Dil Sertifikatı (IELTS / TOEFL / Duolingo)",
        category=DocumentCategory.LANGUAGE,
        description="Rəsmi imtahan mərkəzindən təsdiq olunmuş dil biliyi nəticəsi (adətən minimum IELTS 6.5 və ya TOEFL 80).",
        is_mandatory=True,
        issuing_authority="British Council / IDP / ETS",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=14,
    ),
    DocumentItem(
        id="doc_passport",
        title="Xarici Pasport (Ümumvətəndaş Pasportu)",
        category=DocumentCategory.LEGAL_IMMIGRATION,
        description="Etibarlılıq müddəti planlaşdırılan təhsil müddətindən ən azı 6 ay artıq olan biometrik pasport.",
        is_mandatory=True,
        issuing_authority="ASAN Xidmət / DİN",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=10,
    ),
]


COUNTRY_SPECIFIC_DOCS: Dict[str, List[DocumentItem]] = {
    "DE": [
        DocumentItem(
            id="doc_de_vpd",
            title="Uni-Assist Vorprüfungsdokumentation (VPD)",
            category=DocumentCategory.ACADEMIC,
            description="Almaniya universitetlərinə müraciət üçün xarici diplomun alman təhsil sisteminə ekvivalentlik rəsmi sertifikatı.",
            is_mandatory=True,
            issuing_authority="Uni-Assist e.V.",
            translation_required=True,
            apostille_required=True,
            estimated_processing_days=35,
            notes="VPD emalı 4-6 həftə çəkir. Mütləq dedlayndan 1.5 ay əvvəl müraciət edilməlidir.",
        ),
        DocumentItem(
            id="doc_de_sperrkonto",
            title="Sperrkonto (Almaniya Bloklanmış Bank Hesabı €11,904)",
            category=DocumentCategory.FINANCIAL,
            description="Tələbə vizası üçün illik €11,904 məbləğində bloklanmış bank hesabı təsdiq sənədi (aylıq €992 çıxarış hüququ ilə).",
            is_mandatory=True,
            issuing_authority="Fintiba / Expatrio / Coracle / Deutsche Bank",
            translation_required=False,
            apostille_required=False,
            estimated_processing_days=5,
        ),
        DocumentItem(
            id="doc_de_health_insurance",
            title="Almaniya İctimai Sığorta Şəhadətnaməsi (Gesetzliche Krankenversicherung)",
            category=DocumentCategory.LEGAL_IMMIGRATION,
            description="Universitetə qeydiyyat və viza üçün dövlət tələbə tibbi sığortası (TK, Barmer, AOK və ya viza üçün incoming sığorta).",
            is_mandatory=True,
            issuing_authority="Techniker Krankenkasse (TK) / Barmer",
            translation_required=False,
            apostille_required=False,
            estimated_processing_days=2,
        ),
    ],
    "GB": [
        DocumentItem(
            id="doc_gb_cas",
            title="CAS (Confirmation of Acceptance for Studies)",
            category=DocumentCategory.ACADEMIC,
            description="Böyük Britaniya universitetinin daxili müraciətçiyə təqdim etdiyi unikal viza sponsorluq nömrəsi.",
            is_mandatory=True,
            issuing_authority="Qəbul Olunmuş UK Universiteti",
            translation_required=False,
            apostille_required=False,
            estimated_processing_days=10,
        ),
        DocumentItem(
            id="doc_gb_maintenance_funds",
            title="28 Günlük Bank Çıxarışı (UK Maintenance Proof)",
            category=DocumentCategory.FINANCIAL,
            description="Təhsil haqqı qalığı + 9 aylıq yaşayış xərclərinin (£1,334/ay London, £1,023/ay kənar) bank hesabında fasiləsiz 28 gün qalmasını təsdiq edən çıxarış.",
            is_mandatory=True,
            issuing_authority="Rəsmi Kommersiya Bankı (ABB, PASHA və s.)",
            translation_required=True,
            apostille_required=False,
            estimated_processing_days=28,
            notes="Çıxarış viza ərizəsi verilən gündən ən çox 31 gün əvvələ aid olmalıdır.",
        ),
        DocumentItem(
            id="doc_gb_tb_test",
            title="Vərəm (TB) Test Sertifikatı",
            category=DocumentCategory.LEGAL_IMMIGRATION,
            description="Böyük Britaniyada 6 aydan çox təhsil alacaq Azərbaycan vətəndaşları üçün rəsmi IOM tibbi yoxlama arayışı.",
            is_mandatory=True,
            issuing_authority="IOM Baku (Beynəlxalq Miqrasiya Təşkilatı)",
            translation_required=False,
            apostille_required=False,
            estimated_processing_days=3,
        ),
    ],
    "US": [
        DocumentItem(
            id="doc_us_i20",
            title="Form I-20 (Certificate of Eligibility for Nonimmigrant Student Status)",
            category=DocumentCategory.LEGAL_IMMIGRATION,
            description="ABŞ universitetinin SEVIS bazasında yaratdığı və F-1 vizası üçün tələb olunan rəsmi qəbul sənədi.",
            is_mandatory=True,
            issuing_authority="Qəbul Olunmuş ABŞ Universiteti",
            translation_required=False,
            apostille_required=False,
            estimated_processing_days=7,
        ),
        DocumentItem(
            id="doc_us_financial_cert",
            title="Financial Affidavit of Support & Bank Certification",
            category=DocumentCategory.FINANCIAL,
            description="I-20 sənədinin verilməsi üçün illik Total Cost of Attendance (orta hesabla $35,000–$65,000) məbləğində zəmanət məktubu və bank çıxarışı.",
            is_mandatory=True,
            issuing_authority="Bank və Zamin (Valideyn)",
            translation_required=True,
            apostille_required=False,
            estimated_processing_days=4,
        ),
        DocumentItem(
            id="doc_us_sevis_receipt",
            title="SEVIS I-901 Ödəniş Qəbzi ($350)",
            category=DocumentCategory.FINANCIAL,
            description="ABŞ Daxili Təhlükəsizlik Nazirliyinə (DHS) ödənilən məcburi tələbə qeydiyyat rüsumu.",
            is_mandatory=True,
            issuing_authority="US Department of Homeland Security (FMJfee.com)",
            translation_required=False,
            apostille_required=False,
            estimated_processing_days=1,
        ),
    ],
    "IT": [
        DocumentItem(
            id="doc_it_universitaly",
            title="Universitaly Qabaqcadan Qeydiyyat Xülasəsi (Summary)",
            category=DocumentCategory.ACADEMIC,
            description="İtaliya Xarici İşlər Nazirliyinin portalında universitet tərəfindən təsdiq olunmuş elektron qeydiyyat vərəqəsi.",
            is_mandatory=True,
            issuing_authority="Universitaly / İtaliya Universiteti",
            translation_required=False,
            apostille_required=False,
            estimated_processing_days=14,
        ),
        DocumentItem(
            id="doc_it_dov_cimea",
            title="Declaration of Value (DOV) və ya CIMEA Müqayisəlilik Sertifikatı",
            category=DocumentCategory.ACADEMIC,
            description="Diplomun İtaliya təhsil pilləsinə uyğunluğunu təsdiq edən səfirlik bəyannaməsi (DOV) və ya CIMEA rəqəmsal arayışı.",
            is_mandatory=True,
            issuing_authority="İtaliyanın Bakıdakı Səfirliyi və ya CIMEA",
            translation_required=True,
            apostille_required=True,
            estimated_processing_days=30,
        ),
        DocumentItem(
            id="doc_it_isee_parificato",
            title="ISEE Parificato (Ailə Gəlir və Əmlak İndeksi Sertifikatı)",
            category=DocumentCategory.FINANCIAL,
            description="İtaliya universitetlərində təhsil haqqı güzəşti və DSU təqaüdü almaq üçün tələb olunan ailə gəlir hesabatı (< €27,000).",
            is_mandatory=True,
            issuing_authority="İtaliya CAF Mərkəzi",
            translation_required=True,
            apostille_required=True,
            estimated_processing_days=20,
        ),
    ],
    "TR": [
        DocumentItem(
            id="doc_tr_denklik",
            title="Təhsil Denklik Belgesi (Türkiyə MEB / YÖK Ekvivalentlik)",
            category=DocumentCategory.ACADEMIC,
            description="Attestat üçün Bakıdakı Türkiyə Təhsil Müşavirliyindən, bakalavr üçün isə YÖK-dən alınan tanınma şəhadətnaməsi.",
            is_mandatory=True,
            issuing_authority="Türkiyə Respublikası Bakı Səfirliyi Təhsil Müşavirliyi / YÖK",
            translation_required=True,
            apostille_required=True,
            estimated_processing_days=10,
        ),
        DocumentItem(
            id="doc_tr_notarized_passport",
            title="Xarici Pasportun Türkiyə Notariat Təsdiqli Tərcüməsi",
            category=DocumentCategory.LEGAL_IMMIGRATION,
            description="Türkiyədə tələbə qeydiyyatı və ikamət (oturma izni) üçün pasportun türk dilinə notarial tərcüməsi.",
            is_mandatory=True,
            issuing_authority="Azərbaycan və ya Türkiyə Notariusu",
            translation_required=True,
            apostille_required=False,
            estimated_processing_days=2,
        ),
    ],
}

STATE_PROGRAMME_SPECIFIC_DOCS = [
    DocumentItem(
        id="doc_sp_acceptance",
        title="Dövlət Proqramı Təsdiq Edilmiş Universitetdən Şərtsiz/Şərtli Qəbul",
        category=DocumentCategory.ACADEMIC,
        description="Nazirlər Kabineti və Təhsil Nazirliyinin təsdiq etdiyi Top-500 xarici ali məktəb siyahısına daxil olan universitetdən rəsmi qəbul məktubu.",
        is_mandatory=True,
        issuing_authority="Xarici Universitet",
        translation_required=True,
        apostille_required=False,
        estimated_processing_days=1,
    ),
    DocumentItem(
        id="doc_sp_motivation",
        title="Dövlət Proqramı Xüsusi Esse (Azərbaycan İqtisadiyyatına Töhfə Maddəsi)",
        category=DocumentCategory.APPLICATION_ASSETS,
        description="Təhsil başa çatdıqdan sonra Azərbaycana qayıdış və ölkənin prioritet iqtisadi sahələrinə verəcəyi töhfəni əsaslandıran inşa.",
        is_mandatory=True,
        issuing_authority="Müraciətçi",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=3,
    ),
    DocumentItem(
        id="doc_sp_medical",
        title="Sağlamlıq Haqqında Rəsmi Arayış (Forma 086/u)",
        category=DocumentCategory.LEGAL_IMMIGRATION,
        description="Xaricdə təhsil almaq üçün yararlılığı təsdiq edən poliklinika və ya ASAN tibb arayışı.",
        is_mandatory=True,
        issuing_authority="Dövlət Poliklinikası / ASAN Sağlamlıq",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=3,
    ),
    DocumentItem(
        id="doc_sp_criminal_record",
        title="Məhkumluğun Olmaması Barədə Arayış",
        category=DocumentCategory.LEGAL_IMMIGRATION,
        description="Daxili İşlər Nazirliyi tərəfindən verilən təmiz məhkumluq arayışı.",
        is_mandatory=True,
        issuing_authority="ASAN Xidmət / DİN",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=2,
    ),
    DocumentItem(
        id="doc_sp_military",
        title="Hərbi Xidmət Haqqında Sənəd (Hərbi Bilet və ya Möhlət Şəhadətnaməsi)",
        category=DocumentCategory.LEGAL_IMMIGRATION,
        description="Kişi vətəndaşlar üçün hərbi mükəlləfiyyət statusunu və ya möhlət hüququnu təsdiq edən sənəd.",
        is_mandatory=True,
        issuing_authority="Səfərbərlik və Hərbi Xidmətə Çağırış üzrə Dövlət Xidməti",
        translation_required=False,
        apostille_required=False,
        estimated_processing_days=5,
    ),
]


# ==============================================================================
# Curated Comparison Data Engine (50+ Target Profiles)
# ==============================================================================

CURATED_COMPARISON_DB: Dict[str, dict] = {
    "tum_cs": {
        "id": "tum_cs",
        "university_name": "Technical University of Munich (TUM)",
        "country_code": "DE",
        "country_name": "Germany",
        "flag": "🇩🇪",
        "city": "Munich",
        "qs_rank": 28,
        "program_name": "MSc Informatics (Computer Science)",
        "degree_level": "master",
        "tuition_eur_annual": 12000.0,  # Non-EU tuition introduced recently (€2,000-€3,000/sem or €6,000/yr)
        "living_cost_eur_monthly": 1250.0,
        "blocked_account_required_eur": 11904.0,
        "original_tuition": "€6,000 / semester (Non-EU)",
        "ielts_min": 6.5,
        "toefl_min": 88,
        "post_study_work_visa_duration_months": 18,
        "post_study_work_visa_name": "German Job Seeker Visa (§ 20 AufenthG)",
        "post_study_work_visa_summary": "18-month open work permit after graduation with pathway to EU Blue Card after 21-27 months of employment.",
        "state_programme_eligible": True,
        "default_tier": AdmissionTier.DREAM,
    },
    "oxford_cs": {
        "id": "oxford_cs",
        "university_name": "University of Oxford",
        "country_code": "GB",
        "country_name": "United Kingdom",
        "flag": "🇬🇧",
        "city": "Oxford",
        "qs_rank": 3,
        "program_name": "MSc in Advanced Computer Science",
        "degree_level": "master",
        "tuition_eur_annual": 43500.0,  # £37,000 converted
        "living_cost_eur_monthly": 1500.0,
        "blocked_account_required_eur": 12000.0,  # Maintenance funds
        "original_tuition": "£37,500 / year",
        "ielts_min": 7.5,
        "toefl_min": 110,
        "post_study_work_visa_duration_months": 24,
        "post_study_work_visa_name": "UK Graduate Route Visa",
        "post_study_work_visa_summary": "2-year unsponsored stay and work authorization in the UK across any sector with direct transition to Skilled Worker visa.",
        "state_programme_eligible": True,
        "default_tier": AdmissionTier.DREAM,
    },
    "imperial_data": {
        "id": "imperial_data",
        "university_name": "Imperial College London",
        "country_code": "GB",
        "country_name": "United Kingdom",
        "flag": "🇬🇧",
        "city": "London",
        "qs_rank": 6,
        "program_name": "MSc Computing (Data Science & ML)",
        "degree_level": "master",
        "tuition_eur_annual": 46000.0,
        "living_cost_eur_monthly": 1750.0,
        "blocked_account_required_eur": 14000.0,
        "original_tuition": "£39,400 / year",
        "ielts_min": 7.0,
        "toefl_min": 100,
        "post_study_work_visa_duration_months": 24,
        "post_study_work_visa_name": "UK Graduate Route Visa",
        "post_study_work_visa_summary": "2-year post-study work authorization with top tech access in London silicon roundabout.",
        "state_programme_eligible": True,
        "default_tier": AdmissionTier.DREAM,
    },
    "rwth_engineering": {
        "id": "rwth_engineering",
        "university_name": "RWTH Aachen University",
        "country_code": "DE",
        "country_name": "Germany",
        "flag": "🇩🇪",
        "city": "Aachen",
        "qs_rank": 99,
        "program_name": "MSc Mechanical Engineering",
        "degree_level": "master",
        "tuition_eur_annual": 0.0,  # Public state of NRW charges no tuition
        "living_cost_eur_monthly": 950.0,
        "blocked_account_required_eur": 11904.0,
        "original_tuition": "€320 / semester (Semesterticket fee only)",
        "ielts_min": 6.5,
        "toefl_min": 90,
        "post_study_work_visa_duration_months": 18,
        "post_study_work_visa_name": "German Job Seeker Visa (§ 20 AufenthG)",
        "post_study_work_visa_summary": "18 months to secure qualified engineer employment; leading industrial recruitment corridor.",
        "state_programme_eligible": True,
        "default_tier": AdmissionTier.TARGET,
    },
    "polimi_cs": {
        "id": "polimi_cs",
        "university_name": "Politecnico di Milano",
        "country_code": "IT",
        "country_name": "Italy",
        "flag": "🇮🇹",
        "city": "Milan",
        "qs_rank": 111,
        "program_name": "MSc Computer Science and Engineering",
        "degree_level": "master",
        "tuition_eur_annual": 3900.0,  # Standard maximum tier without DSU
        "living_cost_eur_monthly": 1050.0,
        "blocked_account_required_eur": 6000.0,
        "original_tuition": "€3,900 / year (Waived to €160 with DSU)",
        "ielts_min": 6.0,
        "toefl_min": 78,
        "post_study_work_visa_duration_months": 12,
        "post_study_work_visa_name": "Permesso di Soggiorno per Ricerca Lavoro",
        "post_study_work_visa_summary": "12-month job search residence permit with direct conversion to Subordinate Work permit upon contract.",
        "state_programme_eligible": True,
        "default_tier": AdmissionTier.TARGET,
    },
    "itu_engineering": {
        "id": "itu_engineering",
        "university_name": "Istanbul Technical University (İTÜ)",
        "country_code": "TR",
        "country_name": "Turkey",
        "flag": "🇹🇷",
        "city": "Istanbul",
        "qs_rank": 404,
        "program_name": "BSc Computer Engineering (100% English)",
        "degree_level": "bachelor",
        "tuition_eur_annual": 1800.0,
        "living_cost_eur_monthly": 650.0,
        "blocked_account_required_eur": 3000.0,
        "original_tuition": "₺65,000 / year",
        "ielts_min": 6.5,
        "toefl_min": 79,
        "post_study_work_visa_duration_months": 12,
        "post_study_work_visa_name": "Kısa Dönem İkamet İzni (Mezuniyet Sonrası)",
        "post_study_work_visa_summary": "12 months short-term residence permit allowing graduate job seeking in Turkish defense & software industries.",
        "state_programme_eligible": False,
        "default_tier": AdmissionTier.SAFETY,
    },
    "bhos_chemical": {
        "id": "bhos_chemical",
        "university_name": "Baku Higher Oil School (BANM)",
        "country_code": "AZ",
        "country_name": "Azerbaijan",
        "flag": "🇦🇿",
        "city": "Baku",
        "qs_rank": None,
        "program_name": "BSc Chemical Engineering (Heriot-Watt Dual Degree)",
        "degree_level": "bachelor",
        "tuition_eur_annual": 0.0,  # Full scholarship default for 650+ score
        "living_cost_eur_monthly": 450.0,
        "blocked_account_required_eur": 0.0,
        "original_tuition": "0 AZN (Full State Scholarship 650+ score) / 5,000 AZN ödənişli",
        "ielts_min": 6.0,
        "toefl_min": 75,
        "post_study_work_visa_duration_months": 0,
        "post_study_work_visa_name": "Domestic Employment Pathway",
        "post_study_work_visa_summary": "Direct domestic hiring priority with SOCAR, bp, and regional energy operators.",
        "state_programme_eligible": False,
        "default_tier": AdmissionTier.SAFETY,
    },
    "cmu_software": {
        "id": "cmu_software",
        "university_name": "Carnegie Mellon University",
        "country_code": "US",
        "country_name": "United States",
        "flag": "🇺🇸",
        "city": "Pittsburgh, PA",
        "qs_rank": 52,
        "program_name": "Master of Software Engineering",
        "degree_level": "master",
        "tuition_eur_annual": 55000.0,
        "living_cost_eur_monthly": 1600.0,
        "blocked_account_required_eur": 25000.0,
        "original_tuition": "$58,500 / year",
        "ielts_min": 7.5,
        "toefl_min": 102,
        "post_study_work_visa_duration_months": 36,
        "post_study_work_visa_name": "F-1 STEM OPT (Optional Practical Training)",
        "post_study_work_visa_summary": "12-month standard OPT + 24-month STEM extension totaling 36 months of full US work authorization with H-1B lottery entry.",
        "state_programme_eligible": True,
        "default_tier": AdmissionTier.DREAM,
    }
}


# ==============================================================================
# Domain Services & Business Logic
# ==============================================================================

def generate_document_checklist(req: DocumentChecklistRequest) -> DocumentChecklistResult:
    """Builds a dynamic document checklist based on destination country, level, and funding."""
    country = req.country_code.upper()
    docs: List[DocumentItem] = list(BASE_ACADEMIC_DOCS)

    # Add country-specific documents
    if country in COUNTRY_SPECIFIC_DOCS:
        docs.extend(COUNTRY_SPECIFIC_DOCS[country])

    # Add State Programme requirements if declared
    if req.is_state_programme:
        docs.extend(STATE_PROGRAMME_SPECIFIC_DOCS)

    country_notes = []
    if country == "DE":
        country_notes.append("Almaniya təhsil vizası üçün Sperrkonto mütləqdir (€11,904). Uni-Assist VPD müraciəti ən azı 40 gün əvvəl başlanmalıdır.")
    elif country == "GB":
        country_notes.append("Böyük Britaniyada 28 günlük bank qaydası mütləqdir: tələb olunan vəsait hesabda fasiləsiz 28 gün qalmalıdır.")
    elif country == "IT":
        country_notes.append("İtaliya DSU təqaüdü və universitet güzəşti üçün ISEE Parificato sənədləri apostil olunub italyan dilinə tərcümə edilməlidir.")
    elif country == "US":
        country_notes.append("F-1 vizası üçün I-20 sənədi və $350 SEVIS rüsumu tələb olunur.")
    elif country == "TR":
        country_notes.append("Türkiyə universitetlərinə qeydiyyat üçün MEB və ya YÖK Denklik belgesi Bakıdakı müşavirlikdən alınmalıdır.")

    mandatory = sum(1 for d in docs if d.is_mandatory)

    return DocumentChecklistResult(
        country_code=country,
        country_name=_get_country_name(country),
        degree_level=req.degree_level,
        total_documents=len(docs),
        mandatory_count=mandatory,
        documents=docs,
        country_specific_notes=country_notes,
    )


def classify_application_tier(req: TierClassificationRequest) -> TierClassificationResult:
    """Classifies a target application as DREAM, TARGET, or SAFETY.
    Strictly rule-based and deterministic according to ADR-0008.
    """
    gpa_scaled = (req.student_gpa / req.student_gpa_max) * 4.0
    qs = req.qs_rank or 999
    ielts = req.student_ielts or 6.0

    qualifications = []
    risks = []
    recommendations = []

    # 1. DREAM criteria
    # QS Top 50, or highly competitive STEM, or student GPA below 3.3 for elite university
    if qs <= 50 or (qs <= 100 and gpa_scaled < 3.4):
        tier = AdmissionTier.DREAM
        badge = "Xəyal / Yüksək Rəqabətli (Dream)"
        rationale = f"{req.university_name} dünya reytinqində (QS #{qs}) yüksək pillədədir və qəbul faizi çox seçicidir."
        
        if gpa_scaled >= 3.7:
            qualifications.append(f"Yüksək GPA göstəriciniz ({req.student_gpa:.2f}) proqramın orta həddinə uyğundur.")
        else:
            risks.append(f"GPA göstəriciniz ({req.student_gpa:.2f}) bu pillə üçün rəqabətli aralığın aşağı sərhədindədir.")
            recommendations.append("Güclü tədqiqat təcrübəsi, konfrans məqaləsi və ya sənaye layihələri ilə kompensasiya edin.")

        if ielts < 7.5 and qs <= 30:
            risks.append(f"IELTS balınız ({ielts}) universitetin ideal C1/7.5 tələbindən aşağı ola bilər.")
            recommendations.append("Dil balını 7.5-ə qaldırmaq və ya GRE imtahanı vermək tövsiyə olunur.")

        recommendations.append("Bu proqramla paralel olaraq mütləq 2 Target və 1 Safety universitet seçin.")

    # 2. SAFETY criteria
    # Student substantially exceeds thresholds: GPA >= 3.7 and QS > 150 or Turkish/domestic state universities
    elif gpa_scaled >= 3.6 and (qs > 150 or req.country_code in ("TR", "PL", "AZ")):
        tier = AdmissionTier.SAFETY
        badge = "Təminatlı Seçim (Safety)"
        rationale = f"Akademik və dil göstəriciləriniz {req.university_name} qəbul standartlarını tam şəkildə üstələyir."
        qualifications.append(f"GPA göstəriciniz ({req.student_gpa:.2f}) qəbul üçün zəmanətli aralıqdadır.")
        if ielts >= 6.5:
            qualifications.append(f"IELTS ({ielts}) minimum həddi rahatlıqla qarşılayır.")
        recommendations.append("Müraciəti erkən dövrdə tamamlayıb təqaüd imkanları üçün əlavə ərizə təqdim edin.")

    # 3. TARGET criteria (Default realistic match)
    else:
        tier = AdmissionTier.TARGET
        badge = "Hədəf Universitet (Target)"
        rationale = f"Profiliniz {req.university_name} proqramının rəsmi qəbul tələblərinə tam cavab verir."
        qualifications.append(f"GPA göstəriciniz ({req.student_gpa:.2f}) və dil nəticəniz proqram profilinə uyğundur.")
        recommendations.append("Motivasiya məktubunu kafedranın laboratoriyalarına və professorlarına uyğun fərdiləşdirin.")
        recommendations.append("Dövlət Proqramı və ya ikitərəfli təqaüd üçün təsdiqlənmiş qəbul məktubunu vaxtında əldə edin.")

    return TierClassificationResult(
        tier=tier,
        badge_label=badge,
        rationale=rationale,
        qualification_factors=qualifications,
        risk_factors=risks,
        action_recommendations=recommendations,
    )


def compare_universities(req: ComparisonRequest) -> ComparisonResult:
    """Builds the multi-variable comparison matrix for requested universities."""
    items: List[UniversityComparisonItem] = []

    for uid in req.university_ids:
        raw = CURATED_COMPARISON_DB.get(uid)
        if not raw:
            # Fallback for dynamic query
            continue

        first_year = raw["tuition_eur_annual"] + (raw["living_cost_eur_monthly"] * 12)

        # Dynamic tiering if student GPA is provided
        tier = raw.get("default_tier", AdmissionTier.TARGET)
        rationale = "Profil tələbləri ilə uyğunlaşdırılmış standart pillə."
        if req.student_gpa is not None:
            t_res = classify_application_tier(
                TierClassificationRequest(
                    university_name=raw["university_name"],
                    country_code=raw["country_code"],
                    qs_rank=raw.get("qs_rank"),
                    student_gpa=req.student_gpa,
                    student_ielts=req.student_ielts,
                )
            )
            tier = t_res.tier
            rationale = t_res.rationale

        item = UniversityComparisonItem(
            id=raw["id"],
            university_name=raw["university_name"],
            country_code=raw["country_code"],
            country_name=raw["country_name"],
            flag=raw["flag"],
            city=raw["city"],
            qs_rank=raw.get("qs_rank"),
            program_name=raw["program_name"],
            degree_level=raw.get("degree_level", "master"),
            tuition_eur_annual=raw["tuition_eur_annual"],
            living_cost_eur_monthly=raw["living_cost_eur_monthly"],
            blocked_account_required_eur=raw["blocked_account_required_eur"],
            total_first_year_eur=round(first_year, 2),
            original_tuition=raw["original_tuition"],
            ielts_min=raw.get("ielts_min", 6.5),
            toefl_min=raw.get("toefl_min", 80),
            post_study_work_visa_duration_months=raw["post_study_work_visa_duration_months"],
            post_study_work_visa_name=raw["post_study_work_visa_name"],
            post_study_work_visa_summary=raw["post_study_work_visa_summary"],
            state_programme_eligible=raw.get("state_programme_eligible", True),
            admission_tier=tier,
            tier_rationale=rationale,
        )
        items.append(item)

    if not items:
        # If no matching IDs found, return first 3 defaults
        for k in ["tum_cs", "oxford_cs", "rwth_engineering"]:
            raw = CURATED_COMPARISON_DB[k]
            first_year = raw["tuition_eur_annual"] + (raw["living_cost_eur_monthly"] * 12)
            items.append(
                UniversityComparisonItem(
                    id=raw["id"],
                    university_name=raw["university_name"],
                    country_code=raw["country_code"],
                    country_name=raw["country_name"],
                    flag=raw["flag"],
                    city=raw["city"],
                    qs_rank=raw.get("qs_rank"),
                    program_name=raw["program_name"],
                    degree_level=raw.get("degree_level", "master"),
                    tuition_eur_annual=raw["tuition_eur_annual"],
                    living_cost_eur_monthly=raw["living_cost_eur_monthly"],
                    blocked_account_required_eur=raw["blocked_account_required_eur"],
                    total_first_year_eur=round(first_year, 2),
                    original_tuition=raw["original_tuition"],
                    ielts_min=raw.get("ielts_min", 6.5),
                    toefl_min=raw.get("toefl_min", 80),
                    post_study_work_visa_duration_months=raw["post_study_work_visa_duration_months"],
                    post_study_work_visa_name=raw["post_study_work_visa_name"],
                    post_study_work_visa_summary=raw["post_study_work_visa_summary"],
                    state_programme_eligible=raw.get("state_programme_eligible", True),
                    admission_tier=raw.get("default_tier", AdmissionTier.TARGET),
                    tier_rationale="Standart profil üzrə müqayisə.",
                )
            )

    # Cost calculation
    sorted_by_cost = sorted(items, key=lambda x: x.total_first_year_eur)
    lowest_cost = sorted_by_cost[0].university_name

    sorted_by_visa = sorted(items, key=lambda x: x.post_study_work_visa_duration_months, reverse=True)
    longest_visa = f"{sorted_by_visa[0].university_name} ({sorted_by_visa[0].post_study_work_visa_duration_months} ay)"

    ranked_items = [x for x in items if x.qs_rank is not None]
    best_ranked = sorted(ranked_items, key=lambda x: x.qs_rank)[0].university_name if ranked_items else None

    avg_cost = sum(x.total_first_year_eur for x in items) / len(items)

    summary_notes = [
        f"Ən sərfəli variant: {lowest_cost} (təxmini ilk il xərci: €{sorted_by_cost[0].total_first_year_eur:,.0f}).",
        f"Ən uzun məzuniyyət sonrası iş vizası: {longest_visa}.",
        f"Müqayisə olunan proqramlar üzrə orta illik ümumi xərc: €{avg_cost:,.0f}.",
    ]

    return ComparisonResult(
        items=items,
        lowest_cost_university=lowest_cost,
        longest_pswr_university=longest_visa,
        best_ranked_university=best_ranked,
        average_first_year_cost_eur=round(avg_cost, 2),
        comparison_summary_notes=summary_notes,
    )


def _get_country_name(code: str) -> str:
    names = {
        "GB": "Böyük Britaniya",
        "DE": "Almaniya",
        "US": "Amerika Birləşmiş Ştatları",
        "IT": "İtaliya",
        "TR": "Türkiyə",
        "HU": "Macarıstan",
        "AZ": "Azərbaycan",
        "FR": "Fransa",
        "PL": "Polşa",
    }
    return names.get(code.upper(), code)
