"""Can a tree model give an HONEST success rate?

P(admit) is unlearnable -- no labels. But P(next year's cutoff <= your score) is
learnable from cutoff variance, and for threshold-admission countries clearing the
cutoff IS admission. So that probability is the success rate, not a proxy for it.

Method: quantile regression. Predict the 10th..90th percentile of the cutoff instead of
a point. A student's score position in that predicted distribution is their success rate.

The test that matters is CALIBRATION: of the actual 2024 cutoffs, does ~10% really fall
below the predicted 10th percentile, ~50% below the 50th, and so on? If the empirical
coverage tracks the nominal quantile, the success rate we show is trustworthy. If it
doesn't, we must not show a number at all.

Also compares CatBoost, which handles high-cardinality categoricals natively instead of
via the arbitrary ordinal codes .cat.codes imposes.
"""

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupShuffleSplit

QUANTILES = [0.1, 0.25, 0.5, 0.75, 0.9]
CATS = ["university_name", "university_type", "city", "faculty_name",
        "department_name", "score_type", "scholarship_type"]
FEATURES = CATS + ["total_quota", "intake_year"]

df = pd.read_csv("data/processed/turkey_cutoff_history.csv").dropna(subset=["cutoff_value"])
for c in CATS:
    df[c] = df[c].fillna("unknown").astype(str)
df["total_quota"] = df["total_quota"].fillna(df["total_quota"].median())

# Cold start: whole programmes held out. This is what ships.
splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
tr_idx, te_idx = next(splitter.split(df, groups=df["source_program_code"]))
train, test = df.iloc[tr_idx], df.iloc[te_idx]
y_te = test["cutoff_value"].to_numpy()
print(f"train {len(train):,} / test {len(test):,} rows "
      f"({test.source_program_code.nunique():,} unseen programmes)\n")

# ---------------------------------------------------------------- point estimates
codes = {c: {v: i for i, v in enumerate(pd.concat([train[c], test[c]]).unique())} for c in CATS}
tr_enc = train[FEATURES].assign(**{c: train[c].map(codes[c]) for c in CATS})
te_enc = test[FEATURES].assign(**{c: test[c].map(codes[c]) for c in CATS})

hgb = HistGradientBoostingRegressor(max_iter=500, learning_rate=0.06, random_state=42)
hgb.fit(tr_enc, train["cutoff_value"])
mae_hgb = mean_absolute_error(y_te, hgb.predict(te_enc))

cat_idx = [FEATURES.index(c) for c in CATS]
cb = CatBoostRegressor(iterations=1200, learning_rate=0.06, depth=8,
                       verbose=0, random_seed=42)
cb.fit(Pool(train[FEATURES], train["cutoff_value"], cat_features=cat_idx))
mae_cb = mean_absolute_error(y_te, cb.predict(Pool(test[FEATURES], cat_features=cat_idx)))

dept_mean = train.groupby("department_name")["cutoff_value"].mean()
base = mean_absolute_error(
    y_te, test["department_name"].map(dept_mean).fillna(train["cutoff_value"].mean()))

print("POINT ESTIMATE (cold start, MAE)")
print(f"  baseline department-mean      {base:8.4f}")
print(f"  HistGradientBoosting (codes)  {mae_hgb:8.4f}   {(base-mae_hgb)/base*100:+.1f}%")
print(f"  CatBoost (native categoricals){mae_cb:8.4f}   {(base-mae_cb)/base*100:+.1f}%")
print(f"  -> CatBoost is {(mae_hgb-mae_cb)/mae_hgb*100:+.1f}% vs HGB\n")

# ------------------------------------------------------------ quantile calibration
print("QUANTILE CALIBRATION -- does the predicted spread mean what it claims?")
print(f"  {'nominal':>9}{'empirical':>11}{'error':>9}   (want empirical ~= nominal)")
preds = {}
for q in QUANTILES:
    m = CatBoostRegressor(iterations=800, learning_rate=0.06, depth=8, verbose=0,
                          random_seed=42, loss_function=f"Quantile:alpha={q}")
    m.fit(Pool(train[FEATURES], train["cutoff_value"], cat_features=cat_idx))
    p = m.predict(Pool(test[FEATURES], cat_features=cat_idx))
    preds[q] = p
    empirical = float((y_te <= p).mean())
    print(f"  {q:>9.2f}{empirical:>11.3f}{empirical - q:>+9.3f}")

# ------------------------------------------------- what a student would actually see
print("\nWORKED EXAMPLE -- success rate read off the predicted distribution")
grid = np.column_stack([preds[q] for q in QUANTILES])
for i in (0, 1, 2):
    row = test.iloc[i]
    qs = grid[i]
    actual = y_te[i]
    print(f"\n  {row.department_name[:38]} @ {row.university_name[:30]}")
    print("    predicted cutoff  " + "  ".join(
        f"p{int(q*100)}={v:6.1f}" for q, v in zip(QUANTILES, qs)))
    print(f"    ACTUAL 2024 cutoff = {actual:.1f}")
    for score in (qs[0] - 20, qs[2], qs[4] + 20):
        rate = float(np.interp(score, qs, QUANTILES))
        band = "REACH" if rate < 0.35 else ("MATCH" if rate < 0.75 else "SAFE")
        print(f"    student scoring {score:6.1f} -> clears cutoff ~{rate:4.0%} of the time  [{band}]")
