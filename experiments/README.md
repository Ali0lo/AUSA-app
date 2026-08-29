# Experiments

Throwaway-but-kept probes that produced the numbers quoted in the ADRs and in
[`../docs/PROJECT-STATE.md`](../docs/PROJECT-STATE.md). They are **not** part of the
serving path and nothing imports them. They are here so a claim in a document can be
re-run rather than taken on trust.

Run from the repository root, with the data collected (see [`../data/README.md`](../data/README.md)):

| Script | Answers | Result |
|---|---|---|
| `quantile_and_catboost_probe.py` | Does CatBoost beat HistGradientBoosting? Can quantile regression give an honest success rate? | CatBoost **+25.1%** over HGB. Quantiles are **6–7 points over-optimistic** and cross — bands only until recalibrated. See PROJECT-STATE §9.3 |
| `pooled_vs_percountry_probe.py` | Can one model with `country` as a feature replace per-country models? | Per-country wins 2 of 3. ADR-0002 holds. Now also runs inside `train_cutoff_models.py` |
| `verify_vs_dim_pdf.py` | Does sec.az agree with the official DİM journal? | BANM İnformasiya təhlükəsizliyi 2025 = **681.0 in both**. See `data-collection-plan.md` §2b |

`quantile_and_catboost_probe.py` needs `catboost`, which is not in
`backend/requirements.txt` — CatBoost is a *proposal* (PROJECT-STATE §9.8 item 7), not an
adopted dependency. Install it ad hoc to re-run:

```bash
pip install catboost
python experiments/quantile_and_catboost_probe.py     # several minutes
```
