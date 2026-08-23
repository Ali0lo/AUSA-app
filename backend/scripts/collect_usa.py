"""Extract US admission cutoff history from the College Scorecard bulk data.

Source: https://collegescorecard.ed.gov/data/ (US Dept of Education, public domain).
Download the raw-data zip first (~448 MB, one file, no rate limits):

    python backend/scripts/collect_usa.py --download

The API route was tried and abandoned: the unregistered DEMO_KEY is throttled to
roughly 30 requests/hour per IP, and a full time-series pull needs 200+. The bulk zip
has no such limit and carries more history.

The US has no published per-program cutoff. The closest analogues are the SAT 25th
percentile (the score at which roughly a quarter of admitted students scored lower --
a soft floor) and the overall admission rate. Both are used as the target.

Two limitations that must be carried into the UI (open question A5):
  * Data is INSTITUTION-level and undergraduate-focused, not program-level.
  * The SAT was redesigned in 2016 (2400-point -> 1600-point scale), so SAT values
    before the 2016_17 file are NOT comparable to later ones. Default range starts
    at 2016_17 for that reason. ADM_RATE has no such break.

Usage:
    python backend/scripts/collect_usa.py --download
    python backend/scripts/collect_usa.py [--years 2016-2024] [--out PATH]
"""

import argparse
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

BULK_URL = (
    "https://ed-public-download.scorecard.network/downloads/"
    "College_Scorecard_Raw_Data_06102026.zip"
)
DEFAULT_ZIP = "data/raw/usa/scorecard_raw.zip"

# Scorecard column -> our name. See the data dictionary in the zip.
COLUMNS = {
    "UNITID": "institution_id",
    "INSTNM": "institution_name",
    "CITY": "city",
    "STABBR": "state",
    "CONTROL": "ownership",
    "PREDDEG": "predominant_degree",
    "ADM_RATE": "admission_rate",
    "SATVR25": "sat_read_p25",
    "SATVR75": "sat_read_p75",
    "SATMT25": "sat_math_p25",
    "SATMT75": "sat_math_p75",
    "SAT_AVG": "sat_avg",
    "UGDS": "undergrad_enrollment",
}
OWNERSHIP = {1: "public", 2: "private_nonprofit", 3: "private_forprofit"}
MISSING = ["NULL", "PrivacySuppressed", ""]


def download(dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(BULK_URL, headers={"User-Agent": "Mozilla/5.0"})
    started, size = time.time(), 0
    with urllib.request.urlopen(req, timeout=120) as resp, dst.open("wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
            size += len(chunk)
            print(f"  {size / 1048576:,.0f} MB", end="\r", file=sys.stderr)
    print(f"  {size / 1048576:,.1f} MB in {time.time() - started:,.0f}s", file=sys.stderr)


def read_year(zf: zipfile.ZipFile, member: str, year: int) -> pd.DataFrame:
    with zf.open(member) as fh:
        df = pd.read_csv(
            fh,
            usecols=lambda c: c in COLUMNS,
            na_values=MISSING,
            low_memory=False,
        )
    df = df.rename(columns=COLUMNS)
    # PREDDEG 3 = predominantly bachelor's degrees. Excludes certificate mills.
    df = df[df.predominant_degree == 3].drop(columns=["predominant_degree"])
    df["intake_year"] = year
    return df


def report(df: pd.DataFrame) -> None:
    print("\n--- Coverage ---")
    print(f"institution-year rows : {len(df):,}")
    print(f"unique institutions   : {df.institution_id.nunique():,}")
    print(f"years                 : {df.intake_year.min()}-{df.intake_year.max()}")

    print("\nnon-null rate by column:")
    for col in ["admission_rate", "sat_read_p25", "sat_math_p25", "sat_avg"]:
        print(f"  {col:22s} {df[col].notna().mean():6.1%}  ({df[col].notna().sum():,})")

    for target in ["admission_rate", "sat_avg"]:
        have = df.dropna(subset=[target])
        per = have.groupby("institution_id")["intake_year"].nunique()
        print(f"\n{target}: institutions with >=3 years = {(per >= 3).sum():,} / {per.size:,}")

        print(f"  persistence baseline (ADR-0003), MAE on {target}:")
        piv = have.pivot_table(index="institution_id", columns="intake_year", values=target)
        years = sorted(piv.columns)
        for a, b in zip(years, years[1:]):
            delta = (piv[b] - piv[a]).dropna()
            if len(delta):
                corr = piv[[a, b]].corr().iloc[0, 1]
                print(f"    {a}->{b}: n={len(delta):5,}  MAE={delta.abs().mean():8.4f}  r={corr:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="fetch the bulk zip, then exit")
    parser.add_argument("--zip", default=DEFAULT_ZIP)
    parser.add_argument("--years", default="2016-2024", help="inclusive, e.g. 2016-2024")
    parser.add_argument("--out", default="data/processed/usa_cutoff_history.csv")
    args = parser.parse_args()

    zip_path = Path(args.zip)
    if args.download:
        download(zip_path)
        return
    if not zip_path.exists():
        sys.exit(f"{zip_path} not found. Run with --download first.")

    start, end = (int(x) for x in args.years.split("-"))

    with zipfile.ZipFile(zip_path) as zf:
        members = {}
        for name in zf.namelist():
            stem = Path(name).name
            if stem.startswith("MERGED") and stem.endswith("_PP.csv"):
                members[int(stem[6:10])] = name

        frames = []
        for year in range(start, end + 1):
            if year not in members:
                print(f"  {year}: not in archive, skipped", file=sys.stderr)
                continue
            print(f"  reading {year}...", file=sys.stderr)
            frames.append(read_year(zf, members[year], year))

    if not frames:
        sys.exit("No year files matched the requested range.")

    df = pd.concat(frames, ignore_index=True)
    df["ownership"] = df.ownership.map(OWNERSHIP).fillna(df.ownership)
    df["country"] = "US"
    df["cutoff_unit"] = "sat_p25_and_admit_rate"
    df["lower_is_better"] = False
    df["source_url"] = "https://collegescorecard.ed.gov/data/"
    df["verified_by"] = pd.NA

    # Drop rows carrying no admissions signal at all.
    signal = ["admission_rate", "sat_read_p25", "sat_math_p25", "sat_avg"]
    df = df.dropna(subset=signal, how="all")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values(["institution_id", "intake_year"]).to_csv(out, index=False, encoding="utf-8")

    report(df)
    print(f"\nWrote {len(df):,} rows to {out}")


if __name__ == "__main__":
    main()
