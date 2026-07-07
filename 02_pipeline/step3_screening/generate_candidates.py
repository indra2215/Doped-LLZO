import itertools
import random
import csv
import numpy as np
from pathlib import Path

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
OUTPUT_FILE = ROOT / "01_data" / "candidates" / "bayesian_virtual_candidates.csv"


def generate_virtual_library(num_candidates=20000):
    """
    Generates a virtual library of charge-balanced, physically plausible
    doped-LLZO candidates based on literature and cost-performance analysis.

    FIX: Output now routes to 01_data/candidates/ instead of script directory.
    """
    print('Generating cost-aware, charge-balanced LLZO Combinatorial Library...')
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Cost-Performance Sweet Spot (Higher probability of selection)
    dopants_sweet_spot = {
        'li_site': {'Al': 3, 'Mg': 2},
        'la_site': {'Sr': 2, 'Y': 3},
        'zr_site': {'Nb': 5, 'W': 6}
    }
    # High-Performance / High-Cost (Lower probability of selection)
    dopants_high_perf = {
        'li_site': {'Ga': 3},
        'la_site': {'Gd': 3, 'Ca': 2, 'Ba': 2},
        'zr_site': {'Ta': 5, 'Te': 6, 'Sb': 5, 'Hf': 4}
    }

    z_ranges = np.round(np.arange(0.0, 0.3, 0.05), 2)
    x_ranges = np.round(np.arange(0.0, 0.5, 0.05), 2)
    y_ranges = np.round(np.arange(0.0, 1.0, 0.05), 2)

    candidates = set()
    attempts = 0
    max_attempts = num_candidates * 150

    while len(candidates) < num_candidates and attempts < max_attempts:
        attempts += 1

        if random.random() < 0.75:
            dopant_pool = dopants_sweet_spot
        else:
            dopant_pool = dopants_high_perf

        li_dop = random.choice(list(dopant_pool['li_site'].keys()))
        v_li_sub = dopant_pool['li_site'][li_dop]
        z = random.choice(z_ranges) if li_dop else 0

        la_dop = random.choice(list(dopant_pool['la_site'].keys()))
        v_la = dopant_pool['la_site'][la_dop]
        x = random.choice(x_ranges) if la_dop else 0

        zr_dop = random.choice(list(dopant_pool['zr_site'].keys()))
        v_zr = dopant_pool['zr_site'][zr_dop]
        y = random.choice(y_ranges) if zr_dop else 0

        la_charge = (3 - x) * 3 + x * v_la
        zr_charge = (2 - y) * 4 + y * v_zr
        li_dop_charge = z * v_li_sub

        li_ion_charge_needed = 24.0 - la_charge - zr_charge - li_dop_charge
        n_li_actual = np.round(li_ion_charge_needed, 3)

        total_li_pfu = n_li_actual + z
        if 6.0 <= total_li_pfu <= 7.0 and n_li_actual > 0:
            parts = {
                'Li': n_li_actual,
                li_dop: z,
                'La': 3 - x,
                la_dop: x,
                'Zr': 2 - y,
                zr_dop: y,
                'O': 12
            }
            formula = "".join([f"{el}{round(val, 2)}" for el, val in parts.items() if val > 0.01])
            candidates.add(formula)

    print(f'Successfully generated {len(candidates)} charge-balanced candidates.')

    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['formula'])
        for c in sorted(list(candidates)):
            writer.writerow([c])

    print(f'Saved candidate space to {OUTPUT_FILE}.')


if __name__ == '__main__':
    generate_virtual_library(num_candidates=20000)