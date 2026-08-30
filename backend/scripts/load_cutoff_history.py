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


def _parse_bool_or_none(value: Any) -> bool | None:
    """Parse a nullable boolean flag explicitly. Never use bool(value) here.

    This backs all three Boolean columns in the model (`lower_is_better`,
    `variant_discriminator_known`, `is_undergraduate`). pandas types a column as
    `object` rather than `bool` the moment a single row is blank or quoted, so the
    value a loader can see for a "false" row can be the *string* "False" -- and
    `bool("False")` is True in Python, because every non-empty string is truthy. For
    a flag like `lower_is_better` that silently flips "score, higher is better" into
    "rank, lower is better" and corrupts every downstream comparison that trusts it.
    So we enumerate every representation the collectors are known to emit and raise
    on anything else, rather than guessing what an unrecognised value means.

    Blank/NaN/None means "the source did not say" and is returned as None here --
    NOT False. None is not a valid boolean, so whether "did not say" should collapse
    to False (as `lower_is_better`, a NOT NULL column with a False default, requires)
    or stay None (as the two nullable columns require) is a decision for the caller
    to make explicitly at the call site, not something this parser decides for every
    caller alike.
    """
    if isinstance(value, np.generic):
        value = value.item()
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        raise ValueError(f"cannot interpret numeric value {value!r} as a boolean")
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "":
            return None
        if normalized in ("true", "1"):
            return True
        if normalized in ("false", "0"):
            return False
    raise ValueError(f"cannot interpret value {value!r} as a boolean")


def _natural_key(
    country: Any, source_program_code: Any, variant_index: Any, intake_year: Any
) -> tuple[str | None, str | None, int | None, int | None]:
    """Build the (country, source_program_code, variant_index, intake_year) natural key.

    This is the ONLY place allowed to construct this key -- for rows freshly parsed
    from a CSV, and for rows read back from the database, alike. The bug this exists
    to prevent: Turkey's real CSV has purely numeric source_program_code values (e.g.
    100110027), so pandas infers int64 for that column and hands back a Python int,
    while the model column is String(300), so a value read back from the database is
    a str. When the CSV-side key and the DB-side key were built separately, one used
    the int and the other used the str, `100110027 != "100110027"`, every "is this
    row already there" check missed, and a re-run silently duplicated the entire
    115,482-row file. Routing both sides through this one function -- which
    normalises each component to the type its own column actually declares -- makes
    that drift structurally impossible rather than merely patched for today's data.
    """
    return (
        None if country is None else str(country),
        None if source_program_code is None else str(source_program_code),
        None if variant_index is None else int(variant_index),
        None if intake_year is None else int(intake_year),
    )


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

        # source_program_code is String(300) in the model. A purely numeric code
        # (as Turkey's CSV has) makes pandas infer int64 for this column, so cast
        # explicitly here rather than relying on SQLite's TEXT affinity to coerce it
        # on write -- Postgres (asyncpg, production) will not do that for you.
        if row["source_program_code"] is not None:
            row["source_program_code"] = str(row["source_program_code"])

        # lower_is_better is NOT NULL with a False default in the model, so "the
        # source did not say" collapses to False here -- explicitly, at this call
        # site, not inside the parser.
        row["lower_is_better"] = _parse_bool_or_none(row["lower_is_better"])
        if row["lower_is_better"] is None:
            row["lower_is_better"] = False

        # variant_discriminator_known and is_undergraduate are nullable in the model:
        # "the source did not say" must stay None, not collapse to False.
        row["variant_discriminator_known"] = _parse_bool_or_none(row["variant_discriminator_known"])
        row["is_undergraduate"] = _parse_bool_or_none(row["is_undergraduate"])

        rows.append(row)
    return rows


async def load_csv(session: AsyncSession, path: Path) -> int:
    """Insert rows not already present. Returns the number inserted."""
    rows = rows_from_csv(path)

    existing = {
        _natural_key(*db_row)
        for db_row in (
            await session.execute(
                select(
                    ProgramCutoffHistory.country,
                    ProgramCutoffHistory.source_program_code,
                    ProgramCutoffHistory.variant_index,
                    ProgramCutoffHistory.intake_year,
                )
            )
        ).all()
    }

    inserted = 0
    for row in rows:
        key = _natural_key(row["country"], row["source_program_code"], row["variant_index"], row["intake_year"])
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
