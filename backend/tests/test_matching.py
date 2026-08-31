import pytest
from app.schemas.matching import ProgramRequirements, ScholarshipSchema, StudentProfile
from app.services.matching.engine import evaluate_match
from app.services.matching.scoring import (
    calculate_academic_score,
    calculate_budget_score,
    calculate_language_score,
    calculate_net_cost,
    convert_toefl_to_ielts_equivalent,
    parse_scholarship_amount,
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
    assert result.admission_probability is None
    assert result.admission_prediction_rationale is not None


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
    
    assert result.is_eligible is True
    assert result.overall_match_percentage == 85.0
    assert result.breakdown.budget.score == 50.0
    assert result.breakdown.budget.weighted_score == 15.0


# -------------------------------------------------------------
# Tests for ADR-0005 Scholarship-First Net-Cost Evaluation
# -------------------------------------------------------------
def test_parse_scholarship_amount():
    assert parse_scholarship_amount(5000.0, 15000.0) == 5000.0
    assert parse_scholarship_amount("$5,000", 15000.0) == 5000.0
    assert parse_scholarship_amount("100% Tuition Waiver", 15000.0) == 15000.0
    assert parse_scholarship_amount("Full-Ride", 15000.0) == 15000.0
    assert parse_scholarship_amount("50% Waiver", 15000.0) == 7500.0


def test_scholarship_first_net_cost_evaluation():
    student = StudentProfile(
        gpa=3.7,
        budget=6000.0,  # Budget ($6,000) is less than sticker tuition ($10,000)
        ielts=7.0,
        degree_level="master"
    )
    program = ProgramRequirements(
        university_name="Bocconi University",
        program_name="M.Sc. Finance",
        degree_level="master",
        min_gpa=3.0,
        tuition_fee=10000.0,
        currency="EUR",
        min_ielts=6.5
    )
    scholarships = [
        ScholarshipSchema(
            name="Merit Excellence Scholarship",
            amount=5000.0,
            degree_level="master",
            min_gpa=3.5,
            min_ielts=6.5
        )
    ]

    result = evaluate_match(student, program, available_scholarships=scholarships)

    assert result.is_eligible is True
    assert result.scholarship_applied is True
    assert result.scholarship_name == "Merit Excellence Scholarship"
    assert result.scholarship_amount == 5000.0
    assert result.original_tuition == 10000.0
    assert result.net_cost == 5000.0
    assert result.breakdown.budget.score == 100.0
    assert "Merit Excellence Scholarship" in result.breakdown.budget.explanation


# -------------------------------------------------------------
# Tests for ADR-0008: admission probability is withdrawn, not estimated
# -------------------------------------------------------------
def test_no_admission_probability_is_published():
    """ADR-0008 withdrew this number. Its absence is deliberate and must stay absent.

    This previously asserted `admission_probability is not None`, which certified a
    fabrication: with the model artifacts absent -- and they are gitignored, so absent on
    every fresh clone -- the number came from a hardcoded arithmetic formula, computed over
    an IELTS of 6.0 invented for students who never sat the exam.
    """
    student = StudentProfile(
        gpa=3.8,
        budget=25000.0,
        ielts=7.5,
        degree_level="master"
    )
    program_turkey = ProgramRequirements(
        university_name="Bilkent University",
        program_name="M.Sc. Computer Engineering",
        degree_level="master",
        country="Turkey",
        min_gpa=3.2,
        tuition_fee=15000.0,
        min_ielts=6.5
    )
    program_usa = ProgramRequirements(
        university_name="MIT",
        program_name="M.Sc. Artificial Intelligence",
        degree_level="master",
        country="USA",
        min_gpa=3.5,
        tuition_fee=50000.0,
        min_ielts=7.0
    )

    result_tr = evaluate_match(student, program_turkey)
    result_us = evaluate_match(student, program_usa)

    assert result_tr.admission_probability is None
    assert result_us.admission_probability is None


def test_the_rationale_promises_no_percentage_and_cites_no_dataset():
    """The withdrawn strings cited '2019-2024' and 'US College Scorecard data' for a number
    that was frequently a formula. Neither claim may return."""
    student = StudentProfile(
        gpa=3.8,
        budget=25000.0,
        ielts=7.5,
        degree_level="master"
    )
    program_turkey = ProgramRequirements(
        university_name="Bilkent University",
        program_name="M.Sc. Computer Engineering",
        degree_level="master",
        country="Turkey",
        min_gpa=3.2,
        tuition_fee=15000.0,
        min_ielts=6.5
    )
    program_usa = ProgramRequirements(
        university_name="MIT",
        program_name="M.Sc. Artificial Intelligence",
        degree_level="master",
        country="USA",
        min_gpa=3.5,
        tuition_fee=50000.0,
        min_ielts=7.0
    )

    result_tr = evaluate_match(student, program_turkey)
    result_us = evaluate_match(student, program_usa)

    for rationale in (result_tr.admission_prediction_rationale, result_us.admission_prediction_rationale):
        assert "%" not in rationale
        assert "Scorecard" not in rationale
        assert "2019-2024" not in rationale
