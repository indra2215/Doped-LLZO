# Pipeline A — Earth-Abundant | Compounds Inventory

**Pipeline:** A — Earth-Abundant (Sustainable Dopants)  
**Constraint:** Only Fe, Mg, Al, Ti, Mn, Nb, Sn, Zn dopant elements allowed  
**Total CIF Structures:** 25  

---

## 📁 all_cif_structures/ — Complete Library (25 CIFs)

All structures are CHGNet-relaxed (position-only relaxation) from the EA candidate generation step.  
Garnet framework: **Li_x M_y La₃ Zr_(2-z) D_z O₁₂** where M = Li-site dopant, D = Zr-site dopant.

### Dopant Group 1: Zn + Nb (Best conductivity family)

| Filename | Zn conc. | Nb conc. | Li pfu | Validated | σ_RT (GPR) |
|----------|----------|----------|--------|-----------|------------|
| `Li6.500Zn0.05La3Zr1.60Nb0.40O12.cif` | 0.05 | 0.40 | 6.500 | ✅ CHGNet | 5.29×10⁻⁴ |
| `Li6.500Zn0.10La3Zr1.70Nb0.30O12.cif` | 0.10 | 0.30 | 6.500 | ✅ CHGNet | 5.85×10⁻⁴ |
| `Li6.500Zn0.15La3Zr1.80Nb0.20O12.cif` | 0.15 | 0.20 | 6.500 | ✅ CHGNet | 6.32×10⁻⁴ |
| `Li6.500Zn0.20La3Zr1.90Nb0.10O12.cif` ⭐ | 0.20 | 0.10 | 6.500 | ✅ CHGNet | **6.67×10⁻⁴** |

### Dopant Group 2: Mn + Nb

| Filename | Mn conc. | Nb conc. | Li pfu | Validated | σ_RT (GPR) |
|----------|----------|----------|--------|-----------|------------|
| `Li6.500Mn0.10La3Zr1.80Nb0.20O12.cif` ⭐ | 0.10 | 0.20 | 6.500 | ✅ CHGNet | **5.42×10⁻⁴** |

### Dopant Group 3: Al + Nb / Sb

| Filename | Al conc. | Co-dopant | Li pfu |
|----------|----------|-----------|--------|
| `Li6.500Al0.10La3Zr1.80Nb0.20O12.cif` | 0.10 | Nb 0.20 | 6.500 |

### Dopant Group 4: Fe + Nb

| Filename | Fe conc. | Co-dopant | Li pfu |
|----------|----------|-----------|--------|
| `Li6.500Fe0.10La3Zr1.80Nb0.20O12.cif` | 0.10 | Nb 0.20 | 6.500 |

### Dopant Group 5: Mg + {Nb, Ti, Sn, Mn, Fe} (Large Mg family)

| Filename | Mg conc. | Co-dopant | Co-dopant conc. |
|----------|----------|-----------|-----------------|
| `Li6.500Mg0.10La3Zr1.70Nb0.30O12.cif` | 0.10 | Nb | 0.30 |
| `Li6.500Mg0.15La3Zr1.80Nb0.20O12.cif` | 0.15 | Nb | 0.20 |
| `Li6.500Mg0.20La3Zr1.90Nb0.10O12.cif` | 0.20 | Nb | 0.10 |
| `Li6.500Mg0.25La3Zr1.60Ti0.40O12.cif` | 0.25 | Ti | 0.40 |
| `Li6.500Mg0.25La3Zr1.70Mn0.30O12.cif` | 0.25 | Mn | 0.30 |
| `Li6.500Mg0.25La3Zr1.70Sn0.30O12.cif` | 0.25 | Sn | 0.30 |
| `Li6.500Mg0.25La3Zr1.70Ti0.30O12.cif` | 0.25 | Ti | 0.30 |
| `Li6.500Mg0.25La3Zr1.75Mn0.25O12.cif` | 0.25 | Mn | 0.25 |
| `Li6.500Mg0.25La3Zr1.75Sn0.25O12.cif` | 0.25 | Sn | 0.25 |
| `Li6.500Mg0.25La3Zr1.80Fe0.20O12.cif` | 0.25 | Fe | 0.20 |
| `Li6.500Mg0.25La3Zr1.80Mn0.20O12.cif` | 0.25 | Mn | 0.20 |
| `Li6.500Mg0.25La3Zr1.80Sn0.20O12.cif` | 0.25 | Sn | 0.20 |
| `Li6.500Mg0.25La3Zr1.85Fe0.15O12.cif` | 0.25 | Fe | 0.15 |
| `Li6.500Mg0.25La3Zr1.85Mn0.15O12.cif` | 0.25 | Mn | 0.15 |
| `Li6.500Mg0.25La3Zr1.85Sn0.15O12.cif` | 0.25 | Sn | 0.15 |
| `Li6.500Mg0.25La3Zr1.90Fe0.10O12.cif` | 0.25 | Fe | 0.10 |
| `Li6.500Mg0.25La3Zr1.90Mn0.10O12.cif` | 0.25 | Mn | 0.10 |
| `Li6.500Mg0.25La3Zr1.90Sn0.10O12.cif` | 0.25 | Sn | 0.10 |

---

## 🎯 md_priority_queue/ — Top 3 Candidates for GPU MD (3 CIFs)

These 3 structures are queued for **Arrhenius NVT Langevin MD** at 600/800/1000 K.  
They are copies from `all_cif_structures/` — do not modify.

| Priority | Filename | Reason Chosen |
|----------|----------|--------------|
| 🥇 #1 | `Li6.500Zn0.20La3Zr1.90Nb0.10O12.cif` | Best EA σ_RT (6.67×10⁻⁴ S/cm) |
| 🥈 #2 | `Li6.500Mn0.10La3Zr1.80Nb0.20O12.cif` | 2nd-best σ_RT, earth-abundant Mn |
| 🥉 #3 | `Li6.500Zn0.05La3Zr1.60Nb0.40O12.cif` | Most thermodynamically stable (ΔE = -9.21 eV/atom) |
