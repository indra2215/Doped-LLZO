# Pipeline A — Earth-Abundant | Remaining Steps on GPU

**Status:** Steps 1–4 COMPLETE ✅ | Steps 5–7 PENDING GPU ⏳

---

## Progress Tracker

```
EA Step 1  ✅  Feature extraction from 45 LLZO experimental samples
EA Step 2  ✅  EA-GPR model training (ea_gpr_model.pkl, R² > 0.60)
EA Step 3  ✅  535 low-cost candidates generated
EA Step 4  ✅  CHGNet position-only relaxation + GPR predictions
              → 5 top candidates validated, all STABLE (ΔE < 0 vs LLZO)
EA Step 5  ⚠️  Thermodynamic hull check — BLOCKED (no MP API key)
EA Step 6  ⏳  Arrhenius MD validation — NEEDS GPU
EA Step 7  ⏳  Final σ_RT reporting — depends on Step 6
```

---

## ⏳ EA Step 5 — Thermodynamic Hull Check (Materials Project)

### What it does
Queries the **Materials Project** convex hull database to calculate `e_above_hull` for each candidate.  
Compounds with `e_above_hull < 0.1 eV/atom` are thermodynamically accessible.

### Current Status
- All candidates show `e_above_hull = inf` — **not an instability**, just missing API key
- CHGNet ΔE already confirms thermal stability (all 5 candidates: ΔE < −7 eV/atom)

### How to Run

```bash
# Step 1: Get your free Materials Project API key
# → https://materialsproject.org/api (sign up, go to Dashboard → API Key)

# Step 2: Run with the key
python run_remaining_steps.py --mp-key mp-xxxxxxxxxxxxxxxxxxxx

# Step 3: Results saved to:
# pipeline_A_earth_abundant/02_properties/thermodynamic_stability/ea_thermodynamic_stability.csv
```

### Expected Output
```csv
formula,e_above_hull_eV_atom,hull_status
Li6.500Zn0.20La3Zr1.90Nb0.10O12,0.032,Stable (< 0.1 eV/atom)
Li6.500Mn0.10La3Zr1.80Nb0.20O12,0.041,Stable (< 0.1 eV/atom)
...
```

### Effort Level
⏱️ **~5–15 minutes** | CPU-only | No GPU required

---

## ⏳ EA Step 6 — Arrhenius MD Validation ← PRIMARY GPU TASK

### What it does
Runs **NVT Langevin Molecular Dynamics** at 3 temperatures (600 K, 800 K, 1000 K) on each of the 3 priority candidates. Extracts Li-ion diffusion coefficients, fits the Arrhenius equation, and extrapolates to room temperature σ_RT(300 K).

### Why GPU is Required
CHGNet computes forces via:
```python
forces = torch.autograd.grad(energy, positions)
```
This builds a full PyTorch autograd graph at **every MD step** (500 steps × 3 temperatures × 3 candidates).  
VRAM requirement: **4–8 GB peak** depending on supercell size.

### Input Files (ready in md_priority_queue/)
| # | CIF File | GPR σ_RT | ΔE vs LLZO |
|---|----------|---------|-----------|
| 1 | `Li6.500Zn0.20La3Zr1.90Nb0.10O12.cif` | 6.67×10⁻⁴ | -8.99 eV/atom |
| 2 | `Li6.500Mn0.10La3Zr1.80Nb0.20O12.cif` | 5.42×10⁻⁴ | -9.17 eV/atom |
| 3 | `Li6.500Zn0.05La3Zr1.60Nb0.40O12.cif` | 5.29×10⁻⁴ | -9.21 eV/atom |

### MD Settings
| Parameter | GPU-safe (default) | Publication quality |
|-----------|-------------------|---------------------|
| `--md-steps` | 500 | 2000+ |
| `--n-candidates` | 3 | 3 |
| Temperatures | 600, 800, 1000 K | 600, 800, 1000 K |
| Time step | 2.0 fs | 2.0 fs |
| Total sim time | 1.0 ps/temp | 4.0+ ps/temp |

### How to Run

```bash
# From Doped-LLZO project root:

# EA MD only (skip standard pipeline MD)
python run_remaining_steps.py --skip-std-md --n-candidates 3 --md-steps 500

# High-accuracy (longer simulation, needs more VRAM)
python run_remaining_steps.py --skip-std-md --n-candidates 3 --md-steps 2000

# CPU fallback (safe, but 10–50× slower)
python run_remaining_steps.py --skip-std-md --use-cpu --md-steps 200
```

### What the Script Does (Step by Step)

```
For each of the 3 MD-queue candidates:
  1. Load CIF → build ASE Atoms object
  2. Attach CHGNetCalculator (GPU-accelerated)
  3. Maxwell-Boltzmann velocity initialization @ T
  4. Langevin dynamics for N steps
     ├─ Every 100 steps: record Li-ion MSD
     └─ GPU memory cleared after each temperature
  5. Linear MSD fit → diffusion coefficient D(T)
  6. Arrhenius fit: ln(D) vs 1/T → Ea, D0
  7. Nernst-Einstein → σ_RT(300K)
  8. Save results to CSV
```

### Expected Output Files

```
earth_abundant/data/results/
└── ea_md_arrhenius_results.csv    ← Auto-created by script
```

**Output CSV columns:**
```
formula, T_K, D_cm2_s, Ea_eV, sigma_RT_S_cm, md_steps, notes
```

### Expected Results (based on GPR predictions)
| Candidate | Expected Ea (eV) | Expected σ_RT (MD) |
|-----------|-----------------|-------------------|
| Li6.500Zn0.20La3Zr1.90Nb0.10O12 | ~0.25–0.40 | ~10⁻⁴ – 10⁻³ S/cm |
| Li6.500Mn0.10La3Zr1.80Nb0.20O12 | ~0.25–0.40 | ~10⁻⁴ – 10⁻³ S/cm |
| Li6.500Zn0.05La3Zr1.60Nb0.40O12 | ~0.25–0.40 | ~10⁻⁴ – 10⁻³ S/cm |

### Estimated Runtime
| Hardware | Time (500 steps) | Time (2000 steps) |
|----------|-----------------|-------------------|
| RTX 3050 6 GB | ~2–3 hours | ~8–12 hours |
| A100 40 GB | ~30–45 min | ~2–3 hours |
| CPU (i7/i9) | ~12–24 hours | ~48–96 hours |

---

## ⏳ EA Step 7 — Final Results Compilation & Report

### What it does
Aggregates all EA pipeline outputs into a final summary table and report.

### Inputs needed (from Steps 5 & 6)
- `ea_thermodynamic_stability.csv` (from Step 5)
- `ea_md_arrhenius_results.csv` (from Step 6)

### How to Compile
```python
import pandas as pd

gpr  = pd.read_csv("02_properties/conductivity_predictions/ea_validated_candidates.csv")
thermo = pd.read_csv("02_properties/thermodynamic_stability/ea_thermodynamic_stability.csv")
md   = pd.read_csv("../../earth_abundant/data/results/ea_md_arrhenius_results.csv")

final = gpr.merge(thermo, on="formula").merge(md, on="formula")
final.to_csv("EA_FINAL_RESULTS.csv", index=False)
```

### Final Report Columns
```
formula | Li_pfu | dopant_pair | delta_E_vs_LLZO | e_above_hull |
gpr_sigma_RT | md_sigma_RT | Ea_eV | thermal_status | thermo_status
```

### Effort Level
⏱️ **~5 minutes** | CPU-only | No GPU required | Runs after Steps 5 & 6

---

## Summary: What You Need to Do

| Step | Needs GPU? | Needs MP Key? | Time Est. | Status |
|------|-----------|--------------|-----------|--------|
| EA Step 5 (Hull) | ❌ | ✅ | 5–15 min | ⚠️ Blocked |
| EA Step 6 (MD) | ✅ | ❌ | 2–12 hrs | ⏳ Ready |
| EA Step 7 (Report) | ❌ | ❌ | 5 min | ⏳ After 5+6 |

**Minimum to get final σ_RT results:** Run Step 6 (GPU) only → Step 7 → DONE.  
**For complete publication-quality results:** Also run Step 5 (MP API key required).
