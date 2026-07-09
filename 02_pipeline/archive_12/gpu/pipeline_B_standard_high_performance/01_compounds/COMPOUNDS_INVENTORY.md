# Pipeline B — Standard | Compounds Inventory

**Pipeline:** B — Standard High-Performance  
**Constraint:** No element restrictions — maximizes predicted ionic conductivity  
**Total CIF Structures:** 41 (CHGNet fully relaxed via `staged_relax`)

---

## 📁 all_cif_structures/ — Complete Library (41 CIFs)

All structures generated from the Bayesian virtual candidate set (14,474 → top 50 → 41 successfully relaxed).  
Garnet framework: **Li_x A_y La_(3-y) Zr_(2-z) D_z O₁₂**  
Where A = La-site dopant (Ba, Ca, Gd, Ga), D = Zr-site dopant (Ta).

---

### Dopant Group 1: Ta only (Zr-site) — Highest Performance

No A-site co-dopant. Simplest chemistry, best predicted conductivity.

| Filename | Li pfu | Ta conc. | GPR σ_RT | Rank |
|----------|--------|----------|----------|------|
| `Li6.45La3.0Zr1.45Ta0.55O12_evaluated.cif` ⭐ | 6.45 | 0.55 | **6.11×10⁻⁴** | #1 |
| `Li6.4La3.0Zr1.4Ta0.6O12_evaluated.cif` ⭐ | 6.40 | 0.60 | **5.85×10⁻⁴** | #2 |
| `Li6.35La3.0Zr1.35Ta0.65O12_evaluated.cif` | 6.35 | 0.65 | 4.97×10⁻⁴ | #7 |

---

### Dopant Group 2: Ba + Ta (A-site Ba, Zr-site Ta)

| Filename | Li pfu | Ba conc. | Ta conc. | GPR σ_RT | Rank |
|----------|--------|----------|----------|----------|------|
| `Li6.45La2.95Ba0.05Zr1.4Ta0.6O12_evaluated.cif` ⭐ | 6.45 | 0.05 | 0.60 | **5.57×10⁻⁴** | #3 |
| `Li6.45La2.9Ba0.1Zr1.35Ta0.65O12_evaluated.cif` | 6.45 | 0.10 | 0.65 | 5.53×10⁻⁴ | #4 |
| `Li6.4La2.95Ba0.05Zr1.35Ta0.65O12_evaluated.cif` | 6.40 | 0.05 | 0.65 | 4.97×10⁻⁴ | #8 |
| `Li6.4Ga0.05La2.9Ba0.1Zr1.45Ta0.55O12_evaluated.cif` | 6.40 | 0.10 | 0.55 (+Ga) | 1.44×10⁻⁴ | #27 |
| `Li6.35Ga0.05La2.95Ba0.05Zr1.45Ta0.55O12_evaluated.cif` | 6.35 | 0.05 | 0.55 (+Ga) | 1.34×10⁻⁴ | #32 |

---

### Dopant Group 3: Ca + Ta (A-site Ca, Zr-site Ta)

| Filename | Li pfu | Ca conc. | Ta conc. | GPR σ_RT | Rank |
|----------|--------|----------|----------|----------|------|
| `Li6.45La2.95Ca0.05Zr1.4Ta0.6O12_evaluated.cif` | 6.45 | 0.05 | 0.60 | 5.33×10⁻⁴ | #5 |
| `Li6.45La2.9Ca0.1Zr1.35Ta0.65O12_evaluated.cif` | 6.45 | 0.10 | 0.65 | 5.06×10⁻⁴ | #6 |
| `Li6.4La2.95Ca0.05Zr1.35Ta0.65O12_evaluated.cif` | 6.40 | 0.05 | 0.65 | 4.78×10⁻⁴ | #10 |

---

### Dopant Group 4: Gd + Ta (A-site Gd, Zr-site Ta)

| Filename | Li pfu | Gd conc. | Ta conc. | GPR σ_RT | Rank |
|----------|--------|----------|----------|----------|------|
| `Li6.4La2.95Gd0.05Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.05 | 0.60 | 4.83×10⁻⁴ | #9 |
| `Li6.4La2.9Gd0.1Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.10 | 0.60 | 4.65×10⁻⁴ | #11 |
| `Li6.4La2.85Gd0.15Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.15 | 0.60 | 4.46×10⁻⁴ | #12 |
| `Li6.4La2.8Gd0.2Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.20 | 0.60 | 4.28×10⁻⁴ | #13 |
| `Li6.4La2.75Gd0.25Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.25 | 0.60 | 4.09×10⁻⁴ | #14 |
| `Li6.35La2.95Gd0.05Zr1.35Ta0.65O12_evaluated.cif` | 6.35 | 0.05 | 0.65 | 3.99×10⁻⁴ | #15 |
| `Li6.4La2.7Gd0.3Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.30 | 0.60 | 3.91×10⁻⁴ | #16 |
| `Li6.4La2.65Gd0.35Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.35 | 0.60 | 3.73×10⁻⁴ | #17 |
| `Li6.4La2.6Gd0.4Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.40 | 0.60 | 3.55×10⁻⁴ | #18 |
| `Li6.4La2.55Gd0.45Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.45 | 0.60 | 3.38×10⁻⁴ | #19 |

---

### Dopant Group 5: Ga + Ba/Ca + Ta (Triple dopant)

| Filename | Li pfu | Ga | A-site | Ta | GPR σ_RT | Rank |
|----------|--------|----|--------|----|----------|------|
| `Li6.4Ga0.1La2.7Ba0.3Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.10 | Ba 0.30 | 0.60 | 1.54×10⁻⁴ | #20 |
| `Li6.45Ga0.05La2.8Ba0.2Zr1.4Ta0.6O12_evaluated.cif` | 6.45 | 0.05 | Ba 0.20 | 0.60 | 1.49×10⁻⁴ | #21 |
| `Li6.35Ga0.1La2.75Ba0.25Zr1.4Ta0.6O12_evaluated.cif` | 6.35 | 0.10 | Ba 0.25 | 0.60 | 1.46×10⁻⁴ | #22 |
| `Li6.35Ga0.15La2.6Ca0.4Zr1.4Ta0.6O12_evaluated.cif` | 6.35 | 0.15 | Ca 0.40 | 0.60 | 1.46×10⁻⁴ | #23 |
| `Li6.4Ga0.1La2.7Ca0.3Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.10 | Ca 0.30 | 0.60 | 1.45×10⁻⁴ | #24 |
| `Li6.45Ga0.1La2.65Ca0.35Zr1.4Ta0.6O12_evaluated.cif` | 6.45 | 0.10 | Ca 0.35 | 0.60 | 1.45×10⁻⁴ | #25 |
| `Li6.4Ga0.15La2.55Ca0.45Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.15 | Ca 0.45 | 0.60 | 1.45×10⁻⁴ | #26 |
| `Li6.45Ga0.05La2.8Ca0.2Zr1.4Ta0.6O12_evaluated.cif` | 6.45 | 0.05 | Ca 0.20 | 0.60 | 1.42×10⁻⁴ | #28 |
| `Li6.35Ga0.1La2.75Ca0.25Zr1.4Ta0.6O12_evaluated.cif` | 6.35 | 0.10 | Ca 0.25 | 0.60 | 1.41×10⁻⁴ | #29 |
| `Li6.4Ga0.05La2.85Ba0.15Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.05 | Ba 0.15 | 0.60 | 1.41×10⁻⁴ | #30 |
| `Li6.4Ga0.05La2.85Ca0.15Zr1.4Ta0.6O12_evaluated.cif` | 6.40 | 0.05 | Ca 0.15 | 0.60 | 1.38×10⁻⁴ | #31 |
| `Li6.4Ga0.05La2.8Ca0.2Zr1.35Ta0.65O12_evaluated.cif` | 6.40 | 0.05 | Ca 0.20 | 0.65 | 1.34×10⁻⁴ | #33 |
| `Li6.35Ga0.05La2.9Ba0.1Zr1.4Ta0.6O12_evaluated.cif` | 6.35 | 0.05 | Ba 0.10 | 0.60 | 1.32×10⁻⁴ | #34 |
| `Li6.35Ga0.05La2.9Ca0.1Zr1.4Ta0.6O12_evaluated.cif` | 6.35 | 0.05 | Ca 0.10 | 0.60 | 1.31×10⁻⁴ | #35 |

---

### Reference / Baseline Structures (in all_cif_structures/)

| Filename | Formula | Role |
|----------|---------|------|
| `Li7.0La3.0Zr2.0O12_evaluated.cif` | Undoped LLZO | Baseline reference |
| `Li7.0La2.9Gd0.1Zr1.9Hf0.1O12_evaluated.cif` | Gd+Hf doped | Comparison |
| `Li7.0La2.9Y0.1Zr2.0O12_evaluated.cif` | Y doped | Comparison |
| `Li6.500Ga0.10La3Zr1.80Nb0.20O12_evaluated.cif` | Ga+Nb | Cross-pipeline |
| `Li6.500Fe0.10La3Zr1.80Nb0.20O12_evaluated.cif` | Fe+Nb | Cross-pipeline |
| `Li6.500Al0.10La3Zr1.80Sb0.20O12_evaluated.cif` | Al+Sb | Cross-pipeline |

---

## 🎯 md_priority_queue/ — Top 3 for GPU MD (3 CIFs)

| Priority | Filename | GPR σ_RT | Notes |
|----------|----------|---------|-------|
| 🥇 #1 | `Li6.45La3.0Zr1.45Ta0.55O12_evaluated.cif` | **6.11×10⁻⁴ S/cm** | Highest σ_RT, simplest |
| 🥈 #2 | `Li6.4La3.0Zr1.4Ta0.6O12_evaluated.cif` | 5.85×10⁻⁴ S/cm | High σ_RT |
| 🥉 #3 | `Li6.45La2.95Ba0.05Zr1.4Ta0.6O12_evaluated.cif` | 5.57×10⁻⁴ S/cm | Best with A-site dopant |
