from typing import Optional, Tuple


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
    currency: str = "USD"
) -> Tuple[float, str, bool]:
    """
    Calculate deterministic budget coverage score (0-100%) and explainable rationale.
    
    Returns:
        (score, explanation_text, passed_hard_filter)
    """
    if program_tuition == 0.0:
        return (
            100.0,
            f"Program tuition is completely free (0 {currency}). Full budget score granted.",
            True
        )

    if student_budget >= program_tuition:
        surplus = round(student_budget - program_tuition, 2)
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

    # Budget is less than program tuition
    shortfall = round(program_tuition - student_budget, 2)
    percentage_covered = round((student_budget / program_tuition) * 100.0, 2)
    score = max(0.0, min(100.0, percentage_covered))
    
    # Hard filter fails if budget covers less than 40% of tuition (severe financial deficit)
    passed_hard_filter = percentage_covered >= 40.0

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
