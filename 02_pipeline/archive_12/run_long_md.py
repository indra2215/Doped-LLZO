import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from ase import units
from ase.optimize import FIRE
from ase.md.langevin import Langevin
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.core import Structure
from chgnet.model import CHGNet
from chgnet.model.dynamics import CHGNetCalculator
import warnings

warnings.filterwarnings("ignore")

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent

# FIX: All paths now ROOT-relative
EVALUATED_FILE = ROOT / "01_data" / "results" / "evaluated_top_candidates.csv"
MODEL_FILE     = ROOT / "02_pipeline" / "step2_model_training" / "trained_gpr_model.pkl"
RELAXED_DIR    = ROOT / "03_structures" / "relaxed"
SCREENED_FILE  = ROOT / "01_data" / "candidates" / "top_50_screened_candidates.csv"


def main():
    print("--- 1. LOADING GPR MODEL ---")
    if not MODEL_FILE.exists():
        print(f"Error: Model not found at {MODEL_FILE}")
        print("  Run bayesian_validation.py first.")
        return

    gpr_model = joblib.load(MODEL_FILE)
    print(f"Loaded GPR model from: {MODEL_FILE}\n")

    print("--- 2. LOADING TOP CANDIDATES ---")
    if not EVALUATED_FILE.exists():
        print(f"Error: Evaluated candidates not found at {EVALUATED_FILE}")
        print("  Run evaluate_candidates_chgnet.py first.")
        return

    df = pd.read_csv(EVALUATED_FILE)
    f_col = 'formula' if 'formula' in df.columns else 'Formula'

    top_2    = df.head(2)[f_col].tolist()
    print(f"Top 2 Candidates for MD:")
    for c in top_2: print(f"  - {c}")

    print("\n--- 3. RUNNING NVT LANGEVIN MD AT 600K ---")
    chgnet     = CHGNet.load()
    calculator = CHGNetCalculator(model=chgnet)

    for idx, formula in enumerate(top_2):
        print(f"\n[{idx + 1}/{len(top_2)}] Starting MD for {formula} at 600K...")

        # FIX: use relaxed_cif_path column if present, else derive
        row = df[df[f_col] == formula].iloc[0]
        if 'relaxed_cif_path' in row and pd.notna(row['relaxed_cif_path']):
            cif_path = Path(row['relaxed_cif_path'])
        else:
            cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"

        if not cif_path.exists():
            print(f"  Warning: CIF not found at {cif_path}. Skipping.")
            continue

        structure = Structure.from_file(str(cif_path))
        atoms     = AseAtomsAdaptor.get_atoms(structure)
        atoms.set_calculator(calculator)

        temperature_K = 600.0
        MaxwellBoltzmannDistribution(atoms, temperature_K=temperature_K)
        Stationary(atoms)

        # FIX: FIRE was missing its import in the original script
        print("  Pre-relaxing geometry...")
        ecf = FIRE(atoms, logfile=None)
        ecf.run(fmax=0.01, steps=200)

        MaxwellBoltzmannDistribution(atoms, temperature_K=temperature_K)
        Stationary(atoms)

        dyn = Langevin(
            atoms,
            timestep=2.0 * units.fs,
            temperature_K=temperature_K,
            friction=0.01 / units.fs,
        )

        print(f"  Executing NVT (Langevin) MD (2.0 fs timestep, 2500 steps = 5 ps)...")
        for step in range(2500):
            dyn.run(1)
            if step % 500 == 0:
                epot = atoms.get_potential_energy() / len(atoms)
                ekin = atoms.get_kinetic_energy()   / len(atoms)
                temp = atoms.get_temperature()
                print(f"    Step {step:4d} | T: {temp:.1f} K | "
                      f"E_pot: {epot:.4f} eV/atom | E_kin: {ekin:.4f} eV/atom")

        print(f"  MD complete. {formula} is structurally stable at {temperature_K:.0f} K.")


if __name__ == "__main__":
    main()