import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import re

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent
FEATURES_FILE  = ROOT / "01_data" / "results"     / "bayesian_features.csv"
CANDS_FILE     = ROOT / "01_data" / "candidates"  / "permutation_candidates.csv"
OUTPUT_FILE    = ROOT / "01_data" / "candidates"  / "novel_screened_candidates.csv"


def run_compositional_screening():
    print("Loading Baseline Training Materials...")
    try:
        train_df = pd.read_csv(FEATURES_FILE)
        cands_df = pd.read_csv(CANDS_FILE)
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        print("  Run fast_surrogate_extraction.py and generate_novel_candidates_FIXED.py first.")
        return

    # Clean target
    train_df = train_df.dropna(subset=['conductivity'])
    train_df['conductivity'] = pd.to_numeric(train_df['conductivity'], errors='coerce')
    train_df = train_df.dropna(subset=['conductivity'])
    train_df = train_df[train_df['conductivity'] > 0].reset_index(drop=True)
    # Garnet-only filter: require Zr in formula (excludes LLTO perovskites etc.)
    if 'formula' in train_df.columns:
        train_df = train_df[train_df['formula'].str.contains('Zr', na=False)].reset_index(drop=True)
    y_train = np.log10(train_df['conductivity'].values)
    print(f"Training samples (garnet LLZO only): {len(train_df)}")

    elements = ['Li', 'La', 'Zr', 'O', 'Fe', 'Ga', 'Al', 'Sr', 'Ba', 'Ca',
                'Mg', 'Y', 'Gd', 'Ta', 'Nb', 'W', 'Te', 'Hf', 'Sb', 'Ru',
                'Zn', 'Ti', 'Sn', 'Mn']

    def extract_composition(formula):
        comp = {}
        for elem in elements:
            match = re.search(rf'{elem}([\d\.]+)', formula)
            if match:
                comp[elem] = float(match.group(1))
            else:
                if re.search(rf'{elem}(?=[A-Z]|$)', formula):
                    comp[elem] = 1.0
                else:
                    comp[elem] = 0.0
        return comp

    # Handle Formula vs formula column name
    f_col = 'Formula' if 'Formula' in cands_df.columns else 'formula'

    X_train_list = [list(extract_composition(f).values()) for f in train_df['formula']]
    X_train = np.array(X_train_list)

    X_cands_list = [list(extract_composition(f).values()) for f in cands_df[f_col]]
    X_cands = np.array(X_cands_list)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_cands_scaled = scaler.transform(X_cands)

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train_scaled, y_train)

    cands_df['predicted_log_sigma'] = model.predict(X_cands_scaled)
    cands_df['predicted_sigma']     = 10 ** cands_df['predicted_log_sigma']

    cands_df = cands_df.sort_values(by='predicted_sigma', ascending=False)

    print("\n--- TOP 10 NOVEL CANDIDATES (Compositional ML RF) ---")
    cols_to_show = [c for c in [f_col, 'base_type', 'predicted_sigma'] if c in cands_df.columns]
    print(cands_df[cols_to_show].head(10).to_string(index=False))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    cands_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved fully ranked list to: {OUTPUT_FILE}")


if __name__ == '__main__':
    run_compositional_screening()
