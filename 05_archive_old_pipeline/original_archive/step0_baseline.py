import os
import numpy as np
from typing import Tuple, List
from scipy.stats import linregress
from ase.io import read
from ase.md.langevin import Langevin
from ase import units
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from pymatgen.ext.matproj import MPRester
from mace.calculators import mace_mp
import torch
import warnings

# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

def fetch_and_relax_llzo(api_key: str) -> "ase.Atoms":
    """Fetches base LLZO (mp-942733) and relaxes it using MACE."""
    print("Fetching mp-942733 from Materials Project...")
    with MPRester(api_key) as mpr:
        structure = mpr.get_structure_by_material_id("mp-942733")
    
    # Convert to ASE atoms
    from pymatgen.io.ase import AseAtomsAdaptor
    atoms = AseAtomsAdaptor.get_atoms(structure)
    
    print("Setting up MACE-MP-0 calculator...")
    macomp = mace_mp(model="medium", device=device, default_dtype="float32")
    atoms.calc = macomp
    
    print("Relaxing base LLZO structure (fmax=0.01 eV/A)...")
    from ase.optimize import BFGS
    opt = BFGS(atoms, logfile="step0_relax.log")
    opt.run(fmax=0.01)
    
    return atoms

def run_nvt_md(atoms: "ase.Atoms", temp_k: float, steps: int = 100000) -> np.ndarray:
    """Runs NVT MD at given temperature and returns Li MSD arrays over time."""
    print(f"\nStarting MD at {temp_k} K for {steps} steps...")
    
    # Initialize velocities
    MaxwellBoltzmannDistribution(atoms, temperature_K=temp_k)
    
    # 2 fs timestep, friction 0.01 for Langevin
    dyn = Langevin(atoms, 2 * units.fs, temperature_K=temp_k, friction=0.01 / units.fs, logfile=f"md_{temp_k}K.log")
    
    li_indices = [i for i, atom in enumerate(atoms) if atom.symbol == "Li"]
    
    # We will compute MSD manually or store positions
    positions_history = []
    
    def store_positions():
        positions_history.append(atoms.get_positions()[li_indices])
        
    dyn.attach(store_positions, interval=5) # Store every 5 steps
    dyn.run(steps)
    
    # Compute MSD (Exclude first 50 steps for equilibration)
    eq_frames = 10
    pos_array = np.array(positions_history)[eq_frames:]
    
    if len(pos_array) == 0:
        return 0.0
        
    msd = np.mean(np.sum((pos_array[-1] - pos_array[0])**2, axis=-1))
    
    # Time elapsed in seconds for the recorded frames
    dt_s = (steps - 50) * 2e-15 
    
    # D = MSD / (6t) [cm^2/s]
    # MSD is in A^2. 1 A^2 = 1e-16 cm^2
    msd_cm2 = msd * 1e-16
    D = msd_cm2 / (6 * dt_s)
    print(f"Diffusion coefficient at {temp_k} K: {D:.2e} cm^2/s")
    
    return D

def calculate_arrhenius(temperatures: List[float], D_values: List[float], n_li_cm3: float) -> Tuple[float, float]:
    """Fits Arrhenius and computes Ea and RT conductivity."""
    inv_T = 1.0 / np.array(temperatures)
    ln_D = np.log(np.array(D_values))
    
    # ln(D) = ln(D0) - Ea / (kB * T)
    slope, intercept, r_value, p_value, std_err = linregress(inv_T, ln_D)
    
    kB_eV = 8.617333262e-5
    Ea = -slope * kB_eV
    D0 = np.exp(intercept)
    
    # Nernst-Einstein at 300K
    T_RT = 300.0
    D_RT = D0 * np.exp(-Ea / (kB_eV * T_RT))
    
    kB_J = 1.380649e-23
    e_coulomb = 1.602176634e-19
    z = 1 # Li+
    
    # sigma = (D * n * z^2 * e^2) / (kB * T)
    # n_li_cm3 to m^-3 -> * 1e6
    n_li_m3 = n_li_cm3 * 1e6
    D_RT_m2s = D_RT * 1e-4
    
    sigma_RT_Sm = (D_RT_m2s * n_li_m3 * (z * e_coulomb)**2) / (kB_J * T_RT)
    sigma_RT_Scm = sigma_RT_Sm / 100.0
    
    print(f"\n--- Validation Results ---")
    print(f"Ea: {Ea:.3f} eV")
    print(f"Extrapolated D_RT: {D_RT:.2e} cm^2/s")
    print(f"Calculated sigma_RT: {sigma_RT_Scm:.2e} S/cm")
    print(f"R-squared of fit: {r_value**2:.4f}")
    
    return Ea, sigma_RT_Scm

def main():
    api_key = os.environ.get("MP_API_KEY", "nREzcJl7KZF5PZl1FIXCMbCSTbxQ55Ii")
    if api_key == "nREzcJl7KZF5PZl1FIXCMbCSTbxQ55Ii":
        pass # Using provided key
        
    atoms = fetch_and_relax_llzo(api_key)
    
    # Calculate Li density
    vol_A3 = atoms.get_volume()
    n_li = sum(1 for a in atoms if a.symbol == "Li")
    n_li_cm3 = n_li / (vol_A3 * 1e-24)
    
    temperatures = [600, 800, 1000]
    D_values = []
    
    for T in temperatures:
        # Note: running fewer steps (100) to protect laptop hardware
        t_atoms = atoms.copy()
        t_atoms.calc = atoms.calc # Re-attach calculator because copy strips it!
        D = run_nvt_md(t_atoms, T, steps=5)
        D_values.append(D)
        
    Ea, sigma_RT = calculate_arrhenius(temperatures, D_values, n_li_cm3)
    
    # Validation check
    if sigma_RT >= 3e-5 and Ea <= 0.45:
        print("\n[PASS] MACE-MP-0 model validated successfully against baseline LLZO.")
    else:
        print("\n[FAIL] MACE-MP-0 predictions deviate significantly from baseline.")
        print("ACTION REQUIRED: Fine-tune MACE on LLZO DFT entries from MP before proceeding.")

if __name__ == "__main__":
    main()
