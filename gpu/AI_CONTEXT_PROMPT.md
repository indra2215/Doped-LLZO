# AI Context Prompt — Doped-LLZO Discovery Pipeline
## Handoff Document for Continuation by Another AI Model

> **Purpose:** This file gives a new AI model (Claude, GPT-4, Gemini, etc.) full context  
> to understand this project, pick up exactly where it left off, and continue work.  
> Copy this entire file as the system prompt or first user message.

---

## 🧠 WHO YOU ARE (Role Definition)

You are assisting a materials science researcher running a **computational solid electrolyte discovery pipeline**. The researcher is using ML + physics simulation to find the best dopant compositions for **LLZO (Li₇La₃Zr₂O₁₂)** — a solid-state battery electrolyte material.

The researcher has a Windows machine with:
- Python environment with CHGNet, ASE, PyMatGen, scikit-learn installed
- NVIDIA GPU (RTX 3050, 6 GB VRAM) — primary compute target
- Access to the Materials Project API (optional — needed for hull checks)
- Project root: `C:\Users\sahasra\Downloads\doped\Doped-LLZO\`

---

## 📖 PROJECT BACKGROUND

### What is LLZO?
**Li₇La₃Zr₂O₁₂ (LLZO)** is a garnet-structured ceramic that conducts lithium ions. It is a candidate **solid electrolyte** for next-generation solid-state batteries — safer than liquid electrolytes, non-flammable, electrochemically stable.

**Problem:** Undoped LLZO has poor ionic conductivity (~10⁻⁶ S/cm). The goal is to find doped compositions that reach **> 10⁻⁴ S/cm** at room temperature.

**Solution approach:** Use AI to screen thousands of compositions, validate with a GNN physics engine (CHGNet), then run Molecular Dynamics simulations to compute the true conductivity.

### Garnet Crystal Structure
```
Li₇La₃Zr₂O₁₂ — Cubic, space group Ia-3̄d (No. 230)
├── A-site (dodecahedral, 8-coord): La³⁺ → can substitute Ba²⁺, Ca²⁺, Gd³⁺
├── B-site (octahedral, 6-coord):  Zr⁴⁺ → can substitute Ta⁵⁺, Nb⁵⁺, Ti⁴⁺
└── C-site (tetrahedral, 4-coord): Li⁺  → can substitute Ga³⁺, Al³⁺, Zn²⁺, Mg²⁺
```

Substituting higher-valence cations (e.g. Ta⁵⁺ for Zr⁴⁺) creates **Li vacancies** — the key to fast Li-ion transport.

---

## 🔁 THE TWO PIPELINES (What Was Built)

### Pipeline A — Earth-Abundant (EA)
**Goal:** Find high-conductivity LLZO using ONLY sustainable, low-cost dopants.

**Allowed dopants:** Fe, Mg, Al, Ti, Mn, Nb, Sn, Zn

**Steps completed:**
- ✅ Feature extraction from 45 LLZO experimental measurements
- ✅ EA-GPR model trained (`ea_gpr_model.pkl`, 3.7 MB, R² > 0.60)
- ✅ 535 low-cost candidate compositions generated
- ✅ Top 5 validated by CHGNet — ALL 5 thermally STABLE (ΔE < −7 eV/atom vs baseline LLZO)
- ✅ GPR conductivity predictions made

**Steps remaining (GPU required):**
- ⏳ EA Step 5: MP thermodynamic hull check (needs API key, optional)
- ⏳ **EA Step 6: Arrhenius MD simulation at 600/800/1000 K** ← PRIMARY TASK
- ⏳ EA Step 7: Compile final σ_RT results

**Best EA candidate:** `Li6.500Zn0.20La3Zr1.90Nb0.10O12`
- ΔE vs LLZO: −8.99 eV/atom (STABLE)
- GPR σ_RT: **6.67 × 10⁻⁴ S/cm**
- Dopants: Zn on Li-site + Nb on Zr-site

---

### Pipeline B — Standard High-Performance
**Goal:** Find the absolute best conductivity LLZO, no elemental constraints.

**Dopants used:** Ba, Ca, Gd, Ga (La-site) + Ta (Zr-site)

**Steps completed:**
- ✅ Feature extraction + GPR + Random Forest screening
- ✅ 14,474 Bayesian virtual candidates generated
- ✅ Random Forest pre-filter → top 50 candidates
- ✅ CHGNet staged_relax → 41 of 50 successfully relaxed → 41 CIF files
- ✅ GPR conductivity predictions (MASTER_RESULTS.csv with 35 ranked candidates)
- ⚠️ Thermodynamic hull: ALL show `e_above_hull = inf` — **this is because the MP API key was missing, NOT because materials are unstable**

**Steps remaining (GPU required):**
- ⏳ Step 4A re-run: MP hull check with API key (optional, resolves `inf` flags)
- ⏳ Step 4B: Phonon/dynamical stability (HPC DFPT — low priority)
- ⏳ Step 4C: Mechanical moduli (HPC DFT elastic tensor — low priority)
- ⏳ **Step 5: Arrhenius MD simulation** ← PRIMARY TASK
- ⏳ Step 6–7: Final compilation and cross-pipeline report

**Best standard candidate:** `Li6.45La3.0Zr1.45Ta0.55O12`
- GPR σ_RT: **6.11 × 10⁻⁴ S/cm** (Rank #1 of 35)
- Simple Ta-only doping (no A-site substitution)

---

## 📂 FILE SYSTEM MAP

```
C:\Users\sahasra\Downloads\doped\Doped-LLZO\     ← PROJECT ROOT
│
├── run_remaining_steps.py                        ← MASTER GPU SCRIPT (850 lines)
├── gpu/                                          ← THIS PACKAGE
│   ├── README.md                                 ← Full project explanation
│   ├── AI_CONTEXT_PROMPT.md                      ← This file
│   ├── pipeline_A_earth_abundant/
│   │   ├── 01_compounds/
│   │   │   ├── all_cif_structures/  (25 CIFs)    ← All EA structures
│   │   │   └── md_priority_queue/   (3 CIFs)     ← GPU MD inputs
│   │   ├── 02_properties/
│   │   │   ├── conductivity_predictions/          ← ea_gpr_predictions.csv, ea_validated_candidates.csv
│   │   │   ├── thermal_stability/                 ← ea_thermal_stability.csv
│   │   │   ├── thermodynamic_stability/           ← ea_thermodynamic_stability.csv (empty)
│   │   │   └── feature_descriptors/               ← ea_gpr_features.csv, raw 535 candidates
│   │   ├── 03_terms_and_definitions/GLOSSARY_EA.md
│   │   └── 04_remaining_steps/REMAINING_STEPS_EA.md
│   ├── pipeline_B_standard_high_performance/
│   │   ├── 01_compounds/
│   │   │   ├── all_cif_structures/  (41 CIFs)    ← All standard structures
│   │   │   └── md_priority_queue/   (3 CIFs)     ← GPU MD inputs
│   │   ├── 02_properties/
│   │   │   ├── conductivity_predictions/          ← MASTER_RESULTS.csv (35 ranked)
│   │   │   ├── thermal_stability/                 ← evaluated_top_candidates.csv
│   │   │   ├── thermodynamic_stability/           ← thermodynamic_stability.csv (all inf)
│   │   │   ├── dynamical_stability/               ← dynamical_stability.csv (2 entries, incomplete)
│   │   │   ├── mechanical_stability/              ← mechanical_stability.csv (3 entries, incomplete)
│   │   │   └── screening_candidates/              ← top_50_screened_candidates.csv, bayesian_features.csv
│   │   ├── 03_terms_and_definitions/GLOSSARY_STD.md
│   │   └── 04_remaining_steps/REMAINING_STEPS_STD.md
│   └── shared_resources/
│       ├── baseline_structure/LLZO_mp-29517_computed.cif
│       ├── models/ea_gpr_model.pkl               ← 3.7 MB trained EA-GPR
│       └── execution_scripts/
│           ├── run_remaining_steps.py
│           └── EXECUTION_GUIDE.md
│
├── earth_abundant/                               ← PIPELINE A SOURCE DATA
│   ├── data/results/                             ← ea_validated_candidates.csv, ea_thermal_stability.csv
│   ├── data/models/ea_gpr_model.pkl
│   └── structures/                              ← 25 EA CIF files (source)
│
├── 03_structures/relaxed/                        ← PIPELINE B SOURCE CIFs (41 files)
│
├── FINAL_Results/High_Performance_Pipeline/      ← PIPELINE B PROPERTY CSVs
│   └── MASTER_RESULTS.csv                        ← 35-row ranked table
│
└── 01_data/results/                              ← Bayesian features, evaluated candidates
```

---

## 🔑 THE MOST IMPORTANT FILES

| File | What It Contains | Why It Matters |
|------|-----------------|----------------|
| `run_remaining_steps.py` | 850-line master runner | Executes ALL remaining pipeline steps |
| `gpu/shared_resources/models/ea_gpr_model.pkl` | Trained EA-GPR surrogate | Predicts conductivity for EA compositions |
| `gpu/pipeline_A_earth_abundant/01_compounds/md_priority_queue/*.cif` | 3 EA candidate structures | Direct input to Arrhenius MD |
| `gpu/pipeline_B_standard_high_performance/01_compounds/md_priority_queue/*.cif` | 3 Standard candidate structures | Direct input to Arrhenius MD |
| `gpu/pipeline_B_standard_high_performance/02_properties/conductivity_predictions/MASTER_RESULTS.csv` | 35-row ranked results table | Source of truth for standard pipeline |
| `gpu/pipeline_A_earth_abundant/02_properties/conductivity_predictions/ea_validated_candidates.csv` | 5-row validated results | Source of truth for EA pipeline |
| `gpu/shared_resources/baseline_structure/LLZO_mp-29517_computed.cif` | Undoped LLZO structure | Energy reference for all ΔE calculations |

---

## ⚙️ HOW THE GPU SCRIPT WORKS

**Script:** `run_remaining_steps.py` — located in project root AND copied to `gpu/shared_resources/execution_scripts/`

```python
# Internal architecture:
# 1. Parses CLI args (--mp-key, --md-steps, --n-candidates, --use-cpu, etc.)
# 2. Detects GPU/CPU and VRAM availability
# 3. Runs functions in sequence:
#    - run_ea_step4()   → CHGNet validation (already done, will skip if CSV exists)
#    - run_ea_step5()   → MP hull check (skipped if no API key)
#    - run_ea_step6()   → Arrhenius MD ← MAIN GPU TASK
#    - run_std_step5()  → Arrhenius MD for Standard candidates ← MAIN GPU TASK

# Key internal function: run_md_arrhenius(cif_path, calc, n_steps, temperatures)
#   - Loads CIF via ASE
#   - Attaches CHGNetCalculator (GPU-accelerated)
#   - Runs NVT Langevin at 600/800/1000 K
#   - Tracks Li MSD (periodic boundary corrected)
#   - Fits D(T) slope, then Arrhenius → Ea, σ_RT(300K)

# CRITICAL: torch.set_grad_enabled(True) MUST be True for CHGNet MD forces
# (forces computed via torch.autograd.grad(energy, positions))
```

---

## 🎯 THE 6 MD CANDIDATES (GPU INPUT)

### EA Pipeline — 3 Candidates
All confirmed **STABLE** (CHGNet ΔE < −7 eV/atom vs undoped LLZO):

```
1. Li6.500Zn0.20La3Zr1.90Nb0.10O12
   CIF: gpu/pipeline_A_earth_abundant/01_compounds/md_priority_queue/
   ΔE vs LLZO: -8.99 eV/atom
   GPR σ_RT: 6.67×10⁻⁴ S/cm  ← Best EA conductivity
   Dopants: Zn (Li-site, 0.20) + Nb (Zr-site, 0.10)

2. Li6.500Mn0.10La3Zr1.80Nb0.20O12
   ΔE vs LLZO: -9.17 eV/atom
   GPR σ_RT: 5.42×10⁻⁴ S/cm
   Dopants: Mn (Li-site, 0.10) + Nb (Zr-site, 0.20)

3. Li6.500Zn0.05La3Zr1.60Nb0.40O12
   ΔE vs LLZO: -9.21 eV/atom  ← Most stable EA candidate
   GPR σ_RT: 5.29×10⁻⁴ S/cm
   Dopants: Zn (Li-site, 0.05) + Nb (Zr-site, 0.40)
```

### Standard Pipeline — 3 Candidates
Hull check shows `inf` (MP key missing), but CHGNet relaxation succeeded:

```
1. Li6.45La3.0Zr1.45Ta0.55O12
   GPR σ_RT: 6.11×10⁻⁴ S/cm  ← Rank #1 of 35 overall
   CHGNet E/atom: 11.97 eV/atom
   Dopant: Ta only (Zr-site, 0.55)

2. Li6.4La3.0Zr1.4Ta0.6O12
   GPR σ_RT: 5.85×10⁻⁴ S/cm  ← Rank #2
   Dopant: Ta only (Zr-site, 0.60)

3. Li6.45La2.95Ba0.05Zr1.4Ta0.6O12
   GPR σ_RT: 5.57×10⁻⁴ S/cm  ← Rank #3, best with A-site dopant
   Dopants: Ba (La-site, 0.05) + Ta (Zr-site, 0.60)
```

---

## 💻 COMMANDS TO RUN

```bash
# Always from project root:
cd C:\Users\sahasra\Downloads\doped\Doped-LLZO

# ── Run everything (both pipelines, GPU-safe) ──────────────────────────────
python run_remaining_steps.py --n-candidates 3 --md-steps 500

# ── EA only ───────────────────────────────────────────────────────────────
python run_remaining_steps.py --skip-std-md --n-candidates 3 --md-steps 500

# ── Standard only ─────────────────────────────────────────────────────────
python run_remaining_steps.py --skip-ea6 --n-candidates 3 --md-steps 500

# ── With MP API key (resolves hull check) ─────────────────────────────────
python run_remaining_steps.py --mp-key mp-YOUR_KEY --n-candidates 3 --md-steps 500

# ── High-accuracy (needs 8+ GB VRAM) ─────────────────────────────────────
python run_remaining_steps.py --n-candidates 3 --md-steps 2000

# ── CPU fallback (slow but safe) ──────────────────────────────────────────
python run_remaining_steps.py --use-cpu --md-steps 200

# ── Single candidate test ─────────────────────────────────────────────────
python run_remaining_steps.py --n-candidates 1 --md-steps 300
```

---

## 📊 CURRENT DATA STATE — What Each CSV Contains

### ea_validated_candidates.csv (5 rows)
Columns: `formula, pair, Li_pfu, Li_site, Li_conc, Zr_site, Zr_conc, is_novel, chgnet_static_E_per_atom, chgnet_static_V_per_atom, chgnet_eval_E_per_atom, chgnet_eval_V_per_atom, was_relaxed, m3gnet_E_per_atom, delta_E_models, cross_model_ok, delta_E_vs_LLZO, thermal_stability, gpr_sigma_RT_bulk_S_cm, gpr_sigma_RT_with_layer_S_cm, gpr_sigma_err_S_cm, conductivity_order`

### MASTER_RESULTS.csv (35 rows, standard pipeline)
Columns: `rank, formula, gpr_predicted_sigma_S_cm, gpr_sigma_uncertainty_S_cm, chgnet_energy_eV_per_atom, chgnet_volume_A3_per_atom, relaxation_mode, e_above_hull_eV_atom, thermodynamically_stable, is_dynamically_stable, max_imaginary_freq_THz, bulk_modulus_vrh, shear_modulus_vrh, poisson_ratio, is_mechanically_stable, md_validated_sigma_S_cm`

Note: `md_validated_sigma_S_cm = "Pending HPC"` for all rows — this is what the MD step will fill in.

---

## ⚠️ KNOWN ISSUES & WORKAROUNDS

| Issue | Cause | Workaround |
|-------|-------|-----------|
| `e_above_hull = inf` for all standard candidates | MP API key not provided | Add `--mp-key` flag |
| `is_dynamically_stable = False` for 2 reference structures | DFPT run crashed/incomplete | Re-run with proper HPC DFPT setup |
| `bulk_modulus = 0` for 3 structures | Mechanical stability run was incomplete | Re-run elastic tensor calc |
| `torch.set_grad_enabled(False)` crash in MD | CHGNet needs autograd for forces | Script sets `True` automatically |
| OOM crash on GPU | Too many atoms × too many steps in autograd graph | Use `--md-steps 200` or `--use-cpu` |
| Windows cp1252 encoding error | Unicode characters in output | Script wraps stdout in UTF-8 automatically |

---

## 🧩 DEPENDENCY STACK

```
Python 3.9+
├── chgnet >= 0.3.0          ← Physics engine (GNN)
│   ├── torch >= 2.0         ← CUDA backend
│   ├── pymatgen >= 2023.5   ← Crystal structure handling
│   └── ase >= 3.22          ← Molecular dynamics
├── scikit-learn >= 1.2      ← GPR, Random Forest
├── numpy >= 1.24
├── pandas >= 1.5
└── mp-api (optional)        ← Materials Project hull check

Install: pip install chgnet scikit-learn pandas numpy mp-api
```

---

## 📝 HOW TO HELP THE USER (Suggested Actions)

If the user asks you to **help run the pipeline**, the most useful things you can do:

1. **Check GPU availability:**
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.get_device_name(0))
   print(torch.cuda.mem_get_info(0))
   ```

2. **Run the MD step:**
   ```bash
   cd C:\Users\sahasra\Downloads\doped\Doped-LLZO
   python run_remaining_steps.py --n-candidates 3 --md-steps 500
   ```

3. **Check if results were written:**
   ```bash
   # EA results:
   cat earth_abundant/data/results/ea_md_arrhenius_results.csv
   # Standard results:
   cat "FINAL_Results/High_Performance_Pipeline/MASTER_RESULTS.csv"
   ```

4. **If OOM error:** Reduce `--md-steps` to 200 or add `--use-cpu`

5. **If MP hull is needed:** User must get free API key at `https://materialsproject.org/api`

6. **To understand a CIF file:** Use pymatgen:
   ```python
   from pymatgen.core import Structure
   s = Structure.from_file("Li6.500Zn0.20La3Zr1.90Nb0.10O12.cif")
   print(s.formula, s.volume, len(s))
   ```

---

## 🏁 WHAT FINAL SUCCESS LOOKS LIKE

After the GPU run completes, the researcher should have:

```csv
# ea_md_arrhenius_results.csv (EA pipeline)
formula, T_K, D_cm2_s, Ea_eV, sigma_RT_S_cm
Li6.500Zn0.20La3Zr1.90Nb0.10O12, 600, 2.3e-09, 0.31, 5.8e-04
Li6.500Zn0.20La3Zr1.90Nb0.10O12, 800, 8.7e-09, 0.31, 5.8e-04
Li6.500Zn0.20La3Zr1.90Nb0.10O12, 1000, 2.1e-08, 0.31, 5.8e-04

# MASTER_RESULTS.csv (standard pipeline, md_validated_sigma_S_cm column filled)
rank, formula, gpr_predicted_sigma_S_cm, ..., md_validated_sigma_S_cm
1, Li6.45La3.0Zr1.45Ta0.55O12, 6.11e-04, ..., 4.9e-04
```

**Interpretation:**
- MD σ_RT will likely be **lower** than GPR σ_RT (GPR is optimistic)
- Ea of 0.25–0.40 eV → good Li-ion conductor
- Final recommendation: Best balance of σ_RT + cost + stability for solid electrolyte synthesis

---

*End of context prompt. Pass this entire document to the new AI model as its initial context.*
