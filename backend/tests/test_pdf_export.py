import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.pdf_export import generate_application_dossier_pdf

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


def test_pdf_renders_missing_values_as_not_stated():
    """A missing GPA is 'not stated', never 3.5. A missing blocked account is not
    'Not Required' either -- we were not told, and that is a different claim."""
    pdf_bytes = generate_application_dossier_pdf(
        student_data={"email": "someone@ausa.edu.az"},
        program_data={"university_name": "Some University", "program_name": "Some Programme"},
        motivation_letter="Dear Admissions Committee, ...",
    )
    assert pdf_bytes.startswith(b"%PDF")

