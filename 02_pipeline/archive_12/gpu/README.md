# 🧪 GPU Execution Package — Doped LLZO Solid Electrolyte Discovery

> **Project:** AI-accelerated discovery of high-conductivity doped Li₇La₃Zr₂O₁₂ (LLZO) solid electrolytes  
> **Prepared:** 2026-07-08 | **Status:** Screening DONE ✅ — MD Simulation PENDING GPU ⏳  
> **Two independent pipelines. Fully separated. All CIFs, properties, and scripts included.**

---

## 🔬 What Is This Project?

**LLZO (Li₇La₃Zr₂O₁₂)** is a garnet-type **solid-state electrolyte** — a key material for next-generation solid-state lithium batteries. Unlike liquid electrolytes, it is non-flammable, chemically stable, and can enable higher energy density batteries.

The problem: **undoped LLZO has low ionic conductivity (~10⁻⁶ S/cm)**. The goal is to discover doped LLZO compositions that raise conductivity above **10⁻⁴ S/cm** — the threshold for practical solid electrolytes.

This project uses a **three-layer computational pipeline**:
1. **Machine Learning (GPR)** — rapidly screens thousands of compositions
2. **CHGNet (GNN physics engine)** — validates structural stability with DFT-level accuracy
3. **Molecular Dynamics (MD)** — physically simulates Li-ion diffusion to get true σ_RT

Everything in this `gpu/` folder represents the **output of completed steps** and the **input for the remaining GPU steps**.

---

## 🏗️ What Are the Two Pipelines?

### Pipeline A — Earth-Abundant (EA)
**Question answered:** *Can we find LLZO compositions that are highly conductive AND made from cheap, abundant elements?*

- Restricts dopants to: **Fe, Mg, Al, Ti, Mn, Nb, Sn, Zn** only
- Generated 535 candidate compositions
- Top 5 validated by CHGNet — all thermally **STABLE** (ΔE < 0 vs undoped LLZO)
- Best predicted conductivity: **6.67 × 10⁻⁴ S/cm** (Zn+Nb co-doped)
- Status: **MD simulation pending** (main GPU task)

### Pipeline B — Standard (High-Performance)
**Question answered:** *What is the absolute highest conductivity LLZO we can predict, ignoring cost?*

- No elemental constraints — uses Ba, Ca, Gd, Ga, Ta (premium/rare elements allowed)
- Screened 14,474 virtual Bayesian candidates → top 50 → 41 CHGNet-relaxed CIFs
- Best predicted conductivity: **6.11 × 10⁻⁴ S/cm** (simple Ta-doped LLZO)
- Status: **MD simulation pending** + hull check needs MP API key

---

## 📁 This Folder's Complete Structure

```
gpu/
├── README.md                                    ← YOU ARE HERE — Read this first
│
├── pipeline_A_earth_abundant/                   ══════ PIPELINE A ══════
│   │
│   ├── 01_compounds/                            ALL CRYSTAL STRUCTURE FILES
│   │   ├── all_cif_structures/  (25 files)      Every EA candidate (CIF format)
│   │   │   ├── Li6.500Zn0.20La3Zr1.90Nb0.10O12.cif  ← Best EA conductivity
│   │   │   ├── Li6.500Mn0.10La3Zr1.80Nb0.20O12.cif  ← Best EA stability
│   │   │   ├── Li6.500Mg0.25La3... (×19 Mg variants)
│   │   │   └── ... (Al, Fe, Zn, Mn dopant families)
│   │   ├── md_priority_queue/   (3 files)       Top 3 queued for GPU MD run
│   │   │   ├── Li6.500Zn0.20La3Zr1.90Nb0.10O12.cif  ← Priority #1
│   │   │   ├── Li6.500Mn0.10La3Zr1.80Nb0.20O12.cif  ← Priority #2
│   │   │   └── Li6.500Zn0.05La3Zr1.60Nb0.40O12.cif  ← Priority #3
│   │   └── COMPOUNDS_INVENTORY.md               Full list with dopant groups & properties
│   │
│   ├── 02_properties/                           ALL COMPUTED PROPERTY DATA
│   │   ├── conductivity_predictions/
│   │   │   ├── ea_gpr_predictions.csv           GPR σ_RT predictions for all 5 candidates
│   │   │   └── ea_validated_candidates.csv      Full record: energies + conductivity + stability
│   │   ├── thermal_stability/
│   │   │   └── ea_thermal_stability.csv         CHGNet ΔE vs LLZO (all 5 STABLE)
│   │   ├── thermodynamic_stability/
│   │   │   └── ea_thermodynamic_stability.csv   MP hull (EMPTY — needs API key)
│   │   └── feature_descriptors/
│   │       ├── ea_gpr_features.csv              680-row feature matrix (training+candidates)
│   │       ├── earth_abundant_candidates_raw.csv    535 generated compositions
│   │       └── earth_abundant_candidates_validated.csv  5 CHGNet-validated results
│   │
│   ├── 03_terms_and_definitions/
│   │   └── GLOSSARY_EA.md                       Every technical term defined with context
│   │
│   └── 04_remaining_steps/
│       └── REMAINING_STEPS_EA.md                Step-by-step GPU tasks with exact commands
│
├── pipeline_B_standard_high_performance/        ══════ PIPELINE B ══════
│   │
│   ├── 01_compounds/                            ALL CRYSTAL STRUCTURE FILES
│   │   ├── all_cif_structures/  (41 files)      Every standard candidate (CHGNet relaxed)
│   │   │   ├── Li6.45La3.0Zr1.45Ta0.55O12_evaluated.cif   ← Rank #1
│   │   │   ├── Li6.4La3.0Zr1.4Ta0.6O12_evaluated.cif      ← Rank #2
│   │   │   ├── Li6.45La2.95Ba0.05...  (Ba+Ta family)
│   │   │   ├── Li6.4La2.xGd...        (Gd+Ta family, 9 variants)
│   │   │   ├── Li6.xGa...La...Ba/Ca   (Triple dopant family)
│   │   │   └── Li7.0La3.0Zr2.0O12_evaluated.cif   ← Baseline undoped LLZO
│   │   ├── md_priority_queue/   (3 files)       Top 3 queued for GPU MD run
│   │   │   ├── Li6.45La3.0Zr1.45Ta0.55O12_evaluated.cif   ← Priority #1
│   │   │   ├── Li6.4La3.0Zr1.4Ta0.6O12_evaluated.cif      ← Priority #2
│   │   │   └── Li6.45La2.95Ba0.05Zr1.4Ta0.6O12_evaluated.cif ← Priority #3
│   │   └── COMPOUNDS_INVENTORY.md               All 41 ranked by GPR, grouped by dopant
│   │
│   ├── 02_properties/                           ALL COMPUTED PROPERTY DATA
│   │   ├── conductivity_predictions/
│   │   │   ├── MASTER_RESULTS.csv               MAIN TABLE: 35 candidates fully ranked
│   │   │   ├── evaluated_top_candidates_in_progress.csv  Early run snapshot
│   │   │   └── finalresults.csv                 Placeholder (empty, pending MD)
│   │   ├── thermal_stability/
│   │   │   └── evaluated_top_candidates.csv     CHGNet E/atom + volume for all 41
│   │   ├── thermodynamic_stability/
│   │   │   └── thermodynamic_stability.csv      Hull data (all inf — needs MP API key)
│   │   ├── dynamical_stability/
│   │   │   └── dynamical_stability.csv          Phonon data (only 2 structs, incomplete)
│   │   ├── mechanical_stability/
│   │   │   └── mechanical_stability.csv         Moduli data (3 structs, values = 0, incomplete)
│   │   └── screening_candidates/
│   │       ├── top_50_screened_candidates_original.csv  Top 50 by Random Forest
│   │       └── bayesian_features.csv            Full 680-row Bayesian feature matrix
│   │
│   ├── 03_terms_and_definitions/
│   │   └── GLOSSARY_STD.md                      All standard pipeline terms defined
│   │
│   └── 04_remaining_steps/
│       └── REMAINING_STEPS_STD.md               All 7 remaining steps with commands & timing
│
└── shared_resources/                            ══ SHARED ACROSS BOTH PIPELINES ══
    ├── baseline_structure/
    │   └── LLZO_mp-29517_computed.cif           Undoped LLZO — energy reference for all ΔE
    ├── models/
    │   └── ea_gpr_model.pkl                     Trained EA-GPR surrogate (3.7 MB, scikit-learn)
    └── execution_scripts/
        ├── run_remaining_steps.py               Master runner — executes ALL remaining steps
        └── EXECUTION_GUIDE.md                   Full CLI reference + SLURM script
```

---

## 🔄 How the Pipelines Work (End-to-End)

```
RAW DATA (45 LLZO experimental conductivity measurements)
    │
    ▼
Step 1: Feature Engineering
    Extract 7 compositional descriptors per compound:
    Li fraction, electronegativity, atomic mass, radius, row, col, num_elements
    │
    ▼
Step 2: ML Model Training
    Pipeline A: EA-GPR trained on 45 samples (ea_gpr_model.pkl)
    Pipeline B: Standard GPR + Random Forest ensemble
    │
    ▼
Step 3: Virtual Candidate Generation & Screening
    Pipeline A: 535 EA-constrained compositions generated
    Pipeline B: 14,474 Bayesian compositions → Random Forest → top 50
    │
    ▼
Step 4: CHGNet Physics Validation
    Pipeline A: Top 5 candidates → position-only relaxation → ΔE vs LLZO
                → ALL 5 STABLE (ΔE < -7 eV/atom)
    Pipeline B: Top 50 → staged_relax → 41 CIF files generated
    │
    ▼ ← YOU ARE HERE — GPU PICKS UP FROM THIS POINT
    │
Step 5/6: Arrhenius MD Simulation (GPU REQUIRED)
    NVT Langevin MD @ 600K, 800K, 1000K
    Extract Li-ion MSD → D(T) diffusion coefficients
    Fit Arrhenius: ln(D) vs 1/T → activation energy Ea
    Nernst-Einstein: D_RT → σ_RT(300K) [true MD-validated conductivity]
    │
    ▼
Step 7: Final Results
    Complete MASTER_RESULTS.csv with MD-validated σ_RT
    Cross-pipeline comparison: EA vs Standard
    Synthesis recommendations
```

---

## ⚡ Pipeline A vs B — Key Differences

| | **Pipeline A (EA)** | **Pipeline B (Standard)** |
|---|---|---|
| **Philosophy** | Sustainable materials | Best possible performance |
| **Dopant pool** | Fe, Mg, Al, Ti, Mn, Nb, Sn, Zn | Ba, Ca, Gd, Ga, Ta + others |
| **Screening model** | EA-GPR (`ea_gpr_model.pkl`) | GPR + Random Forest |
| **Generation** | 535 candidates | 14,474 candidates |
| **Validation level** | CHGNet + ΔE vs LLZO | CHGNet full staged relaxation |
| **Stability confirmed** | ✅ YES (all 5 stable) | ⚠️ Hull check missing MP key |
| **CIFs available** | 25 | 41 |
| **MD inputs** | 3 CIFs in md_priority_queue | 3 CIFs in md_priority_queue |
| **Best σ_RT (GPR)** | 6.67×10⁻⁴ S/cm | 6.11×10⁻⁴ S/cm |
| **Ea (expected)** | ~0.25–0.40 eV | ~0.25–0.40 eV |

---

## 🎯 The 6 Candidates Queued for GPU

These are the only structures that need MD simulation. Everything else is complete.

### 🌿 EA Candidates (Pipeline A) — `pipeline_A_earth_abundant/01_compounds/md_priority_queue/`

| # | Formula | Why Selected | ΔE (eV/atom) | GPR σ_RT |
|---|---------|-------------|-------------|---------|
| 1 | **Li6.500Zn0.20La3Zr1.90Nb0.10O12** | Best predicted conductivity | -8.99 | **6.67×10⁻⁴** |
| 2 | **Li6.500Mn0.10La3Zr1.80Nb0.20O12** | 2nd best, earth-abundant Mn | -9.17 | 5.42×10⁻⁴ |
| 3 | **Li6.500Zn0.05La3Zr1.60Nb0.40O12** | Most thermodynamically stable | **-9.21** | 5.29×10⁻⁴ |

### ⚡ Standard Candidates (Pipeline B) — `pipeline_B_standard_high_performance/01_compounds/md_priority_queue/`

| # | Formula | Why Selected | GPR σ_RT | Dopant System |
|---|---------|-------------|---------|--------------|
| 1 | **Li6.45La3.0Zr1.45Ta0.55O12** | Rank #1 overall | **6.11×10⁻⁴** | Ta only |
| 2 | **Li6.4La3.0Zr1.4Ta0.6O12** | Rank #2 overall | 5.85×10⁻⁴ | Ta only |
| 3 | **Li6.45La2.95Ba0.05Zr1.4Ta0.6O12** | Best with A-site dopant | 5.57×10⁻⁴ | Ba + Ta |

---

## 🚀 How to Run on GPU

> ⚠️ **Must run from the `Doped-LLZO/` project root** — not from inside `gpu/`

```bash
# 1. Go to project root
cd C:\Users\sahasra\Downloads\doped\Doped-LLZO

# 2. Run both pipelines (recommended — 2–6 hrs on RTX 3050)
python run_remaining_steps.py --n-candidates 3 --md-steps 500

# 3. With Materials Project API key (resolves hull check flags)
python run_remaining_steps.py --mp-key mp-YOUR_KEY --n-candidates 3 --md-steps 500

# 4. CPU fallback (safe on any machine, 10–50x slower)
python run_remaining_steps.py --use-cpu --md-steps 200

# 5. High-accuracy publication run (needs 8+ GB VRAM)
python run_remaining_steps.py --mp-key mp-xxx --n-candidates 3 --md-steps 2000
```

---

## 📋 Remaining Steps — What's Left to Do

| Priority | Step | Task | GPU? | Est. Time |
|----------|------|------|------|-----------|
| 🔴 **1st** | EA Step 6 | Arrhenius MD — 3 EA candidates | ✅ Yes | 2–12 hrs |
| 🔴 **1st** | Std Step 5 | Arrhenius MD — 3 Standard candidates | ✅ Yes | 2–12 hrs |
| 🟡 **2nd** | Both | MP thermodynamic hull check | ❌ No | 5–20 min |
| 🟢 **3rd** | Both | Final results compilation | ❌ No | 5 min |
| 🔵 **Later** | Std Step 4B | Phonon stability (DFPT) | ✅ HPC | 4–48 hr/struct |
| 🔵 **Later** | Std Step 4C | Mechanical moduli (DFT elastic) | ✅ HPC | 2–24 hr/struct |
| ⚪ **Final** | Both | Cross-pipeline report + synthesis rec. | ❌ No | 1 hr |

**Minimum path to σ_RT results:** Just run the MD step above → done in 2–12 hours.

---

## 📚 Where to Read More

| Need | File to Read |
|------|-------------|
| All EA terms explained | `pipeline_A_earth_abundant/03_terms_and_definitions/GLOSSARY_EA.md` |
| All Standard terms explained | `pipeline_B_standard_high_performance/03_terms_and_definitions/GLOSSARY_STD.md` |
| EA step-by-step remaining tasks | `pipeline_A_earth_abundant/04_remaining_steps/REMAINING_STEPS_EA.md` |
| Standard step-by-step remaining tasks | `pipeline_B_standard_high_performance/04_remaining_steps/REMAINING_STEPS_STD.md` |
| EA compound list with properties | `pipeline_A_earth_abundant/01_compounds/COMPOUNDS_INVENTORY.md` |
| Standard compound list with rankings | `pipeline_B_standard_high_performance/01_compounds/COMPOUNDS_INVENTORY.md` |
| GPU script CLI reference | `shared_resources/execution_scripts/EXECUTION_GUIDE.md` |
| AI handoff prompt (for other models) | `AI_CONTEXT_PROMPT.md` ← in this folder |

---

*This package is self-contained. Every CIF, every property CSV, every trained model, and every execution script needed to complete the pipeline is included.*
