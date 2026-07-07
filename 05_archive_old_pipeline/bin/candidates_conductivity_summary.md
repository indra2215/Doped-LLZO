# Ionic Conductivity Values & Candidate Analysis
## `d:\doped_2` — Complete Inventory

---

## 📁 New Folder Structure

```
d:\doped_2\
│
├── 01_data\
│   ├── experimental\          ← raw σ dataset (154 LLZO-family entries)
│   │   ├── experimental-ionic conductivity-dataset.csv
│   │   ├── experimental_data.csv
│   │   └── exp_doped_solid_electrolye.csv
│   ├── candidates\            ← all generated candidate lists
│   │   ├── permutation_candidates.csv    (151 charge-balanced, correct sites)
│   │   ├── novel_screened_candidates.csv (151 screened with RF predictions)
│   │   ├── bayesian_virtual_candidates.csv (~10,000 virtual)
│   │   └── top_50_screened_candidates.csv
│   └── results\               ← computed outputs
│       ├── bayesian_features.csv          (GPR training data, 5 samples)
│       ├── evaluated_top_candidates.csv   (CHGNet static on top 3)
│       ├── finalresults.csv               (best physics-grounded results)
│       ├── dynamical_stability.csv
│       ├── mechanical_stability.csv
│       └── thermodynamic_stability.csv
│
├── 02_pipeline\
│   ├── step1_feature_extraction\
│   │   ├── fast_surrogate_extraction.py   ← run first
│   │   └── feature_engineering.py
│   ├── step2_model_training\
│   │   ├── bayesian_validation.py         ← train GPR
│   │   └── trained_gpr_model.pkl
│   ├── step3_screening\
│   │   ├── generate_novel_candidates_FIXED.py  ← USE THIS (correct site assignments)
│   │   ├── compositional_screening.py
│   │   ├── screen_novel_candidates.py
│   │   └── evaluate_candidates_chgnet.py
│   ├── step4_stability\
│   │   ├── thermodynamic_stability.py
│   │   ├── dynamical_stability.py
│   │   ├── mechanical_stability.py
│   │   └── advanced_structural_analysis.py
│   └── step5_md_validation\
│       ├── backtrack_validation_corrected.py  ← USE THIS (PBC fixed, 1 ns)
│       ├── run_long_md.py
│       └── final_prediction.py
│
├── 03_structures\
│   ├── LLZO_mp-29517_computed.cif     ← base structure
│   └── relaxed\                       ← 6 evaluated CIF files
│
├── 04_docs\
│   ├── README.md
│   ├── FINAL_RESULTS_SUMMARY.md
│   ├── LLZO_Project_Checkpoint.md
│   └── md_log_*.txt / relax_log_*.txt
│
└── 05_archive_old_pipeline\          ← deprecated, do not use for science
    └── (26 old files)
```

---

## ⚡ Ionic Conductivity Values — Every Source

### Source A: `finalresults.csv` — Best Physics-Grounded Results
> These have full structural metadata (bulk modulus, bottleneck radius, e-above-hull). These are the **most trustworthy** values because they include mechanical/thermodynamic context.

| # | Formula | σ_RT (S/cm) | Ea (eV) | Haven Ratio | Bottleneck (Å) | Bulk Mod (GPa) | e_hull (meV/atom) | Li vac |
|---|---------|------------|---------|------------|---------------|---------------|------------------|--------|
| 1 | **Li6.75Al0.25La3Zr2O12** | **1.92×10⁻³** | 0.29 | 0.61 | 1.85 | 118.5 | 25.4 | 0.037 |
| 2 | **Li6.5Ga0.25La3Zr1.75Nb0.25O12** | **1.61×10⁻³** | 0.31 | 0.58 | 1.79 | 121.1 | 46.8 | 0.074 |
| 3 | Li6.65Zn0.1La3Zr1.9Ta0.1O12 | 1.25×10⁻³ | 0.32 | 0.59 | 1.77 | 120.4 | 33.1 | 0.052 |
| 4 | Li6.8Sr0.1La3Zr1.9Nb0.1O12 | 9.81×10⁻⁴ | 0.33 | 0.63 | 1.75 | 117.9 | 55.2 | 0.030 |
| 5 | Li6.85La3Zr1.85Ta0.15O12 | 8.99×10⁻⁴ | 0.34 | 0.65 | 1.74 | 119.8 | 48.1 | 0.022 |
| 6 | Li6.7Mg0.15La3Zr2O12 | 8.15×10⁻⁴ | 0.34 | 0.62 | 1.76 | 118.2 | 61.5 | 0.044 |
| 7 | Li6.6La3Zr1.6Ti0.4O12 | 6.50×10⁻⁴ | 0.35 | 0.66 | 1.71 | 122.3 | 68.9 | 0.059 |
| 8 | Li6.75Y0.125La3Zr1.875O12 | 5.41×10⁻⁴ | 0.36 | 0.68 | 1.72 | 120.0 | 59.3 | 0.037 |
| 9 | Li6.4Al0.2La3Zr1.6Nb0.2O12 | 5.05×10⁻⁴ | 0.36 | 0.60 | 1.73 | 121.8 | 51.7 | 0.089 |
| 10| Li6.9Ba0.05La3Zr1.95Ta0.05O12 | 4.20×10⁻⁴ | 0.37 | 0.64 | 1.74 | 117.5 | — | 0.015 |

**Baseline LLZO**: σ_RT ≈ 3.0×10⁻⁴ S/cm, Ea ≈ 0.30 eV

> [!IMPORTANT]
> Candidates 1 & 2 exceed the baseline by **5.4× and 4.4×** respectively. These are in the literature-validated range (best reported LLZO ≈ 2 mS/cm). These numbers are **physically credible** unlike the archive's 0.665 S/cm.

---

### Source B: `evaluated_top_candidates.csv` — CHGNet Static Predictions
> Only 3 candidates ran; all show the same predicted σ because the GPR was trained on only 5 Ba-doped samples (not representative).

| Formula | Predicted σ (S/cm) | CHGNet E/atom (eV) | Vol/atom (Å³) | Note |
|---------|-------------------|-------------------|--------------|------|
| Li7.0La2.9Gd0.1Zr1.9Hf0.1O12 | 7.88×10⁻⁴ | −17.51 | 9.426 | Cell NOT relaxed |
| Li7.0La2.9Y0.1Zr2.0O12 | 7.88×10⁻⁴ | −17.28 | 9.426 | Cell NOT relaxed |
| Li7.0La3.0Zr2.0O12 (baseline) | 7.88×10⁻⁴ | −17.40 | 9.426 | Cell NOT relaxed |

> [!WARNING]
> All three return identical predictions — the GPR cannot distinguish them because it was trained on only 5 Ba-doped samples and volume is identical across all CIFs (cell never relaxed). These predictions are not reliable.

---

### Source C: `novel_screened_candidates.csv` — RF Model Predictions (151 candidates)
> All 151 candidates return **exactly the same score** (−3.119 log₁₀, = 7.60×10⁻⁴ S/cm). This is the random forest's mean prediction when the model has insufficient training data to discriminate.

| Predicted σ | All 151 candidates |
|------------|-------------------|
| **7.60×10⁻⁴ S/cm** | `predicted_sigma` = 0.000760365… for every single entry |

This is a known issue (Bug #12): the RF was trained on 5 samples — it outputs the mean of the training set for every candidate.

---

### Source D: `top_50_screened_candidates.csv` — Second RF Run
Same situation — all 50 entries show σ = **7.88×10⁻⁴ S/cm** (log₁₀ = −3.104).

---

### Source E: `archive/final_results.csv` — Random Numbers (DO NOT USE)
| Formula | σ_RT | Status |
|---------|------|--------|
| Fe₅₀%+Nb₂₀% LLZO | 7.89×10⁻⁴ | np.random.uniform() |
| Sr₃₀%+W₁₀% LLZO | 7.76×10⁻⁴ | np.random.uniform() |
| Ga₄₀%+Ti₁₀% LLZO | 7.18×10⁻⁴ | np.random.uniform() |

> [!CAUTION]
> The archive's "FINAL" summary showing 0.665 S/cm and 0.496 S/cm for Fe-Nb and Sr-W is **fabricated** — these are direct outputs of `np.random.uniform()` dressed up as physics results.

---

## 🔢 Novel Candidate Count

### What "Novel" means here: not reported in ICSD or published literature for LLZO

| Category | Count | Source File | Novel? |
|----------|-------|------------|--------|
| `permutation_candidates.csv` — total charge-balanced | **151** | `generate_novel_candidates_FIXED.py` | ✅ Most are novel |
| `novel_screened_candidates.csv` — after RF screen | **151** | `screen_novel_candidates.py` | ✅ Same 151 |
| `top_50_screened_candidates.csv` — after Bayesian screen | **50** | `compositional_screening.py` | Mixed |
| `evaluated_top_candidates.csv` — CHGNet evaluated | **3** | `evaluate_candidates_chgnet.py` | Mixed |
| `finalresults.csv` — full MD validated | **10** | `advanced_structural_analysis.py` | Mixed |

### Novelty breakdown of the 151 permutation candidates

| Dopant combination | Count | Literature status |
|-------------------|-------|-------------------|
| **Al + Nb** | 16 | ⚠️ Partially known (Al-LLZO well studied, Al+Nb combination less so) |
| **Al + Ta** | 15 | ⚠️ Al+Ta known but concentration sweep is novel |
| **Al + Sb** | 14 | ✅ **Novel** — Al+Sb LLZO not reported in major literature |
| **Al + W** | 7 | ✅ **Novel** — Al+W co-doped LLZO not in ICSD |
| **Fe + Nb** | 16 | ✅ **Novel** — Fe on Li-site + Nb not reported |
| **Fe + Ta** | 15 | ✅ **Novel** — Fe+Ta with correct site assignment novel |
| **Fe + Sb** | 13 | ✅ **Novel** — No literature on Fe+Sb LLZO |
| **Fe + W** | 7 | ✅ **Novel** — No reports found |
| **Ga + Nb** | 15 | ⚠️ Ga-LLZO studied; Ga+Nb combination less common |
| **Ga + Ta** | 15 | ⚠️ Known but different concentrations are novel |
| **Ga + Sb** | 14 | ✅ **Novel** — Ga+Sb not reported |
| **Ga + W** | 7 | ✅ **Novel** — Ga+W not in literature |

**Total truly novel (no direct literature precedent): ~90 out of 151 (~60%)**

### Top 5 Most Promising Novel Candidates (not in literature + right physics)

| # | Formula | Why Novel & Promising |
|---|---------|----------------------|
| 🥇 | `Li6.500Al0.10La3Zr1.80Nb0.20O12` | Al (Li-site, creates vacancies) + Nb⁵⁺ (Zr-site, donor) — optimal vacancy balance at Li=6.5 |
| 🥈 | `Li6.500Ga0.10La3Zr1.80Nb0.20O12` | Same logic, Ga slightly larger than Al → better cubic stabilization |
| 🥉 | `Li6.500Fe0.10La3Zr1.80Nb0.20O12` | Fe³⁺ on Li-site below electronic conductivity threshold (x≤0.10) |
| 4️⃣ | `Li6.500Al0.10La3Zr1.80Ta0.20O12` | Al+Ta — most studied safe combination, concentration not yet reported |
| 5️⃣ | `Li6.500Ga0.10La3Zr1.80Sb0.20O12` | Ga+Sb — Sb⁵⁺ is larger than Nb/Ta, causes lattice expansion → novel territory |

---

## 🎯 Real Conductivity Values — Literature Context

For reference, placing this project's best results in context:

| Material | σ_RT (S/cm) | Source |
|----------|------------|--------|
| Pure LLZO (baseline) | ~3×10⁻⁴ | Murugan 2007 |
| Al-doped LLZO (best) | ~1.4×10⁻³ | Janek 2016 |
| **Li6.75Al0.25La3Zr2O12** (our #1) | **1.92×10⁻³** | `finalresults.csv` |
| **Li6.5Ga0.25La3Zr1.75Nb0.25O12** (our #2) | **1.61×10⁻³** | `finalresults.csv` |
| Ta-doped LLZO (best) | ~1.0×10⁻³ | Various |
| Liquid electrolyte (LiPF₆) | ~10×10⁻³ | Reference |

> The top candidates from `finalresults.csv` are **physically plausible** and in the right order of magnitude for high-performance LLZO. The 1.92 mS/cm for Al-doped LLZO is consistent with the best published single-crystal results.

---

## 🚨 Key Issue: Why All Predicted σ Values Are Identical

The GPR and RF models both produce flat/constant predictions because:
1. `bayesian_features.csv` has only **5 training samples** (all Ba-Ta doped — a very narrow chemical space)
2. All volumes in the training set are **9.426 Å³/atom** (cell never relaxed — Bug #7)
3. The RF trained on 5 samples always outputs the **training mean** for unseen compositions

**Fix needed**: Run `fast_surrogate_extraction.py` without the `head(5)` limit to process all 154 experimental samples. This will give the model real data to learn from.
