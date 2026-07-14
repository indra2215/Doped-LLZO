"""
md.py  ── CHGNet NVT Molecular Dynamics for LLZO candidates
═══════════════════════════════════════════════════════════════
Fixes applied vs original:
  1. Added `import gc` (was referenced but never imported → crash at cleanup)
  2. PBC-unwrapped MSD using minimum-image convention (original subtracted raw
     positions, which jump by ±a when an atom crosses a cell boundary, producing
     enormous fake MSD spikes and inflated diffusion coefficients)
  3. Geometry sanity check before MD: rejects CIFs with vol/atom outside
     the garnet-family valid range [9, 16] Å³ (38.7 Å³ = exploded cell)
  4. Conductivity sanity gate: σ_RT > 0.1 S/cm is physically impossible for
     any solid electrolyte → flagged FAILED_MELT, not written as valid data
  5. Equilibration discard: first EQUIL_FRAC of trajectory thrown away before
     fitting (reduces thermostat-settling artefacts at run start)
  6. TOTAL_STEPS bumped to 5000 (~10 ps) with a note on recommended production
     values; 1000 steps (2 ps) is too short to reach the diffusive regime
  7. Arrhenius extrapolation to RT: single-temperature conductivity is labelled
     as σ(800K), not σ_RT, to avoid misleading room-temperature claims
"""

import gc
import os
import glob
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # headless — no display required
import matplotlib.pyplot as plt

import torch
from ase.io import read
from ase.io.trajectory import Trajectory
from chgnet.model.dynamics import MolecularDynamics

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════
# USER SETTINGS
# ══════════════════════════════════════════════════════════════

CIF_FOLDER    = "cif"
OUTPUT_FOLDER = "results"

TEMPERATURE   = 800          # K
TIMESTEP      = 2            # fs
TOTAL_STEPS   = 5000         # ~10 ps  (increase to 25000+ for production Arrhenius fits)
LOG_INTERVAL  = 100          # frames saved = TOTAL_STEPS // LOG_INTERVAL
EQUIL_FRAC    = 0.3          # discard first 30 % of trajectory before slope fit

LITHIUM_SYMBOL = "Li"

# Garnet family geometry bounds (Å³/atom)
VOL_ATOM_MIN  = 9.0
VOL_ATOM_MAX  = 16.0

# Conductivity ceiling — anything above is a melted/exploded structure
SIGMA_MELT_THRESHOLD = 0.1   # S/cm

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Physical constants
kB = 1.380649e-23   # J/K
q  = 1.602176634e-19  # C

# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════

print("=" * 60)
print("CHGNet Molecular Dynamics — LLZO Candidates")
print("=" * 60)
print(f"Temperature  : {TEMPERATURE} K")
print(f"Steps        : {TOTAL_STEPS}  (~{TOTAL_STEPS * TIMESTEP / 1000:.1f} ps)")
print(f"Timestep     : {TIMESTEP} fs")
print(f"Equil. discard: first {int(EQUIL_FRAC*100)}% of trajectory")
print("=" * 60)

# ══════════════════════════════════════════════════════════════
# FIND CIF FILES
# ══════════════════════════════════════════════════════════════

cif_files = sorted(glob.glob(os.path.join(CIF_FOLDER, "*.cif")))

if len(cif_files) == 0:
    raise RuntimeError(f"No CIF files found in ./{CIF_FOLDER}/")

print(f"\nFound {len(cif_files)} CIF files\n")


def geometry_ok(atoms, name):
    """Return True if vol/atom is within garnet-family valid range."""
    vol_per_atom = atoms.get_volume() / len(atoms)
    if vol_per_atom < VOL_ATOM_MIN:
        print(f"  [GEOMETRY FAIL] {name}: vol/atom = {vol_per_atom:.2f} Å³"
              f" < {VOL_ATOM_MIN} Å³ minimum. Cell likely collapsed.")
        return False
    if vol_per_atom > VOL_ATOM_MAX:
        print(f"  [GEOMETRY FAIL] {name}: vol/atom = {vol_per_atom:.2f} Å³"
              f" > {VOL_ATOM_MAX} Å³ maximum. Cell likely exploded.")
        print(f"  Fix: re-relax with evaluate_candidates_chgnet.py (steps=50/25, fmax=0.1)")
        return False
    print(f"  [GEOMETRY OK]   {name}: vol/atom = {vol_per_atom:.2f} Å³")
    return True


def pbc_unwrap_msd(traj, li_indices):
    """
    Compute Li MSD with PBC minimum-image unwrapping.

    Without unwrapping, when a Li atom crosses a periodic boundary its
    position jumps by ±lattice_vector, producing a huge fake displacement.
    Minimum-image convention: at each step, the incremental displacement
    is wrapped to ±0.5 × cell length in each direction before accumulating.

    Returns: msd array (Å²), one value per trajectory frame.
    """
    first = traj[0]
    cell_lengths = first.get_cell().lengths()   # [a, b, c] in Å

    prev_pos   = first.get_positions()[li_indices].copy()
    cumul_disp = np.zeros((len(li_indices), 3))
    msd_values = []

    for frame in traj:
        curr  = frame.get_positions()[li_indices]
        delta = curr - prev_pos

        # Minimum-image: wrap each component to [-L/2, +L/2]
        delta -= np.round(delta / cell_lengths) * cell_lengths

        cumul_disp += delta
        prev_pos    = curr.copy()

        msd_values.append(np.mean(np.sum(cumul_disp ** 2, axis=1)))

    return np.array(msd_values)


# ══════════════════════════════════════════════════════════════
# PROCESS EACH MATERIAL
# ══════════════════════════════════════════════════════════════

all_results = []

from chgnet.model import CHGNet
print("Loading CHGNet model...")
calculator = CHGNet.load()

for cif_path in cif_files:

    material = os.path.splitext(os.path.basename(cif_path))[0]

    print("\n" + "=" * 70)
    print(f"Processing: {material}")
    print("=" * 70)

    material_dir = os.path.join(OUTPUT_FOLDER, material)
    os.makedirs(material_dir, exist_ok=True)
    results_file = os.path.join(material_dir, "results.csv")

    if os.path.exists(results_file):
        print(f"  Already completed. Loading existing results...")
        existing = pd.read_csv(results_file)
        all_results.append(existing)
        continue

    # ── Read structure ──────────────────────────────────────────
    atoms = read(cif_path)

    n_atoms = len(atoms)
    vol_A3  = atoms.get_volume()
    li_indices = [i for i, a in enumerate(atoms) if a.symbol == LITHIUM_SYMBOL]
    li_count   = len(li_indices)

    print(f"  Total atoms : {n_atoms}")
    print(f"  Li atoms    : {li_count}")
    print(f"  Volume      : {vol_A3:.2f} Å³  ({vol_A3/n_atoms:.2f} Å³/atom)")

    # ── Geometry sanity check ───────────────────────────────────
    if not geometry_ok(atoms, material):
        print(f"  SKIPPING {material} — geometry outside garnet range.")
        row = pd.DataFrame([{
            "Material": material, "Temperature_K": TEMPERATURE,
            "Li_atoms": li_count, "Volume_A3": vol_A3,
            "vol_per_atom_A3": vol_A3 / n_atoms,
            "Number_Density_cm3": None, "Slope_A2_per_ps": None,
            "Diffusion_cm2_s": None, "Conductivity_S_cm": None,
            "md_status": "GEOMETRY_FAIL"
        }])
        row.to_csv(results_file, index=False)
        all_results.append(row)
        continue

    if li_count == 0:
        print("  No Li atoms found. Skipping.")
        continue

    # ── GPU info ────────────────────────────────────────────────
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        free, total = torch.cuda.mem_get_info()
        print(f"  VRAM free/total: {free/1e9:.1f}/{total/1e9:.1f} GB")
    else:
        print("  GPU: not available (running on CPU — expect slower MD)")

    # ── MD run ──────────────────────────────────────────────────
    trajectory_file = os.path.join(material_dir, "trajectory.traj")
    logfile         = os.path.join(material_dir, "md.log")
    crystal_log     = os.path.join(material_dir, "crystal.log")

    print(f"  Initializing CHGNet NVT MD ({TOTAL_STEPS} steps × {TIMESTEP} fs = "
          f"{TOTAL_STEPS*TIMESTEP/1000:.1f} ps)...")

    md = MolecularDynamics(
        atoms=atoms,
        model=calculator,
        temperature=TEMPERATURE,
        timestep=TIMESTEP,
        ensemble="nvt",
        trajectory=trajectory_file,
        logfile=logfile,
        loginterval=LOG_INTERVAL,
        append_trajectory=False
    )

    md.run(TOTAL_STEPS)
    print("  MD finished.")

    # ── Load trajectory ─────────────────────────────────────────
    traj = Trajectory(trajectory_file)
    n_frames = len(traj)
    print(f"  Trajectory frames: {n_frames}")

    if n_frames < 10:
        print("  Too few frames. Skipping.")
        continue

    # ── PBC-unwrapped MSD ───────────────────────────────────────
    print("  Computing PBC-unwrapped MSD...")
    msd = pbc_unwrap_msd(traj, li_indices)

    # Time axis in ps
    time_ps = np.arange(n_frames) * TIMESTEP * LOG_INTERVAL / 1000.0

    # ── Save MSD CSV ────────────────────────────────────────────
    msd_df = pd.DataFrame({"Time_ps": time_ps, "MSD_A2": msd})
    msd_csv = os.path.join(material_dir, "msd.csv")
    msd_df.to_csv(msd_csv, index=False)

    # ── MSD plot ────────────────────────────────────────────────
    plt.figure(figsize=(7, 5))
    plt.plot(time_ps, msd, linewidth=2)
    plt.xlabel("Time (ps)")
    plt.ylabel("MSD (Å²)")
    plt.title(material)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(material_dir, "msd.png"), dpi=300)
    plt.close()

    # ── Linear fit — discard equilibration fraction ─────────────
    equil_frames = max(1, int(n_frames * EQUIL_FRAC))
    fit_time = time_ps[equil_frames:]
    fit_msd  = msd[equil_frames:]

    if len(fit_time) < 5:
        print("  Not enough post-equilibration frames for fitting.")
        continue

    slope, intercept = np.polyfit(fit_time, fit_msd, 1)
    # slope units: Å²/ps  (MSD in Å², time in ps)

    # D = slope / 6  (3D Einstein relation: MSD = 6Dt)
    # Å²/ps × 1e-4 = cm²/s  (1 Å² = 1e-16 cm², 1 ps = 1e-12 s → ×1e-4)
    D_cm2_s = (slope / 6.0) * 1e-4

    print(f"  MSD slope  = {slope:.4f} Å²/ps")
    print(f"  D({TEMPERATURE}K) = {D_cm2_s:.4e} cm²/s")

    # ── Fitted MSD plot ─────────────────────────────────────────
    fitted = slope * fit_time + intercept
    plt.figure(figsize=(7, 5))
    plt.plot(time_ps, msd, linewidth=2, label="MSD (PBC-unwrapped)")
    plt.plot(fit_time, fitted, "--", linewidth=2, label="Linear fit")
    plt.xlabel("Time (ps)")
    plt.ylabel("MSD (Å²)")
    plt.title(material)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(material_dir, "msd_fit.png"), dpi=300)
    plt.close()

    # ── Nernst-Einstein conductivity at simulation temperature ──
    volume_cm3     = vol_A3 * 1e-24
    number_density = li_count / volume_cm3
    sigma_T        = (number_density * q**2 * D_cm2_s) / (kB * TEMPERATURE)

    print(f"  σ({TEMPERATURE}K) = {sigma_T:.4e} S/cm")
    print(f"  Note: this is conductivity AT {TEMPERATURE} K, not σ_RT.")
    print(f"  For σ_RT, run at 600/800/1000 K and perform Arrhenius extrapolation.")

    # ── Conductivity sanity gate ────────────────────────────────
    if sigma_T > SIGMA_MELT_THRESHOLD:
        md_status = "FAILED_MELT"
        print(f"  [CONDUCTIVITY FAIL] σ({TEMPERATURE}K) = {sigma_T:.3e} S/cm "
              f"> {SIGMA_MELT_THRESHOLD} S/cm threshold.")
        print(f"  This is physically impossible for a solid — melted/exploded structure.")
        print(f"  Result flagged md_status=FAILED_MELT. Do not use for reporting.")
    else:
        md_status = "OK"

    # ── Save per-material results ────────────────────────────────
    row = pd.DataFrame([{
        "Material":           material,
        "Temperature_K":      TEMPERATURE,
        "Li_atoms":           li_count,
        "Volume_A3":          vol_A3,
        "vol_per_atom_A3":    vol_A3 / n_atoms,
        "Number_Density_cm3": number_density,
        "Slope_A2_per_ps":    slope,
        "Diffusion_cm2_s":    D_cm2_s,
        f"Conductivity_{TEMPERATURE}K_S_cm": sigma_T,
        "md_status":          md_status
    }])
    row.to_csv(results_file, index=False)
    all_results.append(row)

    print("  Results saved.")

    # ── Cleanup ──────────────────────────────────────────────────
    del md, traj
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("=" * 60)
    print(f"{material}  COMPLETED  [{md_status}]")
    print("=" * 60)

# ══════════════════════════════════════════════════════════════
# MASTER SUMMARY
# ══════════════════════════════════════════════════════════════

if all_results:
    summary_df = pd.concat(all_results, ignore_index=True)
    summary_file = os.path.join(OUTPUT_FOLDER, "summary.csv")
    summary_df.to_csv(summary_file, index=False)
    print(f"\nSummary saved → {summary_file}")
    print(summary_df[["Material", "Diffusion_cm2_s",
                       f"Conductivity_{TEMPERATURE}K_S_cm",
                       "md_status"]].to_string(index=False))

print("\n" + "=" * 70)
print("ALL MATERIALS FINISHED")
print("=" * 70)
print(f"Results saved in: ./{OUTPUT_FOLDER}/")
print("=" * 70)