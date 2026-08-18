"""
compositional_screening.py
──────────────────────────
This module performs rapid pre-screening of thousands of virtual solid-state 
electrolyte candidates using a Random Forest model (Sendek-style approach).

It trains on the experimental dataset using only basic elemental fractions 
and selects the top 50 candidates with the highest predicted room-temperature 
ionic conductivity for further, more expensive neural network evaluations.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import re

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
FEATURES_FILE  = ROOT / "01_data" / "results"     / "bayesian_features.csv"
CANDS_FILE     = ROOT / "01_data" / "candidates"  / "bayesian_virtual_candidates.csv"
OUTPUT_FILE    = ROOT / "01_data" / "candidates"  / "top_50_screened_candidates.csv"


def run_compositional_screening():
    print("Loading Baseline Training Materials...")
    try:
        train_df = pd.read_csv(FEATURES_FILE)
        cands_df = pd.read_csv(CANDS_FILE)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        print("  Run fast_surrogate_extraction.py and generate_candidates.py first.")
        return

    # Clean target — bayesian_features.csv uses 'sigma' column (not 'conductivity')
    train_df = train_df.dropna(subset=['sigma'])
    train_df['sigma'] = pd.to_numeric(train_df['sigma'], errors='coerce')
    train_df = train_df.dropna(subset=['sigma'])
    train_df = train_df[train_df['sigma'] > 0].reset_index(drop=True)
    # Garnet-only filter: require Zr in formula (excludes LLTO perovskites etc.)
    if 'formula' in train_df.columns:
        train_df = train_df[train_df['formula'].str.contains('Zr', na=False)].reset_index(drop=True)
    y_train = np.log10(train_df['sigma'].values)
    print(f"Training samples (garnet LLZO only): {len(train_df)}")

    # Elements used in Garnets
    elements = ['Li', 'La', 'Zr', 'O', 'Fe', 'Ga', 'Al', 'Sr', 'Ba', 'Ca',
                'Mg', 'Y', 'Gd', 'Ta', 'Nb', 'W', 'Te', 'Hf', 'Sb', 'Ru',
                'Zn', 'Ti', 'Sn', 'Mn']

    def extract_composition(formula):
        comp = {}
        for elem in elements:
            match = re.search(rf'{elem}([\d\.]+)', formula)
            if match:
                comp[elem] = float(match.group(1))
            elif elem in formula:
                comp[elem] = 1.0
            else:
                comp[elem] = 0.0
        return comp

    # Featurize training data
    comp_train = pd.DataFrame([extract_composition(f) for f in train_df['formula']])

    # Featurize candidates
    comp_cands = pd.DataFrame([extract_composition(f) for f in cands_df['formula']])

    print(f"Training Compositional Fast-Screening Model (Random Forest — Sendek Method)...")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(comp_train)
    X_cands = scaler.transform(comp_cands)

    rf = RandomForestRegressor(n_estimators=500, random_state=42)
    rf.fit(X_train, y_train)

    score = rf.score(X_train, y_train)
    # Note: score is training-set R² (for model fitting verification). Held-out R² is computed via KFold CV in bayesian_validation.py.
    print(f"Compositional Pre-Screening R² Score (Training fit only, not CV): {score:.4f}")

    print(f"\nEvaluating {len(cands_df)} Virtual Candidates...")
    cands_df['Predicted_log_Sigma']    = rf.predict(X_cands)
    cands_df['Predicted_Sigma_RT_S_cm'] = 10 ** cands_df['Predicted_log_Sigma']

    top_candidates = cands_df.sort_values(by='Predicted_Sigma_RT_S_cm', ascending=False).head(50)

    print("\n--- TOP 10 PREDICTED FAST-CONDUCTORS (Sendek-Style Screening) ---")
    for i, row in top_candidates.head(10).iterrows():
        print(f"Candidate: {row['formula']:<30} | Predicted Sigma: {row['Predicted_Sigma_RT_S_cm']:.2e} S/cm")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    top_candidates.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved Top 50 to: {OUTPUT_FILE}")


if __name__ == '__main__':
    run_compositional_screening()