import re
from typing import Any, List, Optional, Tuple

from app.schemas.matching import StudentProfile


def calculate_academic_score(
    student_gpa: float,
    required_gpa: Optional[float]
) -> Tuple[float, str, bool]:
    """
    Calculate deterministic academic score (0-100%) and explainable rationale based on GPA.
    
    Returns:
        (score, explanation_text, passed_hard_filter)
    """
    if required_gpa is None or required_gpa == 0.0:
        return (
            100.0,
            f"No minimum GPA specified for this program. Student GPA ({student_gpa:.2f}/4.0) granted full score.",
            True
        )

    if student_gpa >= required_gpa:
        gpa_surplus = round(student_gpa - required_gpa, 2)
        if gpa_surplus > 0:
            explanation = (
                f"Student GPA ({student_gpa:.2f}/4.0) exceeds the minimum required GPA "
                f"({required_gpa:.2f}/4.0) by +{gpa_surplus:.2f} points."
            )
        else:
            explanation = (
                f"Student GPA ({student_gpa:.2f}/4.0) exactly meets the minimum required GPA "
                f"({required_gpa:.2f}/4.0)."
            )
        return (100.0, explanation, True)
    
    # Student GPA is below requirement
    gpa_shortfall = round(required_gpa - student_gpa, 2)
    percentage = round((student_gpa / required_gpa) * 100.0, 2)
    score = max(0.0, min(100.0, percentage))
    
    # Hard filter fails if GPA shortfall exceeds 0.2 points
    passed_hard_filter = gpa_shortfall <= 0.2
    
    explanation = (
        f"Student GPA ({student_gpa:.2f}/4.0) is below the minimum requirement ({required_gpa:.2f}/4.0) "
        f"by -{gpa_shortfall:.2f} points ({score:.1f}% of required benchmark)."
    )
    if not passed_hard_filter:
        explanation += " (Fails strict academic cutoff threshold)."

    return (score, explanation, passed_hard_filter)


def calculate_budget_score(
    student_budget: float,
    program_tuition: float,
    currency: str = "USD",
    scholarship_name: Optional[str] = None,
    scholarship_amount: float = 0.0,
    original_tuition: Optional[float] = None,
) -> Tuple[float, str, bool]:
    """
    Calculate deterministic budget coverage score (0-100%) and explainable rationale,
    factoring in net tuition cost after applied scholarships (ADR-0005).
    
    Returns:
        (score, explanation_text, passed_hard_filter)
    """
    orig_tuition = original_tuition if original_tuition is not None else program_tuition

    if program_tuition == 0.0:
        if scholarship_name and scholarship_amount > 0:
            exp = (
                f"Budget match: 100% - The {currency} {orig_tuition:,.2f} tuition is fully covered "
                f"after applying the '{scholarship_name}' ({currency} {scholarship_amount:,.2f} discount)."
            )
        else:
            exp = f"Program tuition is completely free (0 {currency}). Full budget score granted."
        return (100.0, exp, True)

    if student_budget >= program_tuition:
        surplus = round(student_budget - program_tuition, 2)
        if scholarship_name and scholarship_amount > 0:
            if surplus > 0:
                explanation = (
                    f"Budget match: 100% - The net tuition of {currency} {program_tuition:,.2f} is fully covered "
                    f"by your {currency} {student_budget:,.2f} budget after applying the '{scholarship_name}' "
                    f"({currency} {scholarship_amount:,.2f} discount off original {currency} {orig_tuition:,.2f} tuition) "
                    f"with a surplus of {currency} {surplus:,.2f}."
                )
            else:
                explanation = (
                    f"Budget match: 100% - Your {currency} {student_budget:,.2f} budget exactly matches net tuition "
                    f"of {currency} {program_tuition:,.2f} after applying the '{scholarship_name}'."
                )
        else:
            if surplus > 0:
                explanation = (
                    f"Student annual budget ({currency} {student_budget:,.2f}) fully covers "
                    f"tuition ({currency} {program_tuition:,.2f}) with a surplus of {currency} {surplus:,.2f}."
                )
            else:
                explanation = (
                    f"Student annual budget ({currency} {student_budget:,.2f}) exactly matches tuition ({currency} {program_tuition:,.2f})."
                )
        return (100.0, explanation, True)

    # Budget is less than net tuition
    shortfall = round(program_tuition - student_budget, 2)
    percentage_covered = round((student_budget / program_tuition) * 100.0, 2)
    score = max(0.0, min(100.0, percentage_covered))
    
    # Hard filter fails if budget covers less than 40% of net tuition
    passed_hard_filter = percentage_covered >= 40.0

    if scholarship_name and scholarship_amount > 0:
        explanation = (
            f"Student annual budget ({currency} {student_budget:,.2f}) falls short of net tuition "
            f"({currency} {program_tuition:,.2f}) by {currency} {shortfall:,.2f} ({percentage_covered:.1f}% covered) "
            f"after applying the '{scholarship_name}' ({currency} {scholarship_amount:,.2f} discount off original {currency} {orig_tuition:,.2f} tuition)."
        )
    else:
        explanation = (
            f"Student annual budget ({currency} {student_budget:,.2f}) falls short of tuition "
            f"({currency} {program_tuition:,.2f}) by {currency} {shortfall:,.2f} ({percentage_covered:.1f}% covered)."
        )

    if not passed_hard_filter:
        explanation += " (Fails minimum financial feasibility threshold of 40% coverage)."

    return (score, explanation, passed_hard_filter)


def convert_toefl_to_ielts_equivalent(toefl: int) -> float:
    """Standard ETS score conversion table for TOEFL iBT to IELTS overall band score."""
    if toefl >= 118:
        return 9.0
    elif toefl >= 115:
        return 8.5
    elif toefl >= 110:
        return 8.0
    elif toefl >= 102:
        return 7.5
    elif toefl >= 94:
        return 7.0
    elif toefl >= 79:
        return 6.5
    elif toefl >= 60:
        return 6.0
    elif toefl >= 46:
        return 5.5
    elif toefl >= 35:
        return 5.0
    elif toefl >= 32:
        return 4.5
    return 4.0


def calculate_language_score(
    student_ielts: Optional[float],
    student_toefl: Optional[int],
    min_ielts: Optional[float],
    min_toefl: Optional[int]
) -> Tuple[float, str, bool]:
    """
    Calculate deterministic language proficiency score (0-100%) and explainable rationale.
    
    Returns:
        (score, explanation_text, passed_hard_filter)
    """
    if min_ielts is None and min_toefl is None:
        return (
            100.0,
            "No English language proficiency test scores required for this program.",
            True
        )

    # Resolve effective student IELTS equivalent score
    effective_student_ielts: Optional[float] = student_ielts
    if effective_student_ielts is None and student_toefl is not None:
        effective_student_ielts = convert_toefl_to_ielts_equivalent(student_toefl)

    # Resolve effective program minimum required IELTS score
    effective_min_ielts: Optional[float] = min_ielts
    if effective_min_ielts is None and min_toefl is not None:
        effective_min_ielts = convert_toefl_to_ielts_equivalent(min_toefl)

    if effective_student_ielts is None:
        req_str = []
        if min_ielts:
            req_str.append(f"IELTS {min_ielts}")
        if min_toefl:
            req_str.append(f"TOEFL {min_toefl}")
        return (
            0.0,
            f"Language score missing: Program requires ({' or '.join(req_str)}), but no student language score was provided.",
            False
        )

    if effective_min_ielts is None or effective_min_ielts == 0.0:
        return (
            100.0,
            f"Student provided language score (IELTS {effective_student_ielts:.1f} equivalent) which satisfies requirement.",
            True
        )

    if effective_student_ielts >= effective_min_ielts:
        surplus = round(effective_student_ielts - effective_min_ielts, 1)
        score_desc = f"IELTS {student_ielts}" if student_ielts else f"TOEFL {student_toefl} (IELTS ~{effective_student_ielts:.1f})"
        if surplus > 0:
            explanation = (
                f"Student language score ({score_desc}) exceeds minimum requirement "
                f"(IELTS {effective_min_ielts:.1f}) by +{surplus:.1f} band points."
            )
        else:
            explanation = (
                f"Student language score ({score_desc}) meets minimum requirement "
                f"(IELTS {effective_min_ielts:.1f})."
            )
        return (100.0, explanation, True)

    # Student language score is below requirement
    shortfall = round(effective_min_ielts - effective_student_ielts, 1)
    score = max(0.0, round((effective_student_ielts / effective_min_ielts) * 100.0, 2))
    passed_hard_filter = shortfall <= 0.5  # Hard filter fails if shortfall > 0.5 band points

    score_desc = f"IELTS {student_ielts}" if student_ielts else f"TOEFL {student_toefl} (IELTS ~{effective_student_ielts:.1f})"
    explanation = (
        f"Student language score ({score_desc}) is below minimum requirement (IELTS {effective_min_ielts:.1f}) "
        f"by -{shortfall:.1f} band points ({score:.1f}% of required benchmark)."
    )
    if not passed_hard_filter:
        explanation += " (Fails strict language cutoff threshold)."

    return (score, explanation, passed_hard_filter)


def parse_scholarship_amount(amount_raw: Any, tuition: float) -> float:
    """
    Parse various scholarship amount formats (numeric float, string like '$5,000', 
    percentage like '50%', or full-ride descriptors) into a numeric float monetary value.
    """
    if amount_raw is None:
        return 0.0
    if isinstance(amount_raw, (int, float)):
        return float(amount_raw)
    
    amount_str = str(amount_raw).lower().strip()
    if not amount_str:
        return 0.0
    
    # Check for full-ride / 100% tuition coverage
    if "full" in amount_str or "100%" in amount_str or "free" in amount_str or "complete" in amount_str:
        return float(tuition)

    # Check for percentage waiver (e.g. "50%", "50% tuition waiver")
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", amount_str)
    if pct_match:
        pct = float(pct_match.group(1))
        return round(tuition * (pct / 100.0), 2)

    # Extract numeric digits (e.g. "$5,000", "5000 USD", "5000")
    clean_str = amount_str.replace(",", "")
    num_match = re.search(r"(\d+(?:\.\d+)?)", clean_str)
    if num_match:
        return float(num_match.group(1))

    return 0.0


def is_student_eligible_for_scholarship(
    student_profile: StudentProfile,
    scholarship: Any
) -> bool:
    """
    Evaluate whether a student satisfies eligibility criteria for a given scholarship.
    Checks degree level, minimum GPA, and minimum language requirements.
    """
    def get_attr(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # 1. Degree level check
    sch_degree = get_attr(scholarship, "degree_level")
    if sch_degree:
        sch_degree_str = str(sch_degree).strip().lower()
        stu_degree_str = str(student_profile.degree_level).strip().lower()
        if sch_degree_str and sch_degree_str != stu_degree_str:
            return False

    # 2. Minimum GPA check
    sch_min_gpa = get_attr(scholarship, "min_gpa")
    if sch_min_gpa is not None and sch_min_gpa > 0:
        if student_profile.gpa < sch_min_gpa:
            return False

    # 3. Minimum IELTS / language score check
    sch_min_ielts = get_attr(scholarship, "min_ielts")
    if sch_min_ielts is not None and sch_min_ielts > 0:
        effective_ielts = student_profile.ielts
        if effective_ielts is None and student_profile.toefl is not None:
            effective_ielts = convert_toefl_to_ielts_equivalent(student_profile.toefl)
        if effective_ielts is None or effective_ielts < sch_min_ielts:
            return False

    return True


def calculate_net_cost(
    program_tuition: float,
    student_profile: StudentProfile,
    available_scholarships: List[Any]
) -> Tuple[float, Optional[Any]]:
    """
    Calculate net tuition cost after evaluating available scholarships (ADR-0005).

    Iterates through available_scholarships, verifies student eligibility criteria,
    and subtracts the highest eligible scholarship amount from program_tuition.

    Args:
        program_tuition: Sticker tuition fee before scholarship.
        student_profile: Student profile to evaluate eligibility against.
        available_scholarships: List of Scholarship ORM models or Pydantic schemas.

    Returns:
        (net_cost, highest_eligible_scholarship)
    """
    if program_tuition <= 0.0 or not available_scholarships:
        return (max(0.0, program_tuition), None)

    best_scholarship = None
    max_discount = 0.0

    for sch in available_scholarships:
        if is_student_eligible_for_scholarship(student_profile, sch):
            raw_amount = getattr(sch, "amount", None) if not isinstance(sch, dict) else sch.get("amount")
            discount = parse_scholarship_amount(raw_amount, program_tuition)
            discount = min(discount, program_tuition)  # Discount cannot exceed tuition

            if discount > max_discount:
                max_discount = discount
                best_scholarship = sch

    if best_scholarship is not None and max_discount > 0:
        net_cost = max(0.0, round(program_tuition - max_discount, 2))
        return (net_cost, best_scholarship)

    return (max(0.0, program_tuition), None)
