import os
import numpy as np
from pymatgen.ext.matproj import MPRester
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.analysis.structure_analyzer import SpacegroupAnalyzer
from mace.calculators import mace_mp
from ase.optimize import BFGS
from ase.md.langevin import Langevin
from ase import units
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from scipy.stats import linregress
import warnings

warnings.filterwarnings("ignore")

API_KEY = "nREzcJl7KZF5PZl1FIXCMbCSTbxQ55Ii"
DEVICE = "cpu"

def calculate_msd_time_origins(positions_history, step_interval=2, dt_fs=2.0):
    """
    Computes MSD using proper time-origin averaging to extract D.
    Fixes the 'only reading frame 0 and frame N' critical flaw.
    """
    pos_array = np.array(positions_history)
    n_frames = len(pos_array)
    if n_frames < 4: 
        return 1e-12
        
    msds = []
    # Average over multiple time origins (up to half the trajectory)
    max_dt_frames = n_frames // 2
    
    for t in range(1, max_dt_frames):
        # Diff between all frames separated by t
        diff = pos_array[t:] - pos_array[:-t]
        sq_dist = np.sum(diff**2, axis=-1)
        msds.append(np.mean(sq_dist))
        
    if len(msds) < 2: 
        return 1e-12
        
    # Time array in seconds
    t_array = np.arange(1, len(msds) + 1) * step_interval * dt_fs * 1e-15
    
    # Linear fit of MSD vs time: MSD = 6 * D * t
    slope, _ = np.polyfit(t_array, msds, 1)
    
    # Convert slope from Angstrom^2/s to cm^2/s
    D = (slope * 1e-16) / 6.0
    return max(D, 1e-15)

def evaluate_paper_compound():
    print("BACKTRACKING VALIDATION: Ga-Doped LLZO")
    print("Target Experimental Formula: Li6.25Ga0.25La3Zr2O12 (Target Ea: 0.25-0.27 eV)")
    
    with MPRester(API_KEY) as mpr:
        base_struct = mpr.get_structure_by_material_id("mp-942733")
        
    atoms = AseAtomsAdaptor.get_atoms(base_struct)
    li_indices = [i for i, a in enumerate(atoms) if a.symbol == "Li"]
    
    # 1. Replace 2 Li with Ga
    atoms.symbols[li_indices[0]] = "Ga"
    atoms.symbols[li_indices[1]] = "Ga"
    
    # 2. Charge balancing
    del atoms[li_indices[2:6]]
    
    macomp = mace_mp(model="medium", device=DEVICE, default_dtype="float32")
    atoms.calc = macomp
    
    print("\n--- Relaxing geometry (fmax=0.05 eV/A) ---")
    opt = BFGS(atoms, logfile=None)
    opt.run(fmax=0.05) # FIXED: Tolerances tightened
    
    # FIXED: Check actual spacegroup instead of hardcoding
    # NOTE: Converting back to PMG to check SG can be noisy if the MD relaxation broke symmetry.
    relaxed_struct = AseAtomsAdaptor.get_structure(atoms)
    analyzer = SpacegroupAnalyzer(relaxed_struct, symprec=0.1)
    sg = analyzer.get_space_group_symbol()
    print(f"Post-relaxation Actual Spacegroup: {sg} (Aiming for Ia-3d / Garnet cubic)")
    
    temps = [600, 800, 1000]
    D_vals = []
    
    # IMPORTANT: Set to 200 for code execution test. To get REAL PHYSICS, set to 500,000.
    MD_STEPS = 200 
    print(f"\n--- Running MD Simulations ({MD_STEPS} steps per temp) ---")
    print("WARNING: MD_STEPS is low to prevent laptop freeze. Real values require 500k steps.")
    
    for T in temps:
        t_atoms = atoms.copy()
        t_atoms.calc = atoms.calc
        MaxwellBoltzmannDistribution(t_atoms, temperature_K=T)
        dyn = Langevin(t_atoms, 2 * units.fs, temperature_K=T, friction=0.01 / units.fs)
        
        positions_history = []
        current_li = [i for i, atom in enumerate(t_atoms) if atom.symbol == "Li"]
        
        def store():
            positions_history.append(t_atoms.get_positions()[current_li])
            
        dyn.attach(store, interval=2)
        dyn.run(MD_STEPS)
        
        D = calculate_msd_time_origins(positions_history)
        D_vals.append(D)
        print(f"Temp: {T}K | Calculated D: {D:.4e} cm^2/s")
        
    inv_T = 1.0 / np.array(temps)
    ln_D = np.log(np.array(D_vals))
    slope, intercept, _, _, _ = linregress(inv_T, ln_D)
    
    # FIXED: NO MORE RANDOM NUMBER FALLBACKS. 
    Ea = -slope * 8.617e-5
    
    # FIXED: Real Nernst-Einstein extrapolation to RT (298K)
    D_RT = np.exp(intercept + slope * (1.0 / 298.15))
    volume_cm3 = atoms.get_volume() * 1e-24
    N_li = len(current_li)
    q = 1.602e-19
    kB = 1.3806e-23
    T_RT = 298.15
    # sigma = (N * q^2 * D) / (V * k_B * T) -> Need to convert e to coulombs carefully 
    # Proper scale factor for NE conductivity here:
    sigma_RT = (N_li * (q**2) * D_RT) / (volume_cm3 * kB * T_RT)
    
    print(f"\n--- TRUE UNFILTERED COMPUTATIONAL PREDICTION ---")
    print("NOTE: These values depend purely on MD_STEPS length. Short steps yield high noise.")
    print(f"Predicted Ea:       {Ea:.4f} eV")
    print(f"Predicted sigma_RT: {sigma_RT:.2e} S/cm")
    print(f"Experimental Ea:    0.27 eV")
    print(f"Exp. sigma_RT:      1.49e-3 S/cm")

if __name__ == "__main__":
    evaluate_paper_compound()