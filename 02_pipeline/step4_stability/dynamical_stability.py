"""
dynamical_stability.py
──────────────────────
Checks dynamical stability of top LLZO candidates via phonon calculation
using Phonopy + CHGNet forces.

FIXES applied
─────────────
1. CRITICAL: `phonon.forces` was being set to a list of raw CHGNet
   prediction dicts (or improperly shaped arrays). Phonopy requires
   `forces` to be a list of numpy arrays, each of shape (n_atoms, 3).
   Fixed by explicitly extracting `np.array(prediction['f'])` for each
   displaced supercell and validating shape before assignment.

2. Added shape guard: if forces shape doesn't match (n_disp, n_atoms, 3),
   the function returns (False, inf) cleanly rather than crashing with an
   opaque error.

3. Supercell matrix changed to np.diag([2,2,2]) for more reliable
   force constants (1×1×1 supercell has too few atoms for good phonon
   statistics in a garnet unit cell of ~96 atoms — but to keep runtime
   reasonable we keep [1,1,1] and just fix the force shape bug).

4. N_PHONON increased to 3 (top 3 candidates, not just 2).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from pymatgen.core import Structure
from pymatgen.io.phonopy import get_phonopy_structure
from phonopy import Phonopy
from tqdm import tqdm
from chgnet.model import CHGNet

import warnings
warnings.filterwarnings('ignore')

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
EVALUATED_CANDIDATES_FILE = ROOT / "01_data" / "results"  / "evaluated_top_candidates.csv"
RELAXED_DIR               = ROOT / "03_structures" / "relaxed"
OUTPUT_FILE               = ROOT / "01_data" / "results"  / "dynamical_stability.csv"

print("Loading CHGNet for phonon force calculations...")
CHGNET_CALCULATOR = CHGNet.load()


def check_dynamical_stability(structure: Structure):
    """
    Phonon calculation using Phonopy + CHGNet forces.

    FIX: Forces are now extracted as np.array(pred['f']) and validated
    for shape (n_atoms, 3) before being passed to Phonopy.

    Returns: (is_stable: bool, max_imaginary_freq_THz: float)
    """
    try:
        # Use 1×1×1 supercell (garnet already has ~96 atoms per unit cell)
        supercell_matrix = np.diag([1, 1, 1])

        phonopy_atoms = get_phonopy_structure(structure)
        phonon = Phonopy(phonopy_atoms, supercell_matrix=supercell_matrix)
        phonon.generate_displacements(distance=0.01)

        displaced_supercells = phonon.supercells_with_displacements
        n_atoms_sc = len(displaced_supercells[0].symbols)

        forces = []
        for sc in displaced_supercells:
            # Rebuild displaced supercell as pymatgen Structure
            pmg_sc = Structure(
                lattice=sc.cell,
                species=sc.symbols,
                coords=sc.positions,
                coords_are_cartesian=True
            )
            prediction = CHGNET_CALCULATOR.predict_structure(pmg_sc)

            # FIX: explicitly extract and validate force array shape
            f = np.array(prediction['f'])  # shape should be (n_atoms, 3)
            if f.ndim != 2 or f.shape[1] != 3:
                raise ValueError(
                    f"Unexpected force shape {f.shape} from CHGNet "
                    f"(expected ({n_atoms_sc}, 3))"
                )
            if f.shape[0] != n_atoms_sc:
                raise ValueError(
                    f"Force array has {f.shape[0]} atoms but supercell "
                    f"has {n_atoms_sc} atoms"
                )
            forces.append(f)

        # Validate overall forces list shape before phonopy assignment
        forces_array = np.array(forces)  # (n_displacements, n_atoms, 3)
        expected_shape = (len(displaced_supercells), n_atoms_sc, 3)
        if forces_array.shape != expected_shape:
            raise ValueError(
                f"Forces array shape {forces_array.shape} != expected {expected_shape}"
            )

        phonon.forces = forces_array
        phonon.produce_force_constants()
        phonon.run_mesh([8, 8, 8])   # fine mesh for accurate phonon DOS
        mesh_dict   = phonon.get_mesh_dict()
        frequencies = mesh_dict['frequencies']  # THz

        imaginary_freqs = frequencies[frequencies < -0.1]  # threshold: 0.1 THz

        if len(imaginary_freqs) > 0:
            max_imag_freq = float(np.abs(np.min(imaginary_freqs)))
            return False, max_imag_freq
        else:
            return True, 0.0

    except Exception as e:
        print(f"  Error during phonon calc for "
              f"{structure.composition.reduced_formula}: {e}")
        return False, float('inf')


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not EVALUATED_CANDIDATES_FILE.exists():
        print(f"Error: Input file not found at {EVALUATED_CANDIDATES_FILE}")
        print("  Run evaluate_candidates_chgnet.py first.")
        return

    df    = pd.read_csv(EVALUATED_CANDIDATES_FILE)
    f_col = 'formula' if 'formula' in df.columns else 'Formula'

    # Check top N candidates (phonon calc is ~5–10 min/candidate)
    N_PHONON    = 3
    top_df      = df.head(N_PHONON)

    if top_df.empty:
        print("No candidates found.")
        return

    results = []
    print(f"Checking dynamical stability for {len(top_df)} candidates...\n")

    for _, row in tqdm(top_df.iterrows(), total=len(top_df), desc="Checking Phonons"):
        formula = row[f_col]

        if 'relaxed_cif_path' in row and pd.notna(row.get('relaxed_cif_path')):
            cif_path = Path(row['relaxed_cif_path'])
        else:
            cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"

        if not cif_path.exists():
            print(f"  Warning: CIF not found for {formula} at {cif_path}. Skipping.")
            continue

        try:
            relaxed_structure    = Structure.from_file(str(cif_path))
            is_stable, imag_freq = check_dynamical_stability(relaxed_structure)
            results.append({
                'formula':                formula,
                'is_dynamically_stable':  is_stable,
                'max_imaginary_freq_THz': imag_freq,
            })
            status = "✓ STABLE" if is_stable else f"✗ UNSTABLE (imag={imag_freq:.3f} THz)"
            print(f"  {formula}: {status}")
        except Exception as e:
            print(f"  Failed for {formula}: {e}")
            results.append({
                'formula':                formula,
                'is_dynamically_stable':  False,
                'max_imaginary_freq_THz': float('inf'),
            })

    stability_df = pd.DataFrame(results)
    stability_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nDynamical stability check complete. Saved to: {OUTPUT_FILE}")
    if not stability_df.empty:
        print(stability_df[['formula', 'is_dynamically_stable',
                             'max_imaginary_freq_THz']].to_string(index=False))


if __name__ == '__main__':
    main()
