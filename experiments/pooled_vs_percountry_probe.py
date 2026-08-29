"""Can ONE model with `country` as a feature replace the three per-country models?

The obstacle is the target. Raw cutoffs are in incompatible units -- YKS ~0-560,
DIM 0-700, SAT-p25 ~600-1500 -- so a single regressor on raw values would mostly be
learning "which country is this", and MAE would be dominated by the largest scale.

The fix is to predict the WITHIN-COUNTRY-YEAR PERCENTILE of the cutoff instead. That is
unit-free, comparable across countries, and it is exactly the selectivity index the
product already decided to display (grilling Q2). A predicted percentile converts back
to native units by looking it up in that country's cutoff distribution.

Compares, on the identical percentile target and identical cold-start splits:
  (a) three per-country models
  (b) one pooled model with `country` as a feature
"""

import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit

sys.path.insert(0, "backend/scripts")
from train_cutoff_models import load_country  # noqa: E402

from pathlib import Path  # noqa: E402

DATA = Path("data/processed")
SHARED = ["university_name", "department_name", "score_type", "scholarship_type", "intake_year"]

frames = []
for country in ("TR", "US", "AZ"):
    df = load_country(country, DATA).dropna(subset=["cutoff_value"]).copy()
    df["country"] = country
    df["program_key"] = country + "::" + df["program_key"].astype(str)
    # Percentile of this cutoff within its own country-year. Unit-free by construction.
    df["target_pct"] = df.groupby("intake_year")["cutoff_value"].rank(pct=True)
    frames.append(df[SHARED + ["country", "program_key", "target_pct", "cutoff_value"]])

pool = pd.concat(frames, ignore_index=True)
print("rows per country:")
print(pool.groupby("country").size().to_string(), "\n")

# Encode categoricals GLOBALLY so the pooled model sees one consistent code space.
# Names do not translate across languages, so a Turkish and an Azerbaijani department
# get different codes -- the tree can still split on `country` first and recover.
for col in ["university_name", "department_name", "score_type", "scholarship_type", "country"]:
    pool[col + "_code"] = pool[col].astype("category").cat.codes

FEATURES = [c + "_code" for c in
            ["university_name", "department_name", "score_type", "scholarship_type"]] + ["intake_year"]
POOLED_FEATURES = FEATURES + ["country_code"]


def split(df):
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    tr, te = next(splitter.split(df, groups=df["program_key"]))
    return df.iloc[tr], df.iloc[te]


def model():
    return HistGradientBoostingRegressor(max_iter=500, learning_rate=0.06, random_state=42)


# Split each country separately, then concatenate, so both approaches are tested on
# exactly the same held-out programs.
train_parts, test_parts = [], []
for country in ("TR", "US", "AZ"):
    sub = pool[pool.country == country]
    tr, te = split(sub)
    train_parts.append(tr)
    test_parts.append(te)
train_all = pd.concat(train_parts)
test_all = pd.concat(test_parts)

# (b) one pooled model
pooled = model().fit(train_all[POOLED_FEATURES], train_all["target_pct"])

# (c) pooled, but each country weighted equally -- Turkey is 90% of the rows, so test
# whether the pooled model is simply being swamped rather than genuinely unable to learn.
counts = train_all["country"].value_counts()
weights = train_all["country"].map(len(train_all) / (len(counts) * counts))
pooled_bal = model().fit(train_all[POOLED_FEATURES], train_all["target_pct"], sample_weight=weights)

print(f"{'country':<9}{'baseline':>10}{'per-country':>13}{'pooled':>9}{'pooled-bal':>12}{'winner':>14}")
print("-" * 68)
for country in ("TR", "US", "AZ"):
    tr = train_all[train_all.country == country]
    te = test_all[test_all.country == country]

    # Baseline: predict the department's mean percentile.
    dept_mean = tr.groupby("department_name_code")["target_pct"].mean()
    base_pred = te["department_name_code"].map(dept_mean).fillna(tr["target_pct"].mean())
    base = mean_absolute_error(te["target_pct"], base_pred)

    solo = mean_absolute_error(te["target_pct"], model().fit(tr[FEATURES], tr["target_pct"]).predict(te[FEATURES]))
    pool_mae = mean_absolute_error(te["target_pct"], pooled.predict(te[POOLED_FEATURES]))
    bal_mae = mean_absolute_error(te["target_pct"], pooled_bal.predict(te[POOLED_FEATURES]))

    best = min([("per-country", solo), ("pooled", pool_mae), ("pooled-bal", bal_mae)], key=lambda x: x[1])
    print(f"{country:<9}{base:>10.4f}{solo:>13.4f}{pool_mae:>9.4f}{bal_mae:>12.4f}   {best[0]:<12}")
