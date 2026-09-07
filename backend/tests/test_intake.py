"""Free-text intake: read what was said, ask for the rest, invent nothing.

Most of these are the cases where a helpful parser lies -- a number with no anchor, a
subject that looks like a field group, a grade with no scale, a score given twice. Each
assertion is that the module declined to answer rather than answered plausibly.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.agent.intake import Intake, parse_intake, read_student_message
from app.services.agent.route_tools import assess_student_routes

# The sentence Track C's brief is written around.
ROBOTICS = "I want to study robotics, I have DİM 520 and IELTS 7"


def _values(intake: Intake) -> dict:
    return intake.fields


def test_the_briefs_own_sentence_reads_the_two_scores_it_contains():
    intake = parse_intake(ROBOTICS)
    assert _values(intake)["dim_score"] == 520
    assert _values(intake)["ielts"] == 7.0


def test_a_subject_never_becomes_a_dim_field_group():
    """Robotics is engineering, engineering is Group 1, and Group 1's Dövlət Proqramı
    threshold is 400 against 550 for everything else. Reading the group out of the subject
    would move a real gate by 150 points on the strength of one word."""
    intake = parse_intake(ROBOTICS)
    assert "dim_field_group" not in intake.fields
    assert intake.interest == "robotics"
    # And the omission is surfaced as a question rather than left silent.
    assert any("ixtisas qrupu" in ask for ask in intake.worth_asking)


def test_a_named_group_is_read_because_the_student_named_it():
    assert parse_intake("DİM 520, 1-ci qrup").fields["dim_field_group"] == 1
    assert parse_intake("dim 610, group 3").fields["dim_field_group"] == 3


def test_bare_numbers_produce_nothing():
    """Every value is anchored to a token naming its field. 520 is a DİM score because the
    word DİM is beside it, never because 520 looks like one."""
    intake = parse_intake("520, 7, 1350, 19")
    assert intake.fields == {}
    assert intake.still_needed == ("level_sought", "qualification_held")


def test_an_exam_named_without_a_score_sets_nothing():
    intake = parse_intake("I have not taken IELTS yet and I have not sat the SAT")
    assert "ielts" not in intake.fields
    assert "sat" not in intake.fields


def test_sitting_an_exam_is_not_an_sat_score():
    """`sat` is an English verb. The published range is what keeps it from being a score."""
    intake = parse_intake("I sat 3 exams last year")
    assert "sat" not in intake.fields


def test_an_azerbaijani_sentence_reads_the_same_as_an_english_one():
    intake = parse_intake(
        "Mən attestatla xaricdə bakalavr oxumaq istəyirəm. DİM balım 520, yaşım 19."
    )
    assert intake.fields["qualification_held"] == "attestat"
    assert intake.fields["level_sought"] == "bachelor"
    assert intake.fields["dim_score"] == 520
    assert intake.fields["age"] == 19
    assert intake.ready_to_assess


def test_the_quote_is_the_students_own_text_not_a_transliteration():
    """Matching happens on an ASCII-folded copy; the quote is sliced from the original, so
    a student reading their answer back sees the sentence they wrote."""
    intake = parse_intake("DİM balım 520 idi")
    quote = next(h.quote for h in intake.heard if h.field == "dim_score")
    assert "İ" in quote and "ı" in quote


def test_a_held_degree_and_a_sought_level_are_told_apart():
    """The commonest sentence in the product, and the one where both level words appear.
    The intent verb decides; without it this would be a conflict and answer nothing."""
    intake = parse_intake("I finished my bachelor's degree and I want to do a master's")
    assert intake.fields["level_sought"] == "master"
    assert intake.fields["qualification_held"] == "bachelor_degree"
    assert "level_sought" not in intake.conflicts


def test_a_score_stated_twice_with_two_values_is_dropped_not_chosen():
    """Retake or typo, we cannot tell. Taking the higher flatters a student into a route;
    taking the lower closes one."""
    intake = parse_intake("I got IELTS 6.5 in May, then IELTS 7 in August")
    assert "ielts" not in intake.fields
    assert intake.conflicts == ("ielts",)
    assert any("ask the student" in note.lower() for note in intake.notes)


def test_a_grade_without_its_scale_is_not_read_as_a_grade():
    """4.5 is excellent out of 5 and impossible out of 4 -- the same rule the registration
    form enforces (app/domain/grades.py)."""
    intake = parse_intake("My GPA is 4.5")
    assert "gpa" not in intake.fields
    assert "gpa_scale" not in intake.fields
    assert any("scale" in note for note in intake.notes)


def test_a_grade_with_its_scale_is_read():
    intake = parse_intake("Attestat ortalamam 4.5/5")
    assert intake.fields["gpa"] == 4.5
    assert intake.fields["gpa_scale"] == "5.0"


def test_a_score_outside_its_published_range_is_reported_not_clamped():
    intake = parse_intake("I scored DİM 850")
    assert "dim_score" not in intake.fields
    assert any("850" in note for note in intake.notes)


def test_a_one_off_sum_is_not_read_as_a_yearly_budget():
    """Read as annual, a one-off saving triples the student's means over a three-year
    degree and opens routes their money does not reach."""
    assert "budget_azn_per_year" not in parse_intake("I have 8000 AZN saved").fields
    assert parse_intake("I can pay 8000 AZN per year").fields["budget_azn_per_year"] == 8000


def test_a_cefr_level_needs_a_language_beside_it():
    assert parse_intake("My German is B2").fields["language_certificate_level"] == "B2"
    assert "language_certificate_level" not in parse_intake("I live in block C1").fields


def test_chevenings_hour_count_survives_its_thousands_comma():
    intake = parse_intake("I have 2,800 hours of documented work")
    assert intake.fields["work_experience_hours"] == 2800


def test_a_free_text_profile_reaches_the_same_assessment_the_form_does():
    """The point of the module: a sentence produces the engine's real answer, and every
    field the sentence did not state stays unset rather than becoming a default."""
    intake = parse_intake(
        "Attestatım var, bakalavr oxumaq istəyirəm. DİM 520, IELTS 7."
    )
    assert intake.ready_to_assess
    result = assess_student_routes.invoke(intake.fields)
    assert {b["country_code"] for b in result["blocked"]} == {"DE", "GB"}
    # Nothing filled a score the student did not mention.
    assert "toefl" not in intake.fields and "sat" not in intake.fields


def test_the_tool_says_what_it_did_not_read():
    payload = read_student_message.invoke({"message": ROBOTICS})
    assert payload["ready_to_assess"] is False
    assert "qualification_held" in payload["still_needed"]
    # SOCAR's gate is employment and nothing here parses an employer. Saying so is the
    # difference between an unchecked gate and one nobody knows is unchecked.
    assert "employer" in payload["not_parsed"]
    assert "not a DİM ixtisas qrupu" in payload["instruction"]


@pytest.mark.asyncio
async def test_the_endpoint_returns_a_reading_the_student_can_check():
    """`/routes/parse` is reachable with no language model and no API key, which is what
    makes free-text intake something the frontend can ship rather than a chat-only path."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/routes/parse", json={"message": ROBOTICS})

    assert res.status_code == 200
    body = res.json()
    assert body["fields"]["dim_score"] == 520
    assert body["ready_to_assess"] is False
    assert body["interest"] == "robotics"
    assert "dim_field_group" not in body["fields"]
    # Every value comes back with the words behind it, so a misreading is correctable.
    assert {h["field"] for h in body["heard"]} == {"dim_score", "ielts"}
    assert "520" in next(h["quote"] for h in body["heard"] if h["field"] == "dim_score")


@pytest.mark.asyncio
async def test_an_empty_message_is_refused_rather_than_parsed_into_nothing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/routes/parse", json={"message": ""})
    assert res.status_code == 422
