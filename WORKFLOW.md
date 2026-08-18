# ⚙️ WORKFLOW GUIDE — Doped-LLZO Pipeline Execution

This document provides the official, step-by-step execution workflows for both research tracks in the **Doped-LLZO Solid-State Electrolyte Discovery** repository.

---

## 🛠️ Track A: High-Performance / Standard Pipeline (`02_pipeline/`)

Focus: High-performance Li-site (Al, Ga, Fe, Zn), La-site (Sr, Y, Gd, Ca, Ba), and Zr-site (Nb, Ta, Sb, W) co-doping.

### 🚀 One-Click PowerShell Runner:
```powershell
.\run_standard_pipeline.ps1
```

### 📋 Step-by-Step Command Sequence:

```powershell
# Optional: Set Materials Project API key for thermodynamic hull calculations (Step 4a)
$env:MP_API_KEY = "your_materials_project_api_key"

# Step 1: Extract compositional features from 679 experimental dataset samples
python 02_pipeline/step1_feature_extraction/fast_surrogate_extraction.py
# → Output: 01_data/results/bayesian_features.csv

# Step 2: Train GPR & Random Forest surrogate models (with 5-fold CV)
python 02_pipeline/step2_model_training/bayesian_validation.py
# → Output: 02_pipeline/step2_model_training/trained_gpr_model.pkl & cv_metrics.json

# Step 3a: Generate virtual charge-balanced combinatorial library (14,474 candidates)
python 02_pipeline/step3_screening/generate_candidates.py
# → Output: 01_data/candidates/bayesian_virtual_candidates.csv

# Step 3b: Fast Random Forest pre-screening (rank & pick top 50 candidates)
python 02_pipeline/step3_screening/compositional_screening.py
# → Output: 01_data/candidates/top_50_screened_candidates.csv

# Step 3c: CHGNet staged relaxation (full-cell) & GPR conductivity evaluation
python 02_pipeline/step3_screening/evaluate_candidates_chgnet.py
# → Output: 01_data/results/evaluated_top_candidates.csv & 03_structures/relaxed/*.cif

# Step 4a: Thermodynamic stability check (Materials Project convex hull)
python 02_pipeline/step4_stability/thermodynamic_stability.py
# → Output: 01_data/results/thermodynamic_stability.csv

# Step 4b: Dynamical stability check (Phonon calculation)
python 02_pipeline/step4_stability/dynamical_stability.py
# → Output: 01_data/results/dynamical_stability.csv

# Step 4c: Mechanical stability check (Elastic tensor)
python 02_pipeline/step4_stability/mechanical_stability.py
# → Output: 01_data/results/mechanical_stability.csv

# Step 5: Arrhenius Molecular Dynamics (NVT Langevin σ_RT & Ea extraction)
python 02_pipeline/step5_md_validation/backtrack_validation_corrected.py
# → Output: 01_data/results/finalresults.csv
```

---

## 🛠️ Track B: Earth-Abundant Pipeline (`earth_abundant/`)

Focus: Sustainable, low-cost dopants only (Fe, Mg, Mn, Zn on Li-site; Ti, Nb, Sn on Zr-site). Excludes Ta, W, Ga.

### 🚀 One-Click PowerShell Runner:
```powershell
.\run_ea_pipeline.ps1
```

### 📋 Step-by-Step Command Sequence:

```powershell
# Optional: Set Materials Project API key for thermodynamic hull calculations (Step 5)
$env:MP_API_KEY = "your_materials_project_api_key"

# Step 1: Feature extraction for Earth-Abundant dataset
python earth_abundant/scripts/ea_step1_feature_extraction.py
# → Output: earth_abundant/data/results/ea_gpr_features.csv

# Step 2: Train EA-specific GPR model (5-fold CV)
python earth_abundant/scripts/ea_step2_model_training.py
# → Output: earth_abundant/data/models/ea_gpr_model.pkl & ea_cv_metrics.json

# Step 3: Generate 535 charge-balanced Earth-Abundant candidates
python earth_abundant/scripts/ea_step3_candidates.py
# → Output: earth_abundant/data/candidates/earth_abundant_candidates_raw.csv

# Step 4: CHGNet staged relaxation & GPR conductivity prediction
python earth_abundant/scripts/ea_step4_validate.py
# → Output: earth_abundant/data/results/ea_validated_candidates.csv & earth_abundant/structures/*.cif

# Step 5: Thermodynamic hull distance (Materials Project API)
python earth_abundant/scripts/ea_step5_stability.py
# → Output: earth_abundant/data/results/ea_thermodynamic_stability.csv

# Step 6: Arrhenius Molecular Dynamics validation
python earth_abundant/scripts/ea_step6_md_validation.py
# → Output: earth_abundant/data/results/ea_finalresults.csv
```

---

## ☁️ Google Colab Execution Instructions

If the direct Colab badge link does not open directly in your browser:

### Method 1: Open via Colab GitHub Search
1. Open [https://colab.research.google.com/](https://colab.research.google.com/)
2. Click the **GitHub** tab.
3. Paste the repository URL: `https://github.com/indra2215/Doped-LLZO`
4. Select `chgnet.ipynb` from the list.

### Method 2: Manual Upload to Colab
1. Open [https://colab.research.google.com/](https://colab.research.google.com/)
2. Click the **Upload** tab.
3. Select `chgnet.ipynb` from your local folder (`d:\doped_2\chgnet.ipynb`).
4. Select **Runtime > Change runtime type > GPU (T4)** and run all cells.
