# -*- coding: utf-8 -*-
"""
run_remaining_steps.py
======================
Master runner to complete ALL remaining pipeline steps.
GPU-safe mode for RTX 3050 / 6 GB VRAM laptops.

  1. Earth-Abundant Step 4 — CHGNet validation + GPR predictions
  2. Earth-Abundant Step 5 — Thermodynamic stability (Materials Project hull)
  3. Earth-Abundant Step 6 — Arrhenius MD → σ_RT
  4. Standard Pipeline Step 5 — Arrhenius MD → σ_RT  (top candidates)

Usage:
    python run_remaining_steps.py [--mp-key YOUR_MP_API_KEY] [--use-cpu]

If --mp-key is not provided, Step 5 (thermodynamic hull) is skipped.
Use --use-cpu to force CPU-only mode (safe but slower).
"""

import sys
import os
import argparse
import warnings
import traceback
import copy
import gc
from pathlib import Path

import numpy as np
import pandas as pd
import sys
import io

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

warnings.filterwarnings("ignore")
import time

# ── Repo root (where this script lives) ────────────────────────────────────
ROOT = Path(__file__).resolve().parent

# ── Parse args ──────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--mp-key", default=os.environ.get("MP_API_KEY", ""), help="Materials Project API key")
parser.add_argument("--skip-ea4", action="store_true", help="Skip EA step 4 (CHGNet validation)")
parser.add_argument("--skip-ea5", action="store_true", help="Skip EA step 5 (thermodynamic hull)")
parser.add_argument("--skip-ea6", action="store_true", help="Skip EA step 6 (MD validation)")
parser.add_argument("--skip-std-md", action="store_true", help="Skip Standard Pipeline MD step")
parser.add_argument("--n-candidates", type=int, default=3,
                    help="Number of candidates for MD (default 3, safe for 6 GB GPU)")
parser.add_argument("--md-steps", type=int, default=500,
                    help="MD steps per temperature (default 500 = GPU-safe; use 1000 for higher accuracy)")
parser.add_argument("--use-cpu", action="store_true",
                    help="Force CPU-only mode (safe on low-VRAM machines, slower)")
parser.add_argument("--vram-limit-mb", type=int, default=3500,
                    help="Min free VRAM (MB) required to use GPU; falls back to CPU if below (default 3500)")
args = parser.parse_args()

MP_API_KEY   = args.mp_key
MD_STEPS     = args.md_steps
N_CANDIDATES = args.n_candidates
TEMPERATURES = [600, 800, 1000]
TIME_STEP    = 2.0  # fs
FORCE_CPU    = args.use_cpu
VRAM_LIMIT   = args.vram_limit_mb

# ── GPU / Device detection ──────────────────────────────────────────────────
try:
    import torch
    _cuda_ok = torch.cuda.is_available() and not FORCE_CPU
    if _cuda_ok:
        _free_mb = torch.cuda.mem_get_info(0)[0] / 1024**2
        if _free_mb < VRAM_LIMIT:
            print(f"  [GPU] Only {_free_mb:.0f} MB VRAM free (limit {VRAM_LIMIT} MB) → switching to CPU")
            _cuda_ok = False
    DEVICE = "cuda" if _cuda_ok else "cpu"
except Exception:
    DEVICE = "cpu"
    _cuda_ok = False

def gpu_cleanup():
    """Free GPU memory and force Python GC — call between heavy steps."""
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except Exception:
        pass

def vram_status():
    """Return a short VRAM usage string, or empty string on CPU."""
    try:
        import torch
        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info(0)
            used = (total - free) / 1024**2
            tot  = total / 1024**2
            return f"  [VRAM] {used:.0f}/{tot:.0f} MB used"
    except Exception:
        pass
    return ""

print("=" * 70)
print("  DOPED-LLZO: COMPLETING REMAINING PIPELINE STEPS")
print("=" * 70)
print(f"  Device:                   {DEVICE.upper()} ({'RTX 3050 6 GB' if DEVICE == 'cuda' else 'CPU-only safe mode'})")
print(f"  MD steps per temperature: {MD_STEPS}")
print(f"  Candidate limit for MD:   {N_CANDIDATES}")
print(f"  MP API key provided:      {'Yes' if MP_API_KEY else 'No (Step 5 will be skipped)'}")
if DEVICE == "cpu":
    print("  NOTE: Running on CPU — slower but zero GPU crash risk.")
print("=" * 70)

# ════════════════════════════════════════════════════════════════════════════
#  SHARED UTILITIES
# ════════════════════════════════════════════════════════════════════════════

def load_chgnet():
    """Load CHGNet once, respecting GPU VRAM limits for RTX 3050 6 GB.

    NOTE: torch.set_grad_enabled(False) must NOT be used here.
    CHGNet computes forces via torch.autograd.grad(energy, positions),
    which requires the computation graph to be intact. Disabling grads
    globally breaks force calculations (documented in Further_Improvements.md).
    """
    import torch
    from chgnet.model import CHGNet
    from chgnet.model.dynamics import StructOptimizer, CHGNetCalculator

    gpu_cleanup()  # free any lingering tensors before loading

    if DEVICE == "cuda":
        free_mb = torch.cuda.mem_get_info(0)[0] / 1024**2
        print(f"  Loading CHGNet on GPU  [{free_mb:.0f} MB VRAM free before load]...")
    else:
        print("  Loading CHGNet on CPU (GPU-safe mode)...")

    # NOTE: Do NOT call torch.set_grad_enabled(False) — CHGNet needs autograd for forces
    model = CHGNet.load()
    # Move model to chosen device
    try:
        model = model.to(DEVICE)
    except Exception:
        pass  # some CHGNet versions handle device internally

    optimizer  = StructOptimizer(model=model)
    calculator = CHGNetCalculator(model=model)

    if DEVICE == "cuda":
        after_mb = torch.cuda.mem_get_info(0)[0] / 1024**2
        print(f"  CHGNet loaded OK.  [{after_mb:.0f} MB VRAM free after load]")
    else:
        print("  CHGNet loaded OK (CPU).")
    return model, optimizer, calculator


def staged_relax(structure, calc, optimizer, steps=300, fmax=0.1):
    """Position-only relaxation (avoids CHGNet cell-filter crash on garnets)."""
    try:
        res = optimizer.relax(structure, relax_cell=False, fmax=fmax,
                              steps=steps, verbose=False)
        relaxed = res['final_structure']
        pred = calc.predict_structure(relaxed)
        e = float(pred['e'])
        v = float(relaxed.volume / len(relaxed))
        gpu_cleanup()  # release intermediate tensors
        return relaxed, e, v, 'pos_only'
    except Exception as err:
        print(f"    [relax] Pos-only failed ({err}). Using static.")
        pred = calc.predict_structure(structure)
        e = float(pred['e'])
        v = float(structure.volume / len(structure))
        gpu_cleanup()
        return structure, e, v, 'static'


def gpr_predict(formula):
    """Use EA GPR model to predict ionic conductivity from formula."""
    import joblib
    from pymatgen.core import Composition

    gpr_path = ROOT / "earth_abundant" / "data" / "models" / "ea_gpr_model.pkl"
    if not gpr_path.exists():
        gpr_path = ROOT / "02_pipeline" / "step2_model_training" / "trained_gpr_model.pkl"
    if not gpr_path.exists():
        return None, None, None

    pipeline = joblib.load(gpr_path)
    comp = Composition(formula)
    total_atoms = comp.num_atoms
    li_frac = comp.get_atomic_fraction("Li")
    num_elements = len(comp.elements)
    avg_eneg = avg_mass = avg_rad = avg_row = avg_col = 0.0
    valid_eneg = valid_rad = 0.0

    for el, amt in comp.items():
        frac = amt / total_atoms
        avg_mass += float(el.atomic_mass) * frac
        avg_row  += el.row * frac
        avg_col  += el.group * frac
        if el.X is not None:
            avg_eneg += el.X * frac
            valid_eneg += frac
        if el.atomic_radius is not None:
            avg_rad  += float(el.atomic_radius) * frac
            valid_rad += frac

    if valid_eneg > 0: avg_eneg /= valid_eneg
    if valid_rad  > 0: avg_rad  /= valid_rad

    X = np.array([[li_frac, avg_eneg, avg_mass, avg_rad, avg_row, avg_col, num_elements]])
    y_pred, y_std = pipeline.predict(X, return_std=True)
    sigma_bulk = 10 ** float(y_pred[0])
    sigma_err  = sigma_bulk * np.log(10) * float(y_std[0])
    return sigma_bulk, sigma_err, sigma_bulk * 0.01  # bulk, err, with-grain-boundary


def run_md_arrhenius(cif_path: Path, calc, n_steps=MD_STEPS, temperatures=TEMPERATURES):
    """
    Runs NVT Langevin MD at each temperature, extracts diffusivity,
    fits Arrhenius, returns (Ea_eV, sigma_RT, diffusivities_dict).
    """
    from ase.io import read
    from ase.md.langevin import Langevin
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
    from ase import units

    base_atoms = read(str(cif_path))
    li_count   = sum(1 for a in base_atoms if a.symbol == 'Li')
    volume_cm3 = base_atoms.get_volume() * 1e-24  # Å³ → cm³
    n_Li       = li_count / volume_cm3

    diffusivities = {}

    for temp in temperatures:
        # ── VRAM check before each temperature run ──────────────────────────
        vs = vram_status()
        if vs:
            print(f"  {vs}")

        print(f"    MD @ {temp}K ... ", end="", flush=True)
        try:
            atoms = copy.deepcopy(base_atoms)
            atoms.set_calculator(calc)
            MaxwellBoltzmannDistribution(atoms, temperature_K=temp)
            dyn = Langevin(atoms, timestep=TIME_STEP * units.fs,
                           temperature_K=temp, friction=0.02)

            li_idx     = [a.index for a in atoms if a.symbol == 'Li']
            cell_len   = atoms.get_cell().lengths()
            prev_pos   = atoms.get_positions()[li_idx].copy()
            cum_disp   = np.zeros((len(li_idx), 3))
            msd_vals   = []

            def log_msd(a=atoms):
                nonlocal prev_pos, cum_disp
                curr  = a.get_positions()[li_idx]
                delta = curr - prev_pos
                delta -= np.round(delta / cell_len) * cell_len  # PBC unwrap
                cum_disp += delta
                prev_pos  = curr.copy()
                msd_vals.append(np.mean(np.sum(cum_disp ** 2, axis=1)))

            dyn.attach(log_msd, interval=100)
            dyn.run(n_steps)

            if len(msd_vals) < 4:
                print("too few MSD points, skipped.")
                gpu_cleanup()
                continue

            time_arr  = np.arange(len(msd_vals)) * 100 * TIME_STEP * 1e-15  # s
            fit_start = max(1, len(time_arr) // 2)
            slope, _  = np.polyfit(time_arr[fit_start:], msd_vals[fit_start:], 1)
            D = (slope / 6.0) * 1e-16  # Å²/s → cm²/s

            if D > 0:
                diffusivities[temp] = D
                print(f"D={D:.3e} cm²/s")
            else:
                print("D\u22640, skipped.")

            # ── Release atoms + GPU memory between temperature runs ─────────
            del atoms, dyn
            gpu_cleanup()
            time.sleep(1)  # 1-second cool-down between temps (protects laptop)

        except Exception as e:
            print(f"ERROR: {e}")
            gpu_cleanup()

    if len(diffusivities) < 2:
        return None, None, diffusivities

    # Arrhenius fit
    from ase import units
    temps     = np.array(list(diffusivities.keys()))
    inv_temps = 1.0 / temps
    log_D     = np.log(list(diffusivities.values()))
    slope_a, intercept = np.polyfit(inv_temps, log_D, 1)
    Ea_eV = -slope_a * units.kB

    D_RT = np.exp(np.polyval([slope_a, intercept], 1.0 / 298.15))
    q      = 1.602e-19
    kB_SI  = 1.381e-23
    sigma_RT = (D_RT * n_Li * q**2) / (kB_SI * 298.15)

    return Ea_eV, sigma_RT, diffusivities


# ════════════════════════════════════════════════════════════════════════════
#  STEP EA-4: Earth-Abundant CHGNet Validation + GPR predictions
# ════════════════════════════════════════════════════════════════════════════
def run_ea_step4():
    print("\n" + "=" * 70)
    print("  EA STEP 4 — CHGNet Validation + GPR Predictions")
    print("=" * 70)

    from pymatgen.core import Structure, Lattice
    from pymatgen.io.ase import AseAtomsAdaptor

    EA_ROOT    = ROOT / "earth_abundant"
    CANDS_CSV  = EA_ROOT / "data" / "candidates" / "earth_abundant_candidates_raw.csv"
    RESDIR     = EA_ROOT / "data" / "results"
    STRDIR     = EA_ROOT / "structures"
    RESDIR.mkdir(exist_ok=True)
    STRDIR.mkdir(exist_ok=True)

    BASE_CIF = ROOT / "03_structures" / "relaxed" / "Li7.0La3.0Zr2.0O12_evaluated.cif"
    if not BASE_CIF.exists():
        print(f"  ERROR: Base structure not found: {BASE_CIF}")
        return None

    print(f"  Loading base structure from: {BASE_CIF.name}")
    base = Structure.from_file(str(BASE_CIF))

    df_in = pd.read_csv(CANDS_CSV)
    df_in["pfu_score"] = (df_in["Li_pfu"] - 6.5).abs()
    df_work = df_in.sort_values("pfu_score").head(5).reset_index(drop=True)
    print(f"  Selected top {len(df_work)} candidates (Li_pfu closest to 6.5)")

    calc, optimizer, _ = load_chgnet()

    # Baseline LLZO energy
    pred_base = calc.predict_structure(base)
    e_baseline = float(pred_base["e"])
    print(f"  Baseline LLZO E/atom = {e_baseline:.4f} eV")
    print()

    results = []
    for idx, row in df_work.iterrows():
        formula  = str(row["formula"])
        li_el    = str(row["Li_site"])
        x        = float(row["Li_conc"])
        zr_el    = str(row["Zr_site"])
        y        = float(row["Zr_conc"])
        li_pfu   = float(row["Li_pfu"])
        pair     = str(row["pair"])
        is_novel = bool(row["is_novel"])

        print(f"  [{idx+1}/{len(df_work)}] {formula}")

        rec = {"formula": formula, "pair": pair, "Li_pfu": li_pfu,
               "Li_site": li_el, "Li_conc": x, "Zr_site": zr_el,
               "Zr_conc": y, "is_novel": is_novel}

        try:
            # Build substituted structure
            atoms = AseAtomsAdaptor.get_atoms(base)
            syms  = list(atoms.get_chemical_symbols())
            li_idx_list = [i for i, s in enumerate(syms) if s == "Li"]
            zr_idx_list = [i for i, s in enumerate(syms) if s == "Zr"]
            n_li_rep = max(1, round(len(li_idx_list) * x))
            n_zr_rep = max(1, round(len(zr_idx_list) * y))
            for i in li_idx_list[:n_li_rep]: syms[i] = li_el
            for i in zr_idx_list[:n_zr_rep]: syms[i] = zr_el
            atoms.set_chemical_symbols(syms)
            struct = AseAtomsAdaptor.get_structure(atoms)

            # CHGNet static
            pred_static = calc.predict_structure(struct)
            e_static = float(pred_static["e"])
            v_static = float(struct.volume / len(struct))
            rec["chgnet_static_E_per_atom"] = e_static
            rec["chgnet_static_V_per_atom"] = v_static
            print(f"    Static  E/atom={e_static:.4f} eV  V/atom={v_static:.3f} Å³")

            # CHGNet relaxation
            final_struct, e_relax, v_relax, mode = staged_relax(struct, calc, optimizer)
            rec["chgnet_eval_E_per_atom"] = e_relax
            rec["chgnet_eval_V_per_atom"] = v_relax
            rec["was_relaxed"] = (mode == 'pos_only')
            print(f"    Relaxed E/atom={e_relax:.4f} eV  V/atom={v_relax:.3f} Å³ [{mode}]")

            # Save CIF
            cif_path = STRDIR / f"{formula}.cif"
            final_struct.to(fmt="cif", filename=str(cif_path))
            print(f"    Saved: {cif_path.name}")

            # M3GNet cross-check (optional, graceful skip if not installed)
            try:
                import matgl
                from matgl.ext.ase import M3GNetCalculator
                pot     = matgl.load_model("M3GNet-MP-2021.2.8-PES")
                m3_calc = M3GNetCalculator(potential=pot)
                from pymatgen.io.ase import AseAtomsAdaptor as AAA
                m3_atoms = AAA.get_atoms(final_struct)
                m3_atoms.set_calculator(m3_calc)
                e_m3g = float(m3_atoms.get_potential_energy() / len(m3_atoms))
                delta = abs(e_relax - e_m3g)
                cross_ok = delta < 0.15
                rec["m3gnet_E_per_atom"] = e_m3g
                rec["delta_E_models"]    = round(delta, 5)
                rec["cross_model_ok"]    = cross_ok
                print(f"    M3GNet  E/atom={e_m3g:.4f}  |delta|={delta:.4f}  {'PASS' if cross_ok else 'FAIL'}")
            except ImportError:
                print("    M3GNet: matgl not installed — skipped")
                rec["m3gnet_E_per_atom"] = None
                rec["delta_E_models"]    = None
                rec["cross_model_ok"]    = None
            except Exception as m3e:
                print(f"    M3GNet error: {m3e}")
                rec["m3gnet_E_per_atom"] = None

            # Thermal stability (delta_E vs LLZO baseline)
            delta_e = e_relax - e_baseline
            if delta_e < 0:
                therm_label = "STABLE (lower E than LLZO)"
            elif delta_e < 0.05:
                therm_label = "LIKELY STABLE"
            elif delta_e < 0.10:
                therm_label = "MARGINAL"
            else:
                therm_label = "UNSTABLE"
            rec["delta_E_vs_LLZO"]   = round(delta_e, 5)
            rec["thermal_stability"] = therm_label
            print(f"    Thermal dE={delta_e:+.4f} eV/atom → {therm_label}")

            # GPR conductivity
            sigma_bulk, sigma_err, sigma_layer = gpr_predict(formula)
            rec["gpr_sigma_RT_bulk_S_cm"]        = sigma_bulk
            rec["gpr_sigma_RT_with_layer_S_cm"]  = sigma_layer
            rec["gpr_sigma_err_S_cm"]            = sigma_err
            if sigma_bulk:
                order = ("ORDER: 10^-3" if sigma_bulk >= 1e-3 else
                         "ORDER: 10^-4" if sigma_bulk >= 1e-4 else
                         "ORDER: 10^-5" if sigma_bulk >= 1e-5 else "ORDER: <10^-5")
                rec["conductivity_order"] = order
                print(f"    GPR     σ_bulk={sigma_bulk:.3e}  σ_layer={sigma_layer:.3e}  {order}")
            else:
                rec["conductivity_order"] = "N/A"
                print("    GPR     model N/A")

        except Exception as err:
            print(f"    FAILED: {err}")
            traceback.print_exc()

        results.append(rec)
        print(vram_status())
        gpu_cleanup()
        time.sleep(2)  # 2-second cool-down between EA candidates (protects RTX 3050)
        print()

    df_out = pd.DataFrame(results)
    out_path = RESDIR / "ea_validated_candidates.csv"
    df_out.to_csv(out_path, index=False)

    # Thermal stability CSV
    therm_cols = ["formula","pair","Li_pfu","chgnet_eval_E_per_atom",
                  "delta_E_vs_LLZO","thermal_stability","is_novel"]
    df_out[[c for c in therm_cols if c in df_out.columns]].to_csv(
        RESDIR / "ea_thermal_stability.csv", index=False)

    # GPR predictions CSV
    gpr_cols = ["formula","pair","Li_pfu","gpr_sigma_RT_bulk_S_cm",
                "gpr_sigma_RT_with_layer_S_cm","gpr_sigma_err_S_cm",
                "conductivity_order","cross_model_ok","thermal_stability","is_novel"]
    df_out[[c for c in gpr_cols if c in df_out.columns]].to_csv(
        RESDIR / "ea_gpr_predictions.csv", index=False)

    print(f"  Saved: {out_path}")
    print(f"  Saved: {RESDIR / 'ea_thermal_stability.csv'}")
    print(f"  Saved: {RESDIR / 'ea_gpr_predictions.csv'}")

    # Summary
    print("\n  EA STEP 4 SUMMARY")
    print(f"  Total validated: {len(df_out)}")
    if "thermal_stability" in df_out.columns:
        print("  Thermal breakdown:")
        for k, v in df_out["thermal_stability"].value_counts().items():
            print(f"    {k}: {v}")
    if "gpr_sigma_RT_bulk_S_cm" in df_out.columns:
        top = df_out.dropna(subset=["gpr_sigma_RT_bulk_S_cm"]).nlargest(5, "gpr_sigma_RT_bulk_S_cm")
        print("\n  Top 5 by GPR σ_RT:")
        for _, r in top.iterrows():
            print(f"    {r['formula']:<55} σ={r['gpr_sigma_RT_bulk_S_cm']:.3e} S/cm  {r.get('thermal_stability','')}")

    return df_out


# ════════════════════════════════════════════════════════════════════════════
#  STEP EA-5: Thermodynamic Stability (Materials Project hull)
# ════════════════════════════════════════════════════════════════════════════
def run_ea_step5(validated_df=None):
    print("\n" + "=" * 70)
    print("  EA STEP 5 — Thermodynamic Stability (MP Hull)")
    print("=" * 70)

    EA_ROOT      = ROOT / "earth_abundant"
    VALIDATED_CSV = EA_ROOT / "data" / "results" / "ea_validated_candidates.csv"
    STRUCTURES    = EA_ROOT / "structures"
    OUTPUT_CSV    = EA_ROOT / "data" / "results" / "ea_thermodynamic_stability.csv"

    if not MP_API_KEY:
        print("  SKIPPED: MP_API_KEY not provided.")
        print("  To enable hull check, re-run with: --mp-key YOUR_KEY")
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["formula","e_above_hull_eV_atom","hull_status"]).to_csv(OUTPUT_CSV, index=False)
        return None

    if validated_df is None:
        if not VALIDATED_CSV.exists():
            print(f"  ERROR: {VALIDATED_CSV} not found. Run EA Step 4 first.")
            return None
        validated_df = pd.read_csv(VALIDATED_CSV)

    from pymatgen.core import Structure
    from pymatgen.ext.matproj import MPRester
    from pymatgen.analysis.phase_diagram import PhaseDiagram
    from pymatgen.entries.computed_entries import ComputedEntry

    stable_mask = validated_df.get("delta_E_vs_LLZO", pd.Series([0]*len(validated_df))) < 0
    stable_df   = validated_df[stable_mask].copy().reset_index(drop=True)
    print(f"  Candidates: {len(validated_df)} total, {len(stable_df)} thermally stable → hull check")

    results = []
    for _, row in stable_df.iterrows():
        formula  = row["formula"]
        cif_path = STRUCTURES / f"{formula}.cif"
        print(f"\n  {formula}")
        if not cif_path.exists():
            print(f"    CIF not found: {cif_path} — skipped")
            continue
        try:
            struct = Structure.from_file(str(cif_path))
            e_col  = ("chgnet_eval_E_per_atom" if "chgnet_eval_E_per_atom" in row
                      else "chgnet_static_E_per_atom")
            if e_col not in row or pd.isna(row[e_col]):
                print("    No energy column — skipped")
                continue
            struct.energy = float(row[e_col]) * len(struct)

            with MPRester(MP_API_KEY) as mpr:
                chemsys = list(struct.composition.as_dict().keys())
                entries = mpr.get_entries_in_chemsys(chemsys)
                if not entries:
                    print(f"    No MP entries for {struct.composition.reduced_formula}")
                    e_hull = float("inf")
                else:
                    pd_obj    = PhaseDiagram(entries)
                    our_entry = ComputedEntry(
                        composition=struct.composition,
                        energy=struct.energy,
                        entry_id=struct.composition.reduced_formula
                    )
                    e_hull = pd_obj.get_e_above_hull(our_entry)

            tag = ("PASS STABLE" if e_hull < 0.05 else
                   "WARN MARGINAL" if e_hull < 0.1 else "FAIL UNSTABLE")
            print(f"    e_above_hull = {e_hull:.4f} eV/atom  {tag}")
            results.append({
                "formula":              formula,
                "pair":                 row.get("pair",""),
                "Li_pfu":               row.get("Li_pfu",""),
                "delta_E_vs_LLZO":      row.get("delta_E_vs_LLZO",""),
                "thermal_stability":    row.get("thermal_stability",""),
                "e_above_hull_eV_atom": e_hull,
                "hull_status":          tag,
                "is_novel":             row.get("is_novel",""),
            })
        except Exception as e:
            print(f"    Failed: {e}")

    out_df = pd.DataFrame(results)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  Saved: {OUTPUT_CSV}")
    if not out_df.empty:
        print("\n  Top by hull stability (lower = better):")
        print(out_df.sort_values("e_above_hull_eV_atom")
              [["formula","e_above_hull_eV_atom","hull_status"]].head().to_string(index=False))
    return out_df


# ════════════════════════════════════════════════════════════════════════════
#  STEP EA-6: Arrhenius MD → σ_RT
# ════════════════════════════════════════════════════════════════════════════
def run_ea_step6(validated_df=None):
    print("\n" + "=" * 70)
    print("  EA STEP 6 — Arrhenius MD Validation")
    print("=" * 70)

    EA_ROOT       = ROOT / "earth_abundant"
    VALIDATED_CSV = EA_ROOT / "data" / "results" / "ea_validated_candidates.csv"
    STRUCTURES    = EA_ROOT / "structures"
    OUTPUT_CSV    = EA_ROOT / "data" / "results" / "ea_finalresults.csv"
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    if validated_df is None:
        if not VALIDATED_CSV.exists():
            print(f"  ERROR: {VALIDATED_CSV} not found. Run EA Step 4 first.")
            return None
        validated_df = pd.read_csv(VALIDATED_CSV)

    # Select top N stable candidates (ΔE < 0), most stable first
    if "delta_E_vs_LLZO" in validated_df.columns:
        stable = validated_df[validated_df["delta_E_vs_LLZO"] < 0].copy()
        stable = stable.sort_values("delta_E_vs_LLZO").head(N_CANDIDATES).reset_index(drop=True)
    else:
        stable = validated_df.head(N_CANDIDATES).reset_index(drop=True)

    if stable.empty:
        # Fallback: use all candidates regardless of thermal stability
        print("  No candidates with ΔE<0 found. Using all validated candidates.")
        stable = validated_df.head(N_CANDIDATES).reset_index(drop=True)

    print(f"  Selected {len(stable)} candidates for MD (max {N_CANDIDATES} — GPU-safe limit):")
    for _, r in stable.iterrows():
        dE = r.get("delta_E_vs_LLZO", "?")
        dE_str = f"{dE:.4f}" if isinstance(dE, float) else str(dE)
        print(f"    {r['formula']}  ΔE={dE_str}")

    _, _, calc = load_chgnet()

    final_results = []
    for _, row in stable.iterrows():
        formula  = str(row["formula"])
        cif_path = STRUCTURES / f"{formula}.cif"

        if not cif_path.exists():
            print(f"\n  Skipping {formula}: CIF not found at {cif_path}")
            continue

        print(f"\n  {'-'*55}")
        print(f"  Processing: {formula}")
        print(f"  {'-'*55}")
        print(vram_status())

        Ea_eV, sigma_RT, diffs = run_md_arrhenius(cif_path, calc, n_steps=MD_STEPS)

        if Ea_eV is None:
            print("  Insufficient MD data — skipping Arrhenius fit.")
            continue

        print(f"  Ea    = {Ea_eV:.3f} eV")
        print(f"  σ_RT  = {sigma_RT:.3e} S/cm")

        result = {
            "formula":               formula,
            "pair":                  row.get("pair",""),
            "Li_pfu":                row.get("Li_pfu",""),
            "delta_E_vs_LLZO":       row.get("delta_E_vs_LLZO",""),
            "activation_energy_eV":  Ea_eV,
            "sigma_RT_S_cm":         sigma_RT,
            "is_novel":              row.get("is_novel", True),
        }
        for temp, v in diffs.items():
            result[f"D_{temp}K_cm2_s"] = v
        final_results.append(result)
        gpu_cleanup()
        time.sleep(3)  # 3-second cool-down between MD candidates (RTX 3050 protection)

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  EA MD Validation complete. Saved to: {OUTPUT_CSV}")

    if not results_df.empty:
        print("\n  Top EA candidates by σ_RT:")
        print(results_df.sort_values("sigma_RT_S_cm", ascending=False)
              [["formula","sigma_RT_S_cm","activation_energy_eV"]].to_string(index=False))
    return results_df


# ════════════════════════════════════════════════════════════════════════════
#  STEP STD-5: Standard Pipeline MD → σ_RT
# ════════════════════════════════════════════════════════════════════════════
def run_std_md():
    print("\n" + "=" * 70)
    print("  STANDARD PIPELINE STEP 5 — Arrhenius MD Validation")
    print("=" * 70)

    EVALUATED_CSV = ROOT / "01_data" / "results" / "evaluated_top_candidates.csv"
    RELAXED_DIR   = ROOT / "03_structures" / "relaxed"
    OUTPUT_CSV    = ROOT / "01_data" / "results" / "finalresults.csv"
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    if not EVALUATED_CSV.exists():
        print(f"  ERROR: {EVALUATED_CSV} not found. Run step3 first.")
        return None

    df = pd.read_csv(EVALUATED_CSV)
    f_col = "formula" if "formula" in df.columns else "Formula"

    # Sort by predicted conductivity (highest first), take top N
    if "predicted_conductivity" in df.columns:
        df = df.sort_values("predicted_conductivity", ascending=False)
    candidates = df.head(N_CANDIDATES)

    print(f"  Top {len(candidates)} candidates for MD (by GPR conductivity):")
    for _, r in candidates.iterrows():
        cond = r.get("predicted_conductivity", "?")
        cond_str = f"{cond:.3e}" if isinstance(cond, float) else str(cond)
        print(f"    {r[f_col]}  σ_pred={cond_str}")

    _, _, calc = load_chgnet()

    final_results = []
    for _, row in candidates.iterrows():
        formula = str(row[f_col])

        # Resolve CIF path — remap old D:\doped_2 paths to current ROOT
        if "relaxed_cif_path" in row and pd.notna(row["relaxed_cif_path"]):
            old_path = str(row["relaxed_cif_path"])
            # Remap D:\doped_2 → current ROOT
            fname    = Path(old_path).name
            cif_path = RELAXED_DIR / fname
        else:
            cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"

        if not cif_path.exists():
            print(f"\n  Skipping {formula}: CIF not found at {cif_path}")
            continue

        print(f"\n  {'='*55}")
        print(f"  Processing: {formula}")
        print(f"  {'='*55}")
        print(vram_status())

        Ea_eV, sigma_RT, diffs = run_md_arrhenius(cif_path, calc, n_steps=MD_STEPS)

        if Ea_eV is None:
            print("  Insufficient MD data — skipping.")
            continue

        print(f"  Ea    = {Ea_eV:.3f} eV")
        print(f"  σ_RT  = {sigma_RT:.3e} S/cm")

        result = {
            "formula":                           formula,
            "md_validated_conductivity_S_cm":    sigma_RT,
            "md_validated_activation_energy_eV": Ea_eV,
            "gpr_predicted_conductivity":        row.get("predicted_conductivity",""),
        }
        for temp, v in diffs.items():
            result[f"D_{temp}K_cm2_s"] = v
        final_results.append(result)
        gpu_cleanup()
        time.sleep(3)  # 3-second cool-down between Std MD candidates (RTX 3050)

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n  Standard MD complete. Saved to: {OUTPUT_CSV}")

    if not results_df.empty:
        print("\n  Results by σ_RT (S/cm):")
        print(results_df.sort_values("md_validated_conductivity_S_cm", ascending=False)
              [["formula","md_validated_conductivity_S_cm","md_validated_activation_energy_eV"]]
              .to_string(index=False))
    return results_df


# ════════════════════════════════════════════════════════════════════════════
#  MAIN EXECUTION
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    ea_validated = None
    ea_hull      = None
    ea_md        = None
    std_md       = None

    # EA Step 4
    if not args.skip_ea4:
        try:
            ea_validated = run_ea_step4()
        except Exception as e:
            print(f"\n[ERROR] EA Step 4 failed: {e}")
            traceback.print_exc()
    else:
        print("\n[SKIP] EA Step 4")

    # EA Step 5
    if not args.skip_ea5:
        try:
            ea_hull = run_ea_step5(ea_validated)
        except Exception as e:
            print(f"\n[ERROR] EA Step 5 failed: {e}")
            traceback.print_exc()
    else:
        print("\n[SKIP] EA Step 5")

    # EA Step 6
    if not args.skip_ea6:
        try:
            ea_md = run_ea_step6(ea_validated)
        except Exception as e:
            print(f"\n[ERROR] EA Step 6 failed: {e}")
            traceback.print_exc()
    else:
        print("\n[SKIP] EA Step 6")

    # Standard Pipeline MD
    if not args.skip_std_md:
        try:
            std_md = run_std_md()
        except Exception as e:
            print(f"\n[ERROR] Standard Pipeline MD failed: {e}")
            traceback.print_exc()
    else:
        print("\n[SKIP] Standard Pipeline MD")

    # ── Final summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  ALL STEPS COMPLETE — FINAL SUMMARY")
    print("=" * 70)

    if ea_md is not None and not ea_md.empty:
        print("\n  Earth-Abundant Pipeline — σ_RT Results:")
        best = ea_md.sort_values("sigma_RT_S_cm", ascending=False)
        for _, r in best.iterrows():
            print(f"    {r['formula']:<55}  σ_RT={r['sigma_RT_S_cm']:.3e}  Ea={r['activation_energy_eV']:.3f} eV")

    if std_md is not None and not std_md.empty:
        print("\n  Standard Pipeline — σ_RT Results:")
        best = std_md.sort_values("md_validated_conductivity_S_cm", ascending=False)
        for _, r in best.iterrows():
            print(f"    {r['formula']:<55}  σ_RT={r['md_validated_conductivity_S_cm']:.3e}  Ea={r['md_validated_activation_energy_eV']:.3f} eV")

    print("\n  Output files:")
    print(f"    EA validated:    earth_abundant/data/results/ea_validated_candidates.csv")
    print(f"    EA thermal:      earth_abundant/data/results/ea_thermal_stability.csv")
    print(f"    EA GPR preds:    earth_abundant/data/results/ea_gpr_predictions.csv")
    print(f"    EA hull:         earth_abundant/data/results/ea_thermodynamic_stability.csv")
    print(f"    EA final MD:     earth_abundant/data/results/ea_finalresults.csv")
    print(f"    Std final MD:    01_data/results/finalresults.csv")
    print("=" * 70)
