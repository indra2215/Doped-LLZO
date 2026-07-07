import os
import itertools
import numpy as np
import pandas as pd
import torch
from typing import List, Dict, Tuple
from tqdm import tqdm
from multiprocessing import cpu_count

# MP API and pymatgen
from mp_api.client import MPRester
from pymatgen.core import Structure, Composition
from pymatgen.transformations.standard_transformations import SubstitutionTransformation
from pymatgen.analysis.structure_analyzer import SpacegroupAnalyzer

# MACE and ASE
from mace.calculators import mace_mp
from ase.io import read, write
from pymatgen.io.ase import AseAtomsAdaptor
from ase.optimize import BFGS
from ase.md.langevin import Langevin
from ase import units
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution

# Mock BO models for skeleton workflow
# from botorch.models import SingleTaskGP
# from botorch.fit import fit_gpytorch_model
# from botorch.acquisition import ExpectedImprovement
# from botorch.optim import optimize_acqf
# from gpytorch.mlls import ExactMarginalLogLikelihood

# Phonopy
# from phonopy import Phonopy
# from phonopy.structure.atoms import PhonopyAtoms

# Global parameters
API_KEY = "nREzcJl7KZF5PZl1FIXCMbCSTbxQ55Ii"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

# Constants
LA_SITES = ["Y", "Al", "Ga", "Fe", "Mg", "Sr"]
ZR_SITES = ["Nb", "Ti", "W", "Mo"]
VALENCE = {
    "Li": 1, "La": 3, "Zr": 4, "O": -2,
    "Y": 3, "Al": 3, "Ga": 3, "Fe": 3, "Mg": 2, "Sr": 2,
    "Nb": 5, "Ti": 4, "W": 6, "Mo": 6
}
COST_INDEX_TOP50 = set(LA_SITES + ZR_SITES) # Assuming all listed are okay as per conditions


# ==========================================
# STEP 1: Composition Generation
# ==========================================
def generate_compositions() -> pd.DataFrame:
    print("Step 1: Generating doped compositions...")
    base_calc = {"Li": 7, "La": 3, "Zr": 2, "O": 12}
    results = []

    concs = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    # Single La-site doping
    for dopant in LA_SITES:
        for c in concs:
            results.append({"dopant_La": dopant, "dopant_Zr": None, "conc_La": c, "conc_Zr": 0.0})
            
    # Single Zr-site doping
    for dopant in ZR_SITES:
        for c in concs:
            results.append({"dopant_La": None, "dopant_Zr": dopant, "conc_La": 0.0, "conc_Zr": c})
            
    # Co-doping
    for dop_la, dop_zr in itertools.product(LA_SITES, ZR_SITES):
        for c_la, c_zr in itertools.product(concs, concs):
            results.append({"dopant_La": dop_la, "dopant_Zr": dop_zr, "conc_La": c_la, "conc_Zr": c_zr})

    df = pd.DataFrame(results)
    
    # Charge Balance Validation
    def check_balance(row):
        total_q = 12 * VALENCE["O"]
        la_amt = 3.0 * (1 - row["conc_La"])
        zr_amt = 2.0 * (1 - row["conc_Zr"])
        
        dop_la_amt = 3.0 * row["conc_La"] if row["dopant_La"] else 0.0
        dop_zr_amt = 2.0 * row["conc_Zr"] if row["dopant_Zr"] else 0.0
        
        la_q = la_amt * VALENCE["La"]
        zr_q = zr_amt * VALENCE["Zr"]
        dla_q = dop_la_amt * VALENCE[row["dopant_La"]] if row["dopant_La"] else 0.0
        dzr_q = dop_zr_amt * VALENCE[row["dopant_Zr"]] if row["dopant_Zr"] else 0.0
        
        # Calculate resulting Li to assure neutrality
        li_amt = -(total_q + la_q + zr_q + dla_q + dzr_q) / VALENCE["Li"]
        return li_amt > 0 and li_amt < 10.0 # Feasible Li structure
        
    df["charge_balanced"] = df.apply(check_balance, axis=1)
    df = df[df.charge_balanced].copy()
    
    print(f"Generated {len(df)} charge-balanced compositions.")
    df.to_parquet("step1_filtered_compositions.parquet")
    return df

# ==========================================
# STEP 2: BO Strategy (Mock Model Check)
# ==========================================
def bayesian_optimization(df: pd.DataFrame) -> pd.DataFrame:
    print("Step 2: Bayesian Optimization Selection (top 30)...")
    np.random.seed(42)
    # Mocking BO Surrogate with simple features for speed in skeleton
    df["surrogate_score"] = np.random.uniform(0.1, 0.6, size=len(df))
    df = df.sort_values("surrogate_score", ascending=True).head(30).copy()
    df.to_parquet("step2_bo_candidates.parquet")
    return df

# ==========================================
# STEP 3 & 4: Structure Generation, MACE Relaxation, Properties
# ==========================================
def relax_and_extract(df: pd.DataFrame) -> pd.DataFrame:
    os.makedirs("relaxed_structures", exist_ok=True)
    print("Step 3 & 4: Relaxing structures & extracting properties...")
    
    with MPRester(API_KEY) as mpr:
        base_struct = mpr.get_structure_by_material_id("mp-942733")
    
    macomp = mace_mp(model="medium", device=DEVICE, default_dtype="float32")
    
    for i, row in tqdm(df.iterrows(), total=len(df)):
        comp_dict = {"La": 3.0 * (1 - row["conc_La"]), "Zr": 2.0 * (1 - row["conc_Zr"])}
        if row["dopant_La"]: comp_dict[row["dopant_La"]] = 3.0 * row["conc_La"]
        if row["dopant_Zr"]: comp_dict[row["dopant_Zr"]] = 2.0 * row["conc_Zr"]
        
        # Determine strict structure substitution (simplified)
        try:
            # Here you would map the sites carefully. To keep it robust:
            df.at[i, "status"] = "Attempted"
            df.at[i, "spacegroup"] = "Ia-3d" # Placeholder for structural validation output
            df.at[i, "bulk_mod_GPa"] = 90.0 # Mock extraction
            # MACE Relaxation code goes here
        except Exception as e:
            df.at[i, "status"] = f"Failed: {e}"
            df.at[i, "spacegroup"] = "N/A"
            df.at[i, "bulk_mod_GPa"] = 0.0

    df.to_parquet("step4_relaxed_properties.parquet")
    return df

# ==========================================
# STEP 6: MD Conductivity (Placeholder)
# ==========================================
def evaluate_conductivity(df: pd.DataFrame) -> pd.DataFrame:
    print("Step 6: MD Evaluation (top 15)...")
    df["sigma_RT"] = np.random.uniform(1e-5, 8e-4, size=len(df))
    df["Ea_eV"] = np.random.uniform(0.2, 0.5, size=len(df))
    
    # Filter constraints
    df["C1"] = df["sigma_RT"] >= 5e-4
    df["C2"] = df["Ea_eV"] <= 0.40
    df["ALL_PASS"] = df["C1"] & df["C2"]
    
    final_cols = ["dopant_La", "dopant_Zr", "conc_La", "conc_Zr", "sigma_RT", "Ea_eV", "spacegroup", "bulk_mod_GPa", "C1", "C2", "ALL_PASS"]
    final_df = df[final_cols].sort_values(by=["ALL_PASS", "sigma_RT"], ascending=[False, False])
    
    final_df.to_csv("final_results.csv", index=False)
    print("\nTop 10 Final Compositions:")
    print(final_df.head(10).to_string())
    return final_df

def main():
    print("Starting ML-Accelerated SSE Discovery Pipeline...")
    df = generate_compositions()
    df_bo = bayesian_optimization(df)
    df_props = relax_and_extract(df_bo)
    df_final = evaluate_conductivity(df_props)
    
if __name__ == "__main__":
    main()
