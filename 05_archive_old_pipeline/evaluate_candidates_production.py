import os
import numpy as np
from pymatgen.ext.matproj import MPRester
from pymatgen.io.ase import AseAtomsAdaptor
from mace.calculators import mace_mp
from ase.optimize import BFGS
from ase.md.langevin import Langevin
from ase import units
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.io.trajectory import Trajectory
from scipy.stats import linregress
import torch
import datetime

# --- INTERMEDIATE ACCURACY CONFIGURATION ---
API_KEY = "nREzcJl7KZF5PZl1FIXCMbCSTbxQ55Ii"
DEVICE = "cpu"
MD_STEPS = 50    # Intermediate: 50 steps (still fast enough for laptop, but better than 5)
EQ_STEPS = 10    # Exclude first 10 steps 
FMAX_TOL = 0.5   # Intermediate relaxation

# Only Candidate 1 and 2
candidates = [
    {"name": "Fe_Nb_doped", "La_dopant": "Fe", "Zr_dopant": "Nb", "c_La": 0.5, "c_Zr": 0.2, "val_La_d": 3, "val_Zr_d": 5},
    {"name": "Sr_W_doped",  "La_dopant": "Sr", "Zr_dopant": "W",  "c_La": 0.3, "c_Zr": 0.1, "val_La_d": 2, "val_Zr_d": 6}
]

def generate_ordered_structure(candidate, base_struct):
    atoms = AseAtomsAdaptor.get_atoms(base_struct)
    
    la_indices = [i for i, a in enumerate(atoms) if a.symbol == "La"]
    zr_indices = [i for i, a in enumerate(atoms) if a.symbol == "Zr"]
    li_indices = [i for i, a in enumerate(atoms) if a.symbol == "Li"]
    
    num_la_replace = int(len(la_indices) * candidate["c_La"])
    num_zr_replace = int(len(zr_indices) * candidate["c_Zr"])
    
    for idx in la_indices[:num_la_replace]: atoms.symbols[idx] = candidate["La_dopant"]
    for idx in zr_indices[:num_zr_replace]: atoms.symbols[idx] = candidate["Zr_dopant"]
        
    if candidate["La_dopant"] == "Fe" and candidate["Zr_dopant"] == "Nb":
        del atoms[li_indices[-3:]]
        
    return atoms

def run_production_md(atoms, temp_k, name):
    print(f"[{datetime.datetime.now()}] Starting {MD_STEPS} MD steps at {temp_k}K for {name}...")
    t_atoms = atoms.copy()
    t_atoms.calc = atoms.calc
    
    MaxwellBoltzmannDistribution(t_atoms, temperature_K=temp_k)
    dyn = Langevin(t_atoms, 2 * units.fs, temperature_K=temp_k, friction=0.01 / units.fs)
    
    traj = Trajectory(f"{name}_{temp_k}K.traj", 'w', t_atoms)
    dyn.attach(traj.write, interval=5)
    
    positions_history = []
    li_indices = [i for i, atom in enumerate(t_atoms) if atom.symbol == "Li"]
    
    def store_positions():
        positions_history.append(t_atoms.get_positions()[li_indices])
        
    dyn.attach(store_positions, interval=1)
    
    dyn.run(MD_STEPS)
    
    # Exclude equilibration
    pos_array = np.array(positions_history)[EQ_STEPS:]
    if len(pos_array) < 2: return 1e-9
    
    msd = np.mean(np.sum((pos_array[-1] - pos_array[0])**2, axis=-1))
    dt_s = (MD_STEPS - EQ_STEPS) * 2e-15
    D = (msd * 1e-16) / (6 * dt_s)
    
    print(f"[{datetime.datetime.now()}] Completed {temp_k}K MD. D = {D:.2e} cm^2/s")
    return D

def run_production_analysis():
    print(f"--- STARTING PRODUCTION-LEVEL ANALYSIS ({DEVICE.upper()}) ---")
    print(f"Warning: At 100k MD steps on CPU, this may take days to complete.\n")
    
    with MPRester(API_KEY) as mpr:
        base_struct = mpr.get_structure_by_material_id("mp-942733")
        
    # Use float64 for geometry, float32 for MD is typical, but we'll stick to a single model
    macomp = mace_mp(model="medium", device=DEVICE, default_dtype="float32")
    
    with open("d:/doped_2/production_analysis.log", "w") as log:
        log.write("--- PRODUCTION ANALYSIS LOG ---\n")
    
    for cand in candidates:
        name = cand['name']
        print(f"\n=== EVALUATING {name} ===")
        try:
            atoms = generate_ordered_structure(cand, base_struct)
            atoms.calc = macomp
            
            print(f"[{datetime.datetime.now()}] Relaxing geometry (fmax={FMAX_TOL})...")
            opt = BFGS(atoms, logfile=f"{name}_relax.log")
            opt.run(fmax=FMAX_TOL)
            
            temps = [600, 800, 1000]
            D_vals = []
            for T in temps:
                D = run_production_md(atoms, T, name)
                D_vals.append(D if D > 0 else 1e-9)
                
            inv_T = 1.0 / np.array(temps)
            ln_D = np.log(np.array(D_vals))
            slope, intercept, _, _, _ = linregress(inv_T, ln_D)
            Ea = -slope * 8.617e-5
            
            D_RT = np.exp(intercept) * np.exp(-Ea / (8.617e-5 * 300))
            sigma_RT = (D_RT * 1e-4 * (1e28) * (1.602e-19)**2) / (1.38e-23 * 300) / 100.0
            
            result_str = f"[{datetime.datetime.now()}] RESULTS FOR {name}:\n  Ea = {Ea:.4f} eV\n  sigma_RT = {sigma_RT:.3e} S/cm\n\n"
            print(result_str)
            
            with open("d:/doped_2/production_analysis.log", "a") as log:
                log.write(result_str)
                
        except Exception as e:
            err_str = f"[{datetime.datetime.now()}] ERROR on {name}: {e}\n"
            print(err_str)
            with open("d:/doped_2/production_analysis.log", "a") as log:
                log.write(err_str)

if __name__ == "__main__":
    run_production_analysis()
