import itertools
import random
import csv
import numpy as np
from pathlib import Path

def generate_virtual_library(num_candidates=20000):
    """
    Generates a virtual library of charge-balanced, physically plausible
    doped-LLZO candidates based on literature and cost-performance analysis.
    """
    print('Generating cost-aware, charge-balanced LLZO Combinatorial Library...')
    CWD = Path(__file__).parent
    OUTPUT_FILE = CWD / 'bayesian_virtual_candidates.csv'

    # --- Dopant Categories based on User Feedback (Cost & Performance) ---
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

    # Allowed fractional ranges for substitution
    # Smaller steps for more granular exploration
    z_ranges = np.round(np.arange(0.0, 0.3, 0.05), 2)  # Li-site substitution
    x_ranges = np.round(np.arange(0.0, 0.5, 0.05), 2)  # La-site substitution
    y_ranges = np.round(np.arange(0.0, 1.0, 0.05), 2)  # Zr-site substitution

    candidates = set()
    attempts = 0
    max_attempts = num_candidates * 150 # Increased attempts for stricter constraints

    while len(candidates) < num_candidates and attempts < max_attempts:
        attempts += 1

        # --- Weighted Dopant Selection ---
        # 75% chance to select from the 'sweet spot' list, 25% from 'high performance'
        if random.random() < 0.75:
            dopant_pool = dopants_sweet_spot
        else:
            dopant_pool = dopants_high_perf

        # Select one dopant for each site from the chosen pool
        li_dop = random.choice(list(dopant_pool['li_site'].keys()))
        v_li_sub = dopant_pool['li_site'][li_dop]
        z = random.choice(z_ranges) if li_dop else 0

        la_dop = random.choice(list(dopant_pool['la_site'].keys()))
        v_la = dopant_pool['la_site'][la_dop]
        x = random.choice(x_ranges) if la_dop else 0

        zr_dop = random.choice(list(dopant_pool['zr_site'].keys()))
        v_zr = dopant_pool['zr_site'][zr_dop]
        y = random.choice(y_ranges) if zr_dop else 0

        # --- Charge Balance Calculation (Aliovalent Substitution) ---
        # Baseline charge of the LLZO unit cell is 24 (Li7La3Zr2O12 -> 7*+1 + 3*+3 + 2*+4 = 24)
        # We calculate the charge from dopants and then determine the Li content needed for neutrality.
        la_charge = (3 - x) * 3 + x * v_la
        zr_charge = (2 - y) * 4 + y * v_zr
        li_dop_charge = z * v_li_sub

        # Total Li+ charge needed to balance the system
        li_ion_charge_needed = 24.0 - la_charge - zr_charge - li_dop_charge

        # The number of Li ions is equal to the charge they must provide (since Li is +1)
        n_li_actual = np.round(li_ion_charge_needed, 3)

        # --- Physical Constraints (from literature) ---
        # 1. Total Li content (ions + dopants on Li sites) must be in the optimal range for cubic phase stability.
        # 2. The number of Li ions must be positive.
        total_li_pfu = n_li_actual + z
        if 6.0 <= total_li_pfu <= 7.0 and n_li_actual > 0:
            
            # --- Build Formula String ---
            # Use a dictionary to handle zero-value components gracefully
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

    print(f'Successfully generated {len(candidates)} charge-balanced, cost-optimized candidates.')

    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['formula'])
        for c in sorted(list(candidates)): # Sort for deterministic output
            writer.writerow([c])

    print(f'Saved candidate space to {OUTPUT_FILE}.')

if __name__ == '__main__':
    generate_virtual_library(num_candidates=20000)