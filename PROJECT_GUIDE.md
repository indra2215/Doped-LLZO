# 📂 PROJECT GUIDE — Doped-LLZO Repository Architecture

This repository is structured into two completely independent, self-contained pipeline tracks (High-Performance and Earth-Abundant), alongside archived historical runs.

---

## 🗂️ 1. High-Performance / Standard Pipeline (`02_pipeline/`)

Focus: High-performance Li-site (Al, Ga, Fe, Zn), La-site (Sr, Y, Gd, Ca, Ba), and Zr-site (Nb, Ta, Sb, W) co-doped garnets.

### Execution Sequence:
1. `02_pipeline/step1_feature_extraction/fast_surrogate_extraction.py` → `01_data/results/bayesian_features.csv`
2. `02_pipeline/step2_model_training/bayesian_validation.py` → `02_pipeline/step2_model_training/trained_gpr_model.pkl` + `cv_metrics.json`
3. `02_pipeline/step3_screening/generate_candidates.py` → `01_data/candidates/bayesian_virtual_candidates.csv`
4. `02_pipeline/step3_screening/compositional_screening.py` → `01_data/candidates/top_50_screened_candidates.csv`
5. `02_pipeline/step3_screening/evaluate_candidates_chgnet.py` → `01_data/results/evaluated_top_candidates.csv` + `03_structures/relaxed/*.cif`
6. `02_pipeline/step4_stability/thermodynamic_stability.py` → `01_data/results/thermodynamic_stability.csv`
7. `02_pipeline/step4_stability/dynamical_stability.py` → `01_data/results/dynamical_stability.csv`
8. `02_pipeline/step4_stability/mechanical_stability.py` → `01_data/results/mechanical_stability.csv`
9. `02_pipeline/step5_md_validation/backtrack_validation_corrected.py` → `01_data/results/finalresults.csv`

**Runner**: `run_standard_pipeline.ps1`

---

## 🗂️ 2. Earth-Abundant Pipeline (`earth_abundant/`)

Focus: Low-cost, sustainable dopants only (Fe, Mg, Mn, Zn on Li-site; Ti, Nb, Sn on Zr-site). Excludes Ta, W, Ga, Hf, Y, Gd.

### Execution Sequence:
1. `earth_abundant/scripts/ea_step1_feature_extraction.py` → `earth_abundant/data/results/ea_gpr_features.csv`
2. `earth_abundant/scripts/ea_step2_model_training.py` → `earth_abundant/data/models/ea_gpr_model.pkl` + `ea_cv_metrics.json`
3. `earth_abundant/scripts/ea_step3_candidates.py` → `earth_abundant/data/candidates/earth_abundant_candidates_raw.csv`
4. `earth_abundant/scripts/ea_step4_validate.py` → `earth_abundant/data/results/ea_validated_candidates.csv` + `earth_abundant/structures/*.cif`
5. `earth_abundant/scripts/ea_step5_stability.py` → `earth_abundant/data/results/ea_thermodynamic_stability.csv`
6. `earth_abundant/scripts/ea_step6_md_validation.py` → `earth_abundant/data/results/ea_finalresults.csv`

**Runner**: `run_ea_pipeline.ps1`

---

## 🗂️ 3. Archived & Backup Results (`05_archive_old_pipeline/` & `01_data/results_v1_backup/`)

- `05_archive_old_pipeline/`: Legacy scripts, early trajectory runs (`*.traj`), and old baseline code.
- `01_data/results_v1_backup/`: Preserved backup of initial pipeline run results.
- `FINAL_Results/`: Organized reference snapshots for `High_Performance_Pipeline/` and `Earth_Abundant_Pipeline/`.
- `FINAL_RESULTS_HACKATHON/`: Validated submission snapshot artifacts.
