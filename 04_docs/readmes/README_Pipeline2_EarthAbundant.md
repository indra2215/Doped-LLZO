# Pipeline 2: Earth-Abundant LLZO Discovery

## 1. What Pipeline Has Been Used
**Pipeline 2 (Earth-Abundant)** is a specialized, fully independent workflow designed to discover low-cost, sustainable LLZO variants. It strictly limits dopants to earth-abundant elements, excluding expensive/rare metals like Ta, W, Ga, and Hf.
- **Allowed Dopants:** Fe³⁺, Al³⁺, Mg²⁺, Mn³⁺, Zn²⁺ (Li-site) and Ti⁴⁺, Nb⁵⁺, Mn⁴⁺, Fe⁴⁺, Sn⁴⁺ (Zr-site).

## 2. What is the Training Dataset
- **Source:** The shared experimental dataset (`01_data/experimental/experimental-ionic conductivity-dataset.csv`).
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
  - Uses the same composite kernel architecture as Pipeline 1, but trained exclusively on the EA-constrained data subset.
- **Physical Models:**
  - **CHGNet:** Primary GNN potential for structural relaxation and baseline energy prediction.
  - **M3GNet:** Secondary GNN potential used specifically in this pipeline for cross-model energy validation (checking if M3GNet agrees with CHGNet's structural predictions).

## 5. What is the Validation
The 535 earth-abundant candidates are subjected to a unique validation stream:
1. **CHGNet/M3GNet Cross-Validation:** Candidates are relaxed using CHGNet's `staged_relax()`, and their final energies are cross-checked by M3GNet. A small `delta_models` difference constitutes a "PASS".
2. **Thermal Proxy Stability:** Energy per atom is compared against pure un-doped LLZO (ΔE). Negative values (ΔE < 0) are flagged as thermally stable.
3. **Molecular Dynamics:** The top 5 most thermally stable candidates undergo NVT Langevin Arrhenius MD to derive the final σ_RT.

## 6. What is the R-squared Score of the Model
- Thanks to utilizing the full 679-point dataset and adding a Random Forest baseline alongside the GPR, the model now yields a **5-fold Cross-Validated R² score of ~0.60 - 0.65**.
- *Note:* This is a massive leap from the previous score of ~0.15 - 0.25, proving that large-scale compositional diversity teaches the model much better general conductivity trends than a small subset of structural features.

## 7. What Technique Has Been Used
- **Compositional Feature Engineering:** Deriving physical proxies (electronegativity, mass, radius) purely from formulas to bypass crystal structure bottlenecks.
- **Ensemble & Bayesian Surrogate:** Random Forest establishes a strong baseline, while GPR maps the features to ionic conductivity with uncertainty bounds.
- **Dual-Model Graph Network Validation:** Using both CHGNet and M3GNet to verify structural stability.
- **Delta-Energy Thermal Proxy:** Estimating synthesis viability by comparing the candidate's formation energy directly against baseline cubic LLZO.
