from typing import List
from app.schemas.matching import (
    FactorScoreDetail,
    MatchBreakdown,
    MatchResult,
    ProgramRequirements,
    StudentProfile,
)
from app.services.matching.scoring import (
    calculate_academic_score,
    calculate_budget_score,
    calculate_language_score,
)

# Standard Default Weights
WEIGHT_ACADEMIC = 0.50  # 50%
WEIGHT_BUDGET = 0.30    # 30%
WEIGHT_LANGUAGE = 0.20  # 20%


def evaluate_match(
    student: StudentProfile,
    program: ProgramRequirements,
    weight_academic: float = WEIGHT_ACADEMIC,
    weight_budget: float = WEIGHT_BUDGET,
    weight_language: float = WEIGHT_LANGUAGE,
) -> MatchResult:
    """
    Main deterministic matching engine function.
    
    1. Evaluates strict Hard Filters (Degree Level, strict cutoffs).
    2. Calculates Soft Ranking weighted scores across Academic, Budget, and Language.
    3. Produces a 100% explainable MatchResult detailing overall percentage and component breakdown.
    """
    ineligibility_reasons: List[str] = []

    # -------------------------------------------------------------
    # Step 1: Degree Level Hard Filter Evaluation
    # -------------------------------------------------------------
    student_degree = student.degree_level.lower()
    program_degree = program.degree_level.lower()

    if student_degree != program_degree:
        degree_passed = False
        degree_score = 0.0
        degree_explanation = (
            f"Degree level mismatch: Student requested '{student_degree.title()}', "
            f"but program is offered for '{program_degree.title()}'."
        )
        ineligibility_reasons.append(degree_explanation)
    else:
        degree_passed = True
        degree_score = 100.0
        degree_explanation = (
            f"Degree level match confirmed: Both student and program target '{student_degree.title()}'."
        )

    degree_factor = FactorScoreDetail(
        score=degree_score,
        weight=0.0,  # Prerequisites / hard filter
        weighted_score=0.0,
        passed_hard_filter=degree_passed,
        explanation=degree_explanation,
    )

    # If degree level hard filter fails, short-circuit soft ranking to 0% match
    if not degree_passed:
        empty_academic = FactorScoreDetail(
            score=0.0, weight=weight_academic, weighted_score=0.0, passed_hard_filter=False, explanation="Evaluation skipped due to degree level mismatch."
        )
        empty_budget = FactorScoreDetail(
            score=0.0, weight=weight_budget, weighted_score=0.0, passed_hard_filter=False, explanation="Evaluation skipped due to degree level mismatch."
        )
        empty_language = FactorScoreDetail(
            score=0.0, weight=weight_language, weighted_score=0.0, passed_hard_filter=False, explanation="Evaluation skipped due to degree level mismatch."
        )
        return MatchResult(
            program_name=program.program_name,
            university_name=program.university_name,
            overall_match_percentage=0.0,
            is_eligible=False,
            ineligibility_reasons=ineligibility_reasons,
            breakdown=MatchBreakdown(
                degree_level=degree_factor,
                academic=empty_academic,
                budget=empty_budget,
                language=empty_language,
            ),
        )

    # -------------------------------------------------------------
    # Step 2: Individual Factor Scoring (Academic, Budget, Language)
    # -------------------------------------------------------------
    acad_score, acad_exp, acad_passed = calculate_academic_score(
        student_gpa=student.gpa, required_gpa=program.min_gpa
    )
    if not acad_passed:
        ineligibility_reasons.append(f"Academic requirement not met: {acad_exp}")

    budg_score, budg_exp, budg_passed = calculate_budget_score(
        student_budget=student.budget,
        program_tuition=program.tuition_fee,
        currency=program.currency,
    )
    if not budg_passed:
        ineligibility_reasons.append(f"Budget constraint not met: {budg_exp}")

    lang_score, lang_exp, lang_passed = calculate_language_score(
        student_ielts=student.ielts,
        student_toefl=student.toefl,
        min_ielts=program.min_ielts,
        min_toefl=program.min_toefl,
    )
    if not lang_passed:
        ineligibility_reasons.append(f"Language proficiency requirement not met: {lang_exp}")

    # -------------------------------------------------------------
    # Step 3: Weighted Soft Ranking Calculation
    # -------------------------------------------------------------
    acad_weighted = round(acad_score * weight_academic, 2)
    budg_weighted = round(budg_score * weight_budget, 2)
    lang_weighted = round(lang_score * weight_language, 2)

    overall_score = round(acad_weighted + budg_weighted + lang_weighted, 2)
    overall_score = max(0.0, min(100.0, overall_score))

    # Overall eligibility requirement: all hard filters must pass
    is_eligible = degree_passed and acad_passed and budg_passed and lang_passed

    # Construct FactorScoreDetails
    academic_factor = FactorScoreDetail(
        score=acad_score,
        weight=weight_academic,
        weighted_score=acad_weighted,
        passed_hard_filter=acad_passed,
        explanation=acad_exp,
    )
    budget_factor = FactorScoreDetail(
        score=budg_score,
        weight=weight_budget,
        weighted_score=budg_weighted,
        passed_hard_filter=budg_passed,
        explanation=budg_exp,
    )
    language_factor = FactorScoreDetail(
        score=lang_score,
        weight=weight_language,
        weighted_score=lang_weighted,
        passed_hard_filter=lang_passed,
        explanation=lang_exp,
    )

    return MatchResult(
        program_name=program.program_name,
        university_name=program.university_name,
        overall_match_percentage=overall_score,
        is_eligible=is_eligible,
        ineligibility_reasons=ineligibility_reasons,
        breakdown=MatchBreakdown(
            degree_level=degree_factor,
            academic=academic_factor,
            budget=budget_factor,
            language=language_factor,
        ),
    )
