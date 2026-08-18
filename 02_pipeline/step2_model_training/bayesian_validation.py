"""
bayesian_validation.py
──────────────────────
This module trains the baseline machine learning models used to quickly screen
newly generated LLZO candidate formulas. 

It trains a Gaussian Process Regressor (GPR) and a Random Forest (RF) on the 
experimental dataset of solid-state electrolytes to learn the correlation 
between compositional features and log(ionic conductivity).
"""
import pandas as pd
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import cross_val_score, KFold
from sklearn.pipeline import Pipeline
import joblib
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
FEATURES_FILE = ROOT / "01_data" / "results" / "bayesian_features.csv"
MODEL_FILE    = Path(__file__).parent / "trained_gpr_model.pkl"

def run_validation():
    """
    Trains and validates models to predict ionic conductivity based on 
    compositional features. With 679 points, we train both a Random Forest 
    baseline and a Gaussian Process Regressor, saving the GPR for uncertainty quantification.
    """
    print(f"Loading features from: {FEATURES_FILE}")

    try:
        df = pd.read_csv(FEATURES_FILE)
    except FileNotFoundError:
        print(f"ERROR: Required features file not found at {FEATURES_FILE}.")
        print("  Run fast_surrogate_extraction.py first.")
        return

    # --- Data Cleaning ---
    df = df.dropna(subset=['sigma'])
    df['sigma'] = pd.to_numeric(df['sigma'], errors='coerce')
    df = df.dropna(subset=['sigma'])
    df = df[df['sigma'] > 0].reset_index(drop=True)
    
    # We DO NOT filter by 'Zr' anymore, allowing the model to learn general
    # conductivity rules across 679 points.
    print(f"Loaded {len(df)} diverse solid-state electrolyte training samples.")

    # --- Feature Engineering ---
    feature_cols = [
        "Li_frac", "avg_electronegativity", "avg_atomic_mass", 
        "avg_atomic_radius", "avg_row", "avg_col", "num_elements"
    ]
    df = df.dropna(subset=feature_cols)
    print(f"Remaining after dropping NaN features: {len(df)}")
    
    X = df[feature_cols].values
    y = np.log10(df['sigma'].values)

    # --- Random Forest Baseline ---
    print("\n--- Training Random Forest Baseline ---")
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    rf_scores = cross_val_score(rf, X, y, cv=cv, scoring='r2')
    print(f"RF Cross-Validated R² Scores: {np.round(rf_scores, 4)}")
    print(f"--> RF Mean R²: {np.mean(rf_scores):.4f}")

    # --- GPR Model and Pipeline Definition ---
    print("\n--- Training Gaussian Process Regressor ---")
    scaler = RobustScaler()
    kernel = (
        ConstantKernel(1.0) * Matern(length_scale=np.ones(X.shape[1]), nu=1.5) +
        WhiteKernel(noise_level=0.1)
    )
    gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, normalize_y=True)

    pipeline = Pipeline([
        ('scaler', scaler),
        ('gpr', gpr)
    ])

    n_folds = 5
    print(f"Performing {n_folds}-Fold Cross-Validation on {len(X)} samples for GPR...")
    gpr_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='r2')
    print(f"GPR Cross-Validated R² Scores: {np.round(gpr_scores, 4)}")
    print(f"--> GPR Mean R²: {np.mean(gpr_scores):.4f}")

    import json
    metrics_file = Path(__file__).parent / "cv_metrics.json"
    metrics_file.write_text(json.dumps({
        "n_samples": int(len(X)),
        "n_folds": int(n_folds),
        "rf_r2": rf_scores.tolist(),
        "gpr_r2": gpr_scores.tolist(),
        "gpr_r2_mean": float(np.mean(gpr_scores)),
        "gpr_r2_std": float(np.std(gpr_scores, ddof=1))
    }, indent=2))
    print(f"CV metrics saved to: {metrics_file}")
    
    # Refit on full data before saving
    print("\nRefitting GPR on full dataset...")
    pipeline.fit(X, y)
    joblib.dump(pipeline, MODEL_FILE)
    print(f"Model saved to: {MODEL_FILE}")

if __name__ == '__main__':
    run_validation()