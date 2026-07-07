# LLZO Doped Solid Electrolyte — Full Project Checkpoint
> Feed this entire document to Gemini 2.5 before starting any task.

---

## PROJECT GOAL
Build a machine learning pipeline to predict room-temperature ionic conductivity (σ_RT, S/cm)
for aliovalent-doped LLZO (Li₇La₃Zr₂O₁₂) garnet solid electrolytes.
Target: identify novel doped compositions exceeding σ_RT > 1 mS/cm = 10⁻³ S/cm.

---

## CRYSTAL STRUCTURE FACTS

- LLZO space group: Ia-3̄d (No. 230), cubic garnet
- Materials Project ID: mp-942733
- Conventional cell: 96 atoms, a ≈ 12.97 Å, V ≈ 2183 Å³
- Primitive cell: 48 atoms, V ≈ 1092 Å³ (BCC primitive = conventional/2)
- Formula: a_conventional = (2 × V_primitive)^(1/3)

### Crystallographic Sites (Wyckoff)
| Site  | Wyckoff | Coord | Host Ion | Valid Dopants             |
|-------|---------|-------|----------|---------------------------|
| 24d   | tetra   | 4     | Li⁺      | Al³⁺, Ga³⁺, Fe³⁺, Mg²⁺  |
| 48g   | octa    | 6     | Li⁺      | Li pathway — do not dope  |
| 24c   | dodeca  | 8     | La³⁺     | Sr²⁺, Ba²⁺, Ca²⁺, Y³⁺, Gd³⁺ |
| 16a   | octa    | 6     | Zr⁴⁺     | Ta⁵⁺, Nb⁵⁺, Ti⁴⁺, W⁶⁺, Mo⁶⁺, Hf⁴⁺ |

### Physical Constraints (Hard Filters — Never Violate)
- Li per formula unit: 6.1 ≤ Li_pfu ≤ 6.8 (Anderson et al. 2024)
- Lattice parameter: 12.91 Å ≤ a ≤ 12.98 Å (Luo et al. 2025)
- Charge balance must be exactly satisfied
- e_above_hull < 0.1 eV/atom (thermodynamic stability)

---

## ML POTENTIAL: USE CHGNet (NOT MACE-MP-0)

### Why CHGNet Over MACE-MP-0 For This Project
- CHGNet tracks magnetic moments → correct for Fe³⁺ doped LLZO
- CHGNet accuracy on oxides: ±30 meV/atom vs MACE ±50 meV/atom
- CHGNet StructOptimizer relaxes BOTH cell + ions natively
- CHGNet benchmarked explicitly on Li-La-Zr-O systems in literature

### Correct CHGNet Relaxation Code
```python
from chgnet.model import CHGNet
from chgnet.model.dynamics import StructOptimizer
from pymatgen.core import Structure

model = CHGNet.load()
relaxer = StructOptimizer()   # handles cell + ionic relaxation

result = relaxer.relax(structure, fmax=0.05, steps=300)

final_struct = result['final_structure']   # pymatgen Structure
E = result['trajectory'].energies[-1]      # eV (total energy)
V = final_struct.volume                    # Å³ (REAL volume, not constant)
a = final_struct.lattice.a                 # Å (REAL lattice parameter)

# Save CIF
final_struct.to(filename='compound_relaxed.cif')
```

### CRITICAL: MACE Bug In Existing Code (Do Not Repeat)
The old code used BFGS(atoms) without ExpCellFilter.
This does IONIC-ONLY relaxation — cell volume stays constant.
Result: ALL 154 training samples have identical Volume = 1112.63 Å³.
CHGNet StructOptimizer fixes this automatically.

---

## TRAINING DATA: 154 SAMPLES

- Mix of pure LLZO + related garnet family compounds
- Experimental σ_RT values from literature
- File: bayesian_features.csv

### First Step — Always Audit The Data
```python
import pandas as pd

df = pd.read_csv('bayesian_features.csv')
print(df.shape)
print(df['Formula'].nunique())
print(df['Sigma_RT_S_cm'].describe())
print(df[['Energy_eV','Volume_A3']].nunique())  # Volume should NOT be 1
```

### Compound Family Classification
```python
def classify_family(formula_dict):
    has_zr = formula_dict.get('Zr', 0) > 0
    has_la = formula_dict.get('La', 0) > 0
    has_ta = formula_dict.get('Ta', 0) > 0
    has_nb = formula_dict.get('Nb', 0) > 0
    li_doped = any(formula_dict.get(e,0)>0 for e in ['Al','Ga','Fe','Mg'])
    zr_doped = any(formula_dict.get(e,0)>0 for e in ['Ta','Nb','Ti','W','Mo'])
    la_doped = any(formula_dict.get(e,0)>0 for e in ['Sr','Ba','Ca','Y','Gd'])

    if has_la and has_zr:
        if li_doped and zr_doped: return 'LLZO_codoped'
        elif li_doped:             return 'LLZO_Li_sub'
        elif zr_doped:             return 'LLZO_Zr_sub'
        elif la_doped:             return 'LLZO_La_sub'
        else:                      return 'LLZO_pure'
    elif has_la and has_ta and not has_zr: return 'LLTO_garnet'
    elif has_la and has_nb and not has_zr: return 'LLNO_garnet'
    else:                                  return 'other_garnet'
```

---

## FEATURE VECTOR: 13 FEATURES (CURRENT) + NEW FEATURES

### Current 13 Features (Some Still Broken)
1. Formula (string — not directly used)
2. Sigma_RT_S_cm (target variable)
3. Energy_eV (partially broken — 21 unique values only)
4. Volume_A3 (BROKEN — only 1 unique value = constant)
5. Lattice_a_Ang (BROKEN — derived from constant volume)
6. Li_pfu
7. Dopant_complexity (crude — just counts unique elements)
8. Volume_per_atom (BROKEN — derived from constant volume)
9-13. [Check actual CSV for remaining columns]

### Tier 1 — Add Immediately (Zero Compute, From Formula Only)

#### Shannon Ionic Radius Mismatch (3 features)
```python
SHANNON_RADII = {
    'Li':{'4':0.59,'6':0.76}, 'La':{'8':1.16}, 'Zr':{'6':0.72},
    'Al':{'4':0.535}, 'Ga':{'4':0.61}, 'Fe':{'4':0.49}, 'Mg':{'4':0.57},
    'Ta':{'6':0.64}, 'Nb':{'6':0.64}, 'Ti':{'6':0.605}, 'W':{'6':0.60},
    'Mo':{'6':0.59}, 'Hf':{'6':0.71}, 'Sn':{'6':0.69},
    'Sr':{'8':1.26}, 'Ba':{'8':1.42}, 'Ca':{'8':1.12},
    'Y':{'8':1.019},'Gd':{'8':1.053},'Nd':{'8':1.109},'Ce':{'8':1.143},
}
# Compute RMS mismatch at each site vs host ion radius
# Features: radius_mismatch_Li_site, radius_mismatch_Zr_site, radius_mismatch_La_site
```

#### Pauling Electronegativity Difference (2 features)
```python
ELECTRONEGATIVITY = {
    'Li':0.98,'La':1.10,'Zr':1.33,'O':3.44,
    'Al':1.61,'Ga':1.81,'Fe':1.83,'Mg':1.31,
    'Ta':1.50,'Nb':1.60,'Ti':1.54,'W':2.36,'Mo':2.16,
    'Sr':0.95,'Ba':0.89,'Ca':1.00,'Y':1.22,'Gd':1.20,
}
# Features: chi_diff_Li_site, chi_diff_Zr_site
# TOP FEATURE from Adhyatma 2021 paper
```

#### Li Vacancy Features (2 features)
```python
# Li_vacancy_fraction = (7.0 - Li_pfu) / 7.0
# Li_vacancy_absolute = 7.0 - Li_pfu
# Use family-normalized reference: LLZO=7, LLTO=5, LLNO=5
```

#### Charge Compensation Mode (3 features)
```python
# zr_site_charge_excess: Ta5+ and Nb5+ add +1 per atom vs Zr4+
# li_site_charge_deficit: Al3+, Ga3+, Fe3+ remove Li, -2 per atom vs Li1+
# is_codoped: binary flag, 1 if both sites doped simultaneously
```

#### B-Site Average Charge (2 features)
```python
B_SITE_CHARGES = {'Zr':4,'Ta':5,'Nb':5,'Ti':4,'W':6,'Mo':6,'Sn':4,'Hf':4}
# b_site_avg_charge: weighted average charge at 16a site
# b_site_charge_variance: variance (captures mixed-valence doping)
```

#### Family One-Hot (8 features)
```python
# One-hot encode: LLZO_pure, LLZO_Li_sub, LLZO_Zr_sub, LLZO_La_sub,
#                 LLZO_codoped, LLTO_garnet, LLNO_garnet, other_garnet
# Use OneHotEncoder — NOT integer encoding (family labels are not ordinal)
```

### Tier 2 — Add After CHGNet Relaxation Is Fixed (5 features)
- Energy_per_atom (real CHGNet value)
- Volume_per_atom (real CHGNet value — not constant)
- Lattice_a_real (real CHGNet value)
- li_o_bond_mean (mean Li-O bond length from relaxed structure)
- zr_site_distortion_index (polyhedral distortion of ZrO₆)

### Tier 3 — Physics Barriers (For MD Validation)
- Bond Valence Sum (BVS) for Li: measures site preference
- Bond Valence Mismatch (BVM = |BVS - 1|): screening descriptor (Xie 2024)
- Bottleneck radius: r_b ≈ 0.1547*a - 0.432 (proxy from lattice param)
- Haven ratio: H_R = D_tracer/D_charge (corrects σ_RT for correlated hops)
- e_above_hull: thermodynamic stability (from Materials Project API)

---

## GPR MODEL: VALIDATION RULES (CRITICAL)

### The 0.99 R² Problem
```python
# WRONG — always gives 0.99 by mathematical construction
gpr.fit(X_scaled, y)
score = gpr.score(X_scaled, y)   # training data = data leakage

# CORRECT — always use cross-validation
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ('scaler', RobustScaler()),
    ('gpr', GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10))
])

# Stratify by family to ensure each fold has all compound types
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(pipe, X, y, cv=skf.split(X, family_labels), scoring='r2')
print(f"Real CV R²: {scores.mean():.3f} ± {scores.std():.3f}")
# Target: > 0.70 is good for this problem size
# Adhyatma 2021 achieved 0.903 with LOOCV on 176 samples
```

### Three Data Leakage Types To Avoid
1. Scoring on training data (shown above)
2. Fitting RobustScaler on all 154 before splitting — use Pipeline
3. Computing feature statistics (mean, std) from full dataset before CV split

### GPR Kernel Choice
```python
from sklearn.gaussian_process.kernels import Matern, RationalQuadratic, WhiteKernel, ConstantKernel

kernel = (
    ConstantKernel(1.0) * Matern(length_scale=1.0, nu=1.5) +
    ConstantKernel(1.0) * RationalQuadratic(length_scale=1.0, alpha=0.1) +
    WhiteKernel(noise_level=0.1)
)
# Matern nu=1.5: physical smoothness (once-differentiable)
# RationalQuadratic: multi-scale (local + global compositional trends)
# WhiteKernel: experimental measurement noise in σ_RT
```

### Bayesian Optimization Acquisition Function
```python
from scipy.stats import norm
import numpy as np

def expected_improvement(mu, sigma, f_best):
    Z = (mu - f_best) / (sigma + 1e-9)
    return (mu - f_best) * norm.cdf(Z) + sigma * norm.pdf(Z)

# After GPR.predict(X_candidates, return_std=True):
mu, sigma = gpr.predict(X_candidates_scaled, return_std=True)
EI = expected_improvement(mu, sigma, y_train.max())
next_candidate = candidates[np.argmax(EI)]
# This replaces Random Forest pre-screening entirely
```

---

## MOLECULAR DYNAMICS: CORRECT PROTOCOL

### Parameters
```python
TIMESTEP_FS    = 2          # fs — safe for Li-O (period ~20-30 fs)
EQUILIBRATION  = 10000      # steps = 20 ps — discard this data
PRODUCTION     = 250000     # steps = 500 ps — use this for MSD
STORE_INTERVAL = 10         # store every 10 steps = 20 fs resolution
TEMPERATURES   = [600, 800, 1000]  # K — need ≥3 for Arrhenius fit
FRICTION       = 0.01       # /fs — Langevin thermostat, not overdamped
ENSEMBLE       = 'NVT'      # Langevin thermostat
```

### Critical: PBC-Unwrapped MSD (Bug In Original Code)
```python
def compute_unwrapped_msd(positions_history, cell_lengths):
    """
    Without unwrapping: Li crossing cell boundary looks like it jumped back.
    MSD → 0 even though ion diffused. Must use minimum image convention.
    """
    n_frames = len(positions_history)
    disp = np.zeros_like(positions_history[0])
    unwrapped = [positions_history[0].copy()]

    for i in range(1, n_frames):
        delta = positions_history[i] - positions_history[i-1]
        # Minimum image convention
        delta -= np.round(delta / cell_lengths) * cell_lengths
        disp += delta
        unwrapped.append(positions_history[0] + disp)

    # MSD from unwrapped positions
    msd = np.mean(np.sum((unwrapped[-1] - unwrapped[0])**2, axis=-1))
    return msd
```

### Arrhenius Extrapolation
```python
import numpy as np

# D(T) = D0 * exp(-Ea / kB*T)
# ln(D) = ln(D0) - Ea/(kB*T)
kB = 8.617e-5  # eV/K

temps = np.array([600, 800, 1000])   # K
D_values = np.array([D_600, D_800, D_1000])  # cm²/s from MSD slopes

inv_T = 1.0 / temps
ln_D = np.log(D_values)

coeffs = np.polyfit(inv_T, ln_D, 1)
Ea = -coeffs[0] * kB     # eV
D0 = np.exp(coeffs[1])   # cm²/s

# Extrapolate to 298K
D_298 = D0 * np.exp(-Ea / (kB * 298))

# Nernst-Einstein → σ_RT
n_Li = n_Li_per_cm3   # from structure volume
sigma_RT = (n_Li * 1.602e-19**2 * D_298) / (kB * 1.381e-23 * 298)
```

### Haven Ratio Correction
```python
# σ_true = σ_Nernst-Einstein * H_R
# H_R for LLZO ≈ 0.4–0.7
# Without this correction, σ_RT is OVERESTIMATED by 1.5–2.5x
H_R = collective_msd / (n_li * individual_msd)
sigma_corrected = sigma_RT * H_R
```

---

## CANDIDATE GENERATION

### Charge Balance Rule
```python
# LLZO charge balance: 7*1 + 3*3 + 2*4 + 12*(-2) = 7+9+8-24 = 0 ✓
# When doping:
# Ta5+ on Zr4+ site → excess +1 per Ta → reduces Li by 1 (Li_pfu decreases)
# Al3+ on Li site  → deficit -2 per Al → Li_pfu decreases further

def check_charge_balance(formula_dict):
    charges = {'Li':1,'La':3,'Zr':4,'O':-2,
                'Al':3,'Ga':3,'Fe':3,'Mg':2,
                'Ta':5,'Nb':5,'Ti':4,'W':6,'Mo':6,'Hf':4,'Sn':4,
                'Sr':2,'Ba':2,'Ca':2,'Y':3,'Gd':3,'Nd':3,'Ce':3}
    total = sum(charges.get(e,0) * a for e,a in formula_dict.items())
    return abs(total) < 0.01   # must be zero
```

### Valid Candidate Space
```python
DOPANT_AMOUNTS = [0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6]

LI_SITE_DOPANTS = ['Al', 'Ga', 'Fe', 'Mg']   # 24d tetrahedral
ZR_SITE_DOPANTS = ['Ta', 'Nb', 'Ti', 'W', 'Mo', 'Hf']   # 16a octahedral
LA_SITE_DOPANTS = ['Sr', 'Ba', 'Ca', 'Y', 'Gd']   # 24c dodecahedral

# Generate all combinations, filter by:
# 1. Charge balance
# 2. 6.1 ≤ Li_pfu ≤ 6.8
# 3. Charge neutrality maintained by adjusting Li
```

---

## KNOWN BUGS IN EXISTING CODE (ALL MUST BE FIXED)

| Bug | File | Severity | Fix |
|-----|------|----------|-----|
| Constant volume (ionic-only relaxation) | fast_surrogate_extraction.py | CRITICAL | Use CHGNet StructOptimizer |
| Fake arithmetic MACE simulation | evaluate_candidates_mace.py | CRITICAL | Run real CHGNet on candidates |
| Training R² reported as validation | bayesian_validation.py | CRITICAL | Use K-fold CV via Pipeline |
| 200-step MD (0.4 ps = noise) | backtrack_validation.py | CRITICAL | Use 250,000 steps (500 ps) |
| No PBC unwrapping in MSD | backtrack_validation.py | CRITICAL | Use minimum image convention |
| Hardcoded Windows paths (d:/) | multiple files | HIGH | Use pathlib.Path |
| API key in source code | multiple files | HIGH | Use os.environ.get("MP_API_KEY") |
| Wrong charge deletion (del 4 Li not 1) | backtrack_validation.py | MEDIUM | Fix stoichiometry math |
| Fe/Al/Ga placed on La-site in archive | pipeline_workflow.py | CRITICAL | Archive is wrong — do not use |
| Numeric filter using .isnumeric() hack | multiple files | LOW | Use pd.to_numeric(errors='coerce') |
| Regex escape sequence warning | multiple files | LOW | Use raw strings r'[\d\.]+' |

---

## PUBLISHED PAPERS USING THESE TECHNIQUES

| Paper | What They Did | Relevance To Your Code |
|-------|--------------|------------------------|
| Adhyatma et al. 2021 (ScienceDirect) | LGBM + BO + LOOCV on 176 LLZO samples | Your direct benchmark — their 0.903 LOOCV is your target |
| Anderson et al. 2024 (Adv. Energy Mater.) | 59 dopants experimental screening in LLZO | Get their supplementary data table → your training data expansion |
| Xie et al. 2024 (Chem. Mater. — NASA) | CHGNet MD + BVM screening of 329 Li SSE candidates | Your MD protocol template + BVM feature |
| Fukuda et al. 2022 (RSC Advances) | BO with transfer learning for NASICON garnets | Multi-task GPR solution for your small dataset problem |
| Deng et al. 2023 (Nature Mach. Intell.) | CHGNet paper | Read to understand the model you're using |
| Böhm & Champagne 2025 (arXiv 2510.09861) | Fine-tuned CHGNet for halide SSE | Fine-tuning workflow if CHGNet base accuracy insufficient |
| npj Comp. Mat. 2026 | Dual-stage CHGNet + ML for garnet LZSP | Most recent — state of the art you're competing with |

---

## WHAT IS NOVEL IN THIS PROJECT (THE GAP)

None of these specific combinations are published:
- CHGNet relaxation (not DFT, not MACE) as feature extractor for LLZO GPR
- GPR trained directly on experimental σ_RT (not DFT-computed proxy)
- BVM + radius mismatch + charge compensation + vacancy fraction combined
- Expected Improvement acquisition for LLZO candidate selection
- Haven ratio correction applied to CHGNet MD predictions
- Simultaneous Li-site + Zr-site + La-site co-doping search space

---

## MINIMUM REQUIREMENTS FOR PUBLICATION

1. Training data: ≥100 experimental (formula, σ_RT) pairs with documented sources
2. Features: BVS/BVM + radius mismatch + electronegativity + real CHGNet E,V
3. Validation: 5-fold stratified CV R² with std dev (NOT training R²)
4. Parity plot: predicted vs actual on held-out test set
5. Uncertainty: GPR σ* reported alongside μ* for every prediction
6. MD: ≥200 ps at ≥3 temperatures with PBC-unwrapped MSD
7. Haven ratio: applied to correct σ_RT predictions
8. Stability: e_hull < 0.1 eV/atom for all reported candidates
9. Novelty: ≥1 predicted composition not in training data, validated by MD
10. SHAP or permutation feature importance analysis

---

## PIPELINE EXECUTION ORDER (CORRECT SEQUENCE)

```
Step 1: audit_data.py
        → classify 154 samples by family
        → check for constant volume bug
        → verify experimental σ_RT range

Step 2: add_tier1_features.py
        → add all zero-compute features to training set
        → radius_mismatch, chi_diff, vacancy, charge_compensation,
          b_site_charge, family_onehot
        → NO data leakage — these are formula-derived only

Step 3: chgnet_relaxation.py
        → replace fast_surrogate_extraction.py entirely
        → use StructOptimizer for all 154 samples
        → save real E, V, a, CIF for each
        → add Tier 2 features (Li-O bond, distortion)

Step 4: gpr_with_cv.py
        → replace bayesian_validation.py
        → use Pipeline(scaler + gpr)
        → stratified 5-fold CV
        → report CV R² ± std, NOT training R²

Step 5: candidate_generation.py
        → generate charge-balanced candidates
        → apply hard physical filters
        → compute Tier 1 features for all candidates

Step 6: bayesian_screening.py
        → GPR.predict(candidates, return_std=True)
        → compute EI acquisition function
        → select top 50 by EI (not random forest)

Step 7: chgnet_candidates.py
        → CHGNet relax top 50 candidates
        → add Tier 2 features
        → filter by lattice_a window and e_hull

Step 8: md_validation.py
        → run 500 ps NVT Langevin MD at 600, 800, 1000K
        → PBC-unwrapped MSD
        → Arrhenius fit → Ea and D_298
        → Haven ratio correction → σ_RT_corrected
        → Nernst-Einstein → final σ_RT prediction

Step 9: results_analysis.py
        → parity plot
        → feature importance (SHAP)
        → uncertainty quantification
        → compare top candidates vs literature benchmarks
```

---

## HARDWARE CONTEXT
- CPU-only Mac laptop
- CHGNet relaxation: ~5–15 min per structure on CPU
- 500 ps MD per temperature: ~2–3 days on CPU, ~3–4 hours on Colab GPU
- Recommendation: run MD on Google Colab (free T4 GPU) not local CPU

---

## KEY PHYSICAL CONSTANTS
```python
kB_eV  = 8.617e-5   # Boltzmann constant, eV/K
kB_J   = 1.381e-23  # Boltzmann constant, J/K
e_charge = 1.602e-19  # electron charge, C
eV_to_GPa = 160.2   # conversion: eV/Å³ → GPa
T_room = 298        # K
```
