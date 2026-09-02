"""Quarantine programme rows written by the extraction fallback deleted on 31 Aug 2026.

That fallback invented a record from regex hits when the LLM call failed: university
"Extracted University", programme "Extracted Program", a hardcoded 11208.0 EUR blocked
account, and a confidence score that reached 100.0 from three matches -- clearing the 85%
review threshold and publishing without a human ever seeing the row.

Rows are deactivated and marked, never deleted: a person still has to decide what the
fallback got wrong, and deleting the evidence would make that impossible.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.program import Program  # noqa: E402

QUARANTINE_STATUS = "quarantined_fallback_extraction"

FALLBACK_UNIVERSITY_NAME = "Extracted University"
FALLBACK_PROGRAM_NAME = "Extracted Program"
FALLBACK_NOTE = "Extracted via fallback parser."


async def find_suspect_programs(session: AsyncSession) -> list[Program]:
    """Every row carrying a marker the deleted fallback is known to have written."""
    stmt = select(Program).where(
        or_(
            Program.university_name == FALLBACK_UNIVERSITY_NAME,
            Program.program_name == FALLBACK_PROGRAM_NAME,
            Program.requirements_text == FALLBACK_NOTE,
        )
    )
    return list((await session.execute(stmt)).scalars().all())


async def quarantine(session: AsyncSession, programs: list[Program]) -> int:
    """Deactivate and mark. Returns how many rows were changed."""
    for program in programs:
        program.is_active = False
        program.verification_status = QUARANTINE_STATUS
        # The fallback's confidence was computed from regex hit count, so it measured
        # nothing. NULL is what "nobody scored this" looks like.
        program.confidence_score = None
    await session.commit()
    return len(programs)


async def _main(dry_run: bool) -> None:
    async with AsyncSessionLocal() as session:
        suspects = await find_suspect_programs(session)
        for program in suspects:
            print(f"  id={program.id}  {program.university_name} / {program.program_name}")
        if dry_run:
            print(f"{len(suspects)} row(s) would be quarantined. Nothing was written.")
            return
        print(f"{await quarantine(session, suspects)} row(s) quarantined.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    asyncio.run(_main(parser.parse_args().dry_run))
