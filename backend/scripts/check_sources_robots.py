"""Ask every source in the curation registry whether we are allowed to fetch it.

Run this before any collection run, and whenever a URL is added to
`data/curation/sources.csv`. It answers the question the project used to answer from
memory: may we read this page?

    cd backend
    python -m scripts.check_sources_robots

Nothing here fetches an admissions page. It reads each origin's robots.txt through the
same code path `fetch_page_content` uses, so a source that prints DISALLOWED here is one
the collector would refuse at runtime -- and a source that prints UNAVAILABLE is one whose
permission we could not establish, which this project treats as a refusal.
"""
import asyncio
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data_pipeline.robots import is_fetch_allowed  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCES = REPO_ROOT / "data" / "curation" / "sources.csv"

GREEN, AMBER, RED, DIM, BOLD, OFF = (
    "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[1m", "\033[0m",
)


async def main() -> int:
    if not SOURCES.exists():
        print(f"No source registry at {SOURCES}", file=sys.stderr)
        return 1

    with io.open(SOURCES, encoding="utf-8-sig", newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r.get("url", "").strip()]

    seen: set[str] = set()
    allowed = refused = 0

    print(f"\n{BOLD}robots.txt verdicts for the curation source registry{OFF}")
    print(f"{DIM}{len(rows)} URLs; one robots.txt per origin, cached{OFF}\n")

    for row in rows:
        url = row["url"].strip()
        if url in seen:
            continue
        seen.add(url)

        try:
            verdict = await is_fetch_allowed(url)
        except Exception as exc:  # a malformed URL in the registry
            print(f"  {RED}ERROR     {OFF}{url[:78]}\n            {DIM}{exc}{OFF}")
            refused += 1
            continue

        if verdict.allowed:
            allowed += 1
            delay = f" · crawl-delay {verdict.crawl_delay}s" if verdict.crawl_delay else ""
            print(f"  {GREEN}ALLOWED   {OFF}{row['university_name'][:34]:<34} {DIM}{delay}{OFF}")
        else:
            refused += 1
            print(f"  {RED}REFUSED   {OFF}{row['university_name'][:34]:<34}")
            print(f"            {DIM}{verdict.reason[:96]}{OFF}")

    print(f"\n  {GREEN}{allowed} allowed{OFF} · {RED}{refused} refused{OFF} "
          f"{DIM}(of {len(seen)} distinct URLs){OFF}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
