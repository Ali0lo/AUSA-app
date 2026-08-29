import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.data_pipeline.extraction import ExtractedProgramData, extract_program_info_from_text
from app.data_pipeline.jobs import (
    refresh_germany_data_job,
    refresh_university_data_job,
)
from app.data_pipeline.scraper import fetch_page_content


def test_extracted_program_data_schema():
    data = ExtractedProgramData(
        university_name="TU Munich",
        program_name="M.Sc. Computer Science",
        degree_level="master",
        min_gpa=3.2,
        tuition_fee_usd=12000.0,
        min_ielts=6.5,
        confidence_score=95.0,
        requires_studienkolleg=False,
        blocked_account_eur=11208.0
    )
    assert data.university_name == "TU Munich"
    assert data.degree_level == "master"
    assert data.confidence_score == 95.0
    assert data.min_gpa == 3.2
    assert data.blocked_account_eur == 11208.0


@pytest.mark.asyncio
async def test_fetch_page_content_html_stripping():
    sample_html = """
    <html>
        <head><title>Test Uni</title><style>.test{color:red;}</style></head>
        <body>
            <header>Header Nav</header>
            <script>console.log('strip me');</script>
            <h1>Master of Computer Science</h1>
            <p>Annual tuition fee: $15,000 USD. Minimum GPA: 3.2.</p>
            <footer>Footer Links</footer>
        </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.text = sample_html
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        text = await fetch_page_content("https://example.edu/program")
        assert "Master of Computer Science" in text
        assert "Annual tuition fee: $15,000 USD" in text
        assert "console.log" not in text
        assert "Header Nav" not in text


@pytest.mark.asyncio
async def test_extract_program_info_from_text_fallback():
    raw_text = (
        "University of Amsterdam. Master of Science in Data Science. "
        "Minimum GPA requirement: 3.5. IELTS requirement: 7.0. "
        "Annual tuition fee: $18,000 USD. Application deadline: December 1, 2026."
    )
    extracted = await extract_program_info_from_text(raw_text)
    assert isinstance(extracted, ExtractedProgramData)
    assert extracted.confidence_score > 0.0
    assert extracted.min_gpa == 3.5 or extracted.min_ielts == 7.0


@pytest.mark.asyncio
async def test_refresh_germany_data_job():
    results = await refresh_germany_data_job(min_confidence_threshold=85.0)
    assert len(results) >= 1
    for rec in results:
        assert rec["country"] == "Germany"
        assert rec["status"] == "success"
        assert rec["verification_status"] in ["verified", "flagged_for_review"]
        assert "blocked_account_eur" in rec["extracted_data"]


# test_refresh_azerbaijan_data_job was removed with the job it covered (2026-08-29).
#
# The test asserted status == "success" for every record, which it could only satisfy
# because the collector fabricated three programs from mock HTML when the network call
# failed. It therefore passed whether or not the real sources were reachable -- a green
# test asserting invented DIM scores. See backend/app/data_pipeline/jobs.py.
