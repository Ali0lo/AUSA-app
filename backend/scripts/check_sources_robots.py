"""Ask every source in the curation registry whether we are allowed to fetch it, and
optionally whether the URL is even real.

Run this before any collection run, and whenever a URL is added to
`data/curation/sources.csv`. It answers the two questions the project used to answer from
memory: may we read this page, and does this page exist?

    cd backend
    python -m scripts.check_sources_robots
    python -m scripts.check_sources_robots --check-urls
    python -m scripts.check_sources_robots --file ../data/curation/incoming.csv --check-urls

By default nothing here fetches an admissions page. It reads each origin's robots.txt
through the same code path `fetch_page_content` uses, so a source that prints REFUSED here
is one the collector would refuse at runtime -- including one whose permission could not be
established, which this project treats as a refusal.

`--check-urls` additionally requests each page and reports its status. That exists because
the failure this project keeps hitting is not a wrong figure but a URL that was never real:
two invented URLs have already been discarded here, and both looked entirely plausible. A
URL arriving from a research agent or a search summary is a claim, not an address, and
checking fifty of them by hand is exactly the step where a fabricated one survives.

**The liveness check runs BEHIND the robots gate, never beside it.** A verifier that
fetched pages to see whether they exist, while skipping the permission it exists to
enforce, would be the one crawler in this codebase exempt from its own policy. So a REFUSED
source is never fetched here, and its URL is reported as UNCHECKED rather than as missing --
"we are not allowed to look" and "it is not there" are different facts, and this file must
not merge them any more than the rest of the project may (ADR-0004).

`--file` points at any CSV carrying a `url` column, so a batch of candidate URLs can be
verified BEFORE it is promoted into the registry, rather than being written in and cleaned
up afterwards.
"""
import argparse
import asyncio
import csv
import io
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data_pipeline.robots import (  # noqa: E402
    DEFAULT_USER_AGENT,
    is_fetch_allowed,
    wait_for_crawl_delay,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES = REPO_ROOT / "data" / "curation" / "sources.csv"

PAGE_TIMEOUT_SECONDS = 20.0

GREEN, AMBER, RED, DIM, BOLD, OFF = (
    "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[1m", "\033[0m",
)


async def _check_url(url: str, crawl_delay: float | None) -> tuple[str, str]:
    """Request one page. Returns (verdict, detail).

    A redirect is followed and reported rather than treated as a pass: a URL that lands
    somewhere else is often a guessed path being swallowed by a catch-all, which looks
    exactly like success in a status code alone.
    """
    await wait_for_crawl_delay(url, crawl_delay)
    headers = {"User-Agent": f"{DEFAULT_USER_AGENT}/1.0 (+https://github.com/Ali0lo/AUSA)"}
    try:
        async with httpx.AsyncClient(
            timeout=PAGE_TIMEOUT_SECONDS, follow_redirects=True, headers=headers
        ) as client:
            response = await client.get(url)
    except Exception as exc:  # DNS failure, TLS error, timeout
        return "DEAD", f"{type(exc).__name__}: {exc}"

    final = str(response.url)
    if response.status_code == 404:
        return "DEAD", "HTTP 404 -- this URL does not exist"
    if response.status_code >= 400:
        return "ERROR", f"HTTP {response.status_code}"
    if final.rstrip("/") != url.rstrip("/"):
        return "MOVED", f"HTTP {response.status_code} -> {final}"
    return "LIVE", f"HTTP {response.status_code}"


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, default=SOURCES,
        help="CSV carrying a `url` column (default: data/curation/sources.csv)",
    )
    parser.add_argument(
        "--check-urls", action="store_true",
        help="also request each allowed page and report whether it exists",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"No source registry at {args.file}", file=sys.stderr)
        return 1

    with io.open(args.file, encoding="utf-8-sig", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r.get("url", "").strip()]

    seen: set[str] = set()
    allowed = refused = 0
    live = moved = dead = unchecked = 0

    print(f"\n{BOLD}robots.txt verdicts for {args.file.name}{OFF}")
    mode = "permission and liveness" if args.check_urls else "permission only"
    print(f"{DIM}{len(rows)} URLs; one robots.txt per origin, cached; {mode}{OFF}\n")

    for row in rows:
        url = row["url"].strip()
        if url in seen:
            continue
        seen.add(url)
        name = row.get("university_name", url)[:34]

        try:
            verdict = await is_fetch_allowed(url)
        except Exception as exc:  # a malformed URL in the registry
            print(f"  {RED}ERROR     {OFF}{url[:78]}\n            {DIM}{exc}{OFF}")
            refused += 1
            continue

        if not verdict.allowed:
            refused += 1
            unchecked += 1
            print(f"  {RED}REFUSED   {OFF}{name:<34}")
            print(f"            {DIM}{verdict.reason[:96]}{OFF}")
            # Deliberately NOT fetched, even with --check-urls. See the module docstring:
            # the verifier does not get an exemption from the policy it enforces.
            if args.check_urls:
                print(f"            {DIM}URL not checked -- we may not fetch it{OFF}")
            continue

        allowed += 1
        delay = f" · crawl-delay {verdict.crawl_delay}s" if verdict.crawl_delay else ""

        if not args.check_urls:
            print(f"  {GREEN}ALLOWED   {OFF}{name:<34} {DIM}{delay}{OFF}")
            continue

        status, detail = await _check_url(url, verdict.crawl_delay)
        colour = {"LIVE": GREEN, "MOVED": AMBER, "DEAD": RED, "ERROR": RED}[status]
        counter = {"LIVE": "live", "MOVED": "moved", "DEAD": "dead", "ERROR": "dead"}[status]
        live += counter == "live"
        moved += counter == "moved"
        dead += counter == "dead"
        print(f"  {colour}{status:<10}{OFF}{name:<34} {DIM}{delay}{OFF}")
        print(f"            {DIM}{detail[:96]}{OFF}")

    print(f"\n  {GREEN}{allowed} allowed{OFF} · {RED}{refused} refused{OFF} "
          f"{DIM}(of {len(seen)} distinct URLs){OFF}")
    if args.check_urls:
        print(f"  {GREEN}{live} live{OFF} · {AMBER}{moved} redirected{OFF} · "
              f"{RED}{dead} dead{OFF} · {DIM}{unchecked} unchecked (refused){OFF}")
        if dead:
            print(f"\n  {RED}{dead} URL(s) do not resolve. Do not record a requirement "
                  f"against them.{OFF}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
