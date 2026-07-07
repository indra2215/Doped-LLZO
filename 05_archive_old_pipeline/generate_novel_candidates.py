import itertools
import pandas as pd

# Base dopant sets — no rare earth, no Zn, no Ti
LI_SITE  = {'Al': 3, 'Fe': 3, 'Ga': 3}
ZR_SITE  = {'Nb': 5, 'Ta': 5, 'Sb': 5, 'W': 6}
LA_SITE  = {'Sr': 2, 'Ba': 2, 'Ca': 2}  # optional third site

# Ratio ranges
X_VALS = [0.10, 0.15, 0.20, 0.25, 0.30]   # Li-site
Y_VALS = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50]  # Zr-site

candidates = []

for (li_el, li_charge), (zr_el, zr_charge) in itertools.product(
        LI_SITE.items(), ZR_SITE.items()):
    for x, y in itertools.product(X_VALS, Y_VALS):

        # Charge balance: Li_pfu depends on both sites
        # Li-site trivalent removes 3x−x = 2x Li equivalents per formula
        # Zr-site pentavalent (charge-x_zr) adds (zr_charge-4)*y Li
        donor = (zr_charge - 4) * y        # extra positive charge from Zr-site
        li_pfu = 7.0 - (li_charge - 1)*x + donor

        # Hard filters
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

df = pd.DataFrame(candidates)
print(f"Valid candidates: {len(df)}")
df.to_csv('permutation_candidates.csv', index=False)
