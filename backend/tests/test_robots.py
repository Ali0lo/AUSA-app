"""The fetcher must ask permission before it reads a page.

Until now the project's crawling policy lived in prose: qebulai.az excluded, hochschulstart's
/fileadmin/ off limits, DAAD owed a 2-second delay. `fetch_page_content` itself would retrieve
any URL handed to it, so every one of those rules depended on whoever called it remembering.
These tests move the rule into the code.

The central decision is that an *undeterminable* robots.txt blocks the fetch. That is the same
principle as ADR-0004 one layer down: an unknown must never read as permission.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.data_pipeline.robots import (
    DisallowedByRobotsError,
    RobotsUnavailableError,
    clear_robots_cache,
    is_fetch_allowed,
)
from app.data_pipeline.scraper import fetch_page_content

ALLOW_ALL = "User-agent: *\nAllow: /\n"

# The real shape of qebulai.az's robots.txt, which is why that site is excluded as a source.
QEBULAI_STYLE = (
    "User-agent: ClaudeBot\nDisallow: /\n\n"
    "User-agent: GPTBot\nDisallow: /\n\n"
    "User-agent: CCBot\nDisallow: /\n\n"
    "User-agent: *\nAllow: /\n"
)

# hochschulstart.de publishes its statistics PDFs under a directory it disallows.
HOCHSCHULSTART_STYLE = "User-agent: *\nDisallow: /fileadmin/\nAllow: /\n"

DAAD_STYLE = (
    "User-agent: *\n"
    "Crawl-delay: 2\n"
    "Disallow: /deutschland/foerderung/stipendiendatenbank/\n"
    "Allow: /\n"
)


@pytest.fixture(autouse=True)
def _clean_cache():
    clear_robots_cache()
    yield
    clear_robots_cache()


def _robots(text: str, status: int = 200):
    """A stand-in for the robots.txt HTTP response."""
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    return resp


@pytest.mark.asyncio
async def test_allows_a_path_the_site_permits():
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(return_value=_robots(ALLOW_ALL))):
        verdict = await is_fetch_allowed("https://www.tum.de/en/studies/application")
    assert verdict.allowed is True


@pytest.mark.asyncio
async def test_blocks_a_user_agent_the_site_names():
    """A site that names our crawler and disallows it is refused, even though `*` is allowed.

    The `User-agent: *` group at the bottom permits everything. A parser that matched the
    wildcard first would read this as permission -- which is how a site that explicitly
    excluded us would get crawled anyway.
    """
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(return_value=_robots(QEBULAI_STYLE))):
        verdict = await is_fetch_allowed(
            "https://qebulai.az/some/page", user_agent="ClaudeBot"
        )
    assert verdict.allowed is False
    assert "ClaudeBot" in verdict.reason or "robots.txt" in verdict.reason


@pytest.mark.asyncio
async def test_blocks_a_disallowed_directory_but_allows_its_siblings():
    fetch = AsyncMock(return_value=_robots(HOCHSCHULSTART_STYLE))
    with patch("app.data_pipeline.robots._get_robots_response", new=fetch):
        blocked = await is_fetch_allowed(
            "https://hochschulstart.de/fileadmin/media/statistik.pdf"
        )
        allowed = await is_fetch_allowed("https://hochschulstart.de/bewerben")
    assert blocked.allowed is False
    assert allowed.allowed is True


@pytest.mark.asyncio
async def test_a_missing_robots_file_permits_the_fetch():
    """404 is a definite answer: the site publishes no rules, so nothing is disallowed."""
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(return_value=_robots("", status=404))):
        verdict = await is_fetch_allowed("https://example.edu/programmes")
    assert verdict.allowed is True


@pytest.mark.asyncio
async def test_an_unreachable_robots_file_blocks_the_fetch():
    """THE test. A robots.txt we could not read is not permission to crawl.

    The tempting behaviour here is to allow the fetch so a flaky network does not stop a
    collection run. That is precisely the silent fallback ADR-0004 forbids, one layer below
    where we usually apply it: it converts "we do not know whether this site permits us"
    into "this site permits us", and the failure is invisible.
    """
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(side_effect=OSError("connection reset"))):
        verdict = await is_fetch_allowed("https://example.edu/programmes")
    assert verdict.allowed is False
    assert "could not" in verdict.reason.lower() or "unavailable" in verdict.reason.lower()


@pytest.mark.asyncio
async def test_a_server_error_on_robots_blocks_the_fetch():
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(return_value=_robots("", status=503))):
        verdict = await is_fetch_allowed("https://example.edu/programmes")
    assert verdict.allowed is False


@pytest.mark.asyncio
async def test_robots_is_fetched_once_per_host():
    fetch = AsyncMock(return_value=_robots(ALLOW_ALL))
    with patch("app.data_pipeline.robots._get_robots_response", new=fetch):
        await is_fetch_allowed("https://www.tum.de/a")
        await is_fetch_allowed("https://www.tum.de/b")
        await is_fetch_allowed("https://www.rwth-aachen.de/c")
    assert fetch.await_count == 2


@pytest.mark.asyncio
async def test_crawl_delay_is_reported_when_the_site_sets_one():
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(return_value=_robots(DAAD_STYLE))):
        verdict = await is_fetch_allowed("https://www.daad.de/en/")
    assert verdict.allowed is True
    assert verdict.crawl_delay == 2.0


@pytest.mark.asyncio
async def test_daad_scholarship_database_is_disallowed():
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(return_value=_robots(DAAD_STYLE))):
        verdict = await is_fetch_allowed(
            "https://www.daad.de/deutschland/foerderung/stipendiendatenbank/00462.en.html"
        )
    assert verdict.allowed is False


# -------------------------------------------------------------
# The guard as wired into the fetcher
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_fetch_page_content_refuses_a_disallowed_url_without_requesting_it():
    """The page must not be requested at all -- not requested and then discarded."""
    page_get = AsyncMock()
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(return_value=_robots(QEBULAI_STYLE))), \
         patch("httpx.AsyncClient.get", new=page_get):
        with pytest.raises(DisallowedByRobotsError):
            await fetch_page_content("https://qebulai.az/page", user_agent="ClaudeBot")

    page_get.assert_not_awaited()


@pytest.mark.asyncio
async def test_fetch_page_content_proceeds_when_allowed():
    page = MagicMock()
    page.text = "<html><body><h1>Admission</h1><p>IELTS 6.5 required.</p></body></html>"
    page.raise_for_status = MagicMock()

    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(return_value=_robots(ALLOW_ALL))), \
         patch("httpx.AsyncClient.get", new=AsyncMock(return_value=page)):
        text = await fetch_page_content("https://www.tum.de/en/studies/application")

    assert "IELTS 6.5 required." in text


@pytest.mark.asyncio
async def test_fetch_page_content_refuses_when_robots_is_unreachable():
    page_get = AsyncMock()
    with patch("app.data_pipeline.robots._get_robots_response",
               new=AsyncMock(side_effect=OSError("dns failure"))), \
         patch("httpx.AsyncClient.get", new=page_get):
        with pytest.raises(DisallowedByRobotsError):
            await fetch_page_content("https://unreachable.example/programmes")

    page_get.assert_not_awaited()


@pytest.mark.asyncio
async def test_robots_unavailable_error_is_a_disallowed_by_robots_error():
    """Callers catch one exception type. The distinction is for the message, not the flow."""
    assert issubclass(RobotsUnavailableError, DisallowedByRobotsError)
