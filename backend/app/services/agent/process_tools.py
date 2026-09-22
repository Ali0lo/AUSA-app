"""The agent's tool over the document legalisation and recognition library.

Separate from `route_tools.py` because it answers a different question. Those tools answer
*where can I go* and *why not there*; this one answers *what do I physically do to my
documents*, which is what a student is left alone with once a route comes back OPEN.

It deliberately does not restate the visa deposit, the programme's portal or a funder's
window. Each of those has an owner, and `see_also` names the owner rather than copying the
value -- a number with two homes drifts, and the deposit in particular is one this project
already took care to keep in one place.
"""

from typing import Any, Dict, List

from langchain_core.tools import tool

from app.domain.process import STATUS_CURATED
from app.domain.process_definitions import PROCESS_BY_ROUTE_KEY
from app.domain.route_definitions import ALL_ROUTES

# Where the three neighbouring layers live. Returned on every curated answer so the model
# can fetch a fact instead of inventing one to fill an obvious hole.
SEE_ALSO = {
    "proof_of_funds": (
        "The visa deposit belongs to the route. Call `describe_route_requirements` with "
        "this route_key; do not state a deposit figure from here."
    ),
    "programme_portal_and_deadline": (
        "The application portal, fee, document list and deadline belong to the individual "
        "programme row in the catalogue, not to the route."
    ),
    "funder_window": (
        "Each scholarship publishes its own application window. Call `list_funding_options` "
        "or `explain_funding_gate`; a funder's deadline is never the university's."
    ),
}


def _step_as_dict(step) -> Dict[str, Any]:
    return {
        "key": step.key,
        "title": step.title,
        "detail": step.detail,
        "when": step.when,
        "authority": step.authority,
        "citation": step.citation,
        "provenance": step.provenance,
        "last_checked": step.last_checked,
    }


@tool
def describe_application_process(route_key: str) -> Dict[str, Any]:
    """What a student must do to their Azerbaijani documents to use them on one route.

    Translation, certification, credential evaluation and recognition -- the paperwork
    between an offer and a place. Use it after `assess_student_routes` has found a route
    the student can actually take.

    Args:
        route_key: e.g. 'de-bachelor-studienkolleg', 'de-bachelor-direct', 'tr-master-direct'.
            Route keys come back from `assess_student_routes`.

    Returns:
        `steps`, each with the page it was read from, plus `known_gaps` -- procedures we
        believe exist but could not verify. State a gap as a gap, never as a requirement.
        `status: 'not_collected'` means nobody curated this route: say so rather than
        implying no documents are needed. `found: false` means the key is not one of ours.
    """
    route = next((r for r in ALL_ROUTES if r.key == route_key.strip().lower()), None)
    if route is None:
        return {
            "found": False,
            "route_key": route_key,
            "steps": [],
            "known_route_keys": [r.key for r in ALL_ROUTES],
            "note": (
                "We hold no route by that key. Tell the student we do not have it rather "
                "than describing apostille or translation rules from general knowledge."
            ),
        }

    process = PROCESS_BY_ROUTE_KEY.get(route.key)
    if process is None:
        # Every route in ALL_ROUTES has an entry; a missing one is a library bug, and
        # reporting it as "no steps" would hide the bug behind a plausible answer.
        raise KeyError(
            f"route {route.key!r} exists but has no process entry. Add one to "
            f"domain/process_definitions.py, as not_collected if nobody has curated it."
        )

    steps: List[Dict[str, Any]] = [_step_as_dict(s) for s in process.steps]

    return {
        "found": True,
        "route_key": route.key,
        "country_code": route.country_code,
        "level": route.level,
        "status": process.status,
        "steps": steps,
        "known_gaps": list(process.known_gaps),
        "note": process.note,
        "see_also": SEE_ALSO,
        "provenance_warning": (
            "Every step here is claude-extracted, never human-verified: a person has not "
            "re-opened these pages. Requirements change; tell the student to confirm each "
            "step against the cited page."
            if process.status == STATUS_CURATED
            else None
        ),
    }


process_tools = [describe_application_process]
