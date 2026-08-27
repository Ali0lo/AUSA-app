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

