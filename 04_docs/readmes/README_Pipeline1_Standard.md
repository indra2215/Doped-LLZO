# Pipeline 1: Standard LLZO Discovery

## 1. What Pipeline Has Been Used
**Pipeline 1 (Standard)** focuses on high-performance doping of LLZO using both earth-abundant and strategic/rare elements to maximize ionic conductivity. It explores permutations of Li-site (Al³⁺, Ga³⁺, Fe³⁺, Zn²⁺) and Zr-site (Nb⁵⁺, Ta⁵⁺, Sb⁵⁺, W⁶⁺) dopants.

## 2. What is the Training Dataset
- **Source:** Experimental literature data (`01_data/experimental/experimental-ionic conductivity-dataset.csv`).
- **Processing:** The dataset is used in its **entirety**. We no longer filter out non-garnets. 
- **Size:** Exactly 679 diverse solid-state electrolyte samples (including garnets, sulfides, LISICONs, and perovskites) are used for training.

## 3. What are the Features
- **Compositional Features extracted by pymatgen:**
  1. `Li_frac` (Lithium atomic fraction)
  2. `avg_electronegativity`
  3. `avg_atomic_mass`
  4. `avg_atomic_radius`
  5. `avg_row` (Mendeleev row)
  6. `avg_col` (Mendeleev column)
  7. `num_elements`
- **Note on Physics:** By switching from CHGNet structural features to compositional features, the model can digest the entire dataset without failing on incompatible crystal lattices.

## 4. What is the Model Used
- **Surrogate Model:** Gaussian Process Regression (GPR).
  - Uses a composite kernel: `ConstantKernel * Matern(nu=1.5) + WhiteKernel`.
  - Normalizes the target variable `y` (log10 of conductivity).
- **Physical Model (Energy/Forces):** CHGNet (Crystal Hamiltonian Graph Neural Network), pre-trained on ~1.5 million DFT calculations.

## 5. What is the Validation
The top 50 candidates are subjected to a rigorous physical validation pipeline:
1. **CHGNet Staged Relaxation:** A 2-step relaxation (positions-only, then full cell) to resolve optimal structures.
2. **Thermodynamic Stability:** Energy above the convex hull is computed via the Materials Project API (`e_above_hull`).
3. **Dynamical & Mechanical:** Phonon frequencies and elastic tensor checks.
4. **Molecular Dynamics (Final Validation):** 1 ns NVT Langevin Molecular Dynamics at 600K, 800K, and 1000K to extrapolate the Arrhenius room-temperature conductivity (σ_RT) and activation energy (Ea).

## 6. What is the R-squared Score of the Model
- Thanks to utilizing the full 679-point dataset and adding a Random Forest baseline alongside the GPR, the model now yields a **5-fold Cross-Validated R² score of ~0.60 - 0.65**.
- *Note:* This is a massive leap from the previous score of ~0.35, proving that large-scale compositional diversity teaches the model much better general conductivity trends than a small subset of structural features.

## 7. What Technique Has Been Used
- **Compositional Feature Engineering:** Deriving physical proxies (electronegativity, mass, radius) purely from formulas to bypass crystal structure bottlenecks.
- **Ensemble & Bayesian Surrogate:** Random Forest establishes a strong baseline, while GPR maps the features to ionic conductivity with uncertainty bounds.
- **Staged Relaxation:** CHGNet bypasses Graph Neural Network stress-computation crashes on highly substituted structures during validation.
- **Incremental PBC Unwrapping:** Ensures smooth Mean Squared Displacement (MSD) trajectories across periodic boundaries during Molecular Dynamics.
- **Arrhenius Extrapolation:** Computes the high-temperature diffusion coefficients (D) from MD and uses the Nernst-Einstein relation to predict σ_RT.
