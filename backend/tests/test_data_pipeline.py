import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.data_pipeline.extraction import ExtractedProgramData, extract_program_info_from_text
from app.data_pipeline.jobs import refresh_university_data_job
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
async def test_refresh_job_fails_loudly_when_fetch_fails():
    """A URL that cannot be fetched must yield no data -- not substitute data."""
    with patch(
        "app.data_pipeline.jobs.fetch_page_content",
        new=AsyncMock(side_effect=RuntimeError("connection refused")),
    ):
        results = await refresh_university_data_job(["https://example.edu/program"])

    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert "connection refused" in results[0]["error"]
    assert "extracted_data" not in results[0]


@pytest.mark.asyncio
async def test_refresh_job_never_marks_a_record_verified():
    """Only a human can move a record to human-verified; LLM confidence cannot."""
    high_confidence = ExtractedProgramData(
        university_name="Example University",
        program_name="M.Sc. Computer Science",
        confidence_score=99.0,
    )
    with patch(
        "app.data_pipeline.jobs.fetch_page_content",
        new=AsyncMock(return_value="Example University M.Sc. Computer Science."),
    ), patch(
        "app.data_pipeline.jobs.extract_program_info_from_text",
        new=AsyncMock(return_value=high_confidence),
    ):
        results = await refresh_university_data_job(["https://example.edu/program"])

    assert results[0]["status"] == "success"
    assert results[0]["provenance"] == "claude-extracted"
    assert results[0]["needs_review"] is False


# test_refresh_azerbaijan_data_job was removed with the job it covered (2026-08-29).
#
# The test asserted status == "success" for every record, which it could only satisfy
# because the collector fabricated three programs from mock HTML when the network call
# failed. It therefore passed whether or not the real sources were reachable -- a green
# test asserting invented DIM scores. See backend/app/data_pipeline/jobs.py.
#
# test_refresh_germany_data_job was removed the same way (2026-08-30). It asserted
# status == "success" and a present blocked_account_eur for every record, both of which
# only held because collect_germany.py fabricated three German programs from mock HTML and
# hardcoded the blocked-account figure. The assertions described the mock, not the source.
