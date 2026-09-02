"""Live demo: what AUSA answers for a real Azerbaijani school-leaver.

Runs the actual FastAPI app in-process against a SQLite database seeded from the
REAL State Programme catalogue CSVs. No Postgres, no running server, no network --
so it reproduces on any teammate's machine.

    cd backend
    ..\\.venv\\Scripts\\python.exe ..\\demo_walkthrough.py

The profile is the spec's own walkthrough case: a school-leaver holding an attestat,
DIM 520, IELTS 7.0, C1 German. The interesting part is not that it returns data --
it is WHICH questions it refuses to answer.
"""
import asyncio
import csv
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "backend"))

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.dp_catalogue import DPCatalogueEntry  # noqa: E402

COUNTRY = {
    "Türkiyə Respublikası": "TR",
    "Almaniya Federativ Respublikası": "DE",
    "Birləşmiş Krallıq": "GB",
    "Amerika Birləşmiş Ştatları": "US",
    "Polşa": "PL",
    "Çin Xalq Respublikası": "CN",
}

BOLD, DIM, GREEN, AMBER, RED, CYAN, OFF = (
    "\033[1m", "\033[2m", "\033[32m", "\033[33m", "\033[31m", "\033[36m", "\033[0m",
)


def rule(title=""):
    print(f"\n{CYAN}{'─' * 74}{OFF}")
    if title:
        print(f"{BOLD}{title}{OFF}\n")


def load_catalogue_rows():
    """Read the real DP CSVs exactly as the loader does."""
    rows = []
    for fn, level in (
        ("dp-bakalavr-2026.csv", "bachelor"),
        ("dp-master-2026.csv", "master"),
    ):
        path = REPO / "data" / "raw" / "azerbaijan" / fn
        if not path.exists():
            print(f"{RED}Missing {path}{OFF}")
            sys.exit(1)
        with io.open(path, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                src = r["Ölkə"]
                rows.append(
                    DPCatalogueEntry(
                        level=level,
                        country_source=src,
                        country_code=COUNTRY.get(src),  # None for the 27 others
                        university_name=r["Universitet"].strip('"').strip("“”"),
                        program_name=r["Təhsil proqramı"].strip('"').strip("“”"),
                        intake_year=2026,
                        source_url="https://dp.edu.az/",
                        retrieved_at=datetime.now(timezone.utc),
                        # verified_by stays NULL: no person has checked these rows.
                    )
                )
    return rows


async def main():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        # Only the table this endpoint reads. Creating all of Base.metadata would pull in
        # Document, whose JSONB and Vector(1536) columns SQLite cannot render -- the same
        # reason the test suite passes an explicit `tables=` list.
        await conn.run_sync(
            Base.metadata.create_all, tables=[DPCatalogueEntry.__table__]
        )
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    rule("Seeding the real State Programme catalogue")
    rows = load_catalogue_rows()
    async with Session() as s:
        s.add_all(rows)
        await s.commit()
    in_scope = sum(1 for r in rows if r.country_code)
    print(f"  {len(rows):,} funded programmes loaded from the official CSVs")
    print(f"  {in_scope:,} in our six target countries")
    print(f"  {len(rows) - in_scope:,} in the other 27 countries "
          f"{DIM}(country_code NULL -- not guessed){OFF}")

    async def override():
        async with Session() as s:
            yield s

    app.dependency_overrides[get_db] = override

    student = {
        "level_sought": "bachelor",
        "qualification_held": "attestat",
        "dim_score": 520,
        "ielts": 7.0,
        "language_certificate_level": "C1",
    }

    rule("The student")
    print("  A school-leaver in Baku, this year's attestat in hand.")
    print(f"  {DIM}DİM 520 · IELTS 7.0 · C1 German · wants a bachelor's abroad{OFF}")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://demo"
    ) as c:
        res = await c.post("/api/v1/routes/assess", json=student)

    if res.status_code != 200:
        print(f"{RED}HTTP {res.status_code}{OFF}\n{res.text[:900]}")
        return
    data = res.json()

    rule("Where they can actually go")
    for plan in data["plans"]:
        hops = plan["hops"]
        status = plan["status"]
        tint = GREEN if status == "open" else AMBER
        path = f" {DIM}→{OFF} ".join(h["key"] for h in hops)
        months = plan["total_months"]
        lo, hi = plan["total_cost_azn_low"], plan["total_cost_azn_high"]
        print(f"  {tint}{status.upper():<11}{OFF} {path}")
        print(f"  {' ' * 11} {DIM}{months} months · {lo:,.0f}–{hi:,.0f} AZN{OFF}")
        for m in plan.get("missing", []):
            print(f"  {' ' * 11} {AMBER}needs:{OFF} {m}")
    if not data["plans"]:
        print(f"  {DIM}(none){OFF}")

    rule("Where they cannot, and the engine says so plainly")
    for key in data["blocked"]:
        print(f"  {RED}BLOCKED{OFF}     {key}")

    rule("State Programme funding")
    dp = data["dp"]
    tint = GREEN if dp["status"] == "open" else AMBER
    print(f"  Status  {tint}{dp['status'].upper()}{OFF}")
    print(f"  Band    {DIM}{dp['band_checked']}{OFF}")
    for g in dp["gates_met"]:
        print(f"  {GREEN}✓{OFF} {g}")
    for g in dp["gates_missing"]:
        print(f"  {AMBER}?{OFF} {g}")
    print(f"\n  {DIM}{dp['note']}{OFF}")

    funded = dp["funded_programmes"]
    rule(f"Funded programmes they could actually reach ({len(funded)})")
    by_country = {}
    for p in funded:
        by_country.setdefault(p["country_code"], []).append(p)
    for cc, items in sorted(by_country.items()):
        print(f"  {BOLD}{cc}{OFF}  {len(items)} programmes")
        for p in items[:3]:
            print(f"      {p['university_name'][:44]:<44} {DIM}{p['program_name'][:26]}{OFF}")
        if len(items) > 3:
            print(f"      {DIM}… and {len(items) - 3} more{OFF}")

    rule("What it refuses to say")
    print(f"  {DIM}This is the part that matters. Every one of these was once")
    print(f"  answered with an invented number.{OFF}\n")
    print(f"  admission_probability   {BOLD}null{OFF}  {DIM}— never estimated where admission is not mechanical{OFF}")
    print(f"  per-programme deadline  {BOLD}absent{OFF}  {DIM}— no verified source is wired in{OFF}")
    print(f"  requirements for 5 of 6 countries  {BOLD}unknown{OFF}  {DIM}— curation has not started{OFF}")
    print(f"\n  {DIM}An unknown never reads as permission. A blank is a labelled")
    print(f"  absence and is never filled by estimation.{OFF}")

    app.dependency_overrides.clear()
    await engine.dispose()
    print()


if __name__ == "__main__":
    asyncio.run(main())
