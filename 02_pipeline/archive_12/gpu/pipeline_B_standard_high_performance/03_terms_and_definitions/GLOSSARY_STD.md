# Pipeline B — Standard | Glossary of Terms & Definitions

**Pipeline:** B — Standard High-Performance  
**Scope:** All terminology specific to the standard pipeline's data, methods, and outputs

---

## A. Material Science Terms

### LLZO — Parent Compound
**Li₇La₃Zr₂O₁₂** — Undoped garnet solid electrolyte. MP ID: mp-29517.  
All candidate compositions are derived from this parent structure by dopant substitution.

### Garnet Dopant Sites
| Site | Coordination | Host ion | Dopants used |
|------|-------------|---------|-------------|
| **A-site** (La-site) | 8-fold (dodecahedral) | La³⁺ | Ba²⁺, Ca²⁺, Gd³⁺, Y³⁺ |
| **B-site** (Zr-site) | 6-fold (octahedral) | Zr⁴⁺ | Ta⁵⁺, Hf⁴⁺ |
| **C-site** (Li-site) | 4+6-fold | Li⁺ | Ga³⁺, Al³⁺ |

### Li Vacancy Engineering
When a higher-valence ion (e.g., Ta⁵⁺) replaces Zr⁴⁺, charge balance requires removing Li⁺:  
`Li₇La₃Zr₂O₁₂ + xTa → Li_(7-x)La₃Zr_(2-x)Ta_xO₁₂`  
This creates **Li vacancies** — the key to enabling fast Li-ion conduction.  
**Optimal Li pfu: ~6.4–6.5** for maximum conductivity in cubic LLZO.

### Dual-Doping (A + B site)
Simultaneously doping both La-site (A) and Zr-site (B) to optimize:
1. Lattice parameter and Li bottleneck size
2. Vacancy concentration
3. Defect formation energy

---

## B. ML/Computational Terms

### Bayesian Optimization / Virtual Candidate Generation
A systematic exploration of composition space using ML-guided search.  
Generated **14,474 virtual candidates** by varying Li, La-site, Zr-site dopant concentrations.

### Random Forest Screener
A fast ensemble ML model used as a **pre-filter** before the GPR:  
14,474 candidates → **top 50** (filtered by predicted log(σ_RT)).  
Much faster than GPR for large candidate sets.

### Gaussian Process Regressor (GPR) — Standard Model
Same architecture as EA-GPR but trained without elemental constraints.  
- Training: 45 LLZO experimental samples
- R² > 0.60 (after fixing structural feature uniformity issue)
- File: `02_pipeline/step2_model_training/trained_gpr_model.pkl`

### Bayesian Features (`bayesian_features.csv`)
The 680-row feature matrix used to train the standard GPR.  
Columns match the 7 compositional descriptors (same as EA pipeline).

### Staged Relaxation (`staged_relax`)
CHGNet geometry optimization strategy used in this pipeline:
1. Position-only relaxation (no cell change) → `fmax = 0.1 eV/Å`, `steps = 300`
2. Falls back to static evaluation if relaxation fails
3. Avoids CHGNet cell-filter crash on garnet supercells

---

## C. Stability Property Terms

### e_above_hull (Thermodynamic Stability)
Distance above the convex hull from the Materials Project:
- `e_above_hull = 0.0` → Ground state stable phase
- `e_above_hull < 0.05 eV/atom` → Experimentally synthesizable (rule of thumb)
- `e_above_hull = inf` → **MP API key missing** — not a real instability

**Current status for all 35 standard candidates: `inf` (needs MP API key)**

### CHGNet Energy / atom (eV/atom)
The total energy per atom predicted by CHGNet after relaxation.  
- Reference LLZO: ~17.9 eV/atom (CHGNet static)
- Variation across candidates: wide range (some negative due to CHGNet numerical artifacts)

### is_dynamically_stable
Whether the phonon spectrum has **no imaginary frequencies** (all modes positive).  
Imaginary frequencies → material is unstable at 0 K → unlikely to synthesize.  
- Tested only for 2 reference structures (Li7.0La2.9Gd0.1Zr1.9Hf0.1O12, Li7.0La2.9Y0.1Zr2.0O12)
- Both returned `False, inf` → indicates phonon calculation failed or those are unstable

### max_imaginary_freq_THz
Maximum imaginary phonon frequency in THz.  
`inf` = DFPT calculation was not completed (HPC required).

### Bulk Modulus VRH (B_VRH, GPa)
Voigt-Reuss-Hill average bulk modulus — resistance to uniform compression.  
`0 GPa` in current data → mechanical stability calculation was incomplete.

### Shear Modulus VRH (G_VRH, GPa)
VRH average shear modulus — resistance to shape change.  
`0 GPa` in current data → mechanical stability calculation was incomplete.

### Poisson Ratio (ν)
`ν = (3B - 2G) / (2(3B + G))`  
Typical garnets: ν ≈ 0.25–0.30. `0` in current data = incomplete calculation.

### is_mechanically_stable
Boolean: True if B_VRH > 0, G_VRH > 0, and ν in [0, 0.5].  
Current status: **False for all tested** (mechanical stability run was incomplete).

---

## D. Screening Pipeline Terms

### top_50_screened_candidates
The 50 compositions selected from 14,474 by the Random Forest pre-filter.  
Stored in: `02_properties/screening_candidates/top_50_screened_candidates_original.csv`  
Columns: `formula, Predicted_log_Sigma, Predicted_Sigma_RT_S_cm`

### evaluated_top_candidates.csv
The full CHGNet relaxation + GPR evaluation record for all successfully relaxed candidates.  
41 structures successfully relaxed out of the top 50 attempted.

### MASTER_RESULTS.csv
The definitive ranked output table for the standard pipeline:
```
rank | formula | gpr_predicted_sigma | gpr_sigma_uncertainty |
chgnet_energy | chgnet_volume | relaxation_mode |
e_above_hull | thermodynamically_stable | is_dynamically_stable |
bulk_modulus | shear_modulus | poisson_ratio | is_mechanically_stable |
md_validated_sigma
```

---

## E. MD Simulation Terms (GPU Step — same as EA)

### NVT Langevin MD
See EA Glossary Section D — identical implementation for both pipelines.

### Arrhenius Fit
`ln(D) = ln(D₀) − Eₐ/(k_B·T)`  
Linear regression of `ln(D)` vs `1/T` to extract activation energy **Eₐ** and pre-factor **D₀**.

### σ_RT (MD-validated)
Nernst-Einstein σ extrapolated to 300 K from the Arrhenius fit.  
This replaces the GPR σ_RT with a physics-validated value once MD is complete.

### D(T) — Diffusion Coefficient at Temperature T
```
D = (1/6) × d(MSD)/dt    [cm²/s]
```
Computed at 600, 800, and 1000 K for each candidate.

---

## F. Reporting Terms

### Predicted_log_Sigma
`log₁₀(σ_RT)` — base-10 logarithm of predicted conductivity.  
More stable for ML training than raw σ. Example: `-3.0` → σ_RT = 10⁻³ S/cm.

### Conductivity Order
Classification:
- `ORDER: 10^-4` → 10⁻⁴ to 9.9×10⁻⁴ S/cm (competitive)
- `ORDER: 10^-3` → 10⁻³ to 9.9×10⁻³ S/cm (excellent)
- `ORDER: 10^-5` → Marginal

### Pending HPC
Status flag for steps not yet run on a GPU/cluster:
- Dynamical stability (DFPT phonons)
- Mechanical properties (elastic tensor)
- MD-validated σ_RT

### GPR Uncertainty
`gpr_sigma_uncertainty_S_cm` = 1σ standard deviation from the GPR.  
High uncertainty → composition is far from training data distribution.
