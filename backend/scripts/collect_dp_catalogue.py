"""Download the Dövlət Proqramı catalogue CSVs from the national open-data portal.

Publisher: Elm və Təhsil Nazirliyi (Ministry of Science and Education), via IDDA's CKAN
portal at opendata.az. Updated once a year, so this is not a job that needs scheduling --
run it when the ministry publishes the next academic year's list.

Downloads only. Parsing and loading are load_dp_catalogue.py's job.
"""

import argparse
import urllib.request
from pathlib import Path

DEFAULT_DESTINATION = Path(__file__).resolve().parents[2] / "data" / "raw" / "azerbaijan"

RESOURCES = {
    "dp-bakalavr-2026.csv": (
        "https://admin.opendata.az/dataset/6d33d639-af0a-46a8-89f5-c20c606cc0f3"
        "/resource/f28081ed-31d0-4ca6-aeb5-4d5a419e986c/download/dp-bakalavr-2026.csv"
    ),
    "dp-master-2026.csv": (
        "https://admin.opendata.az/dataset/0f00bf5a-c10d-4109-80b5-9beecc783027"
        "/resource/7907fba0-acb0-4017-95a7-2411774243a0/download/dp-master-2026.csv"
    ),
}


def download(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for filename, url in RESOURCES.items():
        target = destination / filename
        request = urllib.request.Request(url, headers={"User-Agent": "AUSA/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response:
            target.write_bytes(response.read())
        print(f"{filename}: {target.stat().st_size:,} bytes -> {target}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    download(parser.parse_args().destination)
