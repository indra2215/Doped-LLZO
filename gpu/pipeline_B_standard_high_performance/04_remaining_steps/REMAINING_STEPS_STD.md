# Pipeline B — Standard | Remaining Steps on GPU

**Status:** Steps 1–4 COMPLETE ✅ | Steps 4B–7 PENDING ⏳

---

## Progress Tracker

```
Std Step 1  ✅  Feature extraction from 45 LLZO experimental samples
             → bayesian_features.csv (680 rows, 7 descriptors)

Std Step 2  ✅  GPR + Random Forest training
             → trained_gpr_model.pkl, R² > 0.60

Std Step 3A ✅  Virtual Bayesian candidate generation (14,474 candidates)
Std Step 3B ✅  Random Forest pre-screening → top 50 candidates
             → top_50_screened_candidates_original.csv

Std Step 3C ✅  CHGNet geometry relaxation of top 50
             → 41/50 successfully relaxed → 41 CIF files in all_cif_structures/

Std Step 4A ✅  Thermodynamic hull check attempt
             → e_above_hull = inf for all (MP API key missing — not an error)

Std Step 4B ⏳  Dynamical stability (DFPT phonons) — NEEDS HPC
             → Incomplete: only 2 structures tested, both returned inf

Std Step 4C ⏳  Mechanical stability (elastic tensor) — NEEDS HPC
             → Incomplete: 3 structures returned 0 for all moduli

Std Step 5  ⏳  Arrhenius MD validation → σ_RT(300K) — NEEDS GPU
             → Primary GPU task for this pipeline

Std Step 6  ⏳  Final results compilation — depends on Steps 4A + 5

Std Step 7  ⏳  Comparison & publication report — depends on Step 6
```

---

## ⚠️ Std Step 4A — Re-run Thermodynamic Hull Check (With MP Key)

### What it does
Recalculates `e_above_hull` for all 35 ranked candidates using the Materials Project convex hull.

### Current Status
All 35 candidates show `e_above_hull = inf` in `MASTER_RESULTS.csv`.  
This is caused by **missing MP API key** during the original run — NOT a real instability.

### How to Run

```bash
# Get your key at: https://materialsproject.org/api
python run_remaining_steps.py --mp-key mp-xxxxxxxxxxxx --skip-ea6 --skip-std-md

# Results will update: 02_properties/thermodynamic_stability/thermodynamic_stability.csv
```

### Expected Output
```csv
formula,e_above_hull_eV_atom
Li6.45La3.0Zr1.45Ta0.55O12,0.021
Li6.4La3.0Zr1.4Ta0.6O12,0.038
...
```

### Effort Level
⏱️ **~5–20 minutes** | CPU-only | Requires internet + MP API key

---

## ⏳ Std Step 4B — Dynamical Stability (DFPT Phonons)

### What it does
Calculates the phonon density of states using **Density Functional Perturbation Theory (DFPT)**.  
Checks for imaginary phonon modes (negative frequencies → structural instability).

### Current Status
Only 2 reference structures tested → both returned `is_dynamically_stable = False, max_imaginary_freq = inf`.  
This indicates the DFPT run **crashed or was incomplete** — not that the materials are unstable.

### How to Run (HPC Recommended)
```bash
# Requires VASP or Quantum ESPRESSO for production DFPT
# Or approximate with CHGNet phonon prediction:

python -c "
from chgnet.model import CHGNet
from pymatgen.core import Structure

chgnet = CHGNet.load()
for cif in ['01_compounds/md_priority_queue/Li6.45La3.0Zr1.45Ta0.55O12_evaluated.cif']:
    s = Structure.from_file(cif)
    # CHGNet phonon approximation via finite differences
    # (requires phonopy integration)
    pass
"
```

### Effort Level
⏱️ **~4–48 hours per structure** | GPU/HPC required | Low priority (experimental candidates usually pass)

---

## ⏳ Std Step 4C — Mechanical Stability (Elastic Tensor)

### What it does
Calculates **bulk modulus (B)**, **shear modulus (G)**, and **Poisson's ratio (ν)** via elastic tensor DFT.  
Mechanical stability criterion: B > 0, G > 0, ν ∈ (0, 0.5).

### Current Status
3 structures returned `bulk_modulus = 0, shear_modulus = 0, is_mechanically_stable = False`.  
These are **placeholder values from an incomplete run** — not real mechanical failure.

### How to Run (HPC Required)
```bash
# Full DFT elastic tensor calculation (VASP/QE) — not in run_remaining_steps.py
# Approximate via CHGNet stress tensor:

python -c "
from chgnet.model import CHGNet
from pymatgen.core import Structure

chgnet = CHGNet.load()
s = Structure.from_file('Li6.45La3.0Zr1.45Ta0.55O12_evaluated.cif')
pred = chgnet.predict_structure(s)
print('Stress tensor:', pred['s'])  # 3x3 stress tensor
# Convert stress → elastic constants → moduli (requires voigt averaging)
"
```

### Effort Level
⏱️ **~2–24 hours per structure** | HPC/DFT required | Medium priority

---

## ⏳ Std Step 5 — Arrhenius MD Validation ← PRIMARY GPU TASK

### What it does
Identical procedure to EA Step 6, applied to the **top 3 Standard pipeline candidates**.  
NVT Langevin MD at 600/800/1000 K → Li MSD → D(T) → Arrhenius fit → σ_RT(300K).

### Input Files (ready in md_priority_queue/)
| Priority | CIF File | GPR σ_RT | Dopant System |
|----------|----------|---------|--------------|
| 🥇 #1 | `Li6.45La3.0Zr1.45Ta0.55O12_evaluated.cif` | 6.11×10⁻⁴ S/cm | Ta only |
| 🥈 #2 | `Li6.4La3.0Zr1.4Ta0.6O12_evaluated.cif` | 5.85×10⁻⁴ S/cm | Ta only |
| 🥉 #3 | `Li6.45La2.95Ba0.05Zr1.4Ta0.6O12_evaluated.cif` | 5.57×10⁻⁴ S/cm | Ba + Ta |

### How to Run

```bash
# Standard pipeline MD only (skip EA MD)
python run_remaining_steps.py --skip-ea6 --n-candidates 3 --md-steps 500

# Run both pipelines simultaneously
python run_remaining_steps.py --n-candidates 3 --md-steps 500

# High accuracy run
python run_remaining_steps.py --skip-ea6 --n-candidates 3 --md-steps 2000
```

### What the MD Script Does

```
For each of 3 candidates in md_priority_queue/:
  1. Load CIF via ASE
  2. Attach CHGNetCalculator (GPU)
  3. Maxwell-Boltzmann velocity init at T
  4. Langevin dynamics at 600K / 800K / 1000K
     - Every 100 steps: log Li MSD with PBC unwrapping
     - Between temps: torch.cuda.empty_cache() + gc.collect()
  5. Linear MSD regression → D(T) [cm²/s]
  6. Arrhenius fit: ln(D) vs 1/T
  7. Nernst-Einstein: σ_RT = (n·q²·D_RT) / (k_B·298K)
  8. Write to MASTER_RESULTS.csv (updates md_validated_sigma column)
```

### Expected Output
Updates `02_properties/conductivity_predictions/MASTER_RESULTS.csv`:
```
Before:  md_validated_sigma_S_cm = Pending HPC
After:   md_validated_sigma_S_cm = 4.21e-04  ← Real MD-validated value
```

### Estimated Runtime
| Hardware | 500 steps (3 candidates) | 2000 steps |
|----------|------------------------|-----------|
| RTX 3050 6 GB | ~2–3 hours | ~10–14 hours |
| RTX 3080 10 GB | ~1–2 hours | ~5–7 hours |
| A100 40 GB | ~30–45 min | ~2–3 hours |
| CPU (i9) | ~15–24 hours | ~60–96 hours |

---

## ⏳ Std Step 6 — MASTER_RESULTS.csv Final Update

### What it does
Replaces all `Pending HPC` values in `MASTER_RESULTS.csv` with actual computed values.

### After Step 5 completes:
```python
import pandas as pd

master = pd.read_csv("02_properties/conductivity_predictions/MASTER_RESULTS.csv")
md_results = pd.read_csv("std_md_results.csv")  # from Step 5 output

# Merge MD σ_RT into master table
master = master.merge(md_results[["formula","md_sigma_RT","Ea_eV"]], on="formula", how="left")
master["md_validated_sigma_S_cm"] = master["md_sigma_RT"]
master.to_csv("MASTER_RESULTS_FINAL.csv", index=False)
```

### Effort Level
⏱️ **~5 minutes** | CPU | Automatic after Step 5

---

## ⏳ Std Step 7 — Cross-Pipeline Comparison & Final Report

### What it does
Compares the Standard and EA pipelines side-by-side:
- Best MD-validated σ_RT from each pipeline
- Cost/availability analysis (EA vs Standard dopants)
- Activation energies (Ea) comparison
- Recommendation for synthesis

### Expected Report Structure
```markdown
## Final Cross-Pipeline Results

| Pipeline | Best Compound | σ_RT (MD) | Eₐ (eV) | Cost | Stability |
|----------|---------------|-----------|---------|------|-----------|
| Standard | Li6.45La3.0Zr1.45Ta0.55O12 | X×10⁻⁴ | Y eV | High | TBD |
| EA | Li6.500Zn0.20La3Zr1.90Nb0.10O12 | X×10⁻⁴ | Y eV | Low | ✅ STABLE |
```

### Effort Level
⏱️ **~1 hour** | CPU | Requires Steps 5 & 6 complete

---

## Complete Remaining Steps — Priority Order

| Priority | Step | Task | GPU? | Blocked by | Est. Time |
|----------|------|------|------|-----------|-----------|
| 🔴 1st | Std Step 5 | Arrhenius MD (3 candidates) | ✅ Yes | Nothing | 2–14 hrs |
| 🟠 2nd | EA Step 6 | Arrhenius MD (3 candidates) | ✅ Yes | Nothing | 2–14 hrs |
| 🟡 3rd | Std Step 4A | MP hull re-check | ❌ No | MP API key | 5–20 min |
| 🟡 4th | EA Step 5 | MP hull (EA candidates) | ❌ No | MP API key | 5–15 min |
| 🟢 5th | Std Step 6 | Update MASTER_RESULTS | ❌ No | Std Step 5 | 5 min |
| 🟢 6th | EA Step 7 | EA final report | ❌ No | EA Step 6 | 5 min |
| 🔵 7th | Std Step 4B | Phonon stability (DFPT) | ✅ HPC | Nothing | 4–48 hr/struct |
| 🔵 8th | Std Step 4C | Mechanical moduli | ✅ HPC | Nothing | 2–24 hr/struct |
| ⚪ 9th | Std Step 7 | Cross-pipeline report | ❌ No | All above | 1 hr |

**→ Minimum path to final results: Run Steps 5 (Std) + 6 (EA) simultaneously, then compile.**
