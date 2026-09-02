"""Load hand-curated programme requirements into `program_requirements`.

This is the writer that table never had. It existed with a migration and tests from Task 7
onwards while nothing in the application wrote a row into it, which is why five of the six
target countries answer "requirements unknown".

The rows come from `data/curation/*.csv`, filled in by a person reading an official
admissions page. They are small, not reproducible by any script, and committed to git.

Everything below turns on one distinction: **a blank cell is unknown, not a default.**
A requirements file is mostly blanks, because nobody has read every field off every page.
The dangerous parse is not the one that raises -- `int("")` raises loudly -- but the one
that quietly succeeds: `bool("")` is False, and False in `foundation_required` is a
positive claim that no foundation year is needed. That claim turns a route that should
read BLOCKED into one that tells a student to apply somewhere that will reject them.

    cd backend
    python -m scripts.load_program_requirements                       # the default file
    python -m scripts.load_program_requirements --file path/to.csv
    python -m scripts.load_program_requirements --dry-run
"""
import argparse
import asyncio
import csv
import io
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models.qualifications import ProgramRequirement  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FILE = REPO_ROOT / "data" / "curation" / "program_requirements_2026.csv"

# ADR-0007 §5. 'human-verified' is deliberately unreachable from a file: see _check_provenance.
VALID_PROVENANCE = {"seed", "claude-extracted", "human-verified"}

TRUE_TOKENS = {"true", "yes", "y", "1"}
FALSE_TOKENS = {"false", "no", "n", "0"}

FLOAT_FIELDS = (
    "language_minimum_score",
    "entrance_exam_minimum",
    "gpa_minimum",
    "tuition_per_year",
    "living_cost_estimate_per_year",
    "application_fee",
)
TEXT_FIELDS = (
    "entry_qualification_accepted",
    "foundation_providers",
    "language_test",
    "language_of_instruction",
    "entrance_exam",
    "gpa_scale",
    "currency",
    "application_portal",
    "documents_required",
)
# The natural key. The same university publishes different requirements per level and year.
KEY_FIELDS = ("university_name", "program_name", "level", "intake_year")


class CuratedRowError(ValueError):
    """A curated row is malformed. The load aborts; nothing is written."""


def _blank(value: Optional[str]) -> bool:
    return value is None or value.strip() == ""


def _text(value: Optional[str]) -> Optional[str]:
    """Empty cell -> None, never the empty string.

    '' in a nullable column is a value: it renders as a present-but-empty requirement and
    is indistinguishable from a real answer of "none". NULL is the only honest blank.
    """
    return None if _blank(value) else value.strip()


def _number(value: Optional[str], field: str) -> Optional[float]:
    """Empty cell -> None. A real 0 survives, because free tuition is a genuine answer."""
    if _blank(value):
        return None
    try:
        return float(value.strip())
    except ValueError as exc:
        raise CuratedRowError(f"{field}: {value!r} is not a number") from exc


def _boolean(value: Optional[str], field: str) -> Optional[bool]:
    """Empty cell -> None. NEVER False.

    This is the single most dangerous coercion in the file. `bool("")` is False, and
    foundation_required=False asserts that a university needs no foundation year. Left to
    the obvious parse, every field nobody checked becomes a claim that direct entry works.
    """
    if _blank(value):
        return None
    token = value.strip().lower()
    if token in TRUE_TOKENS:
        return True
    if token in FALSE_TOKENS:
        return False
    raise CuratedRowError(f"{field}: {value!r} is not a boolean")


def _date(value: Optional[str], field: str) -> Optional[date]:
    """Empty cell -> None. A fuzzy deadline ('usually August') is a blank, not a guess."""
    if _blank(value):
        return None
    try:
        return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise CuratedRowError(
            f"{field}: {value!r} is not an ISO date. If the source states no exact date, "
            f"leave the cell empty rather than approximating one."
        ) from exc


def _timestamp(value: Optional[str], field: str) -> Optional[datetime]:
    if _blank(value):
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise CuratedRowError(f"{field}: {value!r} is not an ISO timestamp") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _check_provenance(raw: Dict[str, str]) -> str:
    provenance = _text(raw.get("provenance")) or "claude-extracted"
    if provenance not in VALID_PROVENANCE:
        raise CuratedRowError(
            f"provenance: {provenance!r} is not one of {sorted(VALID_PROVENANCE)}"
        )
    if provenance == "human-verified":
        # A file cannot perform a verification. The state records that a named person opened
        # the source page, and the only place that fact can be established is the admin
        # review queue, where the verifier is the authenticated account.
        raise CuratedRowError(
            "provenance: 'human-verified' cannot be set from a CSV. A file cannot record "
            "that a person read the source page. Load the row as 'claude-extracted' and "
            "verify it in the admin review queue, which stamps the verifier from their "
            "own account."
        )
    return provenance


def parse_row(raw: Dict[str, str]) -> Dict[str, Any]:
    """Turn one CSV row into column values, or raise CuratedRowError."""
    if not _blank(raw.get("verified_by")):
        raise CuratedRowError(
            "verified_by must be empty in a curated file. It records that a named person "
            "checked the source page; a file claiming it asserts a verification nobody "
            "performed. The admin review queue sets it from the authenticated account."
        )

    for required in ("university_name", "program_name", "level", "country_code"):
        if _blank(raw.get(required)):
            raise CuratedRowError(f"{required} is required and was empty")

    if _blank(raw.get("source_url")):
        raise CuratedRowError(
            "source_url is required: a requirement nobody can trace to a page is not a "
            "requirement anyone can check."
        )

    level = raw["level"].strip().lower()
    if level not in {"bachelor", "master"}:
        raise CuratedRowError(f"level: {level!r} must be 'bachelor' or 'master'")

    intake = _number(raw.get("intake_year"), "intake_year")
    if intake is None:
        raise CuratedRowError("intake_year is required and was empty")

    retrieved = _timestamp(raw.get("retrieved_at"), "retrieved_at")
    if retrieved is None:
        raise CuratedRowError(
            "retrieved_at is required: a requirement with no read date cannot be aged out."
        )

    parsed: Dict[str, Any] = {
        "university_name": raw["university_name"].strip(),
        "program_name": raw["program_name"].strip(),
        "level": level,
        "intake_year": int(intake),
        "country_code": raw["country_code"].strip().upper(),
        "foundation_required": _boolean(raw.get("foundation_required"), "foundation_required"),
        "application_deadline": _date(raw.get("application_deadline"), "application_deadline"),
        "provenance": _check_provenance(raw),
        "source_url": raw["source_url"].strip(),
        "retrieved_at": retrieved,
        "last_checked": _timestamp(raw.get("last_checked"), "last_checked"),
        # Never from the file. Only the admin review queue may set this.
        "verified_by": None,
    }
    for field in TEXT_FIELDS:
        parsed[field] = _text(raw.get(field))
    for field in FLOAT_FIELDS:
        parsed[field] = _number(raw.get(field), field)

    return parsed


async def load_program_requirements(
    session: AsyncSession, path: Path, dry_run: bool = False
) -> Dict[str, int]:
    """Load a curated CSV. Idempotent on the natural key; aborts whole on a bad row."""
    with io.open(path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    # Parse everything before writing anything. A file that fails halfway leaves the table
    # in a state nobody chose, and the curator cannot tell which half landed.
    parsed = []
    for number, raw in enumerate(rows, start=2):  # row 1 is the header
        try:
            parsed.append(parse_row(raw))
        except CuratedRowError as exc:
            raise CuratedRowError(f"{path.name} line {number}: {exc}") from exc

    seen = set()
    for row in parsed:
        key = tuple(row[f] for f in KEY_FIELDS)
        if key in seen:
            raise CuratedRowError(
                f"{path.name}: two rows share the natural key {key}. One of them would "
                f"silently overwrite the other."
            )
        seen.add(key)

    inserted = updated = 0
    for row in parsed:
        existing = (
            await session.execute(
                select(ProgramRequirement).where(
                    *[getattr(ProgramRequirement, f) == row[f] for f in KEY_FIELDS]
                )
            )
        ).scalar_one_or_none()

        if existing is None:
            session.add(ProgramRequirement(**row))
            inserted += 1
        else:
            # Every column is assigned, including the blanks. Skipping blanks would mean a
            # curator could never withdraw a value they found to be wrong -- only replace
            # it with another value.
            for column, value in row.items():
                setattr(existing, column, value)
            updated += 1

    if dry_run:
        await session.rollback()
    else:
        await session.commit()

    return {"inserted": inserted, "updated": updated, "total": len(parsed)}


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"No such file: {args.file}", file=sys.stderr)
        return 1

    engine = create_async_engine(settings.DATABASE_URL)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            summary = await load_program_requirements(session, args.file, args.dry_run)
    finally:
        await engine.dispose()

    verb = "would load" if args.dry_run else "loaded"
    print(
        f"{args.file.name}: {verb} {summary['total']} rows "
        f"({summary['inserted']} new, {summary['updated']} updated). "
        f"All rows are unverified until a person checks them in /admin."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
