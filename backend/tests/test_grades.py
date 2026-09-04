"""Comparing a grade to a published minimum.

The tests that matter here are not the ones where two numbers on the same scale are
compared. They are the four ways this can be confidently wrong: comparing across scales
without saying so, comparing a scale that counts downwards as though it counted upwards,
reading a missing minimum as a pass, and accepting a grade whose scale nobody stated.
"""

import pytest

from app.domain.grades import (
    GRADE_BELOW,
    GRADE_MEETS,
    GRADE_NOT_COMPARABLE,
    GRADE_NO_REQUIREMENT,
    GRADE_NO_STUDENT_GRADE,
    check_grade,
    resolve_scale,
)


# -------------------------------------------------------------
# Same scale: the easy case, and the one the real data hits
# -------------------------------------------------------------
def test_an_attestat_average_clears_ucls_stated_minimum():
    """The live example. UCL states 4.5 on the five-point scale for its foundation year,
    and an Azerbaijani attestat is on exactly that scale, so this comparison is exact."""
    result = check_grade(4.8, "5.0", 4.5, "5.0")
    assert result.verdict == GRADE_MEETS
    assert result.exact is True


def test_a_grade_exactly_on_the_minimum_meets_it():
    assert check_grade(4.5, "5.0", 4.5, "5.0").verdict == GRADE_MEETS


def test_a_grade_below_the_minimum_says_so_without_calling_it_a_refusal():
    result = check_grade(3.9, "5.0", 4.5, "5.0")
    assert result.verdict == GRADE_BELOW
    assert result.exact is True
    assert "not an automatic refusal" in result.explanation


def test_the_scale_alias_five_is_the_same_scale_as_five_point_zero():
    """A student's form says 5; UCL's CSV says 5.0. If these resolved to different scales
    the comparison would silently degrade from exact to proportional."""
    assert resolve_scale("5") is resolve_scale("5.0")
    assert check_grade(4.8, "5", 4.5, "5.0").exact is True


# -------------------------------------------------------------
# Crossing scales: allowed, but never silently
# -------------------------------------------------------------
def test_crossing_scales_is_proportional_and_labelled_as_such():
    """Manchester states 80 out of 100; an attestat is out of 5. The comparison is useful
    and it is not an official conversion, so it must not be reported as exact."""
    result = check_grade(4.5, "5.0", 80.0, "100")
    assert result.verdict == GRADE_MEETS
    assert result.exact is False
    assert "NOT AN OFFICIAL CONVERSION" in result.explanation


def test_a_proportional_comparison_can_also_fall_short():
    result = check_grade(3.5, "5.0", 80.0, "100")
    assert result.verdict == GRADE_BELOW
    assert result.exact is False


# -------------------------------------------------------------
# The inverted scale: where a naive compare is BACKWARDS, not just imprecise
# -------------------------------------------------------------
def test_an_excellent_german_grade_is_never_read_as_a_poor_one():
    """THE ONE THAT MATTERS MOST.

    German grades run 1.0 (best) to 4.0 (lowest pass). A comparison assuming bigger is
    better rates 1.3 as failing a minimum of 2.5, which is the exact opposite of the
    truth. Same-scale comparison must honour the direction.
    """
    assert check_grade(1.3, "german", 2.5, "german").verdict == GRADE_MEETS
    assert check_grade(3.7, "german", 2.5, "german").verdict == GRADE_BELOW


def test_comparing_across_an_inverted_scale_is_refused_not_approximated():
    """Proportional comparison would be defensible arithmetic here and is still refused:
    converting to or from the German scale is done with the modified Bavarian formula, and
    a number that looks like its output without being it is worse than no number."""
    result = check_grade(4.5, "5.0", 2.5, "german")
    assert result.verdict == GRADE_NOT_COMPARABLE
    assert "runs the other way" in result.explanation

    reverse = check_grade(1.7, "german", 80.0, "100")
    assert reverse.verdict == GRADE_NOT_COMPARABLE


# -------------------------------------------------------------
# The three non-answers, which are three different facts
# -------------------------------------------------------------
def test_a_university_publishing_no_minimum_is_not_a_university_you_fail():
    """Checked BEFORE the student's grade is checked for absence: telling someone they are
    missing a grade for a university that publishes no grade bar invents a problem."""
    result = check_grade(None, None, None, None)
    assert result.verdict == GRADE_NO_REQUIREMENT
    assert "not the same as there being none" in result.explanation


def test_no_minimum_published_still_reports_no_requirement_even_with_a_grade():
    assert check_grade(4.8, "5.0", None, None).verdict == GRADE_NO_REQUIREMENT


def test_a_missing_student_grade_is_a_prompt_not_a_verdict():
    result = check_grade(None, None, 4.5, "5.0")
    assert result.verdict == GRADE_NO_STUDENT_GRADE
    assert result.exact is False
    assert "4.5" in result.explanation


def test_none_of_the_three_non_answers_is_ever_reported_as_meeting():
    """Guards the whole point: an unknown must never read as permission (ADR-0004)."""
    for args in [(None, None, None, None), (4.8, "5.0", None, None), (None, None, 4.5, "5.0")]:
        assert check_grade(*args).verdict != GRADE_MEETS


# -------------------------------------------------------------
# Scales that were never stated, or that the number cannot be on
# -------------------------------------------------------------
def test_a_grade_with_no_scale_is_not_compared_against_an_assumed_one():
    result = check_grade(4.5, None, 4.5, "5.0")
    assert result.verdict == GRADE_NOT_COMPARABLE
    assert "no scale attached" in result.explanation


def test_a_requirement_with_no_scale_is_not_compared_either():
    result = check_grade(4.5, "5.0", 80.0, None)
    assert result.verdict == GRADE_NOT_COMPARABLE
    assert "scale it is measured on was not recorded" in result.explanation


def test_an_unrecognised_scale_name_is_refused_rather_than_guessed():
    assert check_grade(4.5, "out of five", 4.5, "5.0").verdict == GRADE_NOT_COMPARABLE


def test_a_grade_impossible_on_its_own_scale_is_caught_at_the_student():
    """The exact mistake this module exists to prevent, made by the student rather than by
    the data: entering a five-point attestat average of 4.5 having selected the 4.0 scale.
    A silent comparison would report 4.5 >= 4.0 and call it a pass."""
    result = check_grade(4.5, "4.0", 3.0, "4.0")
    assert result.verdict == GRADE_NOT_COMPARABLE
    assert "not a value on the 4.0 scale" in result.explanation


def test_a_grade_at_the_very_top_of_its_scale_is_still_in_range():
    """Guards the range check against being written with a strict inequality: a perfect
    5.0 is a real attestat result and must not be rejected as impossible."""
    assert check_grade(5.0, "5.0", 4.5, "5.0").verdict == GRADE_MEETS
    assert check_grade(100.0, "100", 80.0, "100").verdict == GRADE_MEETS
    assert check_grade(1.0, "german", 2.5, "german").verdict == GRADE_MEETS
