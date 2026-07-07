import itertools
import pandas as pd
from pathlib import Path

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
OUTPUT_FILE = ROOT / "01_data" / "candidates" / "permutation_candidates.csv"

LI_SITE = {"Al": 3, "Fe": 3, "Ga": 3}
ZR_SITE = {"Nb": 5, "Ta": 5, "Sb": 5, "W": 6}
X_VALS  = [0.10, 0.15, 0.20, 0.25, 0.30]
Y_VALS  = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50]

candidates = []

for (li_el, li_c), (zr_el, zr_c) in itertools.product(LI_SITE.items(), ZR_SITE.items()):
    for x, y in itertools.product(X_VALS, Y_VALS):

        # CORRECT charge-balance formula
        # Neutrality: li_pfu + x*li_c + 9 + (2-y)*4 + y*zr_c - 24 = 0
        li_pfu = 24.0 - x * li_c - 9.0 - (2 - y) * 4.0 - y * zr_c

        if not (6.1 <= li_pfu <= 6.8):
            continue

        chk = li_pfu + x * li_c + 9.0 + (2 - y) * 4.0 + y * zr_c - 24.0
        if abs(chk) > 0.001:
            continue

        # Concentration caps from literature
        if li_el == "Fe" and x > 0.20:   continue
        if li_el == "Ga" and x > 0.25:   continue
        if zr_el == "Sb" and y > 0.40:   continue

        formula = (f"Li{li_pfu:.3f}{li_el}{x:.2f}"
                   f"La3Zr{2 - y:.2f}{zr_el}{y:.2f}O12")

        candidates.append({
            "Formula":        formula,
            "Li_pfu":         round(li_pfu, 3),
            "Li_site_dopant": li_el,
            "Li_site_amount": x,
            "Zr_site_dopant": zr_el,
            "Zr_site_amount": y,
            "base_type":      f"{li_el}+{zr_el}",
            "charge_check":   round(chk, 6),
        })

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df = pd.DataFrame(candidates)
df.to_csv(OUTPUT_FILE, index=False)

print(f"Valid candidates: {len(df)}")
print(f"Saved: {OUTPUT_FILE}")
print()
print(df["base_type"].value_counts().to_string())
print()
print("Li_pfu range:", df["Li_pfu"].min(), "to", df["Li_pfu"].max())
