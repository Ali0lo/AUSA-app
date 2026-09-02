"""Classify routes against a student profile.

The distinction the two non-open statuses draw is the product's core idea: a score you
have not got yet is a gap you can close this cycle (UNLOCKABLE), while a qualification you
do not hold is not (BLOCKED) -- it needs a different route first, which is what Task 9's
composition is for.
"""

from dataclasses import dataclass, replace
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


@dataclass(frozen=True)
class RoutePlan:
    """One or two routes end to end, with their costs summed."""
    hops: tuple[Route, ...]
    total_months: int
    total_cost_azn: tuple[int, int]
    status: RouteStatus
    missing: tuple[str, ...]


def _plan_from_hops(hops: tuple[Route, ...], assessments: tuple[RouteAssessment, ...]) -> RoutePlan:
    return RoutePlan(
        hops=hops,
        total_months=sum(hop.time_cost_months for hop in hops),
        total_cost_azn=(
            sum(hop.money_cost_azn[0] for hop in hops),
            sum(hop.money_cost_azn[1] for hop in hops),
        ),
        # A plan is only as open as its weakest hop. Eligibility defaults are asymmetric:
        # this is OPEN only when every hop is confirmed OPEN, never as a fallback branch --
        # a stray BLOCKED assessment that ever reached this function (it should not; both
        # call sites filter BLOCKED out first) would land on UNLOCKABLE, not be laundered
        # into OPEN.
        status=(
            RouteStatus.OPEN
            if all(a.status is RouteStatus.OPEN for a in assessments)
            else RouteStatus.UNLOCKABLE
        ),
        missing=tuple(gap for a in assessments for gap in a.missing),
    )


def compose_two_hop(
    profile: StudentRouteProfile,
    routes: tuple[Route, ...] = ALL_ROUTES,
) -> list[RoutePlan]:
    """Every reachable plan, one or two hops, cheapest in time first.

    A second hop is only proposed where the direct route is BLOCKED. Composition exists to
    answer a blockage; proposing a 12-month detour to a student who can already go directly
    would be the steering behaviour this product refuses.

    The cap is two. Deeper chains exist but do not help a 17-year-old, and uncapped graph
    search turns a product into a research project (spec §4.1).
    """
    at_level = tuple(r for r in routes if r.level == profile.level_sought)
    plans: list[RoutePlan] = []
    blocked_keys: set[str] = set()

    for route in at_level:
        assessment = classify_route(route, profile)
        if assessment.status is RouteStatus.BLOCKED:
            blocked_keys.add(route.key)
            continue
        plans.append(_plan_from_hops((route,), (assessment,)))

    # Second hop: a route the student CAN start, whose completion satisfies a route that
    # is blocked today.
    unlockers = [
        (r, classify_route(r, profile)) for r in at_level
        if r.produces_qualification is not None
    ]
    for first, first_assessment in unlockers:
        if first_assessment.status is RouteStatus.BLOCKED:
            continue
        # The same student, after finishing the first hop. `replace` rather than rebuilding
        # from __dict__: it fails loudly if the field is ever renamed, instead of silently
        # dropping every score the profile carries.
        after = replace(profile, qualification_held=first.produces_qualification)
        for second in at_level:
            # A route must never compose with itself. Note: given `blocked_keys` and
            # `first_assessment` are both computed from the same `classify_route(route,
            # profile)` call on the ORIGINAL profile, `first.key` can never be a member of
            # `blocked_keys` here -- so `second.key not in blocked_keys` alone already
            # rejects `second.key == first.key` on every path we've found. The explicit
            # check is kept anyway as a named invariant, in case that computation ever
            # changes (e.g. blocked_keys computed from a different profile per hop).
            if second.key == first.key or second.key not in blocked_keys:
                continue
            second_assessment = classify_route(second, after)
            if second_assessment.status is RouteStatus.BLOCKED:
                continue
            plans.append(
                _plan_from_hops((first, second), (first_assessment, second_assessment))
            )

    return sorted(plans, key=lambda p: (p.total_months, p.total_cost_azn[0]))
