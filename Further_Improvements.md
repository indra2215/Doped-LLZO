# Further Improvements & Pending Tasks

## 1. Compute-Limited Stages — What Needs HPC

The following pipeline stages cannot complete reliably on a local consumer machine.
Below are explicit hardware requirements, runtime estimates, and the fallback behaviour
each script uses when it fails locally.

---

### Step 3c — CHGNet Staged Relaxation (`evaluate_candidates_chgnet.py`)

| | Detail |
|---|---|
| **Why it needs compute** | 50 CHGNet geometry optimisations, each running autograd force calls on a 160-atom garnet supercell |
| **Minimum viable** | 16 GB RAM, any NVIDIA GPU (GTX 1070+) |
| **Recommended** | 32 GB RAM, RTX 3080+ or A100 |
| **Runtime estimate** | ~30–60 min/50 candidates on RTX 3080; 3–6 h on CPU-only |
| **Current steps setting** | `steps=10/5, fmax=0.5` (too loose — causes cell collapse on some structures) |
| **Recommended fix** | `steps=50/25, fmax=0.1` — re-run to fix corrupted geometries before MD |
| **Fallback on failure** | Falls back to static CHGNet predict (no relaxation); records `relax_mode='static'` |
| **Known issue** | Several output CIFs have `vol/atom > 16 Å³` (garnet valid: 10–14 Å³). These must be re-relaxed. |

---

### Step 4b — Dynamical Stability (`dynamical_stability.py`)

| | Detail |
|---|---|
| **Why it needs compute** | Phonopy force constants via CHGNet require gradient tracking across ~50+ displaced supercell images per candidate; each displacement runs a full autograd pass |
| **Minimum viable** | 32 GB RAM; local runs crash with `A realloc of memory failed!` at 16 GB |
| **Recommended** | HPC node with 64–128 GB RAM; Phonopy is CPU-parallel |
| **Runtime estimate** | ~15 min/candidate locally (often crashes); ~2–5 min on HPC 16-core node |
| **Fallback on failure** | Bare `except Exception` writes `is_dynamically_stable=False, max_imaginary_freq_THz=inf` — sentinel values, NOT real data |
| **Fix needed** | Log the real exception message before the fallback write. Currently the error is swallowed. |

---

### Step 4c — Mechanical Stability (`mechanical_stability.py`)

| | Detail |
|---|---|
| **Why it needs compute** | Finite-difference elastic tensor: 6 strain directions × 2 displacements × CHGNet stress call per deformed cell |
| **Minimum viable** | 16 GB RAM, GPU recommended |
| **Recommended** | Same as 4b |
| **Runtime estimate** | ~10–20 min/candidate locally |
| **Fallback on failure** | Bare `except Exception` writes `bulk=0, shear=0, poisson=0, is_mechanically_stable=False` — sentinel values |
| **Fix needed** | Same as 4b: log the actual error before writing the fallback row |

---

### Step 5 — MD Arrhenius Validation (`backtrack_validation_corrected.py`)

| | Detail |
|---|---|
| **Why it needs compute** | NVT Langevin MD at 600/800/1000 K; each temperature run requires tracking Li displacements over thousands of steps with gradient-enabled CHGNet forces |
| **FAST_MODE=True** | 1,000 steps (~2 ps) — suitable for testing script runs only; too short for the diffusive regime |
| **FAST_MODE=False** | 25,000 steps (~50 ps) — minimum meaningful Arrhenius fit; ~15–30 min/candidate/temperature on GPU |
| **Recommended production** | 50,000+ steps (100+ ps) at all three temperatures |
| **Minimum viable** | 16 GB RAM + NVIDIA GPU (runs but slow) |
| **Recommended** | A100 or H100 GPU, 32 GB VRAM |
| **Pre-requisite** | All CIF inputs must pass geometry check: `vol/atom ∈ 10–16 Å³`. Script now rejects corrupted structures automatically. |
| **Conductivity gate** | `σ_RT > 0.1 S/cm` is auto-flagged as `FAILED_MELT` — physically impossible for solid electrolytes. |

---

## 2. Streaming Fixes Required Before Next Compute Run

1. **Fix geometry failures in Step 3c**: Re-run `evaluate_candidates_chgnet.py` with `steps=50/25, fmax=0.1` for the ~8 structures with `vol/atom > 16 Å³`.
2. **Add error logging to Step 4b and 4c**: Replace bare `except Exception as e: return sentinel` with `print(f"EXCEPTION: {e}")` before the fallback write, so the real cause is visible.
3. **Set MP_API_KEY**: Required for Steps 4a (standard) and 5 (EA). Without it, thermodynamic hull calculations are skipped.

---

## 3. Candidate Count Terminology Clarification

| Term | Count | Source |
|------|-------|--------|
| Permutation candidates (legacy track) | 150 | `02_pipeline/archive_12/generate_novel_candidates_FIXED.py` → `permutation_candidates.csv` |
| Virtual library (active track) | 14,474 | `02_pipeline/step3_screening/generate_candidates.py` → `bayesian_virtual_candidates.csv` |
| Top screened (active track) | 50 | `compositional_screening.py` → `top_50_screened_candidates.csv` |
| CHGNet-evaluated (active track) | 36 | `evaluate_candidates_chgnet.py` → `evaluated_top_candidates.csv` |
| EA candidates generated | 535 | `ea_step3_candidates.py` |
| EA candidates validated | 5 | `ea_step4_validate.py` → `ea_validated_candidates.csv` |

The "~150 candidates" figure referenced in some docs refers to the older permutation-based track. The active pipeline uses the 14,474-entry virtual library screened down to 50, then evaluated with CHGNet.

---

## 4. Future Work: Completing the Pipeline

### Priority 1 (unblocks everything)
- Re-run Step 3c with tighter relaxation to fix corrupted geometries
- Run Step 5 MD on fixed structures (FAST_MODE=False, GPU required)

### Priority 2 (parallel with above)
- Set MP_API_KEY and run Step 4a thermodynamic stability
- Debug exception sources in Steps 4b/4c (print real error before sentinel fallback)

### Priority 3 (HPC)
- Run Steps 4b/4c on HPC for full 36-candidate batch
- Run Step 6 EA MD validation once EA geometry is also verified

### Future enhancements
- Expand EA pipeline with Ti-only Zr-site substitution (currently excluded due to charge balance complexity)
- Add Bayesian optimisation loop: use MD results to re-rank and re-screen the virtual library
- Add Arrhenius plot generation to the MD validation output
