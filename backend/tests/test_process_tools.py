"""The agent's tool over the document legalisation and recognition library.

This library owns exactly one layer: what a student must do to their AZERBAIJANI DOCUMENTS
to make them usable in the destination -- apostille, sworn translation, credential
evaluation, and recognition on return. Three neighbouring layers are owned elsewhere and
must not be copied here, because a fact with two homes drifts:

    the visa deposit          -> `Route.proof_of_funds` (domain/route_definitions.py)
    the portal and documents  -> the catalogue row (data/curation/*.csv)
    a funder's own window     -> `Scholarship.window` (domain/scholarship_definitions.py)

These tests assert the layer stays its own, that an uncollected route reads as a named
absence rather than as "nothing required", and that two routes into the same country at the
same level do not share one checklist.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.domain.route_definitions import ALL_ROUTES
from app.main import app
from app.domain.process_definitions import ALL_ROUTE_PROCESSES
from app.services.agent.numerals import unsupported_numerals
from app.services.agent.process_tools import describe_application_process


def test_an_unknown_route_key_is_refused_rather_than_described():
    """The cite-or-drop rule at the tool boundary.

    A model asked about a route we do not hold will describe one from general knowledge
    unless the tool tells it not to. Apostille and translation rules are exactly the kind
    of plausible-sounding process detail it would invent.
    """
    result = describe_application_process.invoke({"route_key": "fr-bachelor-direct"})

    assert result["found"] is False
    assert result["steps"] == []
    assert "fr-bachelor-direct" not in result["known_route_keys"]
    assert set(result["known_route_keys"]) == {r.key for r in ALL_ROUTES}


def test_an_uncollected_route_names_its_absence_instead_of_returning_nothing():
    """Rule 1: an unknown must never read as permission.

    `pl-master-direct` is a real route we have not curated the paperwork for. An empty
    step list on its own says "no documents needed", which is the direction of error that
    costs a student an application. It has to arrive labelled.
    """
    result = describe_application_process.invoke({"route_key": "pl-master-direct"})

    assert result["found"] is True
    assert result["status"] == "not_collected"
    assert result["steps"] == []
    assert result["note"].strip(), "an empty step list must arrive with the reason it is empty"


def test_a_curated_route_is_not_confusable_with_an_uncollected_one():
    """The two states are read by a model, so they cannot share a shape."""
    result = describe_application_process.invoke({"route_key": "de-bachelor-studienkolleg"})

    assert result["status"] == "curated"
    assert len(result["steps"]) >= 1


def test_two_routes_into_germany_at_the_same_level_do_not_share_one_checklist():
    """The reason the key is a route and not a (country, level) pair.

    An attestat holder goes through a Studienkolleg; a prep-year holder submits a transcript
    of completed university study. Merging them would hand one of the two a checklist that
    omits the document their route actually turns on.
    """
    studienkolleg = describe_application_process.invoke(
        {"route_key": "de-bachelor-studienkolleg"}
    )
    prep_year = describe_application_process.invoke({"route_key": "de-bachelor-direct"})

    studienkolleg_steps = {s["key"] for s in studienkolleg["steps"]}
    prep_year_steps = {s["key"] for s in prep_year["steps"]}

    assert studienkolleg_steps != prep_year_steps
    assert "de-transcript" in prep_year_steps
    assert "de-transcript" not in studienkolleg_steps


def test_every_route_the_engine_can_return_has_a_process_entry():
    """A route with no entry would fall through the tool as silence.

    `assess_student_routes` can return any of the 16. If one has no process entry the
    student is told nothing at all, which reads as nothing being required.
    """
    assert {p.route_key for p in ALL_ROUTE_PROCESSES} == {r.key for r in ALL_ROUTES}


def test_every_curated_step_carries_a_citation_and_the_date_it_was_read():
    """Rule 3: every claim a student sees came from a cited page."""
    for process in ALL_ROUTE_PROCESSES:
        for step in process.steps:
            assert step.citation.strip(), f"{step.key} has no citation"
            assert step.last_checked.strip(), f"{step.key} has no last_checked date"
            assert step.provenance != "human-verified", (
                f"{step.key} claims human verification, which this file cannot confer"
            )


def test_the_library_points_at_the_visa_deposit_instead_of_restating_it():
    """One fact, one home.

    `Route.proof_of_funds` already carries the Sperrkonto with its own citation and a
    docstring explaining why it is not folded into the route's cost. A second copy here
    would drift from it the first time the figure changed.
    """
    result = describe_application_process.invoke({"route_key": "de-bachelor-direct"})

    assert "proof_of_funds" in result["see_also"]
    rendered = " ".join(s["detail"] + s["title"] for s in result["steps"])
    assert "11904" not in rendered.replace(",", "").replace(".", "")
    assert "Sperrkonto" not in rendered


def test_the_agent_is_actually_given_the_process_tool():
    """A tool the graph does not bind is a tool the model cannot call.

    The ML artifacts in this project sat unused for a fortnight for exactly this reason:
    built, measured, and wired to nothing.
    """
    from app.services.agent.graph import tools as bound_tools

    assert "describe_application_process" in {t.name for t in bound_tools}


@pytest.mark.asyncio
async def test_the_process_is_reachable_over_http_without_a_language_model():
    """Curated data, so it works with no API key -- the same reason `/routes/parse` exists.

    There is no OPENAI_API_KEY in this project, so anything reachable only through the agent
    is unreachable in practice.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/routes/de-bachelor-direct/process")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "curated"
    assert any(step["key"] == "de-transcript" for step in body["steps"])
    assert body["steps"][0]["citation"].startswith("https://")


@pytest.mark.asyncio
async def test_an_uncollected_route_is_a_200_saying_so_not_a_404():
    """404 means "no such route", which is a different fact from "nobody curated it".

    Collapsing the two would tell a student their real route does not exist.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/routes/pl-master-direct/process")

    assert response.status_code == 200
    assert response.json()["status"] == "not_collected"


@pytest.mark.asyncio
async def test_a_route_we_do_not_have_is_a_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/routes/fr-bachelor-direct/process")

    assert response.status_code == 404


def test_the_numeral_guard_accepts_the_timings_the_steps_actually_state():
    """C2.3's guard has to let a model repeat a processing time it was handed.

    The VPD's 4-to-6 weeks is the most decision-changing number in the German process --
    a student who learns it late misses the university's deadline with everything else in
    order. If the guard rejected it the model would have to omit it.
    """
    payload = describe_application_process.invoke({"route_key": "de-bachelor-direct"})
    sentence = "Start the VPD early: uni-assist usually takes 4 to 6 weeks to issue it."

    assert unsupported_numerals(sentence, payload) == ()


def test_the_numeral_guard_still_catches_a_timing_nobody_gave_the_model():
    """The same payload must not wave through an invented figure."""
    payload = describe_application_process.invoke({"route_key": "de-bachelor-direct"})
    invented = "Most Azerbaijani students get their VPD back in about 9 weeks."

    assert unsupported_numerals(invented, payload) == ("9",)


def test_the_prompt_tells_the_model_a_gap_is_not_a_cleared_step():
    """The tool returns `known_gaps`; the prompt has to say what to do with them.

    An unverified procedure listed beside verified ones will be narrated as one more
    requirement unless the model is told the difference -- and here the difference is a
    student paying for a legalisation nobody asked for.
    """
    from app.services.agent.graph import SYSTEM_PROMPT

    assert "describe_application_process" in SYSTEM_PROMPT
    assert "known_gaps" in SYSTEM_PROMPT
