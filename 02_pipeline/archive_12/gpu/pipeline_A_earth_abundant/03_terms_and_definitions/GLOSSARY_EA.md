# Pipeline A — Earth-Abundant | Glossary of Terms & Definitions

**Pipeline:** A — Earth-Abundant  
**Scope:** All terminology used in this pipeline's data, methods, and outputs

---

## A. Material Science Terms

### LLZO
**Li₇La₃Zr₂O₁₂** — Lithium Lanthanum Zirconium Oxide. The parent garnet-type solid electrolyte.  
- Crystal structure: Cubic, space group **Ia-3̄d** (No. 230)
- Theoretical ionic conductivity: ~10⁻⁴ S/cm (undoped)
- Role in this pipeline: Baseline reference — all stability comparisons are made against undoped LLZO

### Garnet Structure
A crystal structure framework (formula A₃B₂C₃O₁₂) where:
- **A-site (dodecahedral):** La³⁺ — 8-coordinate
- **B-site (octahedral):** Zr⁴⁺ — 6-coordinate  
- **C-site (tetrahedral):** Li⁺ — 4-coordinate (also occupies 6-coordinate sites at high Li content)

### Doping / Substitution
Replacing a fraction of host atoms with dopant atoms to modify properties.  
In EA pipeline: **dual doping** (two dopant elements simultaneously)

### Li-site Dopant (M)
An element substituting at the **Li tetrahedral/octahedral position** in the garnet.  
EA-allowed Li-site dopants: **Zn, Mn, Mg, Fe, Al**

### Zr-site Dopant (D)
An element substituting at the **Zr octahedral position**.  
EA-allowed Zr-site dopants: **Nb, Ti, Sn, Mn, Fe**

### Li per formula unit (Li pfu)
Number of Li atoms per formula unit of LLZO (ideally 6.5 for optimized conductivity).  
- `Li_pfu = 6.5` → optimal vacancy concentration for Li-ion hopping
- EA pipeline targets compositions with **Li_pfu ≈ 6.5**

---

## B. Computational/ML Terms

### Gaussian Process Regressor (GPR)
A probabilistic ML model that predicts both a **mean value** and **uncertainty** (standard deviation).  
- EA-GPR trained on 45 LLZO experimental data points
- Predicts: `log₁₀(σ_RT)` → converted to `σ_RT` in S/cm
- Returns: `(σ_mean, σ_std)` — uncertainty quantification included

### EA-GPR Model (`ea_gpr_model.pkl`)
The trained EA-specific surrogate model. Located in `shared_resources/models/`.  
- Size: 3.7 MB
- Constraints: Only generates predictions for Fe/Mg/Al/Ti/Mn/Nb/Sn/Zn compositions

### Feature Descriptors (7 compositional features)
The 7 input features used by the EA-GPR:

| Feature | Symbol | Description |
|---------|--------|-------------|
| Li fraction | `Li_frac` | Li atoms / total atoms in formula |
| Avg. electronegativity | `avg_electronegativity` | Weighted Pauling electronegativity |
| Avg. atomic mass | `avg_atomic_mass` | Weighted avg atomic mass (amu) |
| Avg. atomic radius | `avg_atomic_radius` | Weighted avg ionic radius (Å) |
| Avg. periodic row | `avg_row` | Weighted avg periodic table row |
| Avg. periodic column | `avg_col` | Weighted avg periodic table column |
| Number of elements | `num_elements` | Unique element count |

### CHGNet (Crystal Hamiltonian Graph Neural Network)
A pre-trained GNN (~400,438 parameters) that predicts DFT-level energies and forces.
- **Used in EA pipeline for:** Thermal stability cross-validation (position-only relaxation)
- **NOT used for:** Full geometry optimization (EA pipeline uses pos-only)

### Position-Only Relaxation (`staged_relax`)
A constrained CHGNet optimization that moves **atomic positions** but keeps the **unit cell fixed**.  
Avoids CHGNet cell-filter crashes on garnet supercells.

---

## C. Property Terms

### σ_RT (Ionic Conductivity at Room Temperature)
The key performance metric. Units: **S/cm** (Siemens per centimeter).  
- Target for competitive solid electrolyte: σ_RT > 10⁻⁴ S/cm
- All 5 EA candidates achieve: **~5–7 × 10⁻⁴ S/cm** (GPR predicted)
- "Bulk" σ_RT: grain interior only
- "With grain boundary" σ_RT: bulk × 0.01 (grain boundary correction factor)

### GPR Uncertainty (σ_err)
The 1-sigma standard deviation from the GPR prediction.  
`σ_err = σ_RT × ln(10) × GPR_std`  
Indicates confidence — lower is better.

### ΔE vs LLZO (Thermal Stability)
The CHGNet energy difference per atom between the doped compound and baseline LLZO:  
`ΔE = E_candidate(eV/atom) − E_LLZO_baseline(eV/atom)`
- **ΔE < 0** → Candidate is **energetically more stable** than undoped LLZO → ✅ STABLE
- **ΔE > 0** → Less stable (may still be synthesizable but less favorable)
- All 5 EA validated candidates have ΔE < −7.0 eV/atom

### e_above_hull (Thermodynamic Stability)
Convex hull distance from the Materials Project database.  
- `e_above_hull = 0.0` → On the hull (thermodynamically stable ground state)
- `e_above_hull < 0.05 eV/atom` → Likely synthesizable
- `e_above_hull = inf` → **MP API key missing** (not a real instability)

### Thermal Stability (CHGNet-based)
In this pipeline: stability assessed by comparing CHGNet energies against baseline.  
All 5 EA candidates: **STABLE (lower E than LLZO)** — high confidence of synthesizability.

### Conductivity Order
The order-of-magnitude classification of predicted σ_RT:
- `ORDER: 10^-4` → σ_RT between 1×10⁻⁴ and 9.9×10⁻⁴ S/cm (excellent)
- `ORDER: 10^-5` → Marginal
- `ORDER: 10^-6` → Poor (grain boundary dominated)

---

## D. MD Simulation Terms (GPU Step)

### NVT Ensemble (Canonical)
Molecular dynamics at **constant N** (particles), **V** (volume), **T** (temperature).  
No pressure coupling — volume is fixed at the relaxed unit cell volume.

### Langevin Thermostat
A stochastic thermostat that adds friction and random forces to maintain temperature.  
Parameters: `friction = 0.02 fs⁻¹` (aggressive enough for convergence, gentle enough to avoid artifacts)

### Mean Squared Displacement (MSD)
Measures how far Li ions move over time:  
`MSD(t) = ⟨|r(t) − r(0)|²⟩`  
Linear MSD slope → **diffusive behavior** → can extract diffusion coefficient D.

### Diffusion Coefficient D(T)
`D = slope_of_MSD / 6` (units: cm²/s)  
Computed at each temperature (600K, 800K, 1000K).

### Arrhenius Relation
Temperature dependence of diffusion:  
`D(T) = D₀ × exp(−Eₐ / k_B T)`  
Fitting `ln(D)` vs `1/T` gives:
- **Eₐ** — activation energy (eV)
- **D₀** — pre-exponential factor

### Nernst-Einstein Equation
Converts diffusion coefficient to ionic conductivity:  
`σ(T) = (n × q² × D) / (k_B × T)`  
Where `n` = Li carrier density (from structure), `q` = elementary charge.

### σ_RT Extrapolated (MD-validated)
The final, physics-validated ionic conductivity at 300 K, extrapolated from the Arrhenius fit.  
This is the **most trusted value** — more reliable than GPR predictions alone.
