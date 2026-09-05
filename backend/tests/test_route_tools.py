"""The agent's tools over the route engine.

These assert that a tool returns what the service already computed, and -- more importantly
-- that the four kinds of "no" stay four kinds of "no" all the way to the model. An agent
that receives a merged answer will narrate a merged answer, and the distinction between "we
have not checked" and "you do not qualify" is the one this product exists to keep.
"""

from app.services.agent.route_tools import (
    assess_student_routes,
    describe_route_requirements,
    explain_funding_gate,
    list_funding_options,
    route_tools,
)

# The spec's own walkthrough case: a Baku school-leaver with this year's attestat.
SCHOOL_LEAVER = {
    "level_sought": "bachelor",
    "qualification_held": "attestat",
    "dim_score": 520,
    "ielts": 7.0,
    "language_certificate_level": "C1",
}


def test_the_agent_can_see_routes_at_all():
    """Before this module the assistant's tools could see documents and nothing else."""
    assert len(route_tools) == 4
    names = {t.name for t in route_tools}
    assert names == {
        "assess_student_routes",
        "describe_route_requirements",
        "list_funding_options",
        "explain_funding_gate",
    }


def test_a_school_leaver_is_told_germany_and_the_uk_are_blocked():
    """The product's central finding, reachable by the agent rather than only by the API."""
    result = assess_student_routes.invoke(SCHOOL_LEAVER)

    blocked_countries = {b["country_code"] for b in result["blocked"]}
    assert blocked_countries == {"DE", "GB"}

    for entry in result["blocked"]:
        # A blocked route without a reason is the thing an agency does. Every one of ours
        # names the qualification that closed it, and where that was read.
        assert "attestat" in entry["reason"]
        assert entry["citation"]


def test_the_prep_year_two_hop_plan_is_offered_not_just_the_block():
    """"Germany is closed" is only half an answer; the other half is what opens it."""
    result = assess_student_routes.invoke(SCHOOL_LEAVER)

    two_hop = [p for p in result["plans"] if p["route_keys"] == ["az-prep-year", "de-bachelor-direct"]]
    assert len(two_hop) == 1
    plan = two_hop[0]
    assert plan["status"] == "open"
    assert plan["total_months"] == 12
    assert plan["destination_country"] == "DE"


def test_an_unknown_route_key_is_refused_rather_than_described():
    result = describe_route_requirements.invoke({"route_key": "fr-bachelor-direct"})
    assert result["found"] is False
    assert "de-bachelor-direct" in result["known_route_keys"]
    # The instruction matters as much as the flag: without it a model fills the gap from
    # general knowledge, which is exactly a fabricated requirement.
    assert "general knowledge" in result["note"]


def test_a_route_reports_what_it_accepts_and_where_that_was_read():
    result = describe_route_requirements.invoke({"route_key": "de-bachelor-direct"})
    assert result["found"] is True
    assert "one_year_university" in result["accepts_any_one_of"]
    assert "attestat" not in result["accepts_any_one_of"]
    assert result["citation"]


def test_germanys_visa_deposit_is_reported_separately_from_the_route_cost():
    """Folding it in would claim Germany costs the deposit; omitting it quotes a
    tuition-free route to a student who can never be issued the visa."""
    result = describe_route_requirements.invoke({"route_key": "de-bachelor-direct"})
    assert result["proof_of_funds"] is not None
    assert result["proof_of_funds"]["amount"] > 0
    assert result["proof_of_funds"]["currency"]
    # And it is not silently added into the route's own money band.
    assert result["cost_azn_high"] < result["proof_of_funds"]["amount"]


def test_unknown_gates_stay_separate_from_missing_ones():
    """A student who never told us their age has an UNCHECKED age gate, not a passed one.

    Türkiye Bursları is one of only two awards open at bachelor level, and its gate is being
    under 21. Reporting it as met because nobody asked would be the most expensive kind of
    wrong answer this product can give.
    """
    without_age = list_funding_options.invoke(SCHOOL_LEAVER)
    turkiye = next(
        s for s in without_age["scholarships"] if s["key"] == "turkiye-burslari"
    )
    assert any("age" in gate.lower() or "21" in gate for gate in turkiye["gates_unknown"])
    assert turkiye["status"] != "open"

    with_age = list_funding_options.invoke({**SCHOOL_LEAVER, "age": 18})
    turkiye_aged = next(
        s for s in with_age["scholarships"] if s["key"] == "turkiye-burslari"
    )
    assert not turkiye_aged["gates_unknown"]


def test_every_funder_is_offered_not_just_the_state_programme():
    """The catalogue modelled one of eleven instruments until 4 September, because the DP
    was the only one publishing a downloadable file -- data-availability bias, and the
    research says a school-leaver should look at Türkiye Bursları first."""
    result = list_funding_options.invoke(SCHOOL_LEAVER)
    assert len(result["scholarships"]) == 10
    assert result["state_programme"]["name"] == "Dövlət Proqramı"


def test_the_funding_answer_carries_its_own_provenance_warning():
    """Every figure in this catalogue came from a research summary whose primary pages
    nobody has opened. The agent is told so, because the student should be."""
    result = list_funding_options.invoke(SCHOOL_LEAVER)
    assert "research-brief" in result["provenance_warning"]
    assert "possibly eligible" in result["note"].lower()


def test_the_prep_year_scholarship_trade_off_reaches_the_agent():
    """A 20-year-old who takes the prep year to open Germany is 21 at the next Turkish
    window and loses a fully funded place in the same move."""
    result = list_funding_options.invoke({**SCHOOL_LEAVER, "age": 20})
    assert result["prep_year_warning"]
    assert "21" in result["prep_year_warning"]


def test_a_bachelor_applicant_is_told_chevening_is_closed_not_competitive():
    result = explain_funding_gate.invoke(
        {"scholarship_key": "chevening", "level_sought": "bachelor", "qualification_held": "attestat"}
    )
    assert result["found"] is True
    assert result["status"] == "blocked"
    assert result["gates_blocked"]
    assert "closed" in result["gates_blocked"][0]


def test_an_unknown_award_is_refused_rather_than_described():
    result = explain_funding_gate.invoke(
        {"scholarship_key": "gates-foundation", "level_sought": "master", "qualification_held": "bachelor_degree"}
    )
    assert result["found"] is False
    assert "chevening" in result["known_keys"]
    assert "general knowledge" in result["note"]


def test_the_cost_band_says_it_is_not_a_total():
    """A model handed two numbers will add them. The tool says not to, in the payload,
    because the system prompt is not where a caller looks."""
    result = assess_student_routes.invoke(SCHOOL_LEAVER)
    assert "Do not add these numbers together." in result["note"]
