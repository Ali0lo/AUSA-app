"""Compare a student's grade average to a university's minimum, without inventing a
conversion.

`ProgramRequirement` has always stored `gpa_scale` beside `gpa_minimum`, on the rule its
own docstring states: a GPA without its scale is not a number, and mixing scales silently
is how a 3.0 becomes a rejection. That rule was enforced on the university's side and
nowhere on the student's -- the route profile carried no grade at all, so UCL's "4.5" and
Manchester's "80" were displayed to a student and never checked against anything. This
module is the missing half.

**The trap that makes this more than arithmetic: not every scale counts upwards.** German
grades run 1.0 (best) to 4.0 (lowest pass), with 5.0 a fail. A numeric comparison that
assumes bigger is better does not merely lose precision on a German grade -- it inverts the
answer, rating a 3.9 above a 1.3 and telling an excellent student they fall short. So a
scale here carries a direction, and a comparison that crosses an inverted scale is refused
rather than approximated.

**Cross-scale comparisons are proportional, and are labelled as such.** A 4.5 out of 5 and
a minimum of 80 out of 100 can be compared as 90% against 80% of their respective maxima,
and that is a useful screening signal. It is NOT an official conversion: universities apply
their own tables, and Germany uses the modified Bavarian formula. So the result carries
`exact=False` and says so in words. What this module will not do is emit a converted number
as though it were the student's grade.

**Which grade is this?** The grade of the qualification named in `qualification_held` --
the attestat for a school-leaver, the completed bachelor's degree for a master's applicant.
One field pair serves both, because `qualification_held` already says which one it is.
Master's admission abroad routinely turns on the bachelor GPA, and that is the same
comparison against the same kind of published minimum.

Nothing here changes a route's status. A grade is advisory, reported per university:
universities weigh grades holistically alongside everything else, and turning a route
BLOCKED on a proportional comparison would be exactly the false confidence this project
refuses.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GradeScale:
    key: str
    floor: float
    ceiling: float
    # False for scales where the LOWEST number is the best mark. See the module docstring.
    higher_is_better: bool
    description: str


# Deliberately small. Every scale here is one we have seen in curated data or one an
# Azerbaijani applicant actually holds. A scale nobody has produced a real example of would
# be a guess about how somebody else grades.
FIVE_POINT = GradeScale(
    "5.0", 0.0, 5.0, True,
    "five-point scale, 5 best -- the Azerbaijani attestat, and what UCL states its "
    "attestat minimum against",
)
PERCENT = GradeScale(
    "100", 0.0, 100.0, True,
    "percentage out of 100, 100 best -- Azerbaijani universities, Turkish universities, "
    "and Manchester's stated minimum",
)
FOUR_POINT = GradeScale(
    "4.0", 0.0, 4.0, True,
    "US-style four-point GPA, 4.0 best",
)
GERMAN = GradeScale(
    "german", 1.0, 4.0, False,
    "German scale, 1.0 best and 4.0 the lowest pass -- LOWER IS BETTER",
)

_ALIASES = {
    "5": FIVE_POINT, "5.0": FIVE_POINT, "five": FIVE_POINT, "five-point": FIVE_POINT,
    "100": PERCENT, "100.0": PERCENT, "percent": PERCENT, "%": PERCENT,
    "4": FOUR_POINT, "4.0": FOUR_POINT,
    "german": GERMAN, "de": GERMAN, "1-4": GERMAN, "1.0-4.0": GERMAN,
}

KNOWN_SCALE_KEYS = tuple(sorted({s.key for s in _ALIASES.values()}))

# Verdicts. The three non-answers are distinct on purpose: "you gave us no grade", "they
# publish no minimum" and "these two numbers cannot be compared" are different facts, and
# none of them is "you meet the requirement".
GRADE_MEETS = "meets"
GRADE_BELOW = "below"
GRADE_NO_STUDENT_GRADE = "no_grade_given"
GRADE_NO_REQUIREMENT = "no_minimum_published"
GRADE_NOT_COMPARABLE = "scales_not_comparable"


@dataclass(frozen=True)
class GradeCheck:
    verdict: str
    # False when the comparison crossed two different scales and is therefore a proportional
    # screening signal rather than an official conversion. Always False for a non-answer.
    exact: bool
    explanation: str


def resolve_scale(raw: Optional[str]) -> Optional[GradeScale]:
    """Map a scale string from a CSV or a form to a known scale, or None."""
    if raw is None:
        return None
    return _ALIASES.get(raw.strip().lower())


def _fraction(value: float, scale: GradeScale) -> float:
    """Where `value` sits between the scale's floor and ceiling, as 0.0-1.0.

    Inverted for a scale where lower is better, so that a larger fraction always means a
    better result regardless of which way the scale runs. That single inversion is what
    keeps every caller below from having to remember the direction.
    """
    span = (value - scale.floor) / (scale.ceiling - scale.floor)
    return span if scale.higher_is_better else 1.0 - span


def _in_range(value: float, scale: GradeScale) -> bool:
    return scale.floor <= value <= scale.ceiling


def check_grade(
    student_grade: Optional[float],
    student_scale_raw: Optional[str],
    required_minimum: Optional[float],
    required_scale_raw: Optional[str],
) -> GradeCheck:
    """Does this student's grade clear this university's published minimum?

    Order matters here. The requirement is checked for absence FIRST, because a university
    that publishes no minimum is not a university the student fails -- and reporting
    "you gave us no grade" to someone applying to a university with no grade bar would
    invent a problem that does not exist.
    """
    if required_minimum is None:
        return GradeCheck(
            GRADE_NO_REQUIREMENT, False,
            "This university's page does not state a minimum grade. That is not the same "
            "as there being none -- it may be published elsewhere, or decided per "
            "programme.",
        )

    if student_grade is None:
        return GradeCheck(
            GRADE_NO_STUDENT_GRADE, False,
            f"This university asks for at least {required_minimum:g}"
            f"{_scale_suffix(required_scale_raw)}. Add your grade average to check it.",
        )

    required_scale = resolve_scale(required_scale_raw)
    student_scale = resolve_scale(student_scale_raw)

    if required_scale is None:
        return GradeCheck(
            GRADE_NOT_COMPARABLE, False,
            f"This university's minimum is recorded as {required_minimum:g} but the scale "
            f"it is measured on was not recorded, so it cannot be compared with your "
            f"{student_grade:g}. A grade without its scale is not a number.",
        )
    if student_scale is None:
        return GradeCheck(
            GRADE_NOT_COMPARABLE, False,
            f"Your grade of {student_grade:g} has no scale attached, so it cannot be "
            f"compared with this university's minimum of {required_minimum:g}"
            f"{_scale_suffix(required_scale_raw)}. "
            f"Known scales: {', '.join(KNOWN_SCALE_KEYS)}.",
        )

    # Catches the exact mistake this whole module exists to prevent, at the point a student
    # makes it: entering a five-point attestat average of 4.5 while the form says 4.0.
    if not _in_range(student_grade, student_scale):
        return GradeCheck(
            GRADE_NOT_COMPARABLE, False,
            f"{student_grade:g} is not a value on the {student_scale.key} scale "
            f"({student_scale.description}), which runs from {student_scale.floor:g} to "
            f"{student_scale.ceiling:g}. Check which scale your grade is on.",
        )

    if student_scale.key == required_scale.key:
        student_better = (
            student_grade >= required_minimum
            if student_scale.higher_is_better
            else student_grade <= required_minimum
        )
        direction = "at least" if student_scale.higher_is_better else "no higher than"
        if student_better:
            return GradeCheck(
                GRADE_MEETS, True,
                f"Your {student_grade:g} clears the stated minimum of "
                f"{required_minimum:g} ({student_scale.description}).",
            )
        return GradeCheck(
            GRADE_BELOW, True,
            f"This university asks for {direction} {required_minimum:g} and your grade is "
            f"{student_grade:g} ({student_scale.description}). Universities weigh grades "
            f"alongside everything else, so this is not an automatic refusal -- but it is "
            f"below what they publish.",
        )

    # Different scales. An inverted one on either side is refused rather than approximated:
    # see the module docstring. Converting to or from the German scale is done with the
    # modified Bavarian formula, and producing a number that looks like its output without
    # applying it would be worse than saying nothing.
    if not (student_scale.higher_is_better and required_scale.higher_is_better):
        inverted = student_scale if not student_scale.higher_is_better else required_scale
        return GradeCheck(
            GRADE_NOT_COMPARABLE, False,
            f"These grades are on different scales and one of them ({inverted.key}) runs "
            f"the other way: {inverted.description}. Comparing them numerically would "
            f"reverse the answer, and converting between them needs an official "
            f"conversion this tool does not perform. Your {student_grade:g} on the "
            f"{student_scale.key} scale, their minimum {required_minimum:g} on the "
            f"{required_scale.key} scale.",
        )

    student_fraction = _fraction(student_grade, student_scale)
    required_fraction = _fraction(required_minimum, required_scale)
    caveat = (
        f"Compared proportionally, because your grade is on the {student_scale.key} scale "
        f"and their minimum is on the {required_scale.key} scale: "
        f"{student_fraction:.0%} of your scale's maximum against "
        f"{required_fraction:.0%} of theirs. THIS IS A ROUGH COMPARISON, NOT AN OFFICIAL "
        f"CONVERSION -- universities apply their own conversion tables and may reach a "
        f"different figure."
    )
    if student_fraction >= required_fraction:
        return GradeCheck(GRADE_MEETS, False, f"You appear to clear this minimum. {caveat}")
    return GradeCheck(GRADE_BELOW, False, f"You appear to fall short of this minimum. {caveat}")


def _scale_suffix(raw: Optional[str]) -> str:
    scale = resolve_scale(raw)
    if scale is None:
        return ""
    return f" out of {scale.ceiling:g}" if scale.higher_is_better else f" on the {scale.key} scale"
