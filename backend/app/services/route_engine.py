"""Classify routes against a student profile.

The distinction the two non-open statuses draw is the product's core idea: a score you
have not got yet is a gap you can close this cycle (UNLOCKABLE), while a qualification you
do not hold is not (BLOCKED) -- it needs a different route first, which is what Task 9's
composition is for.
"""

from typing import Optional

from app.domain.route_definitions import ALL_ROUTES
from app.domain.routes import (
    ExamRequirement,
    Route,
    RouteAssessment,
    RouteStatus,
    StudentRouteProfile,
)


def _exam_gap(requirement: ExamRequirement, profile: StudentRouteProfile) -> Optional[str]:
    """Return a description of the gap, or None when the requirement is met."""
    held = getattr(profile, requirement.profile_field, None)
    if held is None:
        if requirement.minimum is None:
            return f"{requirement.name} required"
        return f"{requirement.name} required, minimum {requirement.minimum}"
    if requirement.minimum is None:
        return None
    # Every exam requirement points at its own numeric field, so this comparison is always
    # like-for-like. If a route ever points one at a non-numeric field, that is a bug in the
    # definition and should fail loudly here rather than quietly passing the requirement.
    if float(held) < requirement.minimum:
        return f"{requirement.name} {held} is below the minimum {requirement.minimum}"
    return None


def classify_route(route: Route, profile: StudentRouteProfile) -> RouteAssessment:
    """OPEN when every precondition is met, UNLOCKABLE when only scores are missing,
    BLOCKED when the qualification itself is wrong."""
    if profile.qualification_held not in route.requires_qualification:
        return RouteAssessment(
            route=route,
            status=RouteStatus.BLOCKED,
            missing=(
                f"This route needs one of: {', '.join(route.requires_qualification)}. "
                f"You hold: {profile.qualification_held}.",
            ),
        )

    gaps = tuple(
        gap for gap in (_exam_gap(exam, profile) for exam in route.exams) if gap is not None
    )
    if gaps:
        return RouteAssessment(route=route, status=RouteStatus.UNLOCKABLE, missing=gaps)
    return RouteAssessment(route=route, status=RouteStatus.OPEN, missing=())


def assess_routes(
    profile: StudentRouteProfile,
    routes: tuple[Route, ...] = ALL_ROUTES,
) -> list[RouteAssessment]:
    """Assess every route at the level the student is asking about.

    Routes at other levels are not filtered out -- they are not applicable. A master's
    route is not a blocked option for a school-leaver, it is a different question. The
    Azerbaijani prep year is defined at bachelor level (`level="bachelor"`) like any other
    bachelor route, so it is included for a bachelor-seeker by this same ordinary filter --
    there is no special case for it here.
    """
    return [
        classify_route(route, profile)
        for route in routes
        if route.level == profile.level_sought
    ]
