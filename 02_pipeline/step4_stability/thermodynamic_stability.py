import pandas as pd
from pathlib import Path
from pymatgen.core import Structure
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.ext.matproj import MPRester
import os
from tqdm import tqdm

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
CANDIDATES_FILE  = ROOT / "01_data" / "candidates" / "top_50_screened_candidates.csv"
EVALUATED_FILE   = ROOT / "01_data" / "results"    / "evaluated_top_candidates.csv"
RELAXED_DIR      = ROOT / "03_structures" / "relaxed"
OUTPUT_FILE      = ROOT / "01_data" / "results"    / "thermodynamic_stability.csv"

MP_API_KEY = os.environ.get("MP_API_KEY", None)


def get_e_above_hull(structure: Structure) -> float:
    """
    Calculates the energy above the convex hull for a given structure using
    the Materials Project phase diagram.

    Args:
        structure (Structure): A pymatgen Structure with .energy attribute set.

    Returns:
        float: Energy above hull in eV/atom. Returns float('inf') on error.
    """
    if not MP_API_KEY:
        raise ValueError("MP_API_KEY environment variable not set.")

    with MPRester(MP_API_KEY) as mpr:
        try:
            chemsys = list(structure.composition.as_dict().keys())
            entries = mpr.get_entries_in_chemsys(chemsys)

            if not entries:
                print(f"  Warning: No MP entries found for {structure.composition.reduced_formula}")
                return float('inf')

            pd_obj = PhaseDiagram(entries)

            from pymatgen.entries.computed_entries import ComputedEntry
            our_entry = ComputedEntry(
                composition=structure.composition,
                energy=structure.energy,
                entry_id=structure.composition.reduced_formula
            )

            e_above_hull = pd_obj.get_e_above_hull(our_entry)
            return e_above_hull

        except Exception as e:
            print(f"  Error for {structure.composition.reduced_formula}: {e}")
            return float('inf')


def main():
    """
    Calculates thermodynamic stability (e_above_hull) for the top candidates.

    FIX: All paths now use ROOT-relative pathlib.
    FIX: 'pd' variable name collision with pandas → renamed to 'pd_obj' inside get_e_above_hull.
    """
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not CANDIDATES_FILE.exists():
        print(f"Error: Candidates file not found at {CANDIDATES_FILE}")
        print("  Run compositional_screening.py first.")
        return

    if not MP_API_KEY:
        print("Error: MP_API_KEY environment variable not found.")
        print("  Set it with: $env:MP_API_KEY = 'your_key_here'")
        pd.DataFrame(columns=['formula', 'e_above_hull_eV_atom']).to_csv(OUTPUT_FILE, index=False)
        print(f"Created placeholder output: {OUTPUT_FILE}")
        return

    top_candidates_df = pd.read_csv(CANDIDATES_FILE)
    f_col = 'formula' if 'formula' in top_candidates_df.columns else 'Formula'

    # Load evaluated candidates for total energy
    evaluated_df = None
    if EVALUATED_FILE.exists():
        evaluated_df = pd.read_csv(EVALUATED_FILE, index_col='formula')

    results = []
    print("Calculating Energy Above Hull for top candidates...")
    for _, row in tqdm(top_candidates_df.iterrows(), total=len(top_candidates_df),
                       desc="Checking Thermo Stability"):
        formula  = row[f_col]
        cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"

        if not cif_path.exists():
            print(f"  Warning: CIF not found for {formula}. Skipping.")
            continue

        try:
            relaxed_structure = Structure.from_file(str(cif_path))

            if evaluated_df is not None and formula in evaluated_df.index:
                n_atoms       = len(relaxed_structure)
                e_per_atom    = evaluated_df.loc[formula, 'relaxed_energy_per_atom']
                relaxed_structure.energy = e_per_atom * n_atoms
            else:
                print(f"  Warning: {formula} not in evaluated file. Skipping hull calc.")
                continue

            e_hull = get_e_above_hull(relaxed_structure)
            results.append({'formula': formula, 'e_above_hull_eV_atom': e_hull})

        except Exception as e:
            print(f"  Failed to process {formula}: {e}")
            results.append({'formula': formula, 'e_above_hull_eV_atom': float('inf')})

    stability_df = pd.DataFrame(results)
    stability_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nThermodynamic stability check complete. Results saved to: {OUTPUT_FILE}")
    if not stability_df.empty:
        print("Candidates sorted by stability (lower is better):")
        print(stability_df.sort_values('e_above_hull_eV_atom').head())


if __name__ == '__main__':
    main()
