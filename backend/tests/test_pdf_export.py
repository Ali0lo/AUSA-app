import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.pdf_export import _display, generate_application_dossier_pdf

client = TestClient(app)


def test_generate_application_dossier_pdf():
    student_data = {
        "email": "test_student@ausa.edu.az",
        "gpa": 3.8,
        "ielts": 7.5,
        "degree_level": "master",
        "field_of_study": "Data Science"
    }
    program_data = {
        "university_name": "ADA University",
        "program_name": "M.S. Data Analytics",
        "degree_level": "master",
        "country": "Azerbaijan",
        "tuition_fee": 4410.0,
        "deadline": "2026-06-01"
    }
    motivation_letter = "Dear Admissions Committee,\n\nI am writing to express my strong interest in the M.S. Data Analytics program at ADA University."

    pdf_bytes = generate_application_dossier_pdf(student_data, program_data, motivation_letter)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_export_motivation_letter_pdf_endpoint():
    payload = {
        "motivation_letter_text": "Dear Admissions Committee,\n\nI am applying for the Computer Science program.",
        "student_data": {
            "email": "std_export@ausa.edu.az",
            "gpa": 3.7,
            "ielts": 7.0,
            "degree_level": "master",
            "field_of_study": "Computer Science"
        },
        "program_data": {
            "university_name": "TU Munich",
            "program_name": "M.Sc. Informatics",
            "degree_level": "master",
            "country": "Germany",
            "tuition_fee": 0.0,
            "blocked_account_eur": 11208.0
        }
    }

    response = client.post("/api/v1/export/motivation-letter/pdf", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_export_refuses_to_invent_a_student():
    """An empty payload used to produce a dossier about a fictional person.

    The defaults were gpa 3.65, ielts 7.0, and a TU Munich programme with an
    11208.0 EUR blocked account -- rendered into a PDF the student could submit.
    """
    response = client.post(
        "/api/v1/export/motivation-letter/pdf",
        json={"motivation_letter_text": "Dear Admissions Committee, ..."},
    )
    assert response.status_code == 422
    assert b"%PDF" not in response.content


def test_export_refuses_when_only_the_programme_is_known():
    """Half a dossier is still a fabricated dossier."""
    response = client.post(
        "/api/v1/export/motivation-letter/pdf",
        json={
            "motivation_letter_text": "Dear Admissions Committee, ...",
            "program_data": {
                "university_name": "TU Munich",
                "program_name": "M.Sc. Informatics",
            },
        },
    )
    assert response.status_code == 422


def test_export_refuses_when_the_programme_has_no_name():
    """A student is known but the programme half doesn't name a programme.

    The dossier is *about* a specific programme -- university_name and program_name
    absent (or blank) means there is no programme to be about, even though other
    fields (tuition, country, ...) were supplied.
    """
    response = client.post(
        "/api/v1/export/motivation-letter/pdf",
        json={
            "motivation_letter_text": "Dear Admissions Committee, ...",
            "student_data": {"email": "someone@ausa.edu.az", "gpa": 3.8},
            "program_data": {"country": "Germany", "tuition_fee": 0.0},
        },
    )
    assert response.status_code == 422


def test_pdf_generates_even_with_missing_values():
    """Smoke test only: a near-empty student/programme dict still yields a valid PDF.

    This does NOT check what gets rendered for the missing fields -- reportlab's
    output is a compressed content stream, not plain text, so this can't assert
    "Not stated" appears without decompressing it. That coverage instead lives in
    the _display unit tests below, which pin the exact rendering rule this smoke
    test cannot see.
    """
    pdf_bytes = generate_application_dossier_pdf(
        student_data={"email": "someone@ausa.edu.az"},
        program_data={"university_name": "Some University", "program_name": "Some Programme"},
        motivation_letter="Dear Admissions Committee, ...",
    )
    assert pdf_bytes.startswith(b"%PDF")


def test_display_none_renders_as_not_stated():
    assert _display(None) == "Not stated"


def test_display_zero_is_not_caught_by_the_truthiness_trap():
    """0.0 is a value the student gave us, not a blank -- `x if value else default`
    would wrongly treat it as missing. `is not None` does not."""
    assert _display(0.0, lambda v: f"{v:.2f}") == "0.00"


def test_display_formats_a_real_value():
    assert _display(3.8, lambda v: f"{v:.2f}") == "3.80"
    assert _display("Some University") == "Some University"

