"""Cross-check sec.az figures against the official DIM journal (n12-2025, page 210-211).

The journal names specific specialties and their `minimal bal` in prose. If sec.az
agrees with DIM on these, sec.az is trustworthy as a compilation.
"""
import pandas as pd

# Quoted verbatim from n12-2025.pdf pages 210-211 (Cedvel 1.64 and surrounding text).
CLAIMS = [
    ("BANM", "İnformasiya təhlükəsizliyi", 2025, 681.0),
    ("ADA", "Dizayn", 2025, 237.1),
]

df = pd.read_csv("data/processed/azerbaijan_cutoff_history.csv")

for uni, spec, year, official in CLAIMS:
    rows = df[
        (df.university_name.str.contains(uni, case=False, na=False))
        & (df.department_name.str.contains(spec, case=False, na=False))
        & (df.intake_year == year)
    ]
    print(f"\nDIM journal says: {uni} / {spec} / {year} = {official}")
    if rows.empty:
        print("  sec.az: NO MATCHING ROW")
        continue
    for _, r in rows.iterrows():
        delta = r.cutoff_value - official
        mark = "EXACT MATCH" if abs(delta) < 0.05 else f"differs by {delta:+.1f}"
        print(f"  sec.az: {r.cutoff_value:7.1f}  [{r.department_name}]  {mark}")
