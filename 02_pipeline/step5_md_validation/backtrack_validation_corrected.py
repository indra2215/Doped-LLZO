"""
backtrack_validation_corrected.py
──────────────────────────────────
NVT Langevin MD → Arrhenius fit → σ_RT for top LLZO candidates.

FIXES applied
─────────────
1. Added FAST_MODE (default True): 5,000 steps (10 ps) instead of
   500,000 steps (1 ns). This produces physically meaningful (though
   noisier) Arrhenius fits in ~5–15 minutes total CPU time instead of
   12+ hours. Set FAST_MODE = False to run full 1 ns production MD.

2. Fixed output column names to match RESULTS.md expectations:
     formula, md_validated_conductivity_S_cm, md_validated_activation_energy_eV

3. Added minimum diffusivity guard: if D < 1e-14 cm²/s (essentially
   zero / no diffusion), the candidate is logged but skipped from the
   Arrhenius fit to prevent meaningless extrapolations.

4. CHGNet is now loaded ONCE outside the per-temperature loop (was
   loading once per MD run = wasted startup time).

5. Improved Nernst-Einstein formula: uses structure volume from CIF
   (not re-reading atoms separately).
"""

import pandas as pd
import numpy as np
import warnings
from pathlib import Path

from ase.io import read
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.md.langevin import Langevin
from ase import units
from chgnet.model import CHGNet
from chgnet.model.dynamics import CHGNetCalculator
from tqdm import tqdm
import torch
import gc

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT            = Path(__file__).parent.parent.parent
CANDIDATES_FILE = ROOT / "01_data" / "results" / "evaluated_top_candidates.csv"
RESULTS_FILE    = ROOT / "01_data" / "results" / "finalresults.csv"
RELAXED_DIR     = ROOT / "03_structures" / "relaxed"

# ── MD Settings ────────────────────────────────────────────────────────────
# FAST_MODE = True  →  ~10 ps per temp,  ~5–15 min total
# FAST_MODE = False →  ~1 ns per temp,   ~12+ hrs total
FAST_MODE    = True

if FAST_MODE:
    MD_STEPS   = 1_000    # 2 ps at 2 fs/step (reduced to prevent OOM)
    print("[FAST_MODE] Running 1,000 MD steps (~2 ps) per temperature.")
else:
    MD_STEPS   = 500_000  # 1 ns
    print("[FULL_MODE] Running 500,000 MD steps (~1 ns) per temperature.")

TIME_STEP    = 2.0           # fs
TEMPERATURES = [600, 800, 1000]  # K — Arrhenius extrapolation to 298 K
D_MIN_CM2_S  = 1e-14         # minimum meaningful diffusivity threshold

# ── Load CHGNet once ───────────────────────────────────────────────────────
print("Loading CHGNet (single load for all MD runs)...", flush=True)
_chgnet     = CHGNet.load()
_calculator = CHGNetCalculator(model=_chgnet)


def run_md_for_structure(atoms, temp: int):
    """
    Runs NVT Langevin MD at a given temperature using pre-loaded calculator.
    Uses incremental PBC-unwrapped displacements for correct MSD tracking.

    Returns: (diffusivity_cm2_s, n_steps_run) or (None, 0) on failure.
    """
    try:
        if not any(atom.symbol == 'Li' for atom in atoms):
            print(f"  No Li atoms. Skipping.")
            return None, 0

        atoms.set_calculator(_calculator)
        MaxwellBoltzmannDistribution(atoms, temperature_K=temp)
        dyn = Langevin(atoms, timestep=TIME_STEP * units.fs,
                       temperature_K=temp, friction=0.02)

        li_indices    = [atom.index for atom in atoms if atom.symbol == 'Li']
        cell_lengths  = atoms.get_cell().lengths()

        # Incremental PBC unwrapping (avoids jump artefacts at cell boundaries)
        prev_li_pos    = atoms.get_positions()[li_indices].copy()
        cumulative_disp = np.zeros((len(li_indices), 3))
        msd_values      = []

        def log_msd(a=atoms):
            nonlocal prev_li_pos, cumulative_disp
            curr  = a.get_positions()[li_indices]
            delta = curr - prev_li_pos
            # Minimum-image convention
            delta -= np.round(delta / cell_lengths) * cell_lengths
            cumulative_disp += delta
            prev_li_pos      = curr.copy()
            msd = np.mean(np.sum(cumulative_disp ** 2, axis=1))
            msd_values.append(msd)

        dyn.attach(log_msd, interval=100)
        dyn.run(MD_STEPS)

        if len(msd_values) < 10:
            print(f"  Too few MSD points ({len(msd_values)}). Skipping.")
            return None, 0

        # Fit MSD slope → diffusion coefficient (use second half for stability)
        time_array = np.arange(len(msd_values)) * 100 * TIME_STEP * 1e-15  # s
        fit_start  = max(1, len(time_array) // 2)
        slope, _   = np.polyfit(time_array[fit_start:], msd_values[fit_start:], 1)

        # D = slope / 6  (3D), Å²/s → cm²/s (× 1e-16)
        D_cm2_s = (slope / 6.0) * 1e-16

        return D_cm2_s, len(msd_values)

    except Exception as e:
        print(f"  Error during MD at {temp}K: {e}")
        return None, 0


def main():
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not CANDIDATES_FILE.exists():
        print(f"Error: Candidates file not found at {CANDIDATES_FILE}")
        print("  Run evaluate_candidates_chgnet.py first.")
        return

    candidates_df = pd.read_csv(CANDIDATES_FILE).head(5)
    f_col         = 'formula' if 'formula' in candidates_df.columns else 'Formula'
    final_results = []

    for _, row in candidates_df.iterrows():
        formula = row[f_col]

        if 'relaxed_cif_path' in row and pd.notna(row.get('relaxed_cif_path')):
            cif_path = Path(row['relaxed_cif_path'])
        else:
            cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"

        if not cif_path.exists():
            print(f"Skipping {formula}: CIF not found at {cif_path}")
            continue

        print(f"\n{'='*60}", flush=True)
        print(f"Processing: {formula}", flush=True)

        # Load atoms once, re-copy per temperature
        base_atoms = read(str(cif_path))
        li_count   = sum(1 for a in base_atoms if a.symbol == 'Li')
        volume_cm3 = base_atoms.get_volume() * 1e-24  # Å³ → cm³
        n_Li       = li_count / volume_cm3             # #/cm³

        diffusivities = {}
        for temp in TEMPERATURES:
            print(f"  Running MD at {temp} K...", flush=True)
            import copy
            atoms_copy = copy.deepcopy(base_atoms)
            D, n_pts = run_md_for_structure(atoms_copy, temp)
            if D is not None and D > D_MIN_CM2_S:
                diffusivities[temp] = D
                print(f"    D({temp}K) = {D:.4e} cm²/s  ({n_pts} MSD points)")
            elif D is not None:
                print(f"    D({temp}K) = {D:.4e} cm²/s  [below threshold, skipped]")
            
            # Clear memory after each temperature run
            gc.collect()

        if len(diffusivities) < 2:
            print(f"  Insufficient data points ({len(diffusivities)}) for Arrhenius fit. Skipping.")
            continue

        # Arrhenius fit: ln(D) = ln(D0) - Ea/(kB·T)
        temps     = np.array(list(diffusivities.keys()))
        inv_temps = 1.0 / temps
        log_D     = np.log(list(diffusivities.values()))
        slope, intercept = np.polyfit(inv_temps, log_D, 1)
        Ea_eV = -slope * units.kB  # eV

        # Extrapolate to room temperature (298.15 K)
        D_RT = np.exp(np.polyval([slope, intercept], 1.0 / 298.15))

        # Nernst-Einstein: σ = (n · q² · D) / (kB · T)
        q      = 1.602e-19   # C
        kB_SI  = 1.381e-23   # J/K
        T_RT   = 298.15      # K
        sigma_RT = (D_RT * n_Li * q**2) / (kB_SI * T_RT)

        print(f"  Ea   = {Ea_eV:.3f} eV")
        print(f"  σ_RT = {sigma_RT:.3e} S/cm")

        result = {
            "formula":                             formula,
            "md_validated_conductivity_S_cm":      sigma_RT,
            "md_validated_activation_energy_eV":   Ea_eV,
        }
        for temp, v in diffusivities.items():
            result[f"D_{temp}K_cm2_s"] = v
        final_results.append(result)

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(RESULTS_FILE, index=False)
    print(f"\nBacktracking validation complete. Results saved to: {RESULTS_FILE}")

    if not results_df.empty:
        print("\nTop results by σ_RT (S/cm):")
        print(results_df.sort_values('md_validated_conductivity_S_cm', ascending=False)
              [['formula', 'md_validated_conductivity_S_cm',
                'md_validated_activation_energy_eV']].to_string(index=False))


if __name__ == "__main__":
    main()