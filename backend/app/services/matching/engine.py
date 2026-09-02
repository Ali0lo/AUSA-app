from typing import Any, List, Optional

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
    calculate_net_cost,
    parse_scholarship_amount,
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
    available_scholarships: Optional[List[Any]] = None,
) -> MatchResult:
    """
    Main deterministic matching engine function with:
    1. Scholarship-First Net-Cost Evaluation (ADR-0005).

    Steps:
    1. Evaluates strict Hard Filters (Degree Level mismatch).
    2. Calculates Net Cost by evaluating eligible scholarships *before* applying budget filters.
    3. Evaluates Soft Ranking weighted scores across Academic (50%), Net Budget (30%), and Language (20%).
    4. Produces an explainable MatchResult detailing net-cost and scholarship metadata. No
       admission-chance estimate is published (ADR-0008); see `prediction_rationale` below.
    """
    ineligibility_reasons: List[str] = []
    original_tuition = program.tuition_fee

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

    # -------------------------------------------------------------
    # Step 2: Scholarship-First Net-Cost Calculation (ADR-0005)
    # -------------------------------------------------------------
    net_cost, applied_scholarship = calculate_net_cost(
        program_tuition=original_tuition,
        student_profile=student,
        available_scholarships=available_scholarships or [],
    )

    scholarship_applied = False
    scholarship_name: Optional[str] = None
    scholarship_amount = 0.0

    if applied_scholarship is not None:
        scholarship_applied = True
        scholarship_name = (
            getattr(applied_scholarship, "name", None)
            or (applied_scholarship.get("name") if isinstance(applied_scholarship, dict) else "Scholarship")
        )
        raw_amt = (
            getattr(applied_scholarship, "amount", None)
            if not isinstance(applied_scholarship, dict)
            else applied_scholarship.get("amount")
        )
        scholarship_amount = min(parse_scholarship_amount(raw_amt, original_tuition), original_tuition)

    # -------------------------------------------------------------
    # Step 3: No admission-chance estimate is published (ADR-0008)
    # -------------------------------------------------------------
    # ADR-0008 withdrew admission probability as a user-facing number, and the 31 Aug
    # narrowing left one model in this project: DIM cutoffs for Azerbaijani programmes.
    # What stood here computed a percentage from a hardcoded formula whenever the model
    # artifacts were missing -- which, since they are gitignored, was every fresh clone --
    # and captioned it "based on historical data from 2019-2024".
    prediction_rationale = (
        "No admission-chance estimate is published for this programme. This product "
        "predicts an admission chance only where admission is mechanical, and estimates "
        "one nowhere else. What is shown instead is whether you meet the stated "
        "requirements, and what the programme costs."
    )
    probability = None

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
            original_tuition=original_tuition,
            scholarship_applied=scholarship_applied,
            scholarship_name=scholarship_name,
            scholarship_amount=scholarship_amount,
            net_cost=net_cost,
            admission_probability=probability,
            admission_prediction_rationale=prediction_rationale,
        )

    # -------------------------------------------------------------
    # Step 4: Individual Factor Scoring (Academic, Net Budget, Language)
    # -------------------------------------------------------------
    acad_score, acad_exp, acad_passed = calculate_academic_score(
        student_gpa=student.gpa, required_gpa=program.min_gpa
    )
    if not acad_passed:
        ineligibility_reasons.append(f"Academic requirement not met: {acad_exp}")

    # Evaluate budget score using net_cost instead of original sticker tuition
    budg_score, budg_exp, budg_passed = calculate_budget_score(
        student_budget=student.budget,
        program_tuition=net_cost,
        currency=program.currency,
        scholarship_name=scholarship_name,
        scholarship_amount=scholarship_amount,
        original_tuition=original_tuition,
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
    # Step 5: Weighted Soft Ranking Calculation
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
        original_tuition=original_tuition,
        scholarship_applied=scholarship_applied,
        scholarship_name=scholarship_name,
        scholarship_amount=scholarship_amount,
        net_cost=net_cost,
        admission_probability=probability,
        admission_prediction_rationale=prediction_rationale,
    )
