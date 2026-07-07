import itertools
import pandas as pd
from pathlib import Path

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
OUTPUT_FILE = ROOT / "01_data" / "candidates" / "permutation_candidates.csv"

# Base dopant sets
LI_SITE  = {'Al': 3, 'Fe': 3, 'Ga': 3}
ZR_SITE  = {'Nb': 5, 'Ta': 5, 'Sb': 5, 'W': 6}

X_VALS = [0.10, 0.15, 0.20, 0.25, 0.30]
Y_VALS = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50]

candidates = []

for (li_el, li_charge), (zr_el, zr_charge) in itertools.product(
        LI_SITE.items(), ZR_SITE.items()):
    for x, y in itertools.product(X_VALS, Y_VALS):

        # Charge balance: full formula
        # Li_pfu + x*li_charge + 3*3 + (2-y)*4 + y*zr_charge = 24
        li_pfu = 24.0 - x * li_charge - 9.0 - (2 - y) * 4.0 - y * zr_charge

        if not (6.1 <= li_pfu <= 6.8):
            continue

        # Charge balance check
        charge = (li_pfu * 1 + x * li_charge + 3 * 3
                  + (2 - y) * 4 + y * zr_charge + 12 * (-2))
        if abs(charge) > 0.01:
            continue

        formula = (f"Li{li_pfu:.3f}{li_el}{x:.2f}"
                   f"La3Zr{2-y:.2f}{zr_el}{y:.2f}O12")

        candidates.append({
            'Formula': formula,
            'Li_pfu': round(li_pfu, 3),
            'Li_site_dopant': li_el,
            'Li_site_amount': x,
            'Zr_site_dopant': zr_el,
            'Zr_site_amount': y,
            'charge_check': round(charge, 4)
        })

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df = pd.DataFrame(candidates)
print(f"Valid candidates: {len(df)}")
df.to_csv(OUTPUT_FILE, index=False)
print(f"Saved: {OUTPUT_FILE}")
