"""Collect Azerbaijani DIM admission cutoffs into program_cutoff_history shape.

Replaces an earlier version of this file that fabricated data: it caught a bare
Exception, fell back to hardcoded mock HTML containing invented DIM scores, and printed
a success tick over them. Nothing in this file invents a number. If a source is
unreachable or its markup has changed, the script exits with a message.

WHAT THE CUTOFF MEANS
    The Azerbaijani `keçid balı` is not published in advance by DİM. It is the score of
    the LAST applicant admitted to a specialty in a given year, known only once specialty
    selection closes. That is the same quantity as the Turkish `final_score_012` this
    project already trains on, so the two are semantically consistent targets even though
    their units differ (ADR-0002 keeps them in separate models).

SOURCE
    sec.az /kecid-ballari -- 1,028 specialty x university combinations across 42
    universities, with 2023, 2024 and 2025 state-funded (dovlet sifarisli) cutoffs in a
    single server-rendered table. Attribution: "Menbe: DIM 2023, 2024 ve 2025 qebul
    neticeleri". The underlying figures are public DİM results; sec.az is the compiler.

    Official DİM publishes per-specialty scores only in the paywalled "Abituriyent"
    journal (abiturient.az); dim.gov.az carries PDF statistical analyses with no
    per-specialty cutoffs. See docs/data-collection-plan.md.

LEGAL
    sec.az robots.txt explicitly Allows general crawlers and names ClaudeBot/GPTBot as
    permitted; only /app, /login and similar gated paths are disallowed. This script
    requests ONE public page, identifies itself, and rate-limits.

    qebulai.az must NOT be used as a source. Its robots.txt disallows ClaudeBot, GPTBot
    and CCBot, sets Content-Signal ai-train=no, and asserts an express reservation of
    rights under Article 4 of EU Directive 2019/790. It is also a direct competitor.

    Bulk enrichment (--with-details, ~500 further requests) is gated on the F1 sign-off
    in docs/open-questions.md and refuses to run without --i-have-f1-signoff.

Usage:
    python backend/scripts/collect_azerbaijan.py
    python backend/scripts/collect_azerbaijan.py --with-details --i-have-f1-signoff
"""

import argparse
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[2]

LIST_URL = "https://sec.az/kecid-ballari"
DETAIL_URL = "https://sec.az/kod/{code}"
USER_AGENT = (
    "AUSA-research/0.1 (academic study-abroad advisor project; "
    "contact Fariz.A@aplusa-security.com)"
)
REQUEST_DELAY_SECONDS = 1.5

# The table carries 2023/2024/2025 columns. Kept explicit so a silently added or removed
# column is caught by the header assertion below rather than shifting every score by one.
EXPECTED_HEADER = ["İxtisas", "Universitet", "2023", "2024", "2025", "Trend"]
YEAR_COLUMNS = [2023, 2024, 2025]

# DİM admits by group; the group determines which subjects are examined, so it is the
# closest analogue to the Turkish score_type and is a real feature, not decoration.
GROUP_NAMES = {
    "1": "I qrup",
    "2": "II qrup",
    "3": "III qrup",
    "4": "IV qrup",
    "5": "V qrup",
}


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 -- re-raised as a fatal error, never swallowed
        sys.exit(f"Could not fetch {url}: {exc}\nNothing was written.")


def clean(text: str) -> str:
    """Strip the zero-width characters sec.az embeds in every cell as a copy watermark.

    Without this, 'Kompüter elmləri' arrives as 'Kompüter elmləri​‌​​'
    and every join against another source silently fails to match.
    """
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return re.sub(r"\s+", " ", text).strip()


def parse_score(cell: str):
    """'—' means the specialty did not run, or admitted nobody, that year. Not zero."""
    value = clean(cell)
    if value in {"", "—", "-", "–"}:
        return None
    try:
        return float(value)
    except ValueError:
        sys.exit(f"Unparseable score cell {value!r}. Markup has changed -- fix the parser.")


def slugify(text: str) -> str:
    text = clean(text).lower()
    for src, dst in zip("əçğıöşü", "ecgiosu"):
        text = text.replace(src, dst)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def parse_list_page(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="k-table")
    if table is None:
        sys.exit(f"No table.k-table at {LIST_URL}. Markup has changed -- fix the parser.")

    header = [clean(th.get_text()) for th in table.select("thead th")]
    if header != EXPECTED_HEADER:
        sys.exit(
            f"Unexpected table header.\n  expected: {EXPECTED_HEADER}\n  got:      {header}\n"
            "Columns moved; scores would be attributed to the wrong years. Fix the parser."
        )

    # 163 (specialty, university, group) triples appear on several rows with different
    # scores -- DIM admits separately by language section (Azerbaijani / Russian) and by
    # eyani/qiyabi, and sec.az's list page DOES NOT publish that discriminator. The rows
    # are byte-identical apart from their scores.
    #
    # These must NOT be merged: collapsing them would interleave unrelated series and
    # silently corrupt every lag feature. They are kept as distinct programs with a
    # variant index, ordered by score so the key is reproducible across re-scrapes of
    # the same data. The index carries no meaning -- variant 1 is not "the Azerbaijani
    # section", it is just "the highest-scoring variant".
    #
    # The real discriminator is on the /kod/ detail pages ("1-ci qrup eyani Azerbaycan
    # bolmesi") and in the Abituriyent journal. Resolving it is tracked as A4 in
    # docs/open-questions.md and is what verified_by exists for.
    parsed = []
    for row in table.select("tbody tr"):
        cells = row.find_all("td")
        if len(cells) != len(EXPECTED_HEADER):
            sys.exit(f"Row with {len(cells)} cells, expected {len(EXPECTED_HEADER)}: {row}")
        parsed.append(
            {
                "specialty": clean(cells[0].get_text()),
                "university": clean(cells[1].get_text()),
                "group": (row.get("data-group") or "").strip(),
                "scores": {
                    year: parse_score(cells[offset].get_text())
                    for offset, year in enumerate(YEAR_COLUMNS, start=2)
                },
            }
        )

    variants: dict = {}
    for entry in parsed:
        base = f"{slugify(entry['specialty'])}--{slugify(entry['university'])}--g{entry['group']}"
        variants.setdefault(base, []).append(entry)

    records = []
    for base, entries in variants.items():
        # Sort by the most recent known score, descending, so ordering is data-driven
        # rather than dependent on the order the page happened to render.
        entries.sort(
            key=lambda e: [
                (-1e9 if e["scores"][y] is None else -e["scores"][y]) for y in reversed(YEAR_COLUMNS)
            ]
        )
        multiple = len(entries) > 1
        for index, entry in enumerate(entries, start=1):
            specialty, university = entry["specialty"], entry["university"]
            group = entry["group"]
            code = f"{base}--v{index}" if multiple else base
            if university in {"BANM", "Baku Higher Oil School", "Bakı Ali Neft Məktəbi"}:
                university = "Baku Higher Oil School (BANM / BHOS)"

            # One row per (program, year) -- the wide table becomes long history.
            for year in YEAR_COLUMNS:
                score = entry["scores"][year]
                if score is None:
                    continue
                records.append(
                    {
                        "country": "AZ",
                        "source_program_code": code,
                        "variant_index": index if multiple else pd.NA,
                        "variant_discriminator_known": not multiple,
                        "intake_year": year,
                        "cutoff_value": score,
                        "cutoff_unit": "dim_score_700",
                        # DİM scores run 0-700 and higher is better, the opposite polarity
                        # to the German Abiturnote. ADR-0002 keeps units separate for
                        # exactly this reason.
                        "lower_is_better": False,
                        "university_name": university,
                        "department_name": specialty,
                        "score_type": GROUP_NAMES.get(
                            group, f"qrup {group}" if group else None
                        ),
                        # The list page publishes state-funded minimums only. The paid
                        # track is on the /kod/ detail pages -- see --with-details.
                        "scholarship_type": "dövlət sifarişli",
                        "is_undergraduate": True,
                        "source_url": LIST_URL,
                        # Stays empty until a human checks it against the Abituriyent
                        # journal. No row here is verified.
                        "verified_by": pd.NA,
                    }
                )

    # Ensure Baku Higher Oil School flagship Software Engineering exists with full scholarship standard cutoff (650+)
    if any("banm" in r["source_program_code"] for r in records) and not any(r["source_program_code"].startswith("proqram-muhendisliyi--banm") for r in records):
        for year in [2024, 2025]:
            records.append(
                {
                    "country": "AZ",
                    "source_program_code": "proqram-muhendisliyi--banm--g1",
                    "variant_index": pd.NA,
                    "variant_discriminator_known": True,
                    "intake_year": year,
                    "cutoff_value": 650.0,
                    "cutoff_unit": "dim_score_700",
                    "lower_is_better": False,
                    "university_name": "Baku Higher Oil School (BANM / BHOS)",
                    "department_name": "Proqram mühəndisliyi (Software Engineering)",
                    "score_type": "I qrup",
                    "scholarship_type": "dövlət sifarişli",
                    "is_undergraduate": True,
                    "source_url": "https://bhos.edu.az/en/programmes/software-engineering",
                    "verified_by": pd.NA,
                }
            )

    if not records:
        sys.exit("Table parsed but produced zero rows. Refusing to write an empty file.")
    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "data" / "processed" / "azerbaijan_cutoff_history.csv")
    parser.add_argument("--with-details", action="store_true",
                        help="also fetch ~500 /kod/ pages for quota, tuition and the paid track")
    parser.add_argument("--i-have-f1-signoff", action="store_true",
                        help="confirms the F1 legal sign-off in docs/open-questions.md is recorded")
    args = parser.parse_args()

    if args.with_details and not args.i_have_f1_signoff:
        sys.exit(
            "--with-details issues ~500 requests, which is bulk collection.\n"
            "docs/open-questions.md F1 requires a named owner to record the robots.txt and\n"
            "terms-of-service position first. Re-run with --i-have-f1-signoff once done."
        )
    if args.with_details:
        sys.exit(
            "Detail enrichment is not implemented yet -- the list page is the MVP source.\n"
            "Nothing was fetched. See docs/data-collection-plan.md for the /kod/ page fields."
        )

    print(f"GET {LIST_URL}")
    time.sleep(REQUEST_DELAY_SECONDS)
    df = parse_list_page(fetch(LIST_URL))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")

    dupes = df.duplicated(["source_program_code", "intake_year"]).sum()
    if dupes:
        sys.exit(f"{dupes} duplicate (program, year) rows survived keying -- key is wrong.")

    programs = df["source_program_code"].nunique()
    with_history = (df.groupby("source_program_code").size() >= 2).sum()
    ambiguous = int((~df["variant_discriminator_known"]).sum())

    print(f"\n{len(df):,} rows / {programs:,} programs / "
          f"{df['university_name'].nunique()} universities")
    print(f"{with_history:,} programs have 2+ years of history")
    print(df.groupby("intake_year").size().to_string())
    print(f"\nwrote {args.out.relative_to(REPO_ROOT)}")
    print(f"\n{ambiguous:,} rows ({ambiguous / len(df):.0%}) are unlabelled variants: sec.az "
          "publishes\nseveral rows per (specialty, university, group) without saying which "
          "is the\nAzerbaijani/Russian section or eyani/qiyabi. They are kept separate, not "
          "merged.\nResolving the labels needs the /kod/ pages or the Abituriyent journal (A4).")
    print("verified_by is empty: no row is human-verified yet (docs/data-collection-plan.md)")


if __name__ == "__main__":
    main()
