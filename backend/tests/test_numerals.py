"""The numeral guard: no number reaches a student unless something produced it.

Spec §8 says numbers come from ML or arithmetic and the LLM supplies framing. That is a
rule about output, so it is checked on output. Each failing case below is a sentence a
competent model would plausibly write and that nothing in the payload supports.
"""

import pytest

from app.services.agent.numerals import (
    assert_numerals_supported,
    numerals_in,
    supported_numerals,
    unsupported_numerals,
)
from app.services.agent.route_tools import assess_student_routes, list_funding_options

SCHOOL_LEAVER = {
    "level_sought": "bachelor",
    "qualification_held": "attestat",
    "dim_score": 520,
    "ielts": 7.0,
    "language_certificate_level": "C1",
}


def test_formatting_a_number_the_way_a_person_writes_it_is_not_a_violation():
    """1,200 and 1200 are the same claim, and 7.0 and 7 are the same score. The guard
    catches invented quantities, not prose conventions."""
    payload = {"cost_azn_low": 1200, "ielts": 7.0}
    assert unsupported_numerals("It costs 1,200 AZN and needs IELTS 7.", payload) == ()
    assert unsupported_numerals("1200 AZN, IELTS 7.0", payload) == ()


def test_a_number_from_inside_a_citation_string_is_supported():
    """A citation reads 'EU Directive 2019/790' and a gate reads '2,800 documented hours'.
    Quoting those back is correct, so string contents are mined, not just numeric fields."""
    payload = {"citation": "chevening.org -- 2,800 documented hours of work experience"}
    assert unsupported_numerals("Chevening asks for 2800 hours.", payload) == ()


def test_the_midpoint_of_a_cost_band_is_caught():
    """The realistic failure. Handed 1,000-4,000, a model writes 'about 2,500 a year'.
    It reads as a fact, it is not in the data, and nothing else would notice."""
    payload = {"cost_azn_low": 1000, "cost_azn_high": 4000}
    assert unsupported_numerals("Budget about 2,500 AZN a year.", payload) == ("2500",)


def test_a_helpfully_rounded_up_requirement_is_caught():
    """Handed IELTS 6.0 a model writes 'IELTS 6.5, which most universities want'. That
    sends a student with 6.0 away from a route that is open to them."""
    payload = {"exams_required": [{"name": "IELTS", "minimum": 6.0}]}
    assert unsupported_numerals("You will need IELTS 6.5 for this.", payload) == ("6.5",)


def test_a_true_boolean_does_not_support_a_bare_one():
    """`True` is an int subclass in Python, so the naive walk would let any '1' through."""
    payload = {"foundation_required": True}
    assert "1" in supported_numerals(payload)  # via the small always-allowed set
    assert unsupported_numerals("There are 47 universities.", payload) == ("47",)


def test_duplicates_are_reported_once_and_in_order():
    payload = {"ielts": 7.0}
    assert unsupported_numerals("6.5, then 5.5, then 6.5 again.", payload) == ("6.5", "5.5")


def test_numerals_in_reads_them_in_order():
    assert numerals_in("IELTS 6.5, DIM 520, cost 1,200") == ("6.5", "520", "1200")


def test_the_assertion_names_what_it_caught():
    """A failure that says 'an unsupported number' sends the reader to diff two blobs."""
    with pytest.raises(ValueError, match="2500"):
        assert_numerals_supported(
            "About 2,500 AZN.", {"cost_azn_low": 1000, "cost_azn_high": 4000}
        )


def test_a_faithful_answer_over_the_real_route_payload_passes():
    """End to end against what the agent is actually handed, not a constructed payload."""
    payload = assess_student_routes.invoke(SCHOOL_LEAVER)
    answer = (
        "Germany and the UK are closed to you on the attestat itself. One year at an "
        "Azerbaijani university opens both: that path takes 12 months and costs between "
        "1,000 and 4,000 AZN, and it also keeps Turkey and Poland available."
    )
    assert unsupported_numerals(answer, payload) == ()


def test_an_invented_total_over_the_real_route_payload_fails():
    """The model adds the prep year to the German route and states a total nobody computed.
    Both inputs are in the payload; the sum is not, and it is wrong besides."""
    payload = assess_student_routes.invoke(SCHOOL_LEAVER)
    answer = "The whole plan comes to roughly 9,600 AZN over two years."
    assert "9600" in unsupported_numerals(answer, payload)


def test_an_invented_scholarship_figure_over_the_real_funding_payload_fails():
    payload = list_funding_options.invoke({**SCHOOL_LEAVER, "age": 18})
    answer = "Türkiye Bursları covers about 3,500 lira a month for living costs."
    assert "3500" in unsupported_numerals(answer, payload)
