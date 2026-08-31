"""Load the Dövlət Proqramı catalogue CSVs into dp_catalogue.

Idempotent: a row is identified by (level, country_source, university_name, program_name,
intake_year). The real files have zero duplicates on that key, verified 31 Aug 2026.

Nothing here fills a gap. A missing column or an unmappable level raises rather than
loading a partial table, and verified_by is never written -- only a person who has opened
the source may set it (ADR-0004 rule 2).
"""

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.models.dp_catalogue import DPCatalogueEntry  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402

COLUMN_LEVEL = "Təhsil səviyyəsi"
COLUMN_COUNTRY = "Ölkə"
COLUMN_UNIVERSITY = "Universitet"
COLUMN_PROGRAM = "Təhsil proqramı"
REQUIRED_COLUMNS = {COLUMN_LEVEL, COLUMN_COUNTRY, COLUMN_UNIVERSITY, COLUMN_PROGRAM}

# The source's own words for the two levels in scope. Doktorantura also appears in the
# ministry's programme but PhD is out of scope (spec §7), so it raises rather than loading.
LEVEL_BY_SOURCE_VALUE = {
    "bakalavriat": "bachelor",
    "magistratura": "master",
}

# The ministry writes country names in Azerbaijani long form. These six strings were read
# off the real files on 31 Aug 2026 -- note Poland is "Polşa", not "Polşa Respublikası".
# The other 27 countries map to None: they are out of scope and guessing their spelling
# would put a code on a row nobody checked.
COUNTRY_CODE_BY_SOURCE_NAME = {
    "Türkiyə Respublikası": "TR",
    "Almaniya Federativ Respublikası": "DE",
    "Birləşmiş Krallıq": "GB",
    "Amerika Birləşmiş Ştatları": "US",
    "Polşa": "PL",
    "Çin Xalq Respublikası": "CN",
}


def _clean_name(value: Any) -> str:
    """Strip the literal double quotes the source wraps every name in.

    In dp-bakalavr-2026.csv and dp-master-2026.csv the Universitet field contains
    `"Technical University of Munich"` -- quote characters inside the value, present on
    4121 of 4121 university rows. Left in place they become part of the stored name and
    nothing joins to it.
    """
    return str(value).strip().strip('"').strip()


def rows_from_csv(path: Path, source_url: str) -> list[dict]:
    """Parse one DP CSV into ORM kwargs. Raises if the file is not what we expect."""
    # utf-8-sig, not utf-8: both files carry a BOM, which otherwise ends up glued to the
    # first column name and makes every column lookup miss.
    frame = pd.read_csv(path, encoding="utf-8-sig")

    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: {sorted(missing)}. "
            "Re-download from the portal rather than loading a partial table."
        )

    # The year is in the filename, which is how the ministry versions these files
    # (dp-bakalavr-2026.csv). A file without one is a file we cannot date, and dating a
    # catalogue wrongly silently mixes two academic years in one table.
    digits = "".join(c for c in path.stem if c.isdigit())
    if len(digits) < 4:
        raise ValueError(
            f"{path.name} has no four-digit intake year in its filename. Keep the "
            "ministry's own name, e.g. dp-bakalavr-2026.csv."
        )
    intake_year = int(digits[-4:])
    retrieved_at = datetime.now(timezone.utc)

    rows: list[dict] = []
    for record in frame.to_dict(orient="records"):
        source_level = str(record[COLUMN_LEVEL]).strip()
        if source_level not in LEVEL_BY_SOURCE_VALUE:
            raise ValueError(
                f"{path.name} contains education level {source_level!r}, which this loader "
                f"does not map. Known: {sorted(LEVEL_BY_SOURCE_VALUE)}. PhD is out of scope."
            )
        country_source = str(record[COLUMN_COUNTRY]).strip()
        rows.append({
            "level": LEVEL_BY_SOURCE_VALUE[source_level],
            "country_source": country_source,
            "country_code": COUNTRY_CODE_BY_SOURCE_NAME.get(country_source),
            "university_name": _clean_name(record[COLUMN_UNIVERSITY]),
            "program_name": _clean_name(record[COLUMN_PROGRAM]),
            "intake_year": intake_year,
            "source_url": source_url,
            "retrieved_at": retrieved_at,
        })
    return rows


def _natural_key(level, country_source, university_name, program_name, intake_year):
    """The one place allowed to build the identity key, for CSV rows and database rows alike.

    Both sides route through here so a type difference between a parsed value and a value
    read back from the database cannot silently defeat the "is this row already there"
    check and duplicate the whole file on a re-run.
    """
    return (
        str(level), str(country_source), str(university_name),
        str(program_name), int(intake_year),
    )


async def load_csv(session: AsyncSession, path: Path, source_url: str) -> int:
    """Insert rows not already present. Returns the number inserted."""
    rows = rows_from_csv(path, source_url)

    existing = {
        _natural_key(*db_row)
        for db_row in (
            await session.execute(
                select(
                    DPCatalogueEntry.level,
                    DPCatalogueEntry.country_source,
                    DPCatalogueEntry.university_name,
                    DPCatalogueEntry.program_name,
                    DPCatalogueEntry.intake_year,
                )
            )
        ).all()
    }

    inserted = 0
    for row in rows:
        key = _natural_key(
            row["level"], row["country_source"], row["university_name"],
            row["program_name"], row["intake_year"],
        )
        if key in existing:
            continue
        session.add(DPCatalogueEntry(**row))
        existing.add(key)
        inserted += 1

    await session.commit()
    return inserted


async def _main(pairs: list[tuple[Path, str]]) -> None:
    async with AsyncSessionLocal() as session:
        for path, source_url in pairs:
            print(f"{path.name}: {await load_csv(session, path, source_url)} new rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="a DP CSV from data/raw/azerbaijan/")
    parser.add_argument("--source-url", required=True, help="the portal URL it came from")
    args = parser.parse_args()
    asyncio.run(_main([(args.csv, args.source_url)]))
