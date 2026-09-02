import re
from bs4 import BeautifulSoup
import httpx

from app.data_pipeline.robots import (
    DEFAULT_USER_AGENT,
    DisallowedByRobotsError,
    is_fetch_allowed,
    wait_for_crawl_delay,
)


async def fetch_page_content(url: str, user_agent: str = DEFAULT_USER_AGENT) -> str:
    """
    Fetch webpage HTML asynchronously via httpx and extract clean text using BeautifulSoup.

    The site's robots.txt is consulted first, and a refusal raises before the page is
    requested at all -- a URL we may not read is never retrieved, not retrieved and then
    discarded. A robots.txt that cannot be read is itself a refusal: see
    app/data_pipeline/robots.py for why an unknown must not read as permission here.

    Args:
        url: Target URL string to fetch.
        user_agent: The crawler identity to present and to match robots.txt groups against.

    Returns:
        Cleaned plain text of the webpage content.

    Raises:
        DisallowedByRobotsError: the site disallows this path, or its robots.txt could not
            be read. Either way nothing was fetched.
    """
    verdict = await is_fetch_allowed(url, user_agent=user_agent)
    if not verdict.allowed:
        raise DisallowedByRobotsError(f"Not fetching {url}: {verdict.reason}")

    await wait_for_crawl_delay(url, verdict.crawl_delay)

    headers = {
        # Identify honestly. A crawler pretending to be a browser cannot be excluded by a
        # site that wants to exclude it, which would make the check above decorative.
        "User-Agent": f"{user_agent}/1.0 (+https://github.com/Ali0lo/AUSA)"
    }

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        html_content = response.text

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove non-content elements (script, style, nav, footer, header)
    for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        element.extract()

    # Extract text content
    raw_text = soup.get_text(separator=" ")

    # Collapse multiple whitespace/newlines into clean single spaces
    cleaned_text = re.sub(r"\s+", " ", raw_text).strip()

    return cleaned_text
