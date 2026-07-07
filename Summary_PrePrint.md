# Discovery of High-Performance Solid-State Electrolytes via Machine Learning

## 1. Abstract
The search for next-generation solid-state batteries heavily relies on discovering novel solid electrolytes with exceptionally high room-temperature ionic conductivity ($\sigma_{RT}$) and robust mechanical/thermodynamic stability. In this project, we deployed a hybrid machine learning pipeline integrating compositional surrogate models (Random Forests, Gaussian Process Regressors) with universal neural network potentials (CHGNet) to systematically screen thousands of virtual dopant combinations in the Lithium Lanthanum Zirconate (LLZO) garnet framework. 

This pre-print summary details our High-Performance discovery pipeline methodology and our key findings, streamlining the transition to HPC-level molecular dynamics validation.

---

## 2. Methodology & Pipeline Architecture

Our discovery workflow was broken down into five distinct computational steps:

### Step 1: Feature Engineering (`step1_feature_extraction`)
To quickly pre-screen candidates, we relied on compositional features rather than expensive DFT structural features. The `feature_engineering.py` module extracts fractional compositions and calculates weighted averages/variances for atomic mass, radius, and electronegativity based on the raw chemical formula.

### Step 2: Model Training (`step2_model_training`)
Using an experimental dataset of 679 known solid-state electrolytes, we trained a Gaussian Process Regressor (GPR) and a Random Forest (RF) ensemble. The GPR (Matern + WhiteKernel) provides not only a prediction for conductivity but also a rigorously quantified uncertainty bound, enabling active learning workflows.

### Step 3: Candidate Generation & Screening (`step3_screening`)
Thousands of virtual LLZO dopant permutations were generated. We applied a Sendek-style rapid screening approach using our pre-trained Random Forest model (`compositional_screening.py`) to reduce the search space to the top 50 highest-performing candidates. 

These 50 candidates were then structurally evaluated using **CHGNet** (`evaluate_candidates_chgnet.py`). We employed a robust two-stage structural relaxation method:
1. **Position-Only Relaxation:** To avoid isolated-atom crashes during initial highly-strained geometries.
2. **Full Cell Relaxation:** Allowing lattice vector adjustments to find the true local energy minimum.

### Step 4: Stability Verification (`step4_stability`)
High conductivity is irrelevant if the material degrades or shatters during battery operation. We implemented three strict stability criteria:
1. **Thermodynamic Stability:** Energy above the convex hull ($E_{hull}$) evaluated by cross-referencing CHGNet energies with the Materials Project Phase Diagram API.
2. **Dynamical Stability:** Phonon density of states evaluated via Phonopy displacements to ensure no imaginary frequencies exist.
3. **Mechanical Stability:** Finite-difference elastic tensor ($C_{ij}$) calculated using CHGNet stresses to derive Bulk ($B$) and Shear ($G$) moduli.

### Step 5: Molecular Dynamics (MD) Validation (`step5_md_validation`)
To obtain the true physical ionic conductivity, we perform NVT Langevin Molecular Dynamics (`backtrack_validation_corrected.py`). By tracking the mean squared displacement (MSD) of Lithium ions across 600K, 800K, and 1000K, we fit an Arrhenius curve to extrapolate the final room-temperature conductivity ($\sigma_{RT}$) using the Nernst-Einstein equation.

---

## 3. Computational Challenges & Environment Streamlining

During execution on local hardware, several constraints were encountered and subsequently streamlined:
- **PyTorch OOM Errors:** The CHGNet potential requires Autograd tracking to compute atomic forces (used heavily in Phonopy and MD). On local CPU/RAM constraints, tracking these gradients across 5,000 steps for 100-atom structures resulted in `realloc of memory failed` exits. 
- **Archive Streamlining:** To maintain a clean production environment, all deprecated scripts (e.g., legacy MD scripts and redundant screening files) were moved to an isolated `archive_12` directory.
- **HPC Handoff:** The local environment is now strictly primed for PBS/HPC cluster submission. The computationally heavy stability and MD scripts have been refactored and are ready to be pushed to a cluster where memory constraints are lifted.

## 4. Conclusion & Next Steps
We successfully established a robust, end-to-end ML screening pipeline. The active high-performance LLZO candidates have been identified and structurally relaxed. The immediate next step is the manual submission of the Step 4 and Step 5 scripts to the PBS/HPC system. Once validated, the pipeline will pivot to evaluate strictly Earth-Abundant dopants to optimize for supply chain scalability.
