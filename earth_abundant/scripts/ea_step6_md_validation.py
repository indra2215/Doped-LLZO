"""
ea_step6_md_validation.py
==============================================================================
EARTH-ABUNDANT PIPELINE — Step 6: Arrhenius MD Validation
==============================================================================

Runs NVT Langevin molecular dynamics at 600 / 800 / 1000 K for the top 5
thermally stable EA candidates, then fits an Arrhenius model to extract:
  • Diffusion coefficient D(T) at each temperature
  • Activation energy Ea (eV)
  • Room-temperature ionic conductivity σ_RT (S/cm) via Nernst-Einstein

Input
-----
  ea_validated_candidates.csv  (for candidate list)
  earth_abundant/structures/   (CIF files from ea_step4_validate.py)

Output
------
  earth_abundant/data/results/ea_finalresults.csv

Candidate selection
-------------------
  Candidates with thermal_stability containing "STABLE" (i.e. delta_E_vs_LLZO < 0),
  sorted by delta_E_vs_LLZO ascending (most stable first), top 5 selected.

Physics
-------
  MSD computed with incremental PBC-unwrapping (fixes snapshot-subtraction bug).
  D = slope(MSD vs t) / 6   [cm²/s]
  σ = n·q²·D / (kB·T)       [S/cm]   (Nernst-Einstein, n = Li density)
"""

import warnings
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from ase import units
from ase.io import read
from ase.md.langevin import Langevin
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from chgnet.model import CHGNet
from chgnet.model.dynamics import CHGNetCalculator

warnings.filterwarnings("ignore")

# -- Paths ----------------------------------------------------------------------
EA_ROOT       = Path(__file__).parent.parent
VALIDATED_CSV = EA_ROOT / "data" / "results" / "ea_validated_candidates.csv"
STRUCTURES    = EA_ROOT / "structures"
OUTPUT_CSV    = EA_ROOT / "data" / "results" / "ea_finalresults.csv"

# -- MD Parameters --------------------------------------------------------------
MD_STEPS     = 1_000     # Short run for quick validation
TIME_STEP    = 2.0       # fs
TEMPERATURES = [600, 800, 1000]   # K
N_CANDIDATES = 5                  # top N thermally stable to run MD on


def run_md(cif_path: Path, temp: int):
    """
    NVT Langevin MD for one structure at one temperature.
    Returns (diffusivity_cm2_s, msd_values) or (None, None) on failure.
    """
    try:
        atoms = read(str(cif_path))
        if not any(atom.symbol == 'Li' for atom in atoms):
            print(f"    No Li atoms in {cif_path.name}.")
            return None, None

        chgnet     = CHGNet.load()
        calculator = CHGNetCalculator(model=chgnet)
        atoms.set_calculator(calculator)

        MaxwellBoltzmannDistribution(atoms, temperature_K=temp)
        dyn = Langevin(atoms, timestep=TIME_STEP * units.fs,
                       temperature_K=temp, friction=0.02)

        li_idx       = [a.index for a in atoms if a.symbol == 'Li']
        cell_lengths = atoms.get_cell().lengths()

        prev_pos       = atoms.get_positions()[li_idx].copy()
        cumulative_disp = np.zeros((len(li_idx), 3))
        msd_values     = []

        def log_msd(a=atoms):
            nonlocal prev_pos, cumulative_disp
            curr  = a.get_positions()[li_idx]
            delta = curr - prev_pos
            delta -= np.round(delta / cell_lengths) * cell_lengths  # PBC unwrap
            cumulative_disp  += delta
            prev_pos          = curr.copy()
            msd_values.append(np.mean(np.sum(cumulative_disp ** 2, axis=1)))

        dyn.attach(log_msd, interval=100)
        dyn.run(MD_STEPS)

        time_arr = np.arange(len(msd_values)) * 100 * TIME_STEP * 1e-15  # s
        fit_start = len(time_arr) // 2
        slope, _ = np.polyfit(time_arr[fit_start:], msd_values[fit_start:], 1)
        D_cm2_s   = (slope / 6.0) * 1e-16   # Å²/s -> cm²/s

        return D_cm2_s, msd_values

    except Exception as e:
        print(f"    MD error at {temp}K: {e}")
        traceback.print_exc()
        return None, None


def main():
    print("=" * 65)
    print("EA PIPELINE — Step 6: Arrhenius MD Validation")
    print("=" * 65)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    if not VALIDATED_CSV.exists():
        print(f"ERROR: {VALIDATED_CSV} not found.")
        print("  Run ea_step4_validate.py first.")
        return

    df = pd.read_csv(VALIDATED_CSV)

    # Select top N thermally stable candidates (ΔE < 0, sorted most stable first)
    if 'delta_E_vs_LLZO' in df.columns:
        stable = df[df['delta_E_vs_LLZO'] < 0].copy()
        stable = stable.sort_values('delta_E_vs_LLZO').head(N_CANDIDATES).reset_index(drop=True)
    else:
        stable = df.head(N_CANDIDATES).reset_index(drop=True)

    print(f"Selected {len(stable)} candidates for MD validation:")
    for _, r in stable.iterrows():
        print(f"  {r['formula']}  ΔE={r.get('delta_E_vs_LLZO', '?'):.4f} eV/atom")

    final_results = []

    for _, row in stable.iterrows():
        formula  = row['formula']
        cif_path = STRUCTURES / f"{formula}.cif"

        if not cif_path.exists():
            print(f"\nSkipping {formula}: CIF not found at {cif_path}")
            continue

        print(f"\n{'-'*55}")
        print(f"Processing: {formula}")
        print(f"{'-'*55}")

        diffusivities = {}
        for temp in TEMPERATURES:
            print(f"  Running MD at {temp} K...")
            D, _ = run_md(cif_path, temp)
            if D is not None and D > 0:
                diffusivities[temp] = D
                print(f"    D({temp}K) = {D:.4e} cm²/s")

        if len(diffusivities) < 2:
            print("  Insufficient data points for Arrhenius fit — skipping.")
            continue

        # Arrhenius: ln(D) = ln(D0) - Ea/(kB·T)
        temps     = np.array(list(diffusivities.keys()))
        inv_temps = 1.0 / temps
        log_D     = np.log(list(diffusivities.values()))
        slope, intercept = np.polyfit(inv_temps, log_D, 1)
        Ea_eV     = -slope * units.kB

        D_RT = np.exp(np.polyval([slope, intercept], 1.0 / 298.15))

        atoms        = read(str(cif_path))
        li_count     = sum(1 for a in atoms if a.symbol == 'Li')
        volume_cm3   = atoms.get_volume() * 1e-24
        n_Li_per_cm3 = li_count / volume_cm3
        q            = 1.602e-19
        kB_SI        = 1.381e-23
        T_RT         = 298.15

        sigma_RT = (D_RT * n_Li_per_cm3 * q**2) / (kB_SI * T_RT)

        print(f"  Ea    = {Ea_eV:.3f} eV")
        print(f"  σ_RT  = {sigma_RT:.3e} S/cm")

        result = {
            'formula':                 formula,
            'pair':                    row.get('pair', ''),
            'Li_pfu':                  row.get('Li_pfu', ''),
            'delta_E_vs_LLZO':         row.get('delta_E_vs_LLZO', ''),
            'activation_energy_eV':    Ea_eV,
            'sigma_RT_S_cm':           sigma_RT,
            'is_novel':                row.get('is_novel', True),
        }
        for temp, v in diffusivities.items():
            result[f'D_{temp}K_cm2_s'] = v
        final_results.append(result)

    results_df = pd.DataFrame(final_results)
    results_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n{'='*65}")
    print(f"EA MD Validation complete. Results saved to: {OUTPUT_CSV}")

    if not results_df.empty:
        print("\nTop EA candidates by σ_RT:")
        print(results_df.sort_values('sigma_RT_S_cm', ascending=False)
              [['formula', 'sigma_RT_S_cm', 'activation_energy_eV', 'delta_E_vs_LLZO']]
              .to_string(index=False))


if __name__ == '__main__':
    main()

