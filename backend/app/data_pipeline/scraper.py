import re
from bs4 import BeautifulSoup
import httpx


async def fetch_page_content(url: str) -> str:
    """
    Fetch webpage HTML asynchronously via httpx and extract clean text using BeautifulSoup.
    
    Args:
        url: Target URL string to fetch.
        
    Returns:
        Cleaned plain text of the webpage content.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (AUSA Bot/1.0; +https://ausa.edu.az)"
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
