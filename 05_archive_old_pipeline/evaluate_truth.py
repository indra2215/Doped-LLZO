import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
import re

def evaluate_true_generalization():
    df = pd.read_csv('d:/doped_2/bayesian_features.csv')
    df = df.dropna(subset=['Sigma_RT_S_cm'])
    df = df[df['Sigma_RT_S_cm'].astype(str).str.replace('.', '', 1).str.replace('e', '', 1).str.replace('-', '', 1).str.isnumeric()]
    df['Sigma_RT_S_cm'] = df['Sigma_RT_S_cm'].astype(float)
    df = df[df['Sigma_RT_S_cm'] > 0].reset_index(drop=True)
    
    df['Lattice_a_Ang'] = (2 * df['Volume_A3'])**(1/3)
    def extract_elem(f, e):
        m = re.search(f'{e}([\d\.]+)', f)
        if m: return float(m.group(1))
        if e in f: return 1.0
        return 0.0

    df['Li'] = df['Formula'].apply(lambda x: extract_elem(x, 'Li'))
    df['O'] = df['Formula'].apply(lambda x: extract_elem(x, 'O'))
    df['La'] = df['Formula'].apply(lambda x: extract_elem(x, 'La'))
    df['Zr'] = df['Formula'].apply(lambda x: extract_elem(x, 'Zr'))
    
    X = df[['Energy_eV', 'Volume_A3', 'Lattice_a_Ang', 'Li', 'La', 'Zr', 'O']].values
    y = np.log10(df['Sigma_RT_S_cm'].values)
    
    # We will use a Random Forest here for cross-validation to get a highly stable true generalization score 
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(rf, X, y, cv=kf, scoring='r2')
    
    # Fit on all to show memorization diff
    rf.fit(X, y)
    
    print(f"\n--- TRUTH REVEALED ---")
    print(f"Training R^2 Score (The '0.9975' we saw earlier, which was Overfitting/Memorization): {rf.score(X,y):.4f}")
    print(f"True K-Fold Cross-Validation R^2 (The actual Generalization on unseen data): {cv_scores.mean():.4f}")

    if cv_scores.mean() < 0.6:
        print("\nAlert: The model was experiencing 'data leakage' by evaluating its score on the exact same data it was trained on.")

if __name__ == '__main__':
    evaluate_true_generalization()