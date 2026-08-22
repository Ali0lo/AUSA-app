import pytest
from app.schemas.matching import ProgramRequirements, StudentProfile
from app.services.matching.engine import evaluate_match
from app.services.matching.scoring import (
    calculate_academic_score,
    calculate_budget_score,
    calculate_language_score,
    convert_toefl_to_ielts_equivalent,
)


def test_convert_toefl_to_ielts_equivalent():
    assert convert_toefl_to_ielts_equivalent(120) == 9.0
    assert convert_toefl_to_ielts_equivalent(100) == 7.0
    assert convert_toefl_to_ielts_equivalent(90) == 6.5
    assert convert_toefl_to_ielts_equivalent(75) == 6.0
    assert convert_toefl_to_ielts_equivalent(55) == 5.5
    assert convert_toefl_to_ielts_equivalent(30) == 4.0


def test_calculate_academic_score_surplus():
    score, exp, passed = calculate_academic_score(student_gpa=3.8, required_gpa=3.2)
    assert score == 100.0
    assert passed is True
    assert "exceeds" in exp


def test_calculate_academic_score_shortfall():
    score, exp, passed = calculate_academic_score(student_gpa=3.0, required_gpa=3.5)
    assert score < 100.0
    assert passed is False
    assert "below" in exp


def test_calculate_budget_score():
    score, exp, passed = calculate_budget_score(student_budget=12000.0, program_tuition=15000.0, currency="USD")
    assert score == 80.0
    assert passed is True
    assert "80.0% covered" in exp


def test_evaluate_match_perfect_match():
    student = StudentProfile(
        gpa=3.8,
        budget=20000.0,
        ielts=7.5,
        degree_level="master",
        field_of_study="Computer Science"
    )
    program = ProgramRequirements(
        university_name="TU Munich",
        program_name="M.Sc. Informatics",
        degree_level="master",
        min_gpa=3.0,
        tuition_fee=15000.0,
        currency="EUR",
        min_ielts=6.5
    )
    
    result = evaluate_match(student, program)
    assert result.is_eligible is True
    assert result.overall_match_percentage == 100.0
    assert result.program_name == "M.Sc. Informatics"
    assert result.university_name == "TU Munich"
    assert result.breakdown.degree_level.passed_hard_filter is True
    assert result.breakdown.academic.score == 100.0
    assert result.breakdown.budget.score == 100.0
    assert result.breakdown.language.score == 100.0


test_evaluate_match_degree_mismatch_data = (
    StudentProfile(
        gpa=3.9,
        budget=50000.0,
        ielts=8.0,
        degree_level="master"
    ),
    ProgramRequirements(
        university_name="Harvard University",
        program_name="B.Sc. Computer Science",
        degree_level="bachelor",
        tuition_fee=40000.0,
        currency="USD"
    )
)


def test_evaluate_match_degree_mismatch():
    student, program = test_evaluate_match_degree_mismatch_data
    result = evaluate_match(student, program)
    
    assert result.is_eligible is False
    assert result.overall_match_percentage == 0.0
    assert len(result.ineligibility_reasons) >= 1
    assert "Degree level mismatch" in result.ineligibility_reasons[0]


def test_evaluate_match_partial_score():
    student = StudentProfile(
        gpa=3.5,
        budget=10000.0,
        toefl=95,  # IELTS ~7.0
        degree_level="master"
    )
    program = ProgramRequirements(
        university_name="University of Amsterdam",
        program_name="M.Sc. Data Science",
        degree_level="master",
        min_gpa=3.2,
        tuition_fee=20000.0,  # 50% budget coverage
        currency="EUR",
        min_ielts=6.5
    )
    
    result = evaluate_match(student, program)
    
    # Academics: 100.0 * 0.50 = 50.0
    # Budget: 50.0 * 0.30 = 15.0
    # Language: 100.0 * 0.20 = 20.0
    # Expected overall = 50.0 + 15.0 + 20.0 = 85.0%
    assert result.is_eligible is True
    assert result.overall_match_percentage == 85.0
    assert result.breakdown.budget.score == 50.0
    assert result.breakdown.budget.weighted_score == 15.0
