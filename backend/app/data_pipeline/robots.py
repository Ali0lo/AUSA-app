"""Ask the site for permission before fetching a page.

This project's crawling policy used to live entirely in prose and in the discipline of
whoever called `fetch_page_content`: qebulai.az excluded, hochschulstart's `/fileadmin/`
off limits, DAAD owed a two-second delay. The fetcher itself would retrieve any URL it was
handed. This module makes the policy a property of the code instead.

**An undeterminable robots.txt blocks the fetch.** That is ADR-0004 one layer down: an
unknown must never read as permission. If a network error or a 5xx meant "go ahead", then
a flaky DNS lookup would silently convert "we do not know whether this site permits us"
into "this site permits us" -- with no error and no record. A collection run that stops is
a problem someone fixes; a collection run that crawls a site which excluded us is not
recoverable after the fact.

A 404 is different, and is treated as permission: the site answered, and its answer is
that it publishes no rules.
"""
import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

# Identifies us honestly. A crawler that disguises itself as a browser cannot be excluded by
# a site that wants to exclude it, which makes its robots.txt compliance meaningless.
DEFAULT_USER_AGENT = "AUSABot"

# Applied when a site sets no Crawl-delay of its own. Politeness default, not a rule.
DEFAULT_CRAWL_DELAY_SECONDS = 1.0

ROBOTS_TIMEOUT_SECONDS = 10.0


class DisallowedByRobotsError(RuntimeError):
    """The fetch was refused. Raised before the target page is ever requested."""


class RobotsUnavailableError(DisallowedByRobotsError):
    """robots.txt could not be read, so permission could not be established.

    A subclass rather than a sibling: callers handle both the same way -- do not fetch --
    and the distinction exists only so the message can say which happened.
    """


@dataclass(frozen=True)
class RobotsVerdict:
    allowed: bool
    reason: str
    crawl_delay: Optional[float] = None


# One parsed robots.txt per origin, plus the time we last fetched from that origin.
_ROBOTS_CACHE: Dict[Tuple[str, str], RobotsVerdict | RobotFileParser | None] = {}
_LAST_FETCH_AT: Dict[Tuple[str, str], float] = {}
_CACHE_LOCK = asyncio.Lock()


def clear_robots_cache() -> None:
    """Drop every cached robots.txt. Used by tests and by long-running collectors."""
    _ROBOTS_CACHE.clear()
    _LAST_FETCH_AT.clear()


def _origin(url: str) -> Tuple[str, str]:
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        raise ValueError(f"Not an absolute URL: {url!r}")
    return parts.scheme, parts.netloc


async def _get_robots_response(robots_url: str) -> httpx.Response:
    """Fetch robots.txt. Separated so tests can substitute a response without a network."""
    async with httpx.AsyncClient(
        timeout=ROBOTS_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": DEFAULT_USER_AGENT},
    ) as client:
        return await client.get(robots_url)


async def is_fetch_allowed(
    url: str, user_agent: str = DEFAULT_USER_AGENT
) -> RobotsVerdict:
    """Decide whether `url` may be fetched, consulting (and caching) its robots.txt."""
    scheme, netloc = _origin(url)
    key = (scheme, netloc)

    async with _CACHE_LOCK:
        cached = _ROBOTS_CACHE.get(key, "__miss__")
        if cached == "__miss__":
            cached = await _load_robots(scheme, netloc)
            _ROBOTS_CACHE[key] = cached

    # A verdict cached in place of a parser is a hard failure for the whole origin:
    # robots.txt was unreachable, so nothing on this host may be fetched.
    if isinstance(cached, RobotsVerdict):
        return cached

    # None means the site answered 404: no rules published, so nothing is disallowed.
    if cached is None:
        return RobotsVerdict(True, "No robots.txt published (404); nothing is disallowed.")

    if not cached.can_fetch(user_agent, url):
        return RobotsVerdict(
            False,
            f"robots.txt at {scheme}://{netloc} disallows {user_agent} for this path.",
        )

    delay = cached.crawl_delay(user_agent)
    return RobotsVerdict(
        True,
        f"Permitted by robots.txt at {scheme}://{netloc}.",
        crawl_delay=float(delay) if delay is not None else None,
    )


async def _load_robots(scheme: str, netloc: str):
    """Return a parser, None for 'no robots.txt', or a failing RobotsVerdict."""
    robots_url = f"{scheme}://{netloc}/robots.txt"
    try:
        response = await _get_robots_response(robots_url)
    except Exception as exc:
        return RobotsVerdict(
            False,
            f"robots.txt at {robots_url} could not be read ({exc}), so permission to "
            f"crawl {netloc} is unknown. An unknown is not permission.",
        )

    status = response.status_code
    if status in (404, 410):
        return None
    if status >= 400:
        return RobotsVerdict(
            False,
            f"robots.txt at {robots_url} returned HTTP {status}, so permission to crawl "
            f"{netloc} is unavailable. An unknown is not permission.",
        )

    parser = RobotFileParser()
    parser.parse(response.text.splitlines())
    return parser


async def wait_for_crawl_delay(url: str, crawl_delay: Optional[float]) -> None:
    """Sleep so consecutive fetches to one host respect its Crawl-delay."""
    key = _origin(url)
    delay = crawl_delay if crawl_delay is not None else DEFAULT_CRAWL_DELAY_SECONDS
    last = _LAST_FETCH_AT.get(key)
    if last is not None:
        remaining = delay - (time.monotonic() - last)
        if remaining > 0:
            await asyncio.sleep(remaining)
    _LAST_FETCH_AT[key] = time.monotonic()
