"""Load collected cutoff-history CSVs into program_cutoff_history.

Idempotent: a row is identified by (country, source_program_code, variant_index,
intake_year), so re-running after a fresh collection inserts only what is new.

Nothing here fills a gap. A CSV missing a required column raises rather than
loading a partial table, and verified_by is never written -- only a person who
has opened the source may set it (ADR-0004 rule 2).
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.cutoff_history import ProgramCutoffHistory  # noqa: E402

REQUIRED_COLUMNS = {
    "country",
    "source_program_code",
    "intake_year",
    "cutoff_value",
    "cutoff_unit",
    "university_name",
}

OPTIONAL_COLUMNS = {
    "variant_index",
    "variant_discriminator_known",
    "lower_is_better",
    "department_name",
    "score_type",
    "scholarship_type",
    "is_undergraduate",
    "source_url",
}


def _clean(value: Any) -> Any:
    """NaN and empty string both mean 'the source did not say', which is None.

    pandas hands back numpy scalars (numpy.bool_, numpy.int64, numpy.float64, ...),
    not Python natives. Those pass SQLAlchemy's isinstance checks silently on SQLite
    but are inconsistently supported by asyncpg (the production driver), so they are
    coerced to native Python types here, at the parsing boundary, before anything
    downstream ever sees them.
    """
    if isinstance(value, np.generic):
        value = value.item()
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _parse_lower_is_better(value: Any) -> bool:
    """Parse the lower_is_better flag explicitly. Never use bool(value) here.

    pandas types this column as `object` rather than `bool` the moment a single row is
    blank or quoted, so the value a loader can see for a "false" row is the *string*
    "False" -- and `bool("False")` is True in Python, because every non-empty string is
    truthy. That silently flips a "score, higher is better" row into "rank, lower is
    better" and corrupts every downstream comparison that trusts this flag. Instead we
    enumerate every representation the collectors are known to emit and raise on
    anything else, rather than guessing what an unrecognised value means.
    """
    if isinstance(value, np.generic):
        value = value.item()
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        raise ValueError(f"lower_is_better: cannot interpret numeric value {value!r} as a boolean")
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "":
            return False
        if normalized in ("true", "1"):
            return True
        if normalized in ("false", "0"):
            return False
    raise ValueError(f"lower_is_better: cannot interpret value {value!r} as a boolean")


def rows_from_csv(path: Path) -> list[dict]:
    """Parse one collected CSV into ORM kwargs. Raises if the schema does not match."""
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: {sorted(missing)}. "
            "Re-run the collector rather than loading a partial table."
        )

    rows: list[dict] = []
    for record in frame.to_dict(orient="records"):
        row = {key: _clean(record.get(key)) for key in REQUIRED_COLUMNS | OPTIONAL_COLUMNS}
        row["intake_year"] = int(row["intake_year"])
        row["cutoff_value"] = float(row["cutoff_value"])
        if row["variant_index"] is not None:
            row["variant_index"] = int(row["variant_index"])
        row["lower_is_better"] = _parse_lower_is_better(row["lower_is_better"])
        rows.append(row)
    return rows


async def load_csv(session: AsyncSession, path: Path) -> int:
    """Insert rows not already present. Returns the number inserted."""
    rows = rows_from_csv(path)

    existing = set(
        (
            await session.execute(
                select(
                    ProgramCutoffHistory.country,
                    ProgramCutoffHistory.source_program_code,
                    ProgramCutoffHistory.variant_index,
                    ProgramCutoffHistory.intake_year,
                )
            )
        ).all()
    )

    inserted = 0
    for row in rows:
        key = (row["country"], row["source_program_code"], row["variant_index"], row["intake_year"])
        if key in existing:
            continue
        session.add(ProgramCutoffHistory(**row))
        existing.add(key)
        inserted += 1

    await session.commit()
    return inserted


async def _main(paths: list[Path]) -> None:
    async with AsyncSessionLocal() as session:
        for path in paths:
            count = await load_csv(session, path)
            print(f"{path.name}: {count} new rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="+", type=Path, help="collected CSVs from data/processed/")
    args = parser.parse_args()
    asyncio.run(_main(args.csv))
