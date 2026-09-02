from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator

DegreeLevel = Literal["bachelor", "master", "phd"]


class StudentProfile(BaseModel):
    """Student profile model containing academic parameters for program matching."""
    gpa: float = Field(..., ge=0.0, le=4.0, description="Grade Point Average on a 4.0 scale")
    budget: float = Field(..., ge=0.0, description="Annual budget available for tuition in USD/EUR")
    ielts: Optional[float] = Field(None, ge=0.0, le=9.0, description="IELTS overall score (0.0 to 9.0)")
    toefl: Optional[int] = Field(None, ge=0, le=120, description="TOEFL iBT overall score (0 to 120)")
    degree_level: DegreeLevel = Field(..., description="Target degree level (bachelor, master, phd)")
    field_of_study: Optional[str] = Field(None, description="Desired field of study")
    preferred_countries: Optional[List[str]] = Field(default_factory=list, description="List of preferred countries")
    research_experience: bool = Field(default=False, description="Whether student has research experience")

    @field_validator("degree_level", mode="before")
    @classmethod
    def normalize_degree_level(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class ProgramRequirements(BaseModel):
    """University program requirements and metadata."""
    program_id: Optional[int] = Field(None, description="Program database primary key ID")
    university_name: str = Field(..., description="Name of the university")
    program_name: str = Field(..., description="Name of the academic program")
    degree_level: DegreeLevel = Field(..., description="Program degree level (bachelor, master, phd)")
    field: Optional[str] = Field(None, description="Academic field of study")
    country: Optional[str] = Field(None, description="Host country")
    min_gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Minimum required GPA (4.0 scale)")
    tuition_fee: float = Field(..., ge=0.0, description="Annual tuition fee")
    currency: str = Field(default="USD", description="Currency of tuition fee")
    min_ielts: Optional[float] = Field(None, ge=0.0, le=9.0, description="Minimum required IELTS score")
    min_toefl: Optional[int] = Field(None, ge=0, le=120, description="Minimum required TOEFL score")

    @field_validator("degree_level", mode="before")
    @classmethod
    def normalize_degree_level(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class ScholarshipSchema(BaseModel):
    """Scholarship schema model for scholarship opportunities."""
    id: Optional[int] = Field(None, description="Scholarship database primary key ID")
    name: str = Field(..., description="Official scholarship name")
    provider: Optional[str] = Field(None, description="Provider or organization name")
    country: Optional[str] = Field(None, description="Target host country")
    degree_level: Optional[str] = Field(None, description="Eligible degree level")
    min_gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="Minimum required GPA")
    min_ielts: Optional[float] = Field(None, ge=0.0, le=9.0, description="Minimum required IELTS score")
    amount: Union[float, int, str] = Field(..., description="Scholarship amount (fixed numeric, string description, or full-ride)")
    eligibility_text: Optional[str] = Field(None, description="Eligibility criteria text")


class FactorScoreDetail(BaseModel):
    """Detailed score breakdown and explainable message for a single matching factor."""
    score: float = Field(..., ge=0.0, le=100.0, description="Unweighted factor score (0-100%)")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight assigned to this factor (0.0 to 1.0)")
    weighted_score: float = Field(..., ge=0.0, le=100.0, description="Weighted contribution to overall match score")
    passed_hard_filter: bool = Field(..., description="Whether student meets minimum requirement for this factor")
    explanation: str = Field(..., description="Human-readable explainable reason for score")


class MatchBreakdown(BaseModel):
    """Breakdown dictionary explaining scores across all matching dimensions."""
    degree_level: FactorScoreDetail
    academic: FactorScoreDetail
    budget: FactorScoreDetail
    language: FactorScoreDetail


class MatchResult(BaseModel):
    """Final deterministic match evaluation result with net-cost and scholarship support. No admission-chance estimate is published (ADR-0008)."""
    program_name: str = Field(..., description="Program name evaluated")
    university_name: str = Field(..., description="University name evaluated")
    overall_match_percentage: float = Field(..., ge=0.0, le=100.0, description="Final overall match percentage (0-100%)")
    is_eligible: bool = Field(..., description="Boolean indicating overall eligibility")
    ineligibility_reasons: List[str] = Field(default_factory=list, description="List of reasons if ineligible")
    breakdown: MatchBreakdown = Field(..., description="Detailed breakdown explaining factor scores")
    original_tuition: float = Field(default=0.0, ge=0.0, description="Original sticker tuition fee before scholarship")
    scholarship_applied: bool = Field(default=False, description="Whether a scholarship was applied to reduce tuition")
    scholarship_name: Optional[str] = Field(None, description="Name of applied scholarship if eligible")
    scholarship_amount: float = Field(default=0.0, ge=0.0, description="Scholarship discount or coverage amount applied")
    net_cost: float = Field(default=0.0, ge=0.0, description="Effective net tuition cost after scholarship application")
    admission_probability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Always null. The project publishes a predicted admission chance only where "
            "admission is mechanical -- Azerbaijani DIM programmes, where clearing the "
            "cutoff IS admission -- and never estimates one for any other country "
            "(ADR-0008). An absent number is deliberate and is never filled in."
        ),
    )
    admission_prediction_rationale: Optional[str] = Field(None, description="Explains why no admission-chance estimate is published for this programme (ADR-0008)")
