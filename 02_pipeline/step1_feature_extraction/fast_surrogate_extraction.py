"""
fast_surrogate_extraction.py
══════════════════════════════════════════════════════════════════
Extracts compositional features for all 676 samples in the dataset using
pymatgen, allowing the surrogate model to train on a much larger dataset.
This replaces the old CHGNet structural relaxation which threw away 90%
of the data due to crystal lattice incompatibilities.

Features extracted:
  - Li_fraction
  - avg_electronegativity
  - avg_atomic_mass
  - avg_atomic_radius
  - avg_row
  - avg_col
  - num_elements
"""

import pandas as pd
import numpy as np
from pathlib import Path
from pymatgen.core import Composition, Element

ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "01_data"
RAW_FILE = DATA_DIR / "experimental" / "experimental-ionic conductivity-dataset.csv"
OUT_FILE = DATA_DIR / "results" / "bayesian_features.csv"

def extract_features(formula):
    try:
        comp = Composition(formula)
        total_atoms = comp.num_atoms
        
        li_frac = comp.get_atomic_fraction("Li")
        
        num_elements = len(comp.elements)
        
        avg_eneg = 0
        avg_mass = 0
        avg_rad = 0
        avg_row = 0
        avg_col = 0
        
        valid_eneg = 0
        valid_rad = 0
        
        for el, amt in comp.items():
            frac = amt / total_atoms
            avg_mass += el.atomic_mass * frac
            avg_row += el.row * frac
            avg_col += el.group * frac
            
            if el.X is not None:
                avg_eneg += el.X * frac
                valid_eneg += frac
            
            rad = el.atomic_radius
            if rad is not None:
                avg_rad += float(rad) * frac
                valid_rad += frac
                
        # Normalize in case some elements lacked data
        if valid_eneg > 0: avg_eneg /= valid_eneg
        if valid_rad > 0: avg_rad /= valid_rad
        
        return {
            "Li_frac": li_frac,
            "avg_electronegativity": avg_eneg,
            "avg_atomic_mass": avg_mass,
            "avg_atomic_radius": avg_rad,
            "avg_row": avg_row,
            "avg_col": avg_col,
            "num_elements": num_elements
        }
    except Exception as e:
        print(f"Error parsing {formula}: {e}")
        return None

def main():
    print(f"Loading raw dataset from {RAW_FILE}")
    df = pd.read_csv(RAW_FILE)
    print(f"Loaded {len(df)} samples.")
    
    features_list = []
    
    for idx, row in df.iterrows():
        formula = row["formula"]
        sigma = row.get("sigma", np.nan)
        log_sigma = row.get("log_sigma", np.nan)
        
        if pd.isna(log_sigma) and not pd.isna(sigma):
            log_sigma = np.log10(sigma)
            
        feats = extract_features(formula)
        if feats is not None:
            feats["formula"] = formula
            feats["sigma"] = sigma
            feats["log_sigma"] = log_sigma
            features_list.append(feats)
            
    df_out = pd.DataFrame(features_list)
    df_out = df_out.dropna() # Drop any rows where features couldn't be computed
    
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(OUT_FILE, index=False)
    print(f"Successfully extracted features for {len(df_out)} samples.")
    print(f"Saved to {OUT_FILE}")

if __name__ == "__main__":
    main()