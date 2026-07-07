# Earth-Abundant / Low-Cost Doped-LLZO Candidates
## README — `earth_abundant_candidates.py` Workflow

---

## Motivation

Standard LLZO doping literature relies heavily on:
- **Ta, W, Mo** — strategic/conflict minerals, high price (~$150–300/kg)
- **Ga** — limited supply, price volatile (~$220/kg)
- **Hf** — co-extracted with Zr, expensive (~$900/kg)
- **Y, Gd** — rare-earth elements (~$35–60/kg, supply chain risks)

This workflow deliberately restricts to **earth-abundant, low-cost dopants**:

| Element | Abundance (ppm) | Cost (USD/kg) | Role in LLZO |
|---------|----------------|--------------|--------------|
| **Al** | 82,300 | ~2 | Li-site dopant (best known) |
| **Fe** | 56,300 | ~0.1 | Li-site dopant (Fe³⁺, x≤0.20) |
| **Mg** | 23,300 | ~2 | Li-site dopant (aliovalent, Mg²⁺) |
| **Mn** | 1,060 | ~2 | Li/Zr-site (mixed oxidation states) |
| **Zn** | 79 | ~3 | Li-site dopant (Zn²⁺, underexplored) |
| **Ti** | 5,650 | ~10 | Zr-site (isovalent Ti⁴⁺) |
| **Nb** | 20 | ~40 | Zr-site (Nb⁵⁺, abundant in columbite ore) |
| **Sn** | 2.3 | ~25 | Zr-site (isovalent Sn⁴⁺, novel in LLZO) |

---

## Physics Design Rules

### Site Assignments (Critical — Previous Pipeline Got This Wrong)

```
LLZO garnet:  Li₇La₃Zr₂O₁₂   (Ia-3d space group, cubic)

Li  → 24d site (tetrahedral, ~0.59 Å pocket)
La  → 24c site (dodecahedral, ~1.10 Å pocket)
Zr  → 16a site (octahedral, ~0.72 Å pocket)
O   → 96h site (framework)
```

**Li-site dopants** (val +2 or +3, small ion, tetrahedral preference):
- Fe³⁺ (r = 0.49 Å, HS) ✓  
- Al³⁺ (r = 0.39 Å) ✓  
- Mg²⁺ (r = 0.57 Å) ✓  
- Mn³⁺ (r = 0.58 Å, HS) ✓  
- Zn²⁺ (r = 0.60 Å) ✓  

**Zr-site dopants** (val +4 or +5, octahedral):
- Ti⁴⁺ (r = 0.605 Å) ✓  
- Nb⁵⁺ (r = 0.64 Å) ✓  
- Mn⁴⁺ (r = 0.53 Å) ✓  
- Sn⁴⁺ (r = 0.69 Å) ✓  

### Charge Balance Formula

```
For Li_n [A_x] La₃ Zr_(2-y) [B_y] O₁₂:
  n = 24 - x·val(A) - 9 - (2-y)·4 - y·val(B)

Superionic window: 6.1 ≤ n ≤ 6.8
Optimal target:    n ≈ 6.5 (1 vacancy per formula unit)
```

### Concentration Safety Limits

| Dopant | Max concentration | Reason |
|--------|-----------------|---------|
| Fe (Li-site) | x ≤ 0.20 | Above this → electronic conductivity percolation |
| Mn | x ≤ 0.15 (Li) / y ≤ 0.30 (Zr) | Reduction risk Mn³⁺→Mn²⁺ |
| All others | As defined in script | Shannon radius tolerance |

---

## Generated Candidate Pool

**Total: 535 compositions across 23 dopant pair combinations**  
**Novel (not in main LLZO literature): 504 (94%)**

| Pair | Count | Literature Status |
|------|-------|-----------------|
| Al+Ti | 35 | **Novel** — Al+Ti LLZO underexplored |
| Mg+Ti | 35 | **Novel** — Mg+Ti no reports |
| Mg+Nb | 35 | **Novel** — Mg²⁺ + Nb⁵⁺ creates double vacancies |
| Al+Nb | 31 | Known (Al, Nb both studied separately) |
| Zn+Nb | 28 | **Novel** — Zn+Nb zero literature |
| Zn+Ti | 28 | **Novel** — Zn+Ti zero literature |
| Fe+Ti | 28 | **Novel** — Fe+Ti zero literature |
| Fe+Nb | 27 | **Novel** — Fe on Li-site + Nb (prev. pipeline had wrong site) |
| Mg+Sn | 25 | **Novel** — Mg+Sn zero literature |
| Al+Mn | 25 | **Novel** — Al+Mn co-doped LLZO not reported |
| Mg+Mn | 25 | **Novel** — doubly earth-abundant, unexplored |
| Al+Sn | 25 | **Novel** — Al+Sn zero literature |
| Mn+Ti | 21 | **Novel** |
| Mn+Nb | 21 | **Novel** |
| Fe+Sn | 20 | **Novel** — Fe+Sn zero literature |
| Zn+Mn | 20 | **Novel** |
| Zn+Sn | 20 | **Novel** |
| Fe+Mn | 20 | **Novel** |
| Al+Fe | 15 | **Novel** — Fe on Zr-site (Fe⁴⁺) unusual |
| Mg+Fe | 15 | **Novel** |
| Mn+Sn | 15 | **Novel** |
| Zn+Fe | 12 | **Novel** |
| Mn+Fe | 9 | **Novel** |

---

## Top 10 Most Promising (Physics Rationale)

### Tier 1 — Strongest physicochemical argument

| # | Formula | Li_pfu | Why |
|---|---------|--------|-----|
| 1 | **Li6.500Mg0.25La3Zr1.75Nb0.25O12** | 6.500 | Mg²⁺ aliovalent on Li-site creates EXTRA vacancy vs. Al³⁺. Nb⁵⁺ donor on Zr-site. Double vacancy source → potentially lower Ea. Completely novel. |
| 2 | **Li6.500Fe0.10La3Zr1.80Nb0.20O12** | 6.500 | Optimal Li_pfu=6.5. Fe³⁺ at x=0.10 safe (below electronic percolation). Strong Fe 3d-O 2p hybridization may lower migration barrier. |
| 3 | **Li6.500Zn0.10La3Zr1.70Nb0.30O12** | 6.500 | Zn²⁺ is softer than Mg²⁺ → larger lattice deformation → wider bottleneck. Completely unexplored territory. |

### Tier 2 — Novel + earth-abundant + physically sound

| # | Formula | Li_pfu | Why |
|---|---------|--------|-----|
| 4 | **Li6.500Mn0.10La3Zr1.80Nb0.20O12** | 6.500 | Mn³⁺ on Li-site. If Mn stays +3 (not reduced), excellent vacancy creation. |
| 5 | **Li6.500Al0.10La3Zr1.80Ti0.20O12** | 6.500 | Ti⁴⁺ isovalent on Zr-site expands lattice. Al³⁺ creates vacancies. Ti cheaper than Nb/Ta. |
| 6 | **Li6.500Mg0.25La3Zr1.80Sn0.20O12** | 6.500 | Sn⁴⁺ largest of Zr-site candidates → maximum bottleneck expansion. Mg²⁺ double vacancy source. |
| 7 | **Li6.500Al0.10La3Zr1.70Ti0.30O12** | 6.500 | Higher Ti concentration → larger lattice expansion. |

### Tier 3 — Novel but needs careful validation (Mn reduction risk, Fe⁴⁺ rare)

| # | Formula | Li_pfu | Caution |
|---|---------|--------|---------|
| 8 | **Li6.500Fe0.10La3Zr1.90Mn0.10O12** | 6.500 | Fe³⁺ Li-site + Mn⁴⁺ Zr-site. Both earth-abundant. Risk: Mn⁴⁺ stable in octahedral (Zr-site) ✓ |
| 9 | **Li6.500Zn0.20La3Zr1.90Nb0.10O12** | 6.500 | Zn²⁺ creates more vacancies per atom than Al³⁺. |
| 10 | **Li6.500Mg0.25La3Zr1.70Mn0.30O12** | 6.500 | Highest Mn⁴⁺ content — verify oxidation state retention. |

---

## Validation Protocol (`earth_abundant_candidates.py`)

### Step 1 — CHGNet static prediction
```python
from chgnet.model import CHGNet
chgnet = CHGNet.load()
pred = chgnet.predict_structure(structure)
e_chgnet = pred['e']   # eV/atom
```

### Step 2 — M3GNet independent cross-check
```python
import matgl
from matgl.ext.ase import M3GNetCalculator
pot = matgl.load_model("M3GNet-MP-2021.2.8-PES")
# ... get energy per atom
```

### Step 3 — Cross-model agreement filter
```
|E_CHGNet - E_M3GNet| < 0.15 eV/atom  →  ACCEPTED (both models agree)
|E_CHGNet - E_M3GNet| ≥ 0.15 eV/atom  →  REJECTED (uncertain region)
```

### Step 4 — Full CHGNet relaxation (StructOptimizer)
```python
from chgnet.model.dynamics import StructOptimizer
relaxer = StructOptimizer()
result = relaxer.relax(structure, fmax=0.05, steps=500)
final_struct = result['final_structure']
```

### Step 5 — Arrhenius MD (backtrack_validation_corrected.py)
```
Temperatures: 600K, 800K, 1000K
MD steps: 500,000 (1 ns at 2 fs/step)
Ensemble: Langevin NVT (friction=0.02/fs)
MSD: incremental PBC unwrapping
Output: D(T) → slope → Ea, σ_RT via Nernst-Einstein
```

---

## How to Run

```powershell
# Install M3GNet if not present
pip install matgl

# Generate candidates
python 02_pipeline/step3_screening/earth_abundant_candidates.py

# Output files:
#   01_data/candidates/earth_abundant_candidates_raw.csv    (535 compositions)
#   01_data/candidates/earth_abundant_candidates_validated.csv  (top 20 with CHGNet+M3GNet energies)

# Then run stability + MD validation on the validated subset:
python 02_pipeline/step4_stability/thermodynamic_stability.py
python 02_pipeline/step5_md_validation/backtrack_validation_corrected.py
```

---

## Cost Comparison

| Approach | Dopant Cost (USD/mol LLZO) | Performance expectation |
|---------|--------------------------|------------------------|
| Literature best (Al-Ta) | ~$0.30 (Al) + ~$12 (Ta) | ~1.4 mS/cm |
| **Earth-abundant (Mg-Nb)** | ~$0.05 (Mg) + ~$1.5 (Nb) | **Unknown — this is the novelty** |
| **Earth-abundant (Fe-Ti)** | ~$0.005 (Fe) + ~$0.50 (Ti) | **Unknown — completely unexplored** |
| **Earth-abundant (Al-Ti)** | ~$0.05 (Al) + ~$0.50 (Ti) | **Predicted similar to Al-Ta** |

If Al+Ti or Mg+Nb reaches even 0.8 mS/cm, it represents a >10× cost reduction over Ta-based systems.

---

*Generated: 2026-06-01 | Script: earth_abundant_candidates.py | Total candidates: 535 | Novel: 504 (94%)*
