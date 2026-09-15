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
import json
import math
import re
import sys
from urllib.parse import urlparse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models.qualifications import ProgramRequirement  # noqa: E402
from app.services.catalogue_evidence import content_fingerprint  # noqa: E402

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
    "notes",
    "source_text_hash",
)
# The natural key. The same university publishes different requirements per level and year.
KEY_FIELDS = ("country_code", "university_name", "program_name", "level", "intake_year", "entry_qualification_accepted")
QUALIFICATIONS = {"attestat", "one_year_university", "a_level", "ib", "foundation_year", "feststellungspruefung", "bachelor_degree"}
ALLOWED_COLUMNS = set(KEY_FIELDS + TEXT_FIELDS + FLOAT_FIELDS) | {
    "foundation_required", "application_deadline", "provenance", "source_url",
    "retrieved_at", "last_checked", "verified_by", "evidence", "requirement_scope",
}


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
        number = float(value.strip())
        if not math.isfinite(number) or number < 0:
            raise ValueError("must be finite and nonnegative")
        return number
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
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
            raise ValueError("use a complete ISO date")
        return date.fromisoformat(value.strip())
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
    if set(raw) - ALLOWED_COLUMNS:
        raise CuratedRowError(f"Unknown CSV columns: {set(raw) - ALLOWED_COLUMNS}")
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
    if not intake.is_integer() or not 2000 <= intake <= 2100:
        raise CuratedRowError("intake_year must be a whole year between 2000 and 2100")

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

    if not re.fullmatch(r"[A-Z]{2}", parsed["country_code"]):
        raise CuratedRowError("country_code must be a two-letter country code")
    if parsed["entry_qualification_accepted"] not in QUALIFICATIONS | {None}:
        raise CuratedRowError("entry_qualification_accepted is not a supported qualification")
    if parsed["gpa_scale"] not in {None, "4.0", "5.0", "100", "german"}:
        raise CuratedRowError("gpa_scale must be 4.0, 5.0, 100 or german")
    if parsed["gpa_minimum"] is not None:
        scale = parsed["gpa_scale"]
        if scale is None:
            raise CuratedRowError("gpa_minimum requires gpa_scale")
        maximum = 6.0 if scale == "german" else float(scale)
        if parsed["gpa_minimum"] > maximum or (scale == "german" and parsed["gpa_minimum"] < 1):
            raise CuratedRowError("gpa_minimum is outside its scale")
    if any(parsed[f] is not None for f in ("tuition_per_year", "application_fee", "living_cost_estimate_per_year")) and not parsed["currency"]:
        raise CuratedRowError("A monetary amount requires currency")
    if parsed["currency"] and parsed["currency"] not in {"EUR", "GBP", "USD", "CNY", "TRY", "PLN", "AZN"}:
        raise CuratedRowError("currency is not a supported ISO currency code")
    for score, label in (("language_minimum_score", "language_test"), ("entrance_exam_minimum", "entrance_exam")):
        if parsed[score] is not None and not parsed[label]:
            raise CuratedRowError(f"{score} requires {label}")
    if parsed["language_test"] == "IELTS" and parsed["language_minimum_score"] is not None and parsed["language_minimum_score"] > 9:
        raise CuratedRowError("IELTS must be between 0 and 9")
    scope = _text(raw.get("requirement_scope")) or "general"
    if scope not in {"general", "degree", "foundation"}:
        raise CuratedRowError("requirement_scope must be general, degree or foundation")
    parsed["requirement_scope"] = scope
    validate_url(parsed["source_url"])
    if parsed["source_text_hash"] and not re.fullmatch(r"[a-f0-9]{64}", parsed["source_text_hash"]):
        raise CuratedRowError("source_text_hash must be a lowercase SHA-256 digest")
    parsed["evidence"] = None
    if not _blank(raw.get("evidence")):
        try:
            evidence = json.loads(raw["evidence"])
            if not isinstance(evidence, list) or not evidence:
                raise ValueError("expected a nonempty list")
            for item in evidence:
                if not isinstance(item, dict) or set(item) != {"url", "fields", "checked_at", "note"}:
                    raise ValueError("evidence requires url, fields, checked_at and note")
                validate_url(item["url"])
                if not isinstance(item["fields"], list) or not item["fields"] or any(f not in ALLOWED_COLUMNS for f in item["fields"]):
                    raise ValueError("evidence fields must name catalogue columns")
                if _date(item["checked_at"], "evidence.checked_at") is None or not isinstance(item["note"], str) or not item["note"].strip():
                    raise ValueError("evidence requires a date and an explanatory note")
            parsed["evidence"] = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
        except (ValueError, TypeError, AttributeError) as exc:
            raise CuratedRowError(f"evidence: {exc}") from exc
    for column in ProgramRequirement.__table__.columns:
        maximum = getattr(column.type, "length", None)
        value = parsed.get(column.name)
        if maximum and isinstance(value, str) and len(value) > maximum:
            raise CuratedRowError(f"{column.name} exceeds {maximum} characters")

    return parsed


def validate_url(url):
    if not isinstance(url, str):
        raise CuratedRowError("source URL must be text")
    parts = urlparse(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or any(c.isspace() for c in url):
        raise CuratedRowError("source URL must be an absolute HTTP(S) URL without credentials")
    host = parts.hostname.lower()
    if host == "qebulai.az" or host.endswith(".qebulai.az") or (host.endswith("hochschulstart.de") and "/fileadmin" in parts.path.lower()) or (host.endswith("daad.de") and any(x in parts.path.lower() for x in ("scholarship-database", "stipendiendatenbank"))):
        raise CuratedRowError("Source is prohibited by the project's data-sourcing policy")


def read_rows(path: Path) -> list[dict]:
    with io.open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise CuratedRowError(f"{path.name}: missing or duplicate headers")
        required = {"university_name", "program_name", "level", "country_code", "intake_year", "source_url", "retrieved_at"}
        missing = required - set(reader.fieldnames)
        unknown = set(reader.fieldnames) - ALLOWED_COLUMNS
        if missing or unknown:
            raise CuratedRowError(f"{path.name}: invalid headers; missing={sorted(missing)}, unknown={sorted(unknown)}")
        rows = list(reader)
    parsed = []
    for number, raw in enumerate(rows, start=2):
        try:
            parsed.append(parse_row(raw))
        except CuratedRowError as exc:
            raise CuratedRowError(f"{path.name} line {number}: {exc}") from exc
    keys = [tuple(row[f] for f in KEY_FIELDS) for row in parsed]
    if len(keys) != len(set(keys)):
        raise CuratedRowError(f"{path.name}: two rows share the natural key")
    return parsed


async def load_program_requirements(
    session: AsyncSession, path: Path, dry_run: bool = False, *, commit: bool = True
) -> Dict[str, int]:
    """Load a curated CSV. Idempotent on the natural key; aborts whole on a bad row."""
    parsed = read_rows(path)

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
                ).with_for_update()
            )
        ).scalar_one_or_none()

        if existing is None:
            session.add(ProgramRequirement(**row))
            inserted += 1
        else:
            unchanged = content_fingerprint(existing) == content_fingerprint(row)
            # Every column is assigned, including the blanks. Skipping blanks would mean a
            # curator could never withdraw a value they found to be wrong -- only replace
            # it with another value.
            for column, value in row.items():
                if unchanged and column in {"provenance", "verified_by"}:
                    continue
                setattr(existing, column, value)
            if not unchanged:
                existing.verified_at = None
            updated += 1

    if dry_run:
        await session.rollback()
    elif commit:
        await session.commit()
    else:
        await session.flush()

    return {"inserted": inserted, "updated": updated, "total": len(parsed)}


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate-only", action="store_true", help="Validate offline without contacting the database")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"No such file: {args.file}", file=sys.stderr)
        return 1

    if args.validate_only:
        print(f"{args.file.name}: {len(read_rows(args.file))} valid rows (no database writes)")
        return 0
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
        f"New or changed facts need review in /admin; unchanged reviews are retained."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
