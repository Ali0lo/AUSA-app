"""Map the Turkish YOK Atlas dataset into program_cutoff_history shape.

Source: https://github.com/izcir/turkish-university-admissions-dataset (MIT licensed,
scraped from YOK Atlas / OSYM). Clone it to data/raw/turkey first:

    git clone --depth 1 https://github.com/izcir/turkish-university-admissions-dataset.git data/raw/turkey

The target column is `final_score_012` -- the placement score of the last student
admitted to a program in a given year. That is a published cutoff, which is exactly
what ADR-0001 says the model predicts.

IMPORTANT: this is DOMESTIC (YKS) placement data for Turkish nationals. Azerbaijani
students apply to Turkish universities through the separate YOS / international quota
route, which has its own cutoffs. This data is therefore valid as ML training data and
as a program-selectivity signal, but a YKS cutoff must never be shown to an Azerbaijani
student as "the score you need". See docs/data-collection-plan.md.

Usage:  python backend/scripts/collect_turkey.py [--src DIR] [--out PATH]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# YOK Atlas publishes one page per program code; keep it as the record's provenance.
SOURCE_URL = "https://yokatlas.yok.gov.tr/lisans.php?y={program_code}"

FEATURE_COLUMNS = [
    "university_name",
    "university_type",
    "city",
    "faculty_name",
    "department_name",
    "score_type",
    "scholarship_type",
    "is_undergraduate",
    "total_quota",
    "total_enrolled",
    "initial_placement_rate",
    "avg_obp_012",
]


def load(src: Path) -> pd.DataFrame:
    p = src / "data" / "processed"
    if not (p / "department_stats.csv").exists():
        sys.exit(f"Dataset not found at {p}. Clone it first -- see this file's docstring.")

    stats = pd.read_csv(p / "department_stats.csv", encoding="utf-8")
    depts = pd.read_csv(p / "departments_normalized.csv", encoding="utf-8")

    lookups = {
        "universities_normalized": ("university_id", None),
        "department_names": ("department_name_id", None),
        "faculty_names": ("faculty_name_id", None),
        "score_types": ("score_type_id", None),
        "scholarship_types": ("scholarship_type_id", None),
        "university_cities": ("university_city_id", None),
        "university_types": ("university_type_id", None),
    }
    tables = {n: pd.read_csv(p / f"{n}.csv", encoding="utf-8") for n in lookups}

    df = stats.merge(depts, on="program_code", how="left")
    df = df.merge(tables["universities_normalized"], on="university_id", how="left")
    df = df.merge(tables["department_names"], on="department_name_id", how="left")
    df = df.merge(tables["faculty_names"], on="faculty_name_id", how="left")
    df = df.merge(tables["score_types"], on="score_type_id", how="left")
    df = df.merge(tables["scholarship_types"], on="scholarship_type_id", how="left")
    df = df.merge(tables["university_cities"], on="university_city_id", how="left")
    df = df.merge(tables["university_types"], on="university_type_id", how="left")
    return df


def report(df: pd.DataFrame) -> None:
    """Coverage and persistence-baseline report. ADR-0003 requires the baseline."""
    print("\n--- Coverage ---")
    print(f"institution-year rows with a cutoff : {len(df):,}")
    print(f"unique programs                     : {df.source_program_code.nunique():,}")
    print(f"years                               : {df.intake_year.min()}-{df.intake_year.max()}")

    per_prog = df.groupby("source_program_code")["intake_year"].nunique()
    print("\nprograms by years of history:")
    for years, count in per_prog.value_counts().sort_index().items():
        marker = "  <- trainable" if years >= 3 else ""
        print(f"  {years} year(s): {count:6,}{marker}")
    trainable = per_prog[per_prog >= 3].index
    print(f"\ntrainable programs (>=3 years): {len(trainable):,}")
    print(f"rows from those programs      : {df.source_program_code.isin(trainable).sum():,}")

    print("\n--- Persistence baseline (ADR-0003) ---")
    print("The model must beat 'next cutoff = last cutoff'.")
    piv = df.pivot_table(index="source_program_code", columns="intake_year", values="cutoff_value")
    years = sorted(c for c in piv.columns)
    for a, b in zip(years, years[1:]):
        delta = (piv[b] - piv[a]).dropna()
        if len(delta):
            corr = piv[[a, b]].corr().iloc[0, 1]
            print(f"  {a}->{b}:  n={len(delta):6,}  MAE={delta.abs().mean():7.3f}  r={corr:.4f}")
    print("\n  The final row is the number to beat on the ADR-0003 test split.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="data/raw/turkey")
    parser.add_argument("--out", default="data/processed/turkey_cutoff_history.csv")
    args = parser.parse_args()

    raw = load(Path(args.src))

    # final_score_012 is the cutoff. Rows without one carry no target and are dropped.
    df = raw.dropna(subset=["final_score_012"]).copy()
    df = df.rename(
        columns={
            "program_code": "source_program_code",
            "year": "intake_year",
            "final_score_012": "cutoff_value",
            "final_rank_012": "cutoff_rank",
        }
    )
    df["country"] = "TR"
    df["cutoff_unit"] = "yks_score_012"
    df["lower_is_better"] = False  # score: higher is better. cutoff_rank is the inverse.
    df["source_url"] = df.source_program_code.map(lambda c: SOURCE_URL.format(program_code=c))
    df["verified_by"] = pd.NA  # stays empty until a human checks it (data-sourcing.md)

    columns = [
        "country",
        "source_program_code",
        "intake_year",
        "cutoff_value",
        "cutoff_unit",
        "lower_is_better",
        "cutoff_rank",
        *FEATURE_COLUMNS,
        "source_url",
        "verified_by",
    ]
    out_df = df[columns].sort_values(["source_program_code", "intake_year"])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out, index=False, encoding="utf-8")

    report(out_df)
    print(f"\nWrote {len(out_df):,} rows to {out}")


if __name__ == "__main__":
    main()
