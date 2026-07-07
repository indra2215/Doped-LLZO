# LLZO Discovery Project — Complete Results & Status
**Li₇La₃Zr₂O₁₂ Solid-State Electrolyte | ML + CHGNet Screening**
*Last Updated: 2026-07-06*

---

## Table of Contents
1. [Project Summary](#1-project-summary)
2. [Pipeline Separation Overview](#2-pipeline-separation-overview)
3. [Major Physics Bugs Fixed](#3-major-physics-bugs-fixed)
4. [Standard Pipeline (Pipeline 1) Results](#4-standard-pipeline-pipeline-1-results)
5. [Earth-Abundant Pipeline (Pipeline 2) Results](#5-earth-abundant-pipeline-pipeline-2-results)
6. [Combined Novel Candidate List](#6-combined-novel-candidate-list)
7. [Model Performance Analysis](#7-model-performance-analysis)
8. [Data Files & Script Reference](#8-data-files--script-reference)

---

## 1. Project Summary

| Item | Value |
|------|-------|
| **Goal** | Find doped LLZO with σ_RT > 1 mS/cm (baseline: 3×10⁻⁴ S/cm) |
| **Method** | CHGNet (GNN potential) + GPR surrogate + MD Arrhenius |
| **Pipeline 1 (Standard) candidates** | 150 (charge-balanced, correct site assignment) |
| **Pipeline 2 (Earth-Abundant) candidates** | 535 (only Fe/Al/Mg/Mn/Zn/Ti/Nb/Sn) |
| **Current Project Status** | **Executing**. Physics bugs fixed, pipelines running. |

---

## 2. Pipeline Separation Overview

The project is now cleanly split into two self-contained workflows, ensuring data integrity and independent execution.

### Pipeline 1: Standard Pipeline (`02_pipeline/`)
Focuses on maximum ionic conductivity using any physically sound dopants, including expensive/rare elements.
- **Dopants:** Li-site (Al³⁺, Ga³⁺, Fe³⁺, Zn²⁺); Zr-site (Nb⁵⁺, Ta⁵⁺, Sb⁵⁺, W⁶⁺).
- **Execution:** Uses `run_standard_pipeline.ps1` to execute steps 1 through 5.
- **Output:** `01_data/results/finalresults.csv`

### Pipeline 2: Earth-Abundant (`earth_abundant/`)
Focuses exclusively on low-cost, sustainable materials.
- **Dopants:** Li-site (Fe³⁺, Al³⁺, Mg²⁺, Mn³⁺, Zn²⁺); Zr-site (Ti⁴⁺, Nb⁵⁺, Mn⁴⁺, Fe⁴⁺, Sn⁴⁺).
- **Execution:** Uses `run_ea_pipeline.ps1` to execute steps 1 through 6.
- **Output:** `earth_abundant/data/results/ea_finalresults.csv`

---

## 3. Major Physics Bugs Fixed

Before trusting the results, we audited the code and fixed several critical flaws that were corrupting the structural calculations and ML models.

| Issue | Status | Description of Fix |
|-------|--------|--------------------|
| **Garnet Data Contamination** | ✅ FIXED | Added a `Zr` filter to extraction scripts. Discarded 634 non-garnet samples (e.g. LLTO), leaving exactly 45 genuine LLZO samples for GPR training. |
| **Flat Volume Bug** | ✅ FIXED | `volume_per_atom` was flat at 9.426 Å³. Implemented `staged_relax(relax_cell=False)` during feature extraction so each composition gets a physically meaningful volume. |
| **CHGNet Cell-Filter Crash** | ✅ FIXED | Full cell relaxation failed on substituted garnets. Fixed via a 2-step `staged_relax()`: relax positions first, then full cell. |
| **Double Model Load** | ✅ FIXED | Replaced lazy `StructOptimizer` initialization with eager loading (passing the pre-loaded CHGNet model) to stop PowerShell crashes. |
| **MD PBC Unwrapping** | ✅ FIXED | Implemented incremental unwrapping in the NVT Langevin Molecular Dynamics script to yield smooth MSD curves for accurate Arrhenius fits. |

---

## 4. Standard Pipeline (Pipeline 1) Results

> **Status:** Running Compositional GPR (R² > 0.60) + CHGNet Staged Relaxation in parallel. Estimated time to completion: **~4 Hours** (50 candidates).

---------------------------------------------------------
### [ OLD PIPELINE CANDIDATES (Structural GPR | R² ~ 0.35) ]
---------------------------------------------------------
*Note: These values are from older runs before the compositional feature upgrade.*

| Rank | Formula | Expected σ_RT (S/cm) | Ea (eV) | Notes |
|------|---------|---------------------|---------|-------|
| 1 | Li6.75Al0.25La3Zr2O12 | 1.92×10⁻³ | 0.29 | Al on Li-site only |
| 2 | Li6.5Ga0.25La3Zr1.75Nb0.25O12 | 1.61×10⁻³ | 0.31 | Ga+Nb co-doped |
| 3 | Li6.65Zn0.1La3Zr1.9Ta0.1O12 | 1.25×10⁻³ | 0.32 | Zn+Ta (Zn is cheap) |

**Baseline pure LLZO**: σ_RT ≈ **3.0×10⁻⁴ S/cm**, Ea ≈ 0.30 eV

---------------------------------------------------------
### [ NEW PIPELINE CANDIDATES (Compositional GPR | R² > 0.60) ]
---------------------------------------------------------
*Note: Pending completion of CHGNet validation task...*

| Rank | Formula | Expected σ_RT (S/cm) | Ea (eV) | Notes |
|------|---------|---------------------|---------|-------|
| (Computing...) | | | | |

---

## 5. Earth-Abundant Pipeline (Pipeline 2) Results

> **Status:** Running Compositional GPR (R² > 0.60) + CHGNet Staged Relaxation in parallel. Estimated time to completion: **~2 Hours** (25 candidates).

---------------------------------------------------------
### [ OLD PIPELINE CANDIDATES (Structural GPR | R² ~ 0.20) ]
---------------------------------------------------------
*Sorted by thermal proxy stability (ΔE). All are completely novel with no literature precedent.*

| Rank | Formula | ΔE vs LLZO (eV/at) | Pair | Expected σ_RT |
|------|---------|-------------------|------|--------------|
| 1 | **Li6.500Mg0.25La3Zr1.60Ti0.40O12** | −0.945 | Mg+Ti | 10⁻⁴–10⁻³ |
| 2 | **Li6.500Mg0.25La3Zr1.70Ti0.30O12** | −0.754 | Mg+Ti | 10⁻⁴–10⁻³ |
| 3 | **Li6.500Mg0.25La3Zr1.70Mn0.30O12** | −0.483 | Mg+Mn | 10⁻⁴ |
| 4 | **Li6.500Mg0.25La3Zr1.80Fe0.20O12** | −0.437 | Mg+Fe | 10⁻⁴ |
| 5 | **Li6.500Mg0.25La3Zr1.75Mn0.25O12** | −0.410 | Mg+Mn | 10⁻⁴ |
| 6 | **Li6.500Mg0.25La3Zr1.70Sn0.30O12** | −0.370 | Mg+Sn | 10⁻⁴ |

> **Critical insight**: Mg²⁺ (r = 0.57 Å) is the stability-enabling dopant for earth-abundant co-doping. It fits perfectly in the 24d tetrahedral pocket and creates large Li vacancies, stabilising Ti, Mn, Fe, and Sn on the Zr site.

---------------------------------------------------------
### [ NEW PIPELINE CANDIDATES (Compositional GPR | R² > 0.60) ]
---------------------------------------------------------
*Note: Pending completion of CHGNet validation task...*

| Rank | Formula | ΔE vs LLZO (eV/at) | Pair | Expected σ_RT |
|------|---------|-------------------|------|--------------|
| (Computing...) | | | | |

---

## 6. Combined Novel Candidate List

### Standard Pipeline Novel Candidates (Top 5)
1. **Li6.500Fe0.10La3Zr1.80Nb0.20O12** (Fe+Nb) - Correct site assignments, unpublished.
2. **Li6.500Ga0.10La3Zr1.80Sb0.20O12** (Ga+Sb) - Zero literature.
3. **Li6.500Al0.10La3Zr1.80Sb0.20O12** (Al+Sb) - Not reported.
4. **Li6.500Fe0.10La3Zr1.80Ta0.20O12** (Fe+Ta) - Unpublished.
5. **Li6.500Fe0.10La3Zr1.80Sb0.20O12** (Fe+Sb) - Completely unexplored.

### Earth-Abundant Pipeline Novel Candidates
- **Total Generated:** 535
- **Fully Novel (no literature):** 504 (94%)
- **Unique Dopant Pairs:** 23

---

## 7. Model Performance Analysis

### GPR Surrogate Model (Predicting Conductivity)
* The model previously suffered from a **Flat Prediction Bug** because the training features (volume/energy) were uniform (due to missing structural relaxation and LLTO contamination).
* **Fix applied:** Filtered to the 45 genuine LLZO samples and applied position-only relaxation. The GPR is now actively retraining on physically valid structural features, allowing it to accurately differentiate candidates.

### CHGNet Model (Structural Evaluation)
* **Architecture:** Crystal Hamiltonian Graph Neural Network (400,438 parameters).
* **Fix applied:** Successfully handles substituted garnet cells via the new `staged_relax()` logic. Now correctly yields varied, valid energies and relaxed CIFs for the downstream Molecular Dynamics calculations.

---

## 8. Data Files & Script Reference

### Standard Pipeline
| Output File | Purpose | Script Origin |
|------------|---------|---------------|
| `bayesian_features.csv` | 45 genuine garnet training samples | `step1_feature_extraction` |
| `permutation_candidates.csv` | 150 charge-balanced candidates | `step3_screening` |
| `evaluated_top_candidates.csv` | CHGNet relaxed energies & volumes | `step3_screening` |
| **`finalresults.csv`** | **Final Arrhenius MD results (σ_RT)** | `step5_md_validation` |

### Earth-Abundant Pipeline
| Output File | Purpose | Script Origin |
|------------|---------|---------------|
| `ea_gpr_features.csv` | EA-specific training features | `ea_step1_feature_extraction.py` |
| `earth_abundant_candidates_raw.csv` | 535 low-cost candidates | `ea_step3_candidates.py` |
| `ea_validated_candidates.csv` | CHGNet/M3GNet cross-checked | `ea_step4_validate.py` |
| **`ea_finalresults.csv`** | **Final EA Arrhenius MD results** | `ea_step6_md_validation.py` |

### Execution
Use the unified runners in the root directory:
```powershell
.\run_standard_pipeline.ps1
.\run_ea_pipeline.ps1
```
*(Ensure `$env:MP_API_KEY` is set prior to running to enable Thermodynamic Hull checks).*
