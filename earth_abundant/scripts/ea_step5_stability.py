"""
ea_step5_stability.py
==============================================================================
EARTH-ABUNDANT PIPELINE — Step 5: Thermodynamic Stability
==============================================================================

Calculates the energy above the convex hull (e_above_hull) for the top
thermally stable EA candidates using the Materials Project phase diagram.

Input  : earth_abundant/data/results/ea_validated_candidates.csv
         (must contain 'delta_E_vs_LLZO' and 'thermal_stability' columns
          produced by ea_step4_validate.py)
Output : earth_abundant/data/results/ea_thermodynamic_stability.csv

Requires
--------
  $env:MP_API_KEY = "your_materials_project_api_key"

Selection
---------
  Only candidates with delta_E_vs_LLZO < 0 (thermally stable, more stable
  than pure LLZO) are submitted to the hull calculation to save API calls.
"""

import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Structure

warnings.filterwarnings("ignore")

# -- Paths ----------------------------------------------------------------------
EA_ROOT       = Path(__file__).parent.parent
VALIDATED_CSV = EA_ROOT / "data" / "results" / "ea_validated_candidates.csv"
STRUCTURES    = EA_ROOT / "structures"
OUTPUT_CSV    = EA_ROOT / "data" / "results" / "ea_thermodynamic_stability.csv"

MP_API_KEY = os.environ.get("MP_API_KEY", None)


def get_e_above_hull(structure: Structure, api_key: str) -> float:
    """
    Queries Materials Project for the phase diagram of the composition's
    chemical system and returns energy above convex hull (eV/atom).
    Returns float('inf') on any failure.
    """
    try:
        from pymatgen.ext.matproj import MPRester
        from pymatgen.analysis.phase_diagram import PhaseDiagram
        from pymatgen.entries.computed_entries import ComputedEntry

        with MPRester(api_key) as mpr:
            chemsys = list(structure.composition.as_dict().keys())
            entries = mpr.get_entries_in_chemsys(chemsys)
            if not entries:
                print(f"    No MP entries for {structure.composition.reduced_formula}")
                return float('inf')

            pd_obj = PhaseDiagram(entries)
            our_entry = ComputedEntry(
                composition=structure.composition,
                energy=structure.energy,
                entry_id=structure.composition.reduced_formula
            )
            return pd_obj.get_e_above_hull(our_entry)

    except Exception as e:
        print(f"    Hull calculation failed: {e}")
        return float('inf')


def main():
    print("=" * 65)
    print("EA PIPELINE — Step 5: Thermodynamic Stability")
    print("=" * 65)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    if not VALIDATED_CSV.exists():
        print(f"ERROR: {VALIDATED_CSV} not found.")
        print("  Run ea_step4_validate.py first.")
        return

    if not MP_API_KEY:
        print("ERROR: MP_API_KEY environment variable not set.")
        print("  Set it with: $env:MP_API_KEY = 'your_key_here'")
        pd.DataFrame(columns=['formula', 'e_above_hull_eV_atom',
                               'delta_E_vs_LLZO', 'thermal_stability']).to_csv(OUTPUT_CSV, index=False)
        print(f"Created placeholder: {OUTPUT_CSV}")
        return

    df = pd.read_csv(VALIDATED_CSV)

    # Select only thermally stable candidates (delta_E < 0 = more stable than LLZO)
    stable_mask = df['delta_E_vs_LLZO'] < 0 if 'delta_E_vs_LLZO' in df.columns else pd.Series([True] * len(df))
    stable_df = df[stable_mask].copy().reset_index(drop=True)
    print(f"Candidates: {len(df)} total, {len(stable_df)} thermally stable (ΔE < 0) -> submitting to hull check")

    results = []
    for _, row in stable_df.iterrows():
        formula = row['formula']
        cif_path = STRUCTURES / f"{formula}.cif"
        print(f"\n  {formula}")

        if not cif_path.exists():
            print(f"    CIF not found at {cif_path} — skipping")
            continue

        try:
            struct = Structure.from_file(str(cif_path))
            # Attach CHGNet energy if available
            e_col = 'chgnet_eval_E_per_atom' if 'chgnet_eval_E_per_atom' in row else 'chgnet_static_E_per_atom'
            if e_col in row and not pd.isna(row[e_col]):
                struct.energy = float(row[e_col]) * len(struct)
            else:
                print(f"    No energy column found — skipping hull calc")
                continue

            e_hull = get_e_above_hull(struct, MP_API_KEY)
            tag    = "PASS STABLE" if e_hull < 0.05 else ("WARN MARGINAL" if e_hull < 0.1 else "FAIL UNSTABLE")
            print(f"    e_above_hull = {e_hull:.4f} eV/atom  {tag}")

            results.append({
                'formula':             formula,
                'pair':                row.get('pair', ''),
                'Li_pfu':              row.get('Li_pfu', ''),
                'delta_E_vs_LLZO':     row.get('delta_E_vs_LLZO', ''),
                'thermal_stability':   row.get('thermal_stability', ''),
                'e_above_hull_eV_atom': e_hull,
                'hull_status':         tag,
                'is_novel':            row.get('is_novel', ''),
            })

        except Exception as e:
            print(f"    Failed: {e}")
            results.append({'formula': formula, 'e_above_hull_eV_atom': float('inf')})

    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nThermodynamic stability complete. Saved to: {OUTPUT_CSV}")

    if not out_df.empty and 'e_above_hull_eV_atom' in out_df.columns:
        print("\nTop candidates by hull stability (lower = better):")
        print(out_df.sort_values('e_above_hull_eV_atom')
              [['formula', 'e_above_hull_eV_atom', 'delta_E_vs_LLZO', 'hull_status']]
              .head(10).to_string(index=False))


if __name__ == '__main__':
    main()

