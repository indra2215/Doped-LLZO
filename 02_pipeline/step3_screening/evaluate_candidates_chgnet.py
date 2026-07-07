"""
evaluate_candidates_chgnet.py
─────────────────────────────
This module takes the top 50 pre-screened LLZO candidates and evaluates their
structural relaxation and energy using the CHGNet universal machine learning potential.

It applies deterministic atom substitution into the base LLZO garnet framework
and uses a robust two-stage relaxation method (positions-only followed by full cell)
to avoid PyTorch/isolated-atom crashes on the local machine. It outputs 
`evaluated_top_candidates.csv` along with relaxed CIF files.
"""
import sys
import pandas as pd
import numpy as np
import csv
from pathlib import Path
from pymatgen.core import Structure, Lattice
from pymatgen.io.ase import AseAtomsAdaptor
from chgnet.model import CHGNet
from chgnet.model.dynamics import StructOptimizer

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
CANDIDATES_FILE = ROOT / "01_data" / "candidates" / "top_50_screened_candidates.csv"
OUTPUT_FILE     = ROOT / "01_data" / "results"    / "evaluated_top_candidates.csv"
RELAXED_DIR     = ROOT / "03_structures" / "relaxed"


def get_base_structure():
    """Builds base LLZO garnet (Ia-3d, a=12.98 Å)."""
    return Structure.from_spacegroup(
        'Ia-3d',
        Lattice.cubic(12.98),
        ['Li', 'La', 'Zr', 'O'],
        [[0.125, 0.5, 0.75], [0.125, 0.25, 0.375], [0, 0, 0], [0.105, 0.19, 0.795]]
    )


def build_substituted_structure(base_structure, formula):
    """
    Builds a substituted LLZO structure by deterministic atom replacement.
    Returns the modified pymatgen Structure.
    """
    atoms = AseAtomsAdaptor.get_atoms(base_structure)
    syms  = list(atoms.get_chemical_symbols())
    li_idx = [i for i, s in enumerate(syms) if s == "Li"]
    la_idx = [i for i, s in enumerate(syms) if s == "La"]
    zr_idx = [i for i, s in enumerate(syms) if s == "Zr"]

    dopants = formula
    if "Al" in dopants and len(li_idx) > 0: syms[li_idx[0]] = "Al"
    if "Ga" in dopants and len(li_idx) > 1: syms[li_idx[1]] = "Ga"
    if "Nb" in dopants and len(zr_idx) > 0: syms[zr_idx[0]] = "Nb"
    if "Ta" in dopants and len(zr_idx) > 1: syms[zr_idx[1]] = "Ta"
    if "Gd" in dopants and len(la_idx) > 0: syms[la_idx[0]] = "Gd"
    if "Mg" in dopants and len(li_idx) > 2: syms[li_idx[2]] = "Mg"
    if "Sr" in dopants and len(la_idx) > 1: syms[la_idx[1]] = "Sr"
    if "Y"  in dopants and "Yb" not in dopants and len(la_idx) > 3: syms[la_idx[3]] = "Y"
    if "Hf" in dopants and len(zr_idx) > 2: syms[zr_idx[2]] = "Hf"
    if "W"  in dopants and len(zr_idx) > 3: syms[zr_idx[3]] = "W"
    if "Sb" in dopants and len(zr_idx) > 4: syms[zr_idx[4]] = "Sb"
    if "Fe" in dopants and len(li_idx) > 4: syms[li_idx[4]] = "Fe"
    if "Zn" in dopants and len(li_idx) > 5: syms[li_idx[5]] = "Zn"
    if "Ti" in dopants and len(zr_idx) > 5: syms[zr_idx[5]] = "Ti"
    if "Sn" in dopants and len(zr_idx) > 6: syms[zr_idx[6]] = "Sn"

    atoms.set_chemical_symbols(syms)
    return AseAtomsAdaptor.get_structure(atoms)


# StructOptimizer is initialised once in rapid_surrogate_extraction() and passed
# into staged_relax() to avoid loading CHGNet a second time (which emits another
# UserWarning to stderr and causes PowerShell to kill the process).


def staged_relax(structure, chgnet_model, optimizer):
    """
    Two-step staged relaxation that avoids the isolated-atom crash in
    CHGNet's StructOptimizer when a cell-filter is applied to substituted
    garnets.

    Parameters
    ----------
    optimizer : StructOptimizer already initialised with model=calculator
                (passed in to avoid re-loading CHGNet and triggering a
                second UserWarning that kills the PowerShell process)

    Step 1 — atomic positions only (no cell-filter, no stress computation).
    Step 2 — full cell + atoms relaxation; falls back to step-1 result on
             any failure (e.g. isolated-atom error, convergence timeout).

    Returns:
        (final_structure, energy_per_atom, relax_mode)
        relax_mode is one of: 'full', 'pos_only', 'static'
    """
    # --- Step 1: atomic positions only -----------------------------------------
    try:
        # REDUCED STEPS FOR LOW COMPUTE: steps=10, fmax=0.5
        res1 = optimizer.relax(structure, relax_cell=False, fmax=0.5,
                               steps=10, verbose=False)
        pos_relaxed = res1['final_structure']
        print("    [relax] Step 1 (positions): OK", flush=True)
    except Exception as e:
        print(f"    [relax] Step 1 failed ({e}). Falling back to static.", flush=True)
        pred = chgnet_model.predict_structure(structure)
        return structure, float(pred['e']), 'static'

    # --- Step 2: full cell + atoms relaxation ----------------------------------
    try:
        # REDUCED STEPS FOR LOW COMPUTE: steps=5, fmax=0.5
        res2 = optimizer.relax(pos_relaxed, relax_cell=True, fmax=0.5,
                               steps=5, verbose=False)
        final = res2['final_structure']
        pred  = chgnet_model.predict_structure(final)
        print("    [relax] Step 2 (cell+atoms): OK", flush=True)
        return final, float(pred['e']), 'full'
    except Exception as e:
        print(f"    [relax] Step 2 failed ({e}). Using position-only result.", flush=True)
        pred = chgnet_model.predict_structure(pos_relaxed)
        return pos_relaxed, float(pred['e']), 'pos_only'


from pymatgen.core import Composition
import joblib

GPR_MODEL = ROOT / "02_pipeline" / "step2_model_training" / "trained_gpr_model.pkl"

def gpr_predict(formula):
    """Uses the trained GPR pipeline to predict log10(sigma) from compositional features."""
    if not GPR_MODEL.exists():
        print(f"Warning: GPR model not found at {GPR_MODEL}")
        return None, None
        
    pipeline = joblib.load(GPR_MODEL)
    
    comp = Composition(formula)
    total_atoms = comp.num_atoms
    li_frac = comp.get_atomic_fraction("Li")
    num_elements = len(comp.elements)
    avg_eneg, avg_mass, avg_rad, avg_row, avg_col = 0, 0, 0, 0, 0
    valid_eneg, valid_rad = 0, 0
    
    for el, amt in comp.items():
        frac = amt / total_atoms
        avg_mass += el.atomic_mass * frac
        avg_row += el.row * frac
        avg_col += el.group * frac
        if el.X is not None:
            avg_eneg += el.X * frac
            valid_eneg += frac
        if el.atomic_radius is not None:
            avg_rad += float(el.atomic_radius) * frac
            valid_rad += frac
            
    if valid_eneg > 0: avg_eneg /= valid_eneg
    if valid_rad > 0: avg_rad /= valid_rad
    
    X = np.array([[li_frac, avg_eneg, avg_mass, avg_rad, avg_row, avg_col, num_elements]])
    y_pred, y_std = pipeline.predict(X, return_std=True)
    sigma = 10 ** float(y_pred[0])
    sigma_err = sigma * np.log(10) * float(y_std[0])
    return sigma, sigma_err


def rapid_surrogate_extraction():
    """
    Takes top screened candidates, evaluates with CHGNet static predict_structure,
    and saves structures as CIF + CSV for downstream stability and MD steps.

    FIX: Paths now use ROOT-relative pathlib.
    FIX: Removed head(3) — processes all candidates.
    FIX: Adds 'relaxed_cif_path' column consumed by backtrack_validation_corrected.py.
    """
    print(f"Loading candidates from: {CANDIDATES_FILE}")

    try:
        df = pd.read_csv(CANDIDATES_FILE)
    except FileNotFoundError:
        print(f"ERROR: Could not find candidates at {CANDIDATES_FILE}.")
        print("  Run compositional_screening.py first.")
        return

    print("Initializing CHGNet for staged-relax evaluation of candidates...", flush=True)
    calculator = CHGNet.load()
    # Eagerly initialise StructOptimizer with the ALREADY-LOADED model.
    # This avoids a second CHGNet.load() call inside StructOptimizer() which
    # emits another UserWarning to stderr and causes PowerShell to terminate.
    print("Initializing StructOptimizer (sharing CHGNet model)...", flush=True)
    optimizer = StructOptimizer(model=calculator)

    RELAXED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    base_structure = get_base_structure()

    # Handle formula column name (Formula vs formula)
    f_col = 'Formula' if 'Formula' in df.columns else 'formula'

    print(f"\nStarting CHGNet staged-relax evaluation for {len(df)} candidates...\n", flush=True)

    results = []
    # FIX: Process ALL candidates (removed head(3))
    for idx, row in df.iterrows():
        formula     = str(row[f_col]).strip()
        print(f"[{idx + 1}/{len(df)}] Evaluating {formula}", flush=True)

        try:
            modified_structure = build_substituted_structure(base_structure, formula)

            # Staged relaxation: positions-only → full cell+atoms (avoids isolated-atom crash)
            relaxed_struct, energy_per_atom, relax_mode = staged_relax(
                modified_structure, calculator, optimizer
            )
            volume_per_atom = relaxed_struct.volume / len(relaxed_struct)

            # Save relaxed (or best-available) structure to CIF
            cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"
            relaxed_struct.to(fmt="cif", filename=str(cif_path))

            # Step 4: GPR conductivity
            sigma, sigma_err = gpr_predict(formula)

            results.append({
                'formula':                formula,
                'predicted_conductivity': sigma,
                'predicted_sigma_err':    sigma_err,
                'relaxed_energy_per_atom': energy_per_atom,
                'relaxed_volume_per_atom': volume_per_atom,
                'relaxed_cif_path':       str(cif_path),
                'relax_mode':             relax_mode,
            })

            print(f"--> [{relax_mode}] Energy/atom: {energy_per_atom:.3f} eV, Vol/atom: {volume_per_atom:.3f} A^3", flush=True)
            sys.stdout.flush()

            # Save row-by-row to prevent data loss on crash
            pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)

        except Exception as e:
            print(f"--> FAILED for {formula}: {e}")
            sys.stdout.flush()

    out_df = pd.DataFrame(results)
    print(f"\nEvaluation complete. {len(out_df)}/{len(df)} succeeded.")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == '__main__':
    rapid_surrogate_extraction()