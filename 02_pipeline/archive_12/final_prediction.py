import pandas as pd
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel, RationalQuadratic
from sklearn.preprocessing import RobustScaler
from pathlib import Path
import re

# ROOT = d:/doped_2
ROOT = Path(__file__).parent.parent.parent

# FIX: All paths now ROOT-relative
FEATURES_FILE = ROOT / "01_data" / "results" / "bayesian_features.csv"
EVAL_FILE     = ROOT / "01_data" / "results" / "evaluated_top_candidates.csv"


def run_final_prediction():
    print(f"Loading training data from: {FEATURES_FILE}")

    # 1. Load Training Data
    if not FEATURES_FILE.exists():
        print(f"ERROR: {FEATURES_FILE} not found. Run fast_surrogate_extraction.py first.")
        return

    train_df = pd.read_csv(FEATURES_FILE)
    train_df = train_df.dropna(subset=['conductivity'])
    train_df['conductivity'] = pd.to_numeric(train_df['conductivity'], errors='coerce')
    train_df = train_df.dropna(subset=['conductivity'])
    train_df = train_df[train_df['conductivity'] > 0].reset_index(drop=True)
    print(f"Training samples: {len(train_df)}")

    # Feature engineering helpers
    def extract_element(formula, elem):
        match = re.search(rf'{elem}([\.\d]+)', formula)
        if match: return float(match.group(1))
        if elem in formula: return 1.0
        return 0.0

    def dopant_count(formula):
        elements = re.findall(r'[A-Z][a-z]?', formula)
        return len(set(elements) - {'Li', 'La', 'Zr', 'O'})

    def add_features(df):
        df['lattice_a_ang']    = (2 * df['volume_per_atom'] * 192) ** (1 / 3)
        df['li_pfu']           = df['formula'].apply(lambda x: extract_element(x, 'Li'))
        df['o_pfu']            = df['formula'].apply(lambda x: extract_element(x, 'O'))
        df['la_pfu']           = df['formula'].apply(lambda x: extract_element(x, 'La'))
        df['zr_pfu']           = df['formula'].apply(lambda x: extract_element(x, 'Zr'))
        df['dopant_complexity'] = df['formula'].apply(dopant_count)
        df['total_volume']     = df['volume_per_atom'] * 192
        return df

    train_df = add_features(train_df)

    FEATURES = ['energy_per_atom', 'total_volume', 'lattice_a_ang',
                'li_pfu', 'dopant_complexity', 'volume_per_atom']

    X_train = train_df[FEATURES].values
    y_train = np.log10(train_df['conductivity'].values)

    scaler       = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    k1     = ConstantKernel(1.0) * Matern(length_scale=np.ones(X_train.shape[1]), nu=1.5)
    k2     = ConstantKernel(1.0) * RationalQuadratic(length_scale=1.0, alpha=0.1)
    kernel = k1 + k2 + WhiteKernel(noise_level=0.1)
    gpr    = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=20, normalize_y=True)
    gpr.fit(X_train_scaled, y_train)

    print(f"Max training conductivity: {train_df['conductivity'].max():.2e} S/cm")

    # 2. Load Evaluated Candidates
    print(f"\nLoading candidates from: {EVAL_FILE}")
    if not EVAL_FILE.exists():
        print(f"ERROR: {EVAL_FILE} not found. Run evaluate_candidates_chgnet.py first.")
        return

    eval_df = pd.read_csv(EVAL_FILE)
    f_col   = 'formula' if 'formula' in eval_df.columns else 'Formula'

    # Map column names for feature computation
    if 'relaxed_energy_per_atom' not in eval_df.columns and 'energy_per_atom' in eval_df.columns:
        eval_df = eval_df.rename(columns={
            'energy_per_atom': 'relaxed_energy_per_atom',
            'volume_per_atom': 'relaxed_volume_per_atom'
        })

    eval_df['formula']       = eval_df[f_col]
    eval_df['energy_per_atom'] = eval_df['relaxed_energy_per_atom']
    eval_df['volume_per_atom'] = eval_df['relaxed_volume_per_atom']
    eval_df = add_features(eval_df)

    eval_features = ['relaxed_energy_per_atom', 'total_volume', 'lattice_a_ang',
                     'li_pfu', 'dopant_complexity', 'relaxed_volume_per_atom']
    X_eval        = eval_df[eval_features].values
    X_eval_scaled = scaler.transform(X_eval)

    predictions, std = gpr.predict(X_eval_scaled, return_std=True)
    eval_df['Final_Predicted_Sigma']     = 10 ** predictions
    eval_df['Sigma_Uncertainty_S_cm']    = eval_df['Final_Predicted_Sigma'] * np.log(10) * std

    print("\n================ FINAL GPR PREDICTIONS ================")
    max_train_sigma = train_df['conductivity'].max()
    for _, row in eval_df.iterrows():
        sigma = row['Final_Predicted_Sigma']
        unc   = row['Sigma_Uncertainty_S_cm']
        tag   = "*** EXCEEDS TRAINING MAXIMUM ***" if sigma > max_train_sigma else "Competitive"
        print(f"Material: {row[f_col]}")
        print(f"  --> Predicted σ_RT: {sigma:.2e} ± {unc:.2e} S/cm  [{tag}]")
        print("---------------------------------------------------")


if __name__ == '__main__':
    run_final_prediction()