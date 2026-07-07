# Standard Pipeline — LLZO Doping (Al / Ga / Fe + Nb / Ta / Sb / W)
## `d:\doped_2\02_pipeline\`

---

## Purpose

This pipeline screens novel **Li-site + Zr-site co-doped LLZO** compositions
using a Bayesian GPR surrogate model pre-screened by a Random Forest and
validated by CHGNet ML-FF relaxation and Arrhenius MD.

**Dopant scope** (includes strategic/expensive elements):

| Site | Dopants | Valence |
|------|---------|---------|
| Li-site (24d) | Al³⁺, Ga³⁺, Fe³⁺, Zn²⁺ | +2 to +3 |
| Zr-site (16a) | Nb⁵⁺, Ta⁵⁺, Sb⁵⁺, W⁶⁺ | +5 to +6 |

For the **earth-abundant** variant (no Ta/W/Ga), see `../earth_abundant/`.

---

## Quick Start

```powershell
$env:MP_API_KEY = "nREzcJl7KZF5PZl1FIXCMbCSTbxQ55Ii"
.\run_standard_pipeline.ps1     # from d:\doped_2\
```

---

## Step-by-Step

| Step | Script | Input | Output |
|------|--------|-------|--------|
| 1 | `step1_feature_extraction/fast_surrogate_extraction.py` | experimental CSV | `01_data/results/bayesian_features.csv` (45 garnet-only samples) |
| 2 | `step2_model_training/bayesian_validation.py` | bayesian_features.csv | `trained_gpr_model.pkl` |
| 3a | `step3_screening/generate_novel_candidates_FIXED.py` | — | `01_data/candidates/permutation_candidates.csv` (150 candidates) |
| 3b | `step3_screening/screen_novel_candidates.py` | permutation_candidates.csv | `novel_screened_candidates.csv` (ranked) |
| 3c | `step3_screening/compositional_screening.py` | bayesian_virtual_candidates.csv | `top_50_screened_candidates.csv` |
| 3d | `step3_screening/evaluate_candidates_chgnet.py` | top_50_screened_candidates.csv | `evaluated_top_candidates.csv` + CIF |
| 4a | `step4_stability/thermodynamic_stability.py` | evaluated CSV | `thermodynamic_stability.csv` (needs MP_API_KEY) |
| 4b | `step4_stability/dynamical_stability.py` | CIF files | `dynamical_stability.csv` |
| 4c | `step4_stability/mechanical_stability.py` | CIF files | `mechanical_stability.csv` |
| 5 | `step5_md_validation/backtrack_validation_corrected.py` | CIF files | `finalresults.csv` |

---

## Data Ownership

All standard pipeline data lives in `d:\doped_2\01_data\`:

```
01_data/
├── experimental/                ← shared raw data (read-only)
├── candidates/                  ← standard pipeline candidates ONLY
│   ├── bayesian_virtual_candidates.csv
│   ├── permutation_candidates.csv
│   ├── novel_screened_candidates.csv
│   └── top_50_screened_candidates.csv
└── results/                     ← standard pipeline results ONLY
    ├── bayesian_features.csv
    ├── evaluated_top_candidates.csv
    ├── finalresults.csv
    ├── thermodynamic_stability.csv
    ├── dynamical_stability.csv
    └── mechanical_stability.csv
```

**EA pipeline data is NOT stored here.** See `earth_abundant/data/`.

---

## Key Design Decisions

### Garnet-only filter
Feature extraction requires `Zr` in the formula. This excludes 634 non-garnet
compounds (LLTO perovskites, plain La-oxides) that would produce fake identical
volumes when mapped onto the garnet base cell. Result: 45 genuine garnet LLZO
training samples with meaningful energy/volume variance.

### staged_relax() in evaluation
CHGNet `StructOptimizer` with `relax_cell=True` crashes on substituted garnets
("isolated atom with r_cutoff=5"). The two-step approach avoids this:
1. Relax atomic positions only (`relax_cell=False`) — avoids cell-filter stress
2. Full cell + atoms relax on the better starting geometry
Fallback chain: `full` → `pos_only` → `static`

### Position-only relax in feature extraction
Applying `relax_cell=False` relaxation in Step 1 gives each garnet composition
its own geometry so that `volume_per_atom` varies meaningfully across samples
(previously flat at 9.426 Å³ for all, making it a useless GPR feature).
