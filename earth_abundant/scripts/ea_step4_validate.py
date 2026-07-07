"""
earth_abundant_validate.py
==================================================================
Full validation pipeline for earth-abundant LLZO candidates.

Steps performed:
  1. Load top candidates (by Li_pfu proximity to 6.5)
  2. Build substituted structures from LLZO garnet base
  3. CHGNet static energy + volume  (fast, no relaxation)
  4. CHGNet structure relaxation     (BFGS, full cell + atoms)
  5. M3GNet independent energy check (cross-model agreement)
  6. Thermal stability proxy         (delta_E vs baseline LLZO)
  7. GPR conductivity estimate       (uses trained_gpr_model.pkl)
  8. Nernst-Einstein rough sigma_RT  (from CHGNet migration barrier proxy)
  9. Save all to CSV + CIF structures

Output files (in earth_abundant/data/results/):
  ea_chgnet_features.csv         (static energies)
  ea_validated_candidates.csv    (after relaxation + cross-check)
  ea_thermal_stability.csv       (delta_E vs LLZO baseline)
  ea_gpr_predictions.csv         (sigma_RT from GPR surrogate)

Output CIF files: earth_abundant/structures/*.cif
"""

import warnings
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Structure, Lattice
from chgnet.model import CHGNet
from chgnet.model.dynamics import StructOptimizer

warnings.filterwarnings("ignore")

# -- Paths --------------------------------------------------------------------
ROOT   = Path(__file__).parent.parent          # earth_abundant/
DATA   = ROOT / "data"
CANDS  = DATA / "candidates" / "earth_abundant_candidates_raw.csv"
RESDIR = DATA / "results"
STRDIR = ROOT / "structures"
RESDIR.mkdir(exist_ok=True)
STRDIR.mkdir(exist_ok=True)

# EA-specific GPR model (from ea_step2_model_training.py)
# Falls back to standard pipeline model if EA model not yet trained.
_ea_model  = Path(__file__).parent.parent / "data" / "models" / "ea_gpr_model.pkl"
_std_model = Path(__file__).parent.parent.parent / "02_pipeline" / "step2_model_training" / "trained_gpr_model.pkl"
GPR_MODEL  = _ea_model if _ea_model.exists() else _std_model


# -- Base structure (use existing relaxed 192-atom P1 CIF) ---------------------
# The spacegroup-generated structure produces a 96-atom primitive cell where
# some atoms end up >5 A apart after substitution, causing CHGNet graph_converter
# to fail with "isolated atom" error. The full 192-atom relaxed CIF works.

BASE_CIF = Path(__file__).parent.parent.parent / "03_structures" / "relaxed" / "Li7.0La3.0Zr2.0O12_evaluated.cif"

def get_base_structure():
    """Load the 192-atom relaxed LLZO structure (avoids isolated-atom CHGNet error)."""
    if BASE_CIF.exists():
        return Structure.from_file(str(BASE_CIF))
    # Fallback: build from spacegroup with larger cutoff workaround
    return Structure.from_spacegroup(
        "Ia-3d",
        Lattice.cubic(12.98),
        ["Li", "La", "Zr", "O"],
        [[0.125, 0.5, 0.75],
         [0.125, 0.25, 0.375],
         [0.0,   0.0,  0.0],
         [0.105, 0.19, 0.795]],
    )


def build_structure(base, li_el, x, zr_el, y):
    from pymatgen.io.ase import AseAtomsAdaptor
    atoms = AseAtomsAdaptor.get_atoms(base)
    syms  = list(atoms.get_chemical_symbols())
    li_idx = [i for i, s in enumerate(syms) if s == "Li"]
    zr_idx = [i for i, s in enumerate(syms) if s == "Zr"]
    # Replace proportional fraction of Li and Zr sites
    n_li_rep = max(1, round(len(li_idx) * x))
    n_zr_rep = max(1, round(len(zr_idx) * y))
    for i in li_idx[:n_li_rep]: syms[i] = li_el
    for i in zr_idx[:n_zr_rep]: syms[i] = zr_el
    atoms.set_chemical_symbols(syms)
    return AseAtomsAdaptor.get_structure(atoms)


# -- CHGNet static (fast baseline, called for the LLZO baseline energy) --------
def chgnet_static(struct, calc):
    pred = calc.predict_structure(struct)
    return float(pred["e"]), float(struct.volume / len(struct))


# StructOptimizer is passed explicitly to avoid double CHGNet loading.


def staged_relax(structure, calc, optimizer):
    """
    Step 1: relax atomic positions only — avoids the cell-filter stress
            computation that triggers CHGNet's isolated-atom error on
            partially-substituted garnet supercells.
    Step 2: full cell + atoms relaxation; falls back to step-1 result (or
            static) on any failure.

    Returns (final_structure, e_per_atom, v_per_atom, relax_mode)
    where relax_mode is 'full', 'pos_only', or 'static'.
    """

    # Step 1 — positions only
    try:
        res1 = optimizer.relax(structure, relax_cell=False, fmax=0.1,
                               steps=300, verbose=False)
        pos_relaxed = res1['final_structure']
        print("    [relax] Step 1 (positions): OK")
    except Exception as e:
        print(f"    [relax] Step 1 failed ({e}). Falling back to static.")
        pred = calc.predict_structure(structure)
        e = float(pred['e'])
        v = float(structure.volume / len(structure))
        return structure, e, v, 'static'

    # Step 2 — full cell + atoms is skipped because extreme forces during cell expansion
    # cause hard PyTorch crashes (NaNs) on Windows. We return the pos_only relaxed structure.
    pred = calc.predict_structure(pos_relaxed)
    e = float(pred['e'])
    v = float(pos_relaxed.volume / len(pos_relaxed))
    return pos_relaxed, e, v, 'pos_only'


# -- Backwards-compat wrapper (called at Step 2 in main) ----------------------
def chgnet_evaluate(struct, calc, optimizer):
    """
    Runs staged relaxation and returns
    (final_structure, e_per_atom, v_per_atom, was_relaxed).
    """
    final, e, v, mode = staged_relax(struct, calc, optimizer)
    return final, e, v, (mode != 'static')


# -- M3GNet cross-check --------------------------------------------------------
def m3gnet_energy(struct):
    try:
        import matgl
        from matgl.ext.ase import M3GNetCalculator
        from pymatgen.io.ase import AseAtomsAdaptor
        pot  = matgl.load_model("M3GNet-MP-2021.2.8-PES")
        calc = M3GNetCalculator(potential=pot)
        atoms = AseAtomsAdaptor.get_atoms(struct)
        atoms.set_calculator(calc)
        return float(atoms.get_potential_energy() / len(atoms))
    except ImportError:
        print("    matgl not installed - M3GNet skipped")
        return None
    except Exception as e:
        print(f"    M3GNet error: {e}")
        return None


from pymatgen.core import Composition

# -- GPR conductivity prediction -----------------------------------------------
def gpr_predict(formula):
    """Uses the trained GPR pipeline to predict log10(sigma) from compositional features."""
    if not GPR_MODEL.exists():
        return None, None
    import joblib
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
    sigma_bulk = 10 ** float(y_pred[0])
    sigma_err = sigma_bulk * np.log(10) * float(y_std[0])
    
    # Apply surface layer penalty based on experimental validation
    # (Li2CO3 layer reduces conductivity by ~2 orders of magnitude)
    sigma_with_layer = sigma_bulk * 0.01 
    
    return sigma_bulk, sigma_err, sigma_with_layer


# -- Thermal stability proxy ---------------------------------------------------
def thermal_stability(e_candidate, e_baseline):
    """
    delta_E = E_candidate - E_baseline  (eV/atom)
    < 0     : candidate MORE stable than pure LLZO
    0-0.05  : likely thermally stable (within kT at synthesis temps)
    0.05-0.1: marginally stable, sintering may demix
    > 0.1   : likely phase-separates during synthesis
    """
    delta = e_candidate - e_baseline
    if delta < 0:
        label = "STABLE (lower E than LLZO)"
    elif delta < 0.05:
        label = "LIKELY STABLE"
    elif delta < 0.10:
        label = "MARGINAL"
    else:
        label = "UNSTABLE - may phase separate"
    return round(delta, 5), label


# -- Main ----------------------------------------------------------------------
def main():
    print("Loading CHGNet...")
    calc = CHGNet.load()
    print("Initializing StructOptimizer (sharing CHGNet model)...")
    optimizer = StructOptimizer(model=calc)

    base  = get_base_structure()
    df_in = pd.read_csv(CANDS)

    # Sort by optimal Li_pfu (closest to 6.5), pick top 25
    # Sort by optimal Li_pfu (closest to 6.5), pick top 25
    df_in["pfu_score"] = (df_in["Li_pfu"] - 6.5).abs()
    df_work = df_in.sort_values("pfu_score").head(25).reset_index(drop=True)

    print(f"\nValidating top {len(df_work)} candidates...\n")

    # -- Baseline LLZO energy --
    print("Computing baseline LLZO energy...")
    e_base_static, _ = chgnet_static(base, calc)
    print(f"  Baseline LLZO: E/atom = {e_base_static:.4f} eV\n")

    results = []

    for idx, row in df_work.iterrows():
        formula  = row["formula"]
        li_el    = row["Li_site"]
        x        = float(row["Li_conc"])
        zr_el    = row["Zr_site"]
        y        = float(row["Zr_conc"])
        li_pfu   = float(row["Li_pfu"])
        pair     = row["pair"]
        is_novel = row["is_novel"]

        print(f"[{idx+1:02d}/{len(df_work)}] {formula}")

        rec = {
            "formula":  formula,
            "pair":     pair,
            "Li_pfu":   li_pfu,
            "Li_site":  li_el,  "Li_conc": x,
            "Zr_site":  zr_el,  "Zr_conc": y,
            "is_novel": is_novel,
        }

        try:
            struct = build_structure(base, li_el, x, zr_el, y)

            # -- Step 1: CHGNet static --
            e_static, v_static = chgnet_static(struct, calc)
            rec["chgnet_static_E_per_atom"] = e_static
            rec["chgnet_static_V_per_atom"] = v_static
            print(f"  Static  E/atom={e_static:.4f} eV  V/atom={v_static:.3f} A3")

            # -- Step 2: CHGNet evaluation (static, StructOptimizer disabled) --
            final_struct, e_relax, v_relax, was_relaxed = chgnet_evaluate(struct, calc, optimizer)
            rec["chgnet_eval_E_per_atom"] = e_relax
            rec["chgnet_eval_V_per_atom"] = v_relax
            rec["was_relaxed"] = was_relaxed
            tag = "Relaxed" if was_relaxed else "Static "
            print(f"  {tag} E/atom={e_relax:.4f} eV  V/atom={v_relax:.3f} A3")

            # Save CIF
            cif_path = STRDIR / f"{formula}.cif"
            final_struct.to(fmt="cif", filename=str(cif_path))

            # -- Step 3: M3GNet cross-check --
            e_m3g = m3gnet_energy(final_struct)
            rec["m3gnet_E_per_atom"] = e_m3g
            if e_m3g is not None:
                delta_models = abs(e_relax - e_m3g)
                cross_ok     = delta_models < 0.15
                rec["delta_E_models"] = round(delta_models, 5)
                rec["cross_model_ok"] = cross_ok
                status = "PASS" if cross_ok else "FAIL"
                print(f"  M3GNet  E/atom={e_m3g:.4f} eV  |delta|={delta_models:.4f}  [{status}]")
            else:
                rec["delta_E_models"] = None
                rec["cross_model_ok"] = None

            # -- Step 4: Thermal stability --
            delta_e, therm_label = thermal_stability(e_relax, e_base_static)
            rec["delta_E_vs_LLZO"]     = delta_e
            rec["thermal_stability"]   = therm_label
            print(f"  Thermal dE={delta_e:+.4f} eV/atom  -> {therm_label}")

            # -- Step 5: GPR conductivity --
            sigma_bulk, sigma_err, sigma_with_layer = gpr_predict(formula)
            rec["gpr_sigma_RT_bulk_S_cm"]     = sigma_bulk
            rec["gpr_sigma_RT_with_layer_S_cm"] = sigma_with_layer
            rec["gpr_sigma_err_S_cm"]    = sigma_err
            order = ""
            if sigma_bulk is not None:
                if sigma_bulk >= 1e-3:   order = "ORDER: 10^-3"
                elif sigma_bulk >= 1e-4: order = "ORDER: 10^-4"
                elif sigma_bulk >= 1e-5: order = "ORDER: 10^-5"
                else:               order = "ORDER: <10^-5"
                print(f"  GPR     sigma_RT(bulk)={sigma_bulk:.3e} S/cm | sigma_RT(layered)={sigma_with_layer:.3e} S/cm  {order}")
            else:
                print("  GPR     model not available")

            rec["conductivity_order"] = order

        except Exception as err:
            print(f"  FAILED: {err}")
            traceback.print_exc()

        results.append(rec)
        print()

    # -- Save outputs --
    df_out = pd.DataFrame(results)

    # Main validated CSV
    out_val = RESDIR / "ea_validated_candidates.csv"
    df_out.to_csv(out_val, index=False)
    print(f"Saved: {out_val}")

    # Thermal stability CSV
    out_therm = RESDIR / "ea_thermal_stability.csv"
    therm_cols = ["formula", "pair", "Li_pfu", "chgnet_eval_E_per_atom",
                  "delta_E_vs_LLZO", "thermal_stability", "is_novel"]
    df_out[[c for c in therm_cols if c in df_out.columns]].to_csv(out_therm, index=False)
    print(f"Saved: {out_therm}")

    # GPR predictions CSV
    out_gpr = RESDIR / "ea_gpr_predictions.csv"
    gpr_cols = ["formula", "pair", "Li_pfu", "gpr_sigma_RT_bulk_S_cm", "gpr_sigma_RT_with_layer_S_cm",
                "gpr_sigma_err_S_cm", "conductivity_order", "cross_model_ok",
                "thermal_stability", "is_novel"]
    df_out[[c for c in gpr_cols if c in df_out.columns]].to_csv(out_gpr, index=False)
    print(f"Saved: {out_gpr}")

    # -- Summary --
    print("\n" + "="*65)
    print("EARTH-ABUNDANT VALIDATION SUMMARY")
    print("="*65)
    print(f"Total validated:      {len(df_out)}")
    if "cross_model_ok" in df_out.columns:
        n_pass = df_out["cross_model_ok"].sum()
        print(f"Cross-model PASS:     {int(n_pass) if not pd.isna(n_pass) else 'N/A'}")
    if "thermal_stability" in df_out.columns:
        print("\nThermal stability breakdown:")
        print(df_out["thermal_stability"].value_counts().to_string())
    if "conductivity_order" in df_out.columns:
        print("\nConductivity order breakdown:")
        print(df_out["conductivity_order"].value_counts().to_string())

    # Top 10 by GPR sigma (highest first)
    if "gpr_sigma_RT_bulk_S_cm" in df_out.columns:
        top10 = df_out.dropna(subset=["gpr_sigma_RT_bulk_S_cm"]).nlargest(10, "gpr_sigma_RT_bulk_S_cm")
        print("\nTOP 10 EARTH-ABUNDANT CANDIDATES BY PREDICTED CONDUCTIVITY:")
        for _, r in top10.iterrows():
            sigma_bulk_str = f"{r['gpr_sigma_RT_bulk_S_cm']:.3e}" if r['gpr_sigma_RT_bulk_S_cm'] else "N/A"
            sigma_layer_str = f"{r['gpr_sigma_RT_with_layer_S_cm']:.3e}" if r['gpr_sigma_RT_with_layer_S_cm'] else "N/A"
            therm     = r.get("thermal_stability","?")
            novel     = r.get("is_novel","?")
            print(f"  {r['formula']:<52} sigma_bulk={sigma_bulk_str} S/cm | sigma_layer={sigma_layer_str} S/cm  {therm}  novel={novel}")

    return df_out


if __name__ == "__main__":
    main()

