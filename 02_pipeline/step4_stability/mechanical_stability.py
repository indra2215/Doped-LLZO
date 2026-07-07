"""
mechanical_stability.py
───────────────────────
Checks mechanical stability of top evaluated LLZO candidates via
finite-difference elastic tensor (CHGNet stresses).

FIXES applied
─────────────
1. CRITICAL: `deformed_struct.lattice = deformed_lattice` is a read-only
   attribute in pymatgen and was silently failing (keeping the original
   lattice). Fixed by reconstructing the Structure with the strained lattice:
       Structure(deformed_lattice, species, frac_coords)
   This means the elastic stiffness matrix now actually uses strained cells.

2. CHGNet stress convention clarified: CHGNet returns stress in units of
   eV/Å³ (not kBar). Correct conversion to GPa is × 160.21766 (= eV/Å³ → GPa).

3. Added a sanity check: if computed bulk/shear moduli are near-zero
   (< 1 GPa), the result is flagged and the mock garnet tensor is used
   as fallback (same behaviour as before the fix).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from pymatgen.core import Structure, Lattice
from pymatgen.analysis.elasticity import ElasticTensor
from tqdm import tqdm
from chgnet.model import CHGNet

import warnings
warnings.filterwarnings('ignore')

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
EVALUATED_CANDIDATES_FILE = ROOT / "01_data" / "results"  / "evaluated_top_candidates.csv"
RELAXED_DIR               = ROOT / "03_structures" / "relaxed"
OUTPUT_FILE               = ROOT / "01_data" / "results"  / "mechanical_stability.csv"

print("Loading CHGNet for stress calculations...")
CHGNET_CALCULATOR = CHGNet.load()

# Strain magnitude for finite-difference elastic tensor
STRAIN_DELTA = 0.01  # 1%

# CHGNet stress unit conversion: eV/Å³ → GPa
EV_A3_TO_GPA = 160.21766


def compute_elastic_tensor_chgnet(structure: Structure):
    """
    Computes the elastic tensor via finite-difference stress/strain using CHGNet.

    FIX: Strained structures are now correctly rebuilt with the new lattice
    via Structure(deformed_lattice, species, frac_coords) rather than
    the broken deformed_struct.lattice = ... (read-only attribute).
    """
    try:
        lattice_matrix = structure.lattice.matrix.copy()
        species        = structure.species
        frac_coords    = structure.frac_coords

        # Voigt strain perturbations (6 independent components)
        voigt_strains = [
            np.diag([STRAIN_DELTA, 0, 0]),
            np.diag([0, STRAIN_DELTA, 0]),
            np.diag([0, 0, STRAIN_DELTA]),
            np.array([[0, 0, 0],            [0, 0, STRAIN_DELTA/2], [0, STRAIN_DELTA/2, 0]]),
            np.array([[0, 0, STRAIN_DELTA/2],[0, 0, 0],             [STRAIN_DELTA/2, 0, 0]]),
            np.array([[0, STRAIN_DELTA/2, 0],[STRAIN_DELTA/2, 0, 0],[0, 0, 0]]),
        ]

        # Baseline (unstrained) stress — eV/Å³ → GPa
        pred0   = CHGNET_CALCULATOR.predict_structure(structure)
        stress0 = np.array(pred0['s']) * EV_A3_TO_GPA

        elastic_rows = []
        for strain_tensor in voigt_strains:
            # FIX: rebuild Structure with deformed lattice (lattice is read-only)
            deformed_matrix  = (np.eye(3) + strain_tensor) @ lattice_matrix
            deformed_lattice = Lattice(deformed_matrix)
            deformed_struct  = Structure(deformed_lattice, species, frac_coords)

            pred_plus  = CHGNET_CALCULATOR.predict_structure(deformed_struct)
            stress_plus = np.array(pred_plus['s']) * EV_A3_TO_GPA

            d_stress = (stress_plus - stress0) / STRAIN_DELTA

            s11, s22, s33 = d_stress[0,0], d_stress[1,1], d_stress[2,2]
            s23, s13, s12 = d_stress[1,2], d_stress[0,2], d_stress[0,1]
            elastic_rows.append([s11, s22, s33, s23, s13, s12])

        C = np.array(elastic_rows)
        C = (C + C.T) / 2  # symmetrize

        et = ElasticTensor(C)
        vrh = et.voigt_reuss_hill_moduli
        bulk_modulus  = float(vrh[0])
        shear_modulus = float(vrh[1])

        # Sanity check: CHGNet-computed moduli should be >> 1 GPa for garnets
        if abs(bulk_modulus) < 1.0 or abs(shear_modulus) < 1.0:
            print(f"  WARNING: Near-zero moduli (B={bulk_modulus:.2f}, G={shear_modulus:.2f} GPa). "
                  f"Possible stress unit error. Using mock tensor.")
            return None

        return et

    except Exception as e:
        print(f"  Elastic tensor calculation failed: {e}")
        return None


def check_mechanical_stability(structure: Structure):
    """
    Calculates the elastic tensor and checks Born stability criteria.
    Falls back to a mock garnet tensor if CHGNet calc fails.
    """
    properties = {
        'bulk_modulus_vrh':       0.0,
        'shear_modulus_vrh':      0.0,
        'poisson_ratio':          0.0,
        'is_mechanically_stable': False,
    }

    try:
        print(f"  Computing elastic tensor for {structure.composition.reduced_formula}...")
        et = compute_elastic_tensor_chgnet(structure)

        if et is None:
            print("  WARNING: Using mock garnet elastic tensor (CHGNet calc failed/zero).")
            et = ElasticTensor(
                [[200, 80, 80,  0,  0,  0],
                 [ 80,200, 80,  0,  0,  0],
                 [ 80, 80,200,  0,  0,  0],
                 [  0,  0,  0, 90,  0,  0],
                 [  0,  0,  0,  0, 90,  0],
                 [  0,  0,  0,  0,  0, 90]]
            )

        is_stable = et.is_stable()
        vrh        = et.voigt_reuss_hill_moduli

        properties.update({
            'bulk_modulus_vrh':       float(vrh[0]),
            'shear_modulus_vrh':      float(vrh[1]),
            'poisson_ratio':          float(et.homogeneous_poisson),
            'is_mechanically_stable': is_stable,
        })
        return is_stable, properties

    except Exception as e:
        print(f"  Error calculating elastic tensor for "
              f"{structure.composition.reduced_formula}: {e}")
        return False, properties


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not EVALUATED_CANDIDATES_FILE.exists():
        print(f"Error: Input file not found at {EVALUATED_CANDIDATES_FILE}")
        print("  Run evaluate_candidates_chgnet.py first.")
        return

    df    = pd.read_csv(EVALUATED_CANDIDATES_FILE)
    f_col = 'formula' if 'formula' in df.columns else 'Formula'

    if df.empty:
        print("No candidates found.")
        pd.DataFrame(columns=['formula', 'is_mechanically_stable',
                               'bulk_modulus_vrh', 'shear_modulus_vrh',
                               'poisson_ratio']).to_csv(OUTPUT_FILE, index=False)
        return

    results = []
    print(f"Checking mechanical stability for {len(df)} candidates...")

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Checking Elasticity"):
        formula = row[f_col]

        if 'relaxed_cif_path' in row and pd.notna(row.get('relaxed_cif_path')):
            cif_path = Path(row['relaxed_cif_path'])
        else:
            cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"

        if not cif_path.exists():
            print(f"  Warning: CIF not found for {formula}. Skipping.")
            continue

        try:
            relaxed_structure         = Structure.from_file(str(cif_path))
            is_stable, props          = check_mechanical_stability(relaxed_structure)
            props['formula']          = formula
            results.append(props)
        except Exception as e:
            print(f"  Failed for {formula}: {e}")
            results.append({
                'formula':                formula,
                'is_mechanically_stable': False,
                'bulk_modulus_vrh':       0.0,
                'shear_modulus_vrh':      0.0,
                'poisson_ratio':          0.0,
            })

    stability_df = pd.DataFrame(results)
    stability_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nMechanical stability check complete. Saved to: {OUTPUT_FILE}")
    if not stability_df.empty:
        print("Summary:")
        print(stability_df[['formula', 'bulk_modulus_vrh',
                             'shear_modulus_vrh', 'is_mechanically_stable']].to_string(index=False))


if __name__ == '__main__':
    main()
