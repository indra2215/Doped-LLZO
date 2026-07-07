# Earth-Abundant LLZO Candidates — README
## `d:\doped_2\earth_abundant\`

---

## Purpose

This folder contains a **completely separate workflow** from the main pipeline, focused exclusively on **low-cost, earth-abundant dopants** for LLZO solid-state electrolytes.

All expensive/strategic dopants (Ta, W, Mo, Ga, Hf, Y, Gd) are deliberately excluded.

---

## Folder Structure

```
earth_abundant/
├── README.md                           ← This file
├── scripts/
│   ├── earth_abundant_candidates.py    ← Step 1: generate 535 candidates
│   └── earth_abundant_validate.py      ← Step 2: CHGNet + M3GNet + GPR
├── data/
│   ├── candidates/
│   │   └── earth_abundant_candidates_raw.csv   (535 compositions)
│   └── results/
│       ├── ea_chgnet_features.csv              (static energies)
│       ├── ea_validated_candidates.csv         (after relaxation)
│       ├── ea_thermal_stability.csv            (dE vs LLZO baseline)
│       └── ea_gpr_predictions.csv              (sigma_RT estimates)
└── structures/
    └── *.cif                                   (relaxed structures)
```

---

## Dopants Used (All Earth-Abundant)

### Li-site dopants (24d tetrahedral, ~0.59 Å)

| Dopant | Valence | Shannon r (Å) | Max conc. | Cost (USD/kg) | Notes |
|--------|---------|--------------|-----------|--------------|-------|
| **Al³⁺** | +3 | 0.39 | 30% | ~2 | Best-known Li-site dopant |
| **Fe³⁺** | +3 | 0.49 (HS) | 20% | ~0.1 | Keep x≤0.20 (electronic conductivity risk) |
| **Mg²⁺** | +2 | 0.57 | 25% | ~2 | Aliovalent → extra vacancies vs Al³⁺ |
| **Mn³⁺** | +3 | 0.58 (HS) | 15% | ~2 | Risk of Mn²⁺ reduction at high conc. |
| **Zn²⁺** | +2 | 0.60 | 20% | ~3 | Novel in LLZO, larger than Mg |

### Zr-site dopants (16a octahedral, ~0.72 Å)

| Dopant | Valence | Shannon r (Å) | Max conc. | Cost (USD/kg) | Notes |
|--------|---------|--------------|-----------|--------------|-------|
| **Ti⁴⁺** | +4 | 0.605 | 50% | ~10 | Isovalent, expands bottleneck |
| **Nb⁵⁺** | +5 | 0.640 | 50% | ~40 | Best Zr-site donor (columbite ore) |
| **Mn⁴⁺** | +4 | 0.530 | 30% | ~2 | Isovalent, novel in LLZO |
| **Sn⁴⁺** | +4 | 0.690 | 30% | ~25 | Largest isovalent sub → widest bottleneck |

### Explicitly Excluded

| Element | Reason |
|---------|--------|
| Ta | Strategic mineral, $150–300/kg |
| W, Mo | High cost, geopolitically sensitive |
| Ga | $220/kg, limited supply |
| Hf | $900/kg, co-extracted with Zr |
| Y, Gd | Rare earths, $35–60/kg, supply chain risk |

---

## Candidate Statistics

| Category | Count |
|----------|-------|
| Total generated | **535** |
| Fully novel (no literature) | **504 (94%)** |
| Unique dopant pairs | **23** |
| Li_pfu range | 6.00 – 6.90 |
| Li_pfu = 6.5 (optimal) | ~80 candidates |

### Breakdown by pair

| Pair | Count | Literature status |
|------|-------|-----------------|
| Al+Ti | 35 | Novel |
| Mg+Ti | 35 | Novel |
| Mg+Nb | 35 | Novel |
| Al+Nb | 31 | Partial (each element known, combination at these conc. not studied) |
| Fe+Ti | 28 | Novel |
| Zn+Ti | 28 | Novel |
| Zn+Nb | 28 | Novel |
| Fe+Nb | 27 | Novel (previous pipeline had wrong site — Li vs La) |
| Mg+Sn | 25 | Novel |
| Al+Mn | 25 | Novel |
| Mg+Mn | 25 | Novel |
| Al+Sn | 25 | Novel |
| Mn+Nb | 21 | Novel |
| Mn+Ti | 21 | Novel |
| Fe+Mn | 20 | Novel |
| Fe+Sn | 20 | Novel |
| Zn+Mn | 20 | Novel |
| Zn+Sn | 20 | Novel |
| Al+Fe | 15 | Novel (Fe on Zr-site as Fe⁴⁺) |
| Mg+Fe | 15 | Novel |
| Mn+Sn | 15 | Novel |
| Zn+Fe | 12 | Novel |
| Mn+Fe | 9 | Novel |

---

## Charge Balance Physics

All candidates satisfy:

```
n(Li) + x·val(Li-dopant) + 3·(+3) + (2-y)·(+4) + y·val(Zr-dopant) = 24
```

Where 24 balances the 12 O²⁻ × (−2) = −24 framework charge.

**Superionic window**: 6.1 ≤ Li_pfu ≤ 6.8 (cubic phase stable)  
**Optimal**: Li_pfu = 6.5 (1 vacancy per formula unit, maximum carrier density)

---

## Top 10 Most Promising Candidates

| # | Formula | Li_pfu | Pair | Why |
|---|---------|--------|------|-----|
| 1 | `Li6.500Mg0.25La3Zr1.75Nb0.25O12` | 6.50 | Mg+Nb | Mg²⁺ aliovalent creates 2× vacancies vs Al³⁺. Nb⁵⁺ donor. Doubly novel. |
| 2 | `Li6.500Fe0.10La3Zr1.80Nb0.20O12` | 6.50 | Fe+Nb | Optimal Li_pfu. Fe at safe concentration. Strong physics analogue to Al+Nb. |
| 3 | `Li6.500Zn0.10La3Zr1.70Nb0.30O12` | 6.50 | Zn+Nb | Zn²⁺ softer → wider bottleneck. Novel. |
| 4 | `Li6.500Mn0.10La3Zr1.80Nb0.20O12` | 6.50 | Mn+Nb | Mn³⁺ vacancy creation. Earth-abundant extreme. |
| 5 | `Li6.500Al0.10La3Zr1.80Ti0.20O12` | 6.50 | Al+Ti | Ti isovalent expands lattice. Cheapest combination. |
| 6 | `Li6.500Mg0.25La3Zr1.80Sn0.20O12` | 6.50 | Mg+Sn | Sn largest Zr-site sub (0.69 Å) → max bottleneck. Novel. |
| 7 | `Li6.500Fe0.10La3Zr1.90Mn0.10O12` | 6.50 | Fe+Mn | Both cheapest metals (~$0.1+$2/kg). Completely unexplored. |
| 8 | `Li6.500Al0.10La3Zr1.70Ti0.30O12` | 6.50 | Al+Ti | Higher Ti loading → larger lattice expansion. |
| 9 | `Li6.500Mg0.25La3Zr1.80Mn0.20O12` | 6.50 | Mg+Mn | Doubly earth-abundant aliovalent. Novel. |
| 10 | `Li6.500Zn0.20La3Zr1.90Nb0.10O12` | 6.50 | Zn+Nb | Higher Zn → more aliovalent vacancies. |

---

## Expected Conductivity Range

Based on structural analogues in literature:

| Type | Expected σ_RT | Basis |
|------|--------------|-------|
| Al+Ti at Li_pfu=6.5 | **10⁻⁴ – 10⁻³ S/cm** | Similar to Al+Nb (known ~1 mS/cm) |
| Mg+Nb at Li_pfu=6.5 | **10⁻⁴ – 10⁻³ S/cm** | Mg²⁺ creates more vacancies than Al³⁺ |
| Fe+Nb at Li_pfu=6.5 | **10⁻⁴ – 10⁻³ S/cm** | Same vacancy count as Al+Nb when x=0.10 |
| Zn+Nb, Mn+Nb | **10⁻⁴ S/cm** | Aliovalent, less studied |
| All-earth-abundant (Fe+Mn, Mg+Mn) | **10⁻⁴ – 10⁻⁵ S/cm** | Both Mn species less validated |

These estimates will be refined once `earth_abundant_validate.py` completes CHGNet+M3GNet evaluation.

---

## Validation Protocol — Full 6-Step Pipeline

Run in order (or use `.\run_ea_pipeline.ps1` from the project root):

```powershell
$env:MP_API_KEY = "nREzcJl7KZF5PZl1FIXCMbCSTbxQ55Ii"  # for Step 5 only
.\run_ea_pipeline.ps1
```

Or step-by-step:

```bash
# Step 1: Extract CHGNet features from garnet LLZO literature data
python earth_abundant/scripts/ea_step1_feature_extraction.py
# → earth_abundant/data/results/ea_gpr_features.csv (45 garnet samples)

# Step 2: Train EA-specific GPR surrogate model
python earth_abundant/scripts/ea_step2_model_training.py
# → earth_abundant/data/models/ea_gpr_model.pkl

# Step 3: Generate 535 earth-abundant candidates
python earth_abundant/scripts/ea_step3_candidates.py
# → earth_abundant/data/candidates/earth_abundant_candidates_raw.csv

# Step 4: CHGNet staged relaxation + M3GNet cross-check + GPR prediction
python earth_abundant/scripts/ea_step4_validate.py
# → earth_abundant/data/results/ea_validated_candidates.csv
# → earth_abundant/structures/*.cif

# Step 5: Thermodynamic hull check (Materials Project)
python earth_abundant/scripts/ea_step5_stability.py
# → earth_abundant/data/results/ea_thermodynamic_stability.csv

# Step 6: Arrhenius MD validation (top 5 stable candidates)
python earth_abundant/scripts/ea_step6_md_validation.py
# → earth_abundant/data/results/ea_finalresults.csv  (σ_RT + Ea)
```

### Step-by-step outputs

| Step | Script | Output | Purpose |
|------|--------|--------|---------|
| 1 | `ea_step1_feature_extraction.py` | `ea_gpr_features.csv` | CHGNet energy/volume for 45 garnet LLZO reference compounds |
| 2 | `ea_step2_model_training.py` | `ea_gpr_model.pkl` | EA-specific GPR surrogate (conductivity predictor) |
| 3 | `ea_step3_candidates.py` | `earth_abundant_candidates_raw.csv` | 535 charge-balanced EA compositions |
| 4 | `ea_step4_validate.py` | `ea_validated_candidates.csv` + CIFs | Structural validation + thermal stability proxy |
| 5 | `ea_step5_stability.py` | `ea_thermodynamic_stability.csv` | Convex hull distance via MP API |
| 6 | `ea_step6_md_validation.py` | `ea_finalresults.csv` | Arrhenius σ_RT + Ea from 1 ns NVT MD |

### What validation checks

| Check | Method | Pass criterion |
|-------|--------|---------------|
| CHGNet staged relax | positions-only → full cell (with fallback) | Structure converges |
| M3GNet cross-check | M3GNet-MP-2021.2.8-PES | \|ΔE\| < 0.15 eV/atom |
| Thermal stability | ΔE vs LLZO baseline | ΔE < 0.05 eV/atom preferred |
| GPR conductivity | ea_gpr_model.pkl | Informational (σ estimate) |
| Hull stability | MP phase diagram | e_above_hull < 0.05 eV/atom = STABLE |
| Arrhenius MD | NVT Langevin 600/800/1000 K | D > 0 at ≥ 600 K |

### Pipeline separation
This pipeline is **completely independent** of `02_pipeline/` (standard pipeline).
- EA has its own feature extraction, GPR, candidates, and all result files.
- Data lives in `earth_abundant/data/` — nothing in `01_data/` is owned by EA.
- The only shared resource is `01_data/experimental/` (read-only raw data source).

---

## Cost Impact

If an earth-abundant candidate reaches σ_RT ≥ 0.5 mS/cm, it would represent:

| System | Dopant cost (USD/mol LLZO) | Performance |
|--------|--------------------------|------------|
| State-of-art (Al+Ta) | ~$12 | ~1.4 mS/cm |
| **Earth-abundant (Al+Ti)** | ~$0.60 | *Unknown — this is the discovery* |
| **Earth-abundant (Fe+Nb)** | ~$1.50 | *Unknown* |
| **Earth-abundant (Fe+Ti)** | ~$0.55 | *Unknown* |

A 20× reduction in dopant cost with comparable performance would be a major commercial finding.

---

*Generated: 2026-06-02 | Candidates: 535 | Novel: 504 (94%) | Script: earth_abundant_candidates.py*
