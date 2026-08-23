from typing import List, Literal, Optional
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
    """Final deterministic match evaluation result."""
    program_name: str = Field(..., description="Program name evaluated")
    university_name: str = Field(..., description="University name evaluated")
    overall_match_percentage: float = Field(..., ge=0.0, le=100.0, description="Final overall match percentage (0-100%)")
    is_eligible: bool = Field(..., description="Boolean indicating overall eligibility")
    ineligibility_reasons: List[str] = Field(default_factory=list, description="List of reasons if ineligible")
    breakdown: MatchBreakdown = Field(..., description="Detailed breakdown explaining factor scores")
