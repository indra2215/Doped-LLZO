"""
evaluate_novel_relaxed.py
─────────────────────────
CHGNet staged-relax evaluation of the novel Standard-Pipeline candidates.

FIXES applied
─────────────
1. Replaced the ASE/FIRE + ExpCellFilter path (which crashes with an
   isolated-atom error on substituted garnets) with the proven two-step
   staged_relax() approach (positions-only first, then full cell+atoms).
2. CHGNet is loaded ONCE and passed into StructOptimizer to avoid the
   double-load PowerShell crash.
3. Real GPR conductivity prediction (instead of hardcoded 0.00076).
4. Results written row-by-row with flush so the file is never empty
   even if a later candidate fails.
"""

import sys
import csv
import warnings
import numpy as np
import joblib
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

from pymatgen.core import Structure, Lattice, Composition
from pymatgen.io.ase import AseAtomsAdaptor
from chgnet.model import CHGNet
from chgnet.model.dynamics import StructOptimizer

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent.parent
OUTPUT_FILE = ROOT / "01_data" / "results"    / "evaluated_novel.csv"
RELAXED_DIR = ROOT / "03_structures" / "relaxed"
GPR_MODEL   = ROOT / "02_pipeline" / "step2_model_training" / "trained_gpr_model.pkl"

RELAXED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Candidates ─────────────────────────────────────────────────────────────
FORMULAS = [
    'Li6.500Ga0.10La3Zr1.80Nb0.20O12',
    'Li6.500Fe0.10La3Zr1.80Nb0.20O12',
    'Li6.500Al0.10La3Zr1.80Sb0.20O12',
    'Li6.500Fe0.10La3Zr1.80Ta0.20O12',
    'Li6.500Fe0.10La3Zr1.80Sb0.20O12',
]


def get_base_structure():
    """Builds the base LLZO garnet (Ia-3d, a = 12.98 Å)."""
    return Structure.from_spacegroup(
        'Ia-3d',
        Lattice.cubic(12.98),
        ['Li', 'La', 'Zr', 'O'],
        [[0.125, 0.5, 0.75], [0.125, 0.25, 0.375], [0, 0, 0], [0.105, 0.19, 0.795]]
    )


def build_substituted_structure(base_structure, formula: str):
    """
    Deterministic atom-replacement on the base LLZO cell.
    Li-site dopants: Ga, Fe, Al, Zn, Mg
    Zr-site dopants: Nb, Ta, Sb, W, Ti, Sn
    """
    atoms = AseAtomsAdaptor.get_atoms(base_structure)
    syms  = list(atoms.get_chemical_symbols())
    li_idx = [i for i, s in enumerate(syms) if s == "Li"]
    zr_idx = [i for i, s in enumerate(syms) if s == "Zr"]
    la_idx = [i for i, s in enumerate(syms) if s == "La"]

    f = formula  # shorter alias
    if "Ga" in f and len(li_idx) > 0:  syms[li_idx[0]] = "Ga"
    if "Fe" in f and len(li_idx) > 0:  syms[li_idx[0]] = "Fe"
    if "Al" in f and len(li_idx) > 0:  syms[li_idx[0]] = "Al"
    if "Zn" in f and len(li_idx) > 1:  syms[li_idx[1]] = "Zn"
    if "Mg" in f and len(li_idx) > 2:  syms[li_idx[2]] = "Mg"
    if "Nb" in f and len(zr_idx) > 0:  syms[zr_idx[0]] = "Nb"
    if "Ta" in f and len(zr_idx) > 0:  syms[zr_idx[0]] = "Ta"
    if "Sb" in f and len(zr_idx) > 0:  syms[zr_idx[0]] = "Sb"
    if "W"  in f and len(zr_idx) > 1:  syms[zr_idx[1]] = "W"
    if "Ti" in f and len(zr_idx) > 1:  syms[zr_idx[1]] = "Ti"
    if "Sn" in f and len(zr_idx) > 2:  syms[zr_idx[2]] = "Sn"

    atoms.set_chemical_symbols(syms)
    return AseAtomsAdaptor.get_structure(atoms)


def staged_relax(structure, chgnet_model, optimizer):
    """
    Two-step staged relaxation (positions-only → full cell+atoms).
    Falls back gracefully so the file is always written.

    Returns: (final_structure, energy_per_atom, relax_mode)
    """
    # Step 1: atomic positions only
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

    # Step 2: full cell + atoms
    try:
        # REDUCED STEPS FOR LOW COMPUTE: steps=5, fmax=0.5
        res2  = optimizer.relax(pos_relaxed, relax_cell=True, fmax=0.5,
                                steps=5, verbose=False)
        final = res2['final_structure']
        pred  = chgnet_model.predict_structure(final)
        print("    [relax] Step 2 (cell+atoms): OK", flush=True)
        return final, float(pred['e']), 'full'
    except Exception as e:
        print(f"    [relax] Step 2 failed ({e}). Using position-only result.", flush=True)
        pred = chgnet_model.predict_structure(pos_relaxed)
        return pos_relaxed, float(pred['e']), 'pos_only'


def gpr_predict(formula: str):
    """GPR surrogate conductivity prediction (log10 scale)."""
    if not GPR_MODEL.exists():
        print(f"  Warning: GPR model not found at {GPR_MODEL}. Using None.")
        return None, None
    try:
        pipeline = joblib.load(GPR_MODEL)
        comp     = Composition(formula)
        total    = comp.num_atoms
        li_frac  = comp.get_atomic_fraction("Li")
        n_el     = len(comp.elements)
        avg_eneg = avg_mass = avg_rad = avg_row = avg_col = 0.0
        ve = vr = 0.0
        for el, amt in comp.items():
            frac = amt / total
            avg_mass += el.atomic_mass * frac
            avg_row  += el.row * frac
            avg_col  += el.group * frac
            if el.X is not None:
                avg_eneg += el.X * frac;  ve += frac
            if el.atomic_radius is not None:
                avg_rad += float(el.atomic_radius) * frac;  vr += frac
        if ve > 0: avg_eneg /= ve
        if vr > 0: avg_rad  /= vr
        X = np.array([[li_frac, avg_eneg, avg_mass, avg_rad, avg_row, avg_col, n_el]])
        y_pred, y_std = pipeline.predict(X, return_std=True)
        sigma     = 10 ** float(y_pred[0])
        sigma_err = sigma * np.log(10) * float(y_std[0])
        return sigma, sigma_err
    except Exception as e:
        print(f"  GPR prediction failed: {e}")
        return None, None


# ── Main ───────────────────────────────────────────────────────────────────

print("Loading CHGNet (single load, shared with StructOptimizer)...", flush=True)
chgnet    = CHGNet.load()
optimizer = StructOptimizer(model=chgnet)

base_structure = get_base_structure()

with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'formula', 'predicted_conductivity', 'predicted_sigma_err',
        'relaxed_energy_per_atom', 'relaxed_volume_per_atom',
        'relaxed_cif_path', 'relax_mode'
    ])
    f.flush()

    for idx, formula in enumerate(FORMULAS):
        print(f"\n{'='*60}", flush=True)
        print(f"[{idx+1}/{len(FORMULAS)}] Evaluating {formula}", flush=True)

        try:
            modified_structure = build_substituted_structure(base_structure, formula)

            relaxed_struct, energy_per_atom, relax_mode = staged_relax(
                modified_structure, chgnet, optimizer
            )
            volume_per_atom = relaxed_struct.volume / len(relaxed_struct)

            cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"
            relaxed_struct.to(fmt="cif", filename=str(cif_path))

            sigma, sigma_err = gpr_predict(formula)

            writer.writerow([
                formula, sigma, sigma_err,
                energy_per_atom, volume_per_atom,
                str(cif_path), relax_mode
            ])
            f.flush()

            print(f"  --> [{relax_mode}] E/atom: {energy_per_atom:.4f} eV  "
                  f"Vol/atom: {volume_per_atom:.4f} A^3  "
                  f"sigma: {sigma:.3e} S/cm" if sigma else
                  f"  --> [{relax_mode}] E/atom: {energy_per_atom:.4f} eV  "
                  f"Vol/atom: {volume_per_atom:.4f} A^3  sigma: N/A",
                  flush=True)

        except Exception as e:
            print(f"  FAILED for {formula}: {e}", flush=True)
            writer.writerow([formula, None, None, None, None, None, 'failed'])
            f.flush()

print(f"\nDone. Results saved to: {OUTPUT_FILE}", flush=True)
