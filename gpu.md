# GPU Execution Guide & Pipeline Status

## 1. Steps Performed So Far

### Standard Pipeline (High-Performance)
*   **Step 1:** Feature Extraction (`bayesian_features.csv` generated from 45 true garnet samples).
*   **Step 2:** GPR Model Training (`trained_gpr_model.pkl` trained).
*   **Step 3A & 3B:** Virtual Candidate Generation & Random Forest Screening (14,474 candidates filtered to top 50).
*   **Step 3C:** CHGNet Relaxation (35 candidates successfully relaxed to CIFs).
*   **Step 4A:** Thermodynamic Hull Check (Completed, but flagged due to missing MP API key).

### Earth-Abundant (EA) Pipeline
*   **EA Step 1 & 2:** Feature Extraction & EA-specific GPR Training (`ea_gpr_model.pkl` generated).
*   **EA Step 3:** Candidate Generation (535 low-cost candidates generated).
*   **EA Step 4:** CHGNet Validation & GPR Predictions. **(Successfully completed!)** 
    *   Validated 5 top candidates using CHGNet position-only relaxation. All 5 were found to be **STABLE** (ΔE < 0 vs baseline LLZO).

---

## 2. Steps Remaining (To be executed on GPU)

The remaining steps are Molecular Dynamics (MD) simulations. These are highly memory-intensive because CHGNet builds a PyTorch autograd graph over hundreds of simulation steps to compute forces via `torch.autograd.grad(energy, positions)`. **A dedicated GPU with sufficient VRAM (or a High-Performance Computing cluster) is highly recommended to avoid Out-Of-Memory (OOM) crashes.**

*   **EA Step 6 (Arrhenius MD Validation):** NVT Langevin MD simulations at 600K, 800K, and 1000K to calculate diffusion coefficients and fit the Arrhenius curve for predicting room-temperature ionic conductivity ($\sigma_{RT}$).
*   **Standard Step 5 (Arrhenius MD Validation):** The exact same MD procedure applied to the top candidates from the High-Performance pipeline.

---

## 3. Candidates Queued for MD Processing

These are the specific structures ready to be processed by the GPU in the next run.

### Earth-Abundant (EA) Candidates:
1.  **`Li6.500Zn0.05La3Zr1.60Nb0.40O12`**
    *   **Stability (ΔE):** -9.21 eV/atom (Highly Stable)
    *   **Predicted $\sigma_{RT}$:** $5.29 \times 10^{-4}$ S/cm
2.  **`Li6.500Mn0.10La3Zr1.80Nb0.20O12`**
    *   **Stability (ΔE):** -9.17 eV/atom (Highly Stable)
    *   **Predicted $\sigma_{RT}$:** $5.42 \times 10^{-4}$ S/cm
3.  **`Li6.500Zn0.20La3Zr1.90Nb0.10O12`**
    *   **Stability (ΔE):** -8.99 eV/atom (Highly Stable)
    *   **Predicted $\sigma_{RT}$:** $6.67 \times 10^{-4}$ S/cm (Best EA conductivity)

### Standard (High-Performance) Candidates:
1.  **`Li6.45La3.0Zr1.45Ta0.55O12`**
    *   **Predicted $\sigma_{RT}$:** $6.11 \times 10^{-4}$ S/cm
2.  **`Li6.4La3.0Zr1.4Ta0.6O12`**
    *   **Predicted $\sigma_{RT}$:** $5.85 \times 10^{-4}$ S/cm
3.  **`Li6.45La2.95Ba0.05Zr1.4Ta0.6O12`**
    *   **Predicted $\sigma_{RT}$:** $5.57 \times 10^{-4}$ S/cm

---

## 4. Model Specifications

### A. High-Performance (Standard) Pipeline
*   **Surrogate Screening Model:** Gaussian Process Regressor (GPR) + Random Forest
    *   **Training Data:** 45 clean, verified LLZO experimental samples.
    *   **Input Features:** 7 compositional descriptors (Li fraction, avg electronegativity, avg mass, avg radius, avg row, avg col, num elements).
    *   **Performance:** $R^2 > 0.60$, fixing previous issues with structural feature uniformity.
*   **Physics Engine:** CHGNet (Crystal Hamiltonian Graph Neural Network)
    *   **Architecture:** GNN with ~400,438 parameters.
    *   **Function:** Performs geometry optimization (`staged_relax`) and computes forces dynamically for Molecular Dynamics. Note: `torch.set_grad_enabled(True)` is strictly required for MD force calculations.

### B. Earth-Abundant (EA) Pipeline
*   **Surrogate Screening Model:** EA-Specific GPR (`ea_gpr_model.pkl`)
    *   **Constraints:** Training and generation strictly limited to sustainable, low-cost dopant elements (Fe, Mg, Al, Ti, Mn, Nb, Sn, Zn).
    *   **Size:** ~3.7 MB footprint.
    *   **Function:** Rapid proxy for bulk and grain-boundary conductivity screening.
*   **Physics Engine:** CHGNet (Same model instance as above)
    *   **Function:** Used primarily to cross-validate thermal stability against baseline LLZO energies before submitting candidates to expensive MD runs.
