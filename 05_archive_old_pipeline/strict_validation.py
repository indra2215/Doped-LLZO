import pandas as pd
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel, RationalQuadratic
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import cross_val_score, KFold
import re

def run_strict_validation():
    df = pd.read_csv('d:/doped_2/bayesian_features.csv')
    df = df.dropna(subset=['Sigma_RT_S_cm'])
    df = df[df['Sigma_RT_S_cm'].astype(str).str.replace('.', '', 1).str.replace('e', '', 1).str.replace('-', '', 1).str.isnumeric()]
    df['Sigma_RT_S_cm'] = df['Sigma_RT_S_cm'].astype(float)
    df = df[df['Sigma_RT_S_cm'] > 0].reset_index(drop=True)
    
    # Feature Eng
    df['Lattice_a_Ang'] = (2 * df['Volume_A3'])**(1/3)
    def extract_element(formula, elem):
        match = re.search(f'{elem}([\d\.]+)', formula)
        if match: return float(match.group(1))
        if elem in formula: return 1.0
        return 0.0
    def dopant_count(formula):
        elements = re.findall(r'[A-Z][a-z]?', formula)
        return len(set(elements) - {'Li', 'La', 'Zr', 'O'})

    df['Li_pfu'] = df['Formula'].apply(lambda x: extract_element(x, 'Li'))
    df['O_pfu'] = df['Formula'].apply(lambda x: extract_element(x, 'O'))
    df['La_pfu'] = df['Formula'].apply(lambda x: extract_element(x, 'La'))
    df['Zr_pfu'] = df['Formula'].apply(lambda x: extract_element(x, 'Zr'))
    df['Dopant_Complexity'] = df['Formula'].apply(dopant_count)
    df['Volume_per_Atom'] = df['Volume_A3'] / (df['Li_pfu'] + df['La_pfu'] + df['Zr_pfu'] + df['O_pfu'] + 0.1)

    X = df[['Energy_eV', 'Volume_A3', 'Lattice_a_Ang', 'Li_pfu', 'Dopant_Complexity', 'Volume_per_Atom']].values
    y = np.log10(df['Sigma_RT_S_cm'].values)
    
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)
    
    k1 = ConstantKernel(1.0) * Matern(length_scale=np.ones(X.shape[1]), nu=1.5)
    k2 = ConstantKernel(1.0) * RationalQuadratic(length_scale=1.0, alpha=0.1)
    kernel = k1 + k2 + WhiteKernel(noise_level=0.1)
    gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5, normalize_y=True)

    print("Checking for Data Leakage/Overfitting using 5-Fold Cross Validation...")
    
    # TRUE EVALUATION: 5-Fold Cross Validation
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(gpr, X_scaled, y, cv=kf, scoring='r2')
    
    # Train on all data purely to see training memorization
    gpr.fit(X_scaled, y)
    train_score = gpr.score(X_scaled, y)
    
    print(f"Training Score (Memorization): {train_score:.4f}")
    print(f"True Cross-Validated Score (Generalization): {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

if __name__ == '__main__':
    run_strict_validation()