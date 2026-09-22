"""The document legalisation and recognition domain: pure data and no I/O.

A `RouteProcess` answers the question a student is left alone with once a route comes back
OPEN: *what do I physically do to my Azerbaijani documents so this country will accept
them?* Translation, certification, credential evaluation, recognition on return.

WHAT THIS LAYER DOES NOT OWN. Three neighbouring facts already have a home, and copying one
here would create a second source of truth that drifts from the first:

    the visa deposit          -> `Route.proof_of_funds`      (domain/route_definitions.py)
    the portal, fee, deadline -> the catalogue row           (data/curation/*.csv)
    a funder's own window     -> `Scholarship.window`        (domain/scholarship_definitions.py)

`see_also` on the tool response points at those rather than restating them.

WHY THE KEY IS A ROUTE AND NOT A COUNTRY. Germany takes an attestat holder through a
Studienkolleg and a prep-year holder through a transcript of completed university study.
Same country, same level, different paperwork. Keying on `(country, level)` would have
merged `de-bachelor-studienkolleg` and `de-bachelor-direct` into one checklist, and a
merged checklist is a confidently wrong one.
"""

from dataclasses import dataclass, field
from typing import Tuple

# When in the application the step falls. Not a date -- the deadline belongs to the
# programme row, and a step's position is stable while a deadline is not.
WHEN_BEFORE_APPLYING = "before_applying"
WHEN_AFTER_OFFER = "after_offer"
WHEN_AFTER_GRADUATION = "after_graduation"

# We have read a primary page and recorded at least one step from it.
STATUS_CURATED = "curated"
# The route is real; nobody has curated its paperwork. NEVER an empty step list on its own
# -- an unchecked route and a route with no requirements must not look the same (ADR-0004).
STATUS_NOT_COLLECTED = "not_collected"


@dataclass(frozen=True)
class ProcessStep:
    """One act the student performs on a document, and the page that says to.

    `citation` carries the URL and the words that were read there. A step without one is a
    process claim nobody can check, which is the thing this project keeps deleting.
    """

    key: str
    title: str
    detail: str
    # One of the WHEN_* constants.
    when: str
    # Who performs or issues it -- a sworn translator, uni-assist, the consulate. The
    # student needs to know who to approach, which is not always who requires it.
    authority: str
    citation: str
    # 'claude-extracted' once a primary page has been read. `human-verified` cannot be set
    # here: only a named person opening the page earns it (tracks/README rule 5).
    provenance: str
    # ISO date the citation was last read.
    last_checked: str

    def __post_init__(self) -> None:
        if not self.citation.strip():
            raise ValueError(f"process step {self.key!r} carries no citation")
        if self.when not in (WHEN_BEFORE_APPLYING, WHEN_AFTER_OFFER, WHEN_AFTER_GRADUATION):
            raise ValueError(f"process step {self.key!r} has an unknown `when`: {self.when!r}")


@dataclass(frozen=True)
class RouteProcess:
    """The paperwork for one route, or a recorded statement that nobody has collected it."""

    route_key: str
    status: str
    steps: Tuple[ProcessStep, ...]
    # For STATUS_NOT_COLLECTED, what is absent and why. For STATUS_CURATED, what the steps
    # cover. Never empty: an empty list of steps must arrive with the reason it is empty.
    note: str
    # Steps we believe exist but could not verify -- an authority whose site refused us, a
    # requirement named only by a secondary source. Carried separately from `steps` so that
    # an unverified claim can be SHOWN without being STATED as a requirement.
    known_gaps: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.note.strip():
            raise ValueError(f"route process {self.route_key!r} carries no note")
        if self.status == STATUS_CURATED and not self.steps:
            raise ValueError(f"route process {self.route_key!r} is curated but holds no steps")
        if self.status == STATUS_NOT_COLLECTED and self.steps:
            raise ValueError(
                f"route process {self.route_key!r} is not_collected but holds steps"
            )
