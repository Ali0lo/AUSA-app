"""Train and evaluate tree models that predict program admission cutoffs.

Implements ADR-0001 (predict the cutoff, not P(admit)), ADR-0002 (one model per
country, native units) and ADR-0003 (two evaluation protocols, honest baselines).

Two tasks are evaluated, because they are genuinely different problems:

  FORECASTING  -- the program has cutoff history; predict next intake.
                  Baseline: persistence, next = last. Split: temporal (ADR-0003).
                  Expect the baseline to WIN. Cutoffs are ~0.97 autocorrelated and
                  persistence is very hard to beat. That is a reportable finding,
                  not a bug -- do not tune until the model "wins".

  COLD START   -- the program has NO history; predict its cutoff from its attributes.
                  Baseline: department mean. Split: grouped, whole programs held out.
                  This is the model AUSA actually ships: every hand-curated program
                  arrives with no history, so persistence is structurally unavailable.

No silent fallbacks (ADR-0004): missing input files and empty splits exit with a
message rather than degrading to a default.

The notebook in notebooks/ imports these functions so the report and the production
job cannot drift apart.

Usage:
    python backend/scripts/train_cutoff_models.py                    # all countries
    python backend/scripts/train_cutoff_models.py --country TR
    python backend/scripts/train_cutoff_models.py --out-dir models/
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from joblib import dump
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.tree import DecisionTreeRegressor

REPO_ROOT = Path(__file__).resolve().parents[2]

# Attributes knowable the first time a program is curated -- no history, no outcomes.
# These are the only features the cold-start model may use.
COLD_START_FEATURES = [
    "university_name",
    "university_type",
    "city",
    "faculty_name",
    "department_name",
    "score_type",
    "scholarship_type",
    "total_quota",
    "intake_year",
]

CATEGORICAL = [
    "university_name",
    "university_type",
    "city",
    "faculty_name",
    "department_name",
    "score_type",
    "scholarship_type",
]

# Lag and trend features, forecasting only. Quota for the intake year is legitimate --
# OSYM publishes it in the guide ahead of placement. Enrolment, placement rate and
# average OBP are outcomes of the placement itself, so they are lagged only.
FORECAST_FEATURES = COLD_START_FEATURES + [
    "cut_lag1",
    "cut_lag2",
    "cut_lag3",
    "delta1",
    "delta2",
    "quota_lag1",
    "quota_delta",
    "enrolled_lag1",
    "placement_lag1",
    "fill_lag1",
]

# Present in some countries only -- Turkey publishes the placement rank and the average
# OBP alongside the score. Giving the baseline the strongest possible opponent matters
# more than a uniform feature list, so these are used wherever the source provides them.
OPTIONAL_FORECAST_FEATURES = ["rank_lag1", "obp_lag1", "quota_ratio"]


def available(df: pd.DataFrame, wanted: list) -> list:
    """Keep the features this country actually publishes.

    Countries publish different things -- Azerbaijan's source has no quota, city or
    faculty. Dropping an absent column is honest; filling it with a zero or a mean would
    invent structure the source never had (ADR-0004). Which features were used is
    recorded in metrics.json so a run is never ambiguous.
    """
    return [c for c in wanted if c in df.columns and df[c].notna().any()]


def cold_start_features(df: pd.DataFrame) -> list:
    return available(df, COLD_START_FEATURES)


def forecast_features(df: pd.DataFrame) -> list:
    return available(df, FORECAST_FEATURES + OPTIONAL_FORECAST_FEATURES)

# ADR-0003: hold out the most recent intake, keep the year before it as validation, and
# train on everything older. Derived from the data rather than hardcoded, because the
# countries cover different spans -- Turkey and the USA run to 2024, Azerbaijan to 2025.
def temporal_split_years(df: pd.DataFrame) -> tuple:
    test_year = int(df["intake_year"].max())
    # Azerbaijan has exactly three observed intakes. Once rows without a prior
    # cutoff are removed, the first usable training year is the middle intake.
    # A one-step forecast is still valid: train on 2024 and test on 2025.
    if df["intake_year"].nunique() == 3:
        return test_year - 1, test_year - 1, test_year
    return test_year - 2, test_year - 1, test_year


def models():
    """The three tree algorithms compared, per open-questions C2."""
    return {
        "DecisionTree": DecisionTreeRegressor(max_depth=10, random_state=42),
        "RandomForest": RandomForestRegressor(
            n_estimators=300, max_depth=16, min_samples_leaf=5, n_jobs=-1, random_state=42
        ),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=500, learning_rate=0.06, random_state=42
        ),
    }


# --------------------------------------------------------------------------- loading


def load_country(country: str, data_dir: Path) -> pd.DataFrame:
    """Load one country's cutoff history into the common program_cutoff_history shape.

    Each country publishes a different quantity as its cutoff; ADR-0002 keeps them in
    native units and never mixes them into one model.
    """
    loaders = {"TR": _load_turkey, "US": _load_usa, "AZ": _load_azerbaijan}
    if country not in loaders:
        sys.exit(f"Unknown country {country!r}. Known: {sorted(loaders)}")
    return loaders[country](data_dir)


def _require(path: Path, how: str) -> pd.DataFrame:
    if not path.exists():
        sys.exit(f"Missing {path}.\nGenerate it first:  {how}")
    return pd.read_csv(path)


def _load_turkey(data_dir: Path) -> pd.DataFrame:
    df = _require(
        data_dir / "turkey_cutoff_history.csv",
        "python backend/scripts/collect_turkey.py",
    )
    df["program_key"] = df["source_program_code"].astype(str)
    return df


def _load_usa(data_dir: Path) -> pd.DataFrame:
    """College Scorecard is institution-level, and has no single `cutoff_value` column.

    The nearest published equivalent to "the score of the last admitted student" is the
    25th-percentile SAT total -- roughly, the bottom of the admitted band. That is what
    we treat as the cutoff, and it is labelled as such rather than presented as an
    official threshold (open-questions A5).
    """
    df = _require(
        data_dir / "usa_cutoff_history.csv",
        "python backend/scripts/collect_usa.py",
    )

    sat_p25 = df["sat_read_p25"] + df["sat_math_p25"]
    df["cutoff_value"] = sat_p25
    df["cutoff_unit"] = "sat_total_p25"
    df["lower_is_better"] = False

    # Map Scorecard's institution columns onto the shared feature names. There is no
    # faculty/department level in this source -- that is the A5 granularity mismatch,
    # recorded rather than papered over.
    df["program_key"] = df["institution_id"].astype(str)
    df["university_name"] = df["institution_name"]
    df["university_type"] = df["ownership"]
    df["faculty_name"] = "institution-level"
    df["department_name"] = "institution-level"
    df["score_type"] = "SAT"
    df["scholarship_type"] = "n/a"
    df["total_quota"] = df["undergrad_enrollment"]
    df["total_enrolled"] = df["undergrad_enrollment"]
    df["initial_placement_rate"] = df["admission_rate"]
    return df


def _load_azerbaijan(data_dir: Path) -> pd.DataFrame:
    df = _require(
        data_dir / "azerbaijan_cutoff_history.csv",
        "python backend/scripts/collect_azerbaijan.py  (see docs/data-collection-plan.md)",
    )
    df["program_key"] = df["source_program_code"].astype(str)
    return df


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Drop unusable rows and add the lag/trend features used by the forecasting task."""
    df = df.dropna(subset=["cutoff_value"]).copy()
    if df.empty:
        sys.exit("No rows with a cutoff_value -- nothing to train on.")

    df = df.sort_values(["program_key", "intake_year"])
    g = df.groupby("program_key")

    for lag in (1, 2, 3):
        df[f"cut_lag{lag}"] = g["cutoff_value"].shift(lag)
    df["delta1"] = df["cut_lag1"] - df["cut_lag2"]
    df["delta2"] = df["cut_lag2"] - df["cut_lag3"]

    # Not every country publishes quota or enrolment -- Azerbaijan's source publishes
    # neither. Derive only what the source supports; `available()` drops the rest.
    for source, lagged in (
        ("total_quota", "quota_lag1"),
        ("total_enrolled", "enrolled_lag1"),
        ("initial_placement_rate", "placement_lag1"),
        ("cutoff_rank", "rank_lag1"),
        ("avg_obp_012", "obp_lag1"),
    ):
        if source in df.columns:
            df[lagged] = g[source].shift(1)

    if "quota_lag1" in df.columns:
        df["quota_delta"] = df["total_quota"] - df["quota_lag1"]
        df["quota_ratio"] = df["total_quota"] / df["quota_lag1"].replace(0, np.nan)
        if "enrolled_lag1" in df.columns:
            df["fill_lag1"] = df["enrolled_lag1"] / df["quota_lag1"].replace(0, np.nan)

    # Trees here need numeric input; keep the codes so a fitted model can be reapplied.
    for col in CATEGORICAL:
        if col in df.columns:
            df[col] = df[col].astype("category").cat.codes
    return df


# ------------------------------------------------------------------------ evaluation


def _score(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2))),
        "r2": float(r2_score(y_true, y_pred)),
        "n": int(len(y_true)),
    }


def _fit_predict(model, train, test, features):
    """RandomForest and DecisionTree cannot take NaN; HistGradientBoosting can."""
    if isinstance(model, HistGradientBoostingRegressor):
        model.fit(train[features], train["cutoff_value"])
        return model.predict(test[features])
    median = train[features].median()
    model.fit(train[features].fillna(median), train["cutoff_value"])
    return model.predict(test[features].fillna(median))


def _trainable_features(train: pd.DataFrame, features: list) -> list:
    """Keep features that a split can actually learn from.

    A one-step country split may have an all-null lag (there is no second prior
    year) or a constant intake year. Passing either to HistGradientBoosting can
    fail during binning, while filling it would invent signal.
    """
    return [
        feature
        for feature in features
        if train[feature].notna().any() and train[feature].nunique(dropna=True) > 1
    ]


def evaluate_forecasting(df: pd.DataFrame) -> dict:
    """Temporal split. Baseline: next cutoff = last cutoff."""
    train_end, val_year, test_year = temporal_split_years(df)
    d = df.dropna(subset=["cut_lag1"])
    train = d[d.intake_year <= train_end]
    test = d[d.intake_year == test_year]

    if train.empty or test.empty:
        return {
            "skipped": f"too few intake years for a temporal split "
            f"(train<={train_end} has {len(train)} rows, test={test_year} has {len(test)})"
        }

    features = _trainable_features(train, forecast_features(d))
    if not features:
        return {"skipped": "no trainable forecasting features after split"}
    one_step = train_end == val_year
    results = {
        "split": (
            f"train={train_end}, test={test_year} (one-step)"
            if one_step
            else f"train<={train_end}, val={val_year}, test={test_year}"
        ),
        "features": features,
        "baselines": {"persistence": _score(test["cutoff_value"], test["cut_lag1"])},
        "models": {},
    }
    baseline_mae = results["baselines"]["persistence"]["mae"]
    persistence_residual = test["cutoff_value"].to_numpy() - test["cut_lag1"].to_numpy()
    results["persistence_interval"] = {
        "lower_offset": float(np.quantile(persistence_residual, 0.1)),
        "upper_offset": float(np.quantile(persistence_residual, 0.9)),
        "coverage": 0.8,
    }

    for name, model in models().items():
        pred = _fit_predict(model, train, test, features)
        scored = _score(test["cutoff_value"], pred)
        scored["vs_baseline_pct"] = round((baseline_mae - scored["mae"]) / baseline_mae * 100, 2)
        scored["beats_baseline"] = scored["mae"] < baseline_mae
        results["models"][name] = scored
    return results


def evaluate_cold_start(df: pd.DataFrame, out_dir: Path, country: str) -> dict:
    """Grouped split -- whole programs held out, so the test set is unseen programs.

    The winning model is persisted, because this is the one that serves the product.
    """
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(splitter.split(df, groups=df["program_key"]))
    train, test = df.iloc[train_idx], df.iloc[test_idx]

    overlap = set(train["program_key"]) & set(test["program_key"])
    if overlap:
        sys.exit(f"Cold-start split leaked {len(overlap)} programs into both sides.")

    features = cold_start_features(df)
    global_mean = train["cutoff_value"].mean()
    dept_mean = train.groupby("department_name")["cutoff_value"].mean()
    # A department absent from training is exactly the cold-start case the baseline
    # cannot handle; falling back to the global mean is the baseline's honest best.
    pred_dept = test["department_name"].map(dept_mean).fillna(global_mean)

    results = {
        "split": "GroupShuffleSplit(test_size=0.25) on program_key",
        "features": features,
        "train_programs": int(train["program_key"].nunique()),
        "test_programs": int(test["program_key"].nunique()),
        "baselines": {
            "global_mean": _score(test["cutoff_value"], np.full(len(test), global_mean)),
            "department_mean": _score(test["cutoff_value"], pred_dept),
        },
        "models": {},
    }
    baseline_mae = results["baselines"]["department_mean"]["mae"]

    best_name, best_mae, best_model = None, np.inf, None
    best_predictions = None
    for name, model in models().items():
        pred = _fit_predict(model, train, test, features)
        scored = _score(test["cutoff_value"], pred)
        scored["vs_baseline_pct"] = round((baseline_mae - scored["mae"]) / baseline_mae * 100, 2)
        scored["beats_baseline"] = scored["mae"] < baseline_mae
        results["models"][name] = scored
        if scored["mae"] < best_mae:
            best_name, best_mae, best_model = name, scored["mae"], model
            best_predictions = pred

    if best_mae < baseline_mae:
        out_dir.mkdir(parents=True, exist_ok=True)
        artifact = out_dir / f"cutoff_coldstart_{country}.joblib"
        residuals = test["cutoff_value"].to_numpy() - np.asarray(best_predictions)
        dump({
            "model": best_model,
            "name": best_name,
            "features": features,
            "country": country,
            "sklearn_version": sklearn.__version__,
            "interval": {
                "lower_offset": float(np.quantile(residuals, 0.1)),
                "upper_offset": float(np.quantile(residuals, 0.9)),
                "coverage": 0.8,
            },
        }, artifact)
        results["shipped_model"] = {"name": best_name, "artifact": str(artifact.relative_to(REPO_ROOT))}
    else:
        # ADR-0004: never ship a model that loses to its baseline just to have one.
        results["shipped_model"] = None
        results["note"] = "No model beat the department-mean baseline; nothing persisted."
    return results


# --------------------------------------------------- one pooled model vs per-country


def evaluate_pooled(data_dir: Path, countries: list) -> dict:
    """Test ADR-0002's per-country decision instead of assuming it.

    A single model with `country` as a feature is only meaningful on a unit-free target:
    raw cutoffs run 0-560 (YKS), 0-700 (DIM) and 600-1500 (SAT p25), so a pooled
    regressor on raw values would mostly learn which country a row came from, and its
    error would be dominated by the largest scale.

    The comparable target is the cutoff's percentile within its own country and year --
    which is also exactly the selectivity index the product displays. A predicted
    percentile converts back to native units through that country's own distribution.

    Three arms, identical held-out programs: per-country models, one pooled model, and
    one pooled model with countries weighted equally (Turkey is ~90% of the rows, so
    swamping has to be ruled out before concluding that pooling simply does not work).
    """
    if len(countries) < 2:
        return {"skipped": "needs at least two countries"}

    frames = []
    for country in countries:
        df = load_country(country, data_dir).dropna(subset=["cutoff_value"]).copy()
        df["country"] = country
        df["program_key"] = country + "::" + df["program_key"].astype(str)
        df["target_pct"] = df.groupby("intake_year")["cutoff_value"].rank(pct=True)
        frames.append(df)
    pool = pd.concat(frames, ignore_index=True)

    shared = ["university_name", "department_name", "score_type", "scholarship_type"]
    # Encode across the pool so every arm sees one consistent code space. Names are in
    # different languages, so a Turkish and an Azerbaijani department never share a code
    # -- there is no shared taxonomy to transfer through, and that is the finding.
    for col in shared + ["country"]:
        pool[col + "_code"] = pool[col].astype("category").cat.codes
    features = [c + "_code" for c in shared] + ["intake_year"]
    pooled_features = features + ["country_code"]

    train_parts, test_parts = [], []
    for country in countries:
        sub = pool[pool.country == country]
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
        tr_idx, te_idx = next(splitter.split(sub, groups=sub["program_key"]))
        train_parts.append(sub.iloc[tr_idx])
        test_parts.append(sub.iloc[te_idx])
    train_all, test_all = pd.concat(train_parts), pd.concat(test_parts)

    def hgb():
        return HistGradientBoostingRegressor(max_iter=500, learning_rate=0.06, random_state=42)

    pooled = hgb().fit(train_all[pooled_features], train_all["target_pct"])
    counts = train_all["country"].value_counts()
    weights = train_all["country"].map(len(train_all) / (len(counts) * counts))
    pooled_balanced = hgb().fit(
        train_all[pooled_features], train_all["target_pct"], sample_weight=weights
    )

    results = {"target": "cutoff percentile within country-year", "per_country": {}}
    print("\n=== ONE POOLED MODEL vs PER-COUNTRY (percentile target) ===")
    print(f"  {'country':<9}{'dept-mean':>11}{'per-country':>13}{'pooled':>9}{'pooled-bal':>12}  winner")
    for country in countries:
        tr = train_all[train_all.country == country]
        te = test_all[test_all.country == country]

        dept_mean = tr.groupby("department_name_code")["target_pct"].mean()
        base = mean_absolute_error(
            te["target_pct"],
            te["department_name_code"].map(dept_mean).fillna(tr["target_pct"].mean()),
        )
        solo = mean_absolute_error(
            te["target_pct"], hgb().fit(tr[features], tr["target_pct"]).predict(te[features])
        )
        pooled_mae = mean_absolute_error(te["target_pct"], pooled.predict(te[pooled_features]))
        balanced_mae = mean_absolute_error(
            te["target_pct"], pooled_balanced.predict(te[pooled_features])
        )

        arms = {"per_country": solo, "pooled": pooled_mae, "pooled_balanced": balanced_mae}
        winner = min(arms, key=arms.get)
        results["per_country"][country] = {
            "baseline_department_mean": float(base),
            **{k: float(v) for k, v in arms.items()},
            "winner": winner,
        }
        print(f"  {country:<9}{base:>11.4f}{solo:>13.4f}{pooled_mae:>9.4f}"
              f"{balanced_mae:>12.4f}  {winner}")

    wins = [v["winner"] for v in results["per_country"].values()]
    results["verdict"] = (
        "per-country retained (ADR-0002 holds)"
        if wins.count("per_country") >= len(wins) / 2
        else "pooled competitive -- revisit ADR-0002"
    )
    print(f"  -> {results['verdict']}")
    return results


# ------------------------------------------------------------------------------ main


def run(country: str, data_dir: Path, out_dir: Path) -> dict:
    df = prepare(load_country(country, data_dir))
    print(f"\n=== {country}: {len(df):,} rows / {df['program_key'].nunique():,} programs "
          f"({df.intake_year.min()}-{df.intake_year.max()}) ===")

    report = {
        "country": country,
        "cutoff_unit": str(df["cutoff_unit"].iloc[0]),
        "lower_is_better": bool(df["lower_is_better"].iloc[0]),
        "rows": int(len(df)),
        "programs": int(df["program_key"].nunique()),
        "forecasting": evaluate_forecasting(df),
        "cold_start": evaluate_cold_start(df, out_dir, country),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
    }
    _print_task("FORECASTING", report["forecasting"])
    _print_task("COLD START", report["cold_start"])
    return report


def _print_task(title: str, task: dict) -> None:
    print(f"\n  {title}")
    if "skipped" in task:
        print(f"    skipped: {task['skipped']}")
        return
    for name, scored in task["baselines"].items():
        print(f"    BASELINE {name:<20} MAE = {scored['mae']:8.4f}")
    for name, scored in task["models"].items():
        verdict = "BEATS" if scored["beats_baseline"] else "loses"
        print(f"    {name:<29} MAE = {scored['mae']:8.4f}"
              f"  {scored['vs_baseline_pct']:+6.1f}%  {verdict}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", action="append", choices=["TR", "US", "AZ"],
                        help="repeatable; default is every country with data present")
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "processed")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "models")
    args = parser.parse_args()

    countries = args.country or ["TR", "US", "AZ"]
    reports = {}
    for country in countries:
        path = args.data_dir / f"{ {'TR': 'turkey', 'US': 'usa', 'AZ': 'azerbaijan'}[country] }_cutoff_history.csv"
        if not args.country and not path.exists():
            print(f"skipping {country}: {path.name} not collected yet")
            continue
        reports[country] = run(country, args.data_dir, args.out_dir)

    if not reports:
        sys.exit("No country data found. Run the collect_*.py scripts first.")

    output = {"per_country": reports,
              "pooled_vs_per_country": evaluate_pooled(args.data_dir, list(reports))}

    args.out_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.out_dir / "metrics.json"
    metrics_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nmetrics -> {metrics_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
