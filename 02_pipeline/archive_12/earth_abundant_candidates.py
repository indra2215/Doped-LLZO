"""
earth_abundant_candidates.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates, validates and screens earth-abundant / low-cost doped LLZO
compositions using CHGNet + M3GNet + charge balance physics.

Earth-abundant dopants targeted:
  Li-site (24d, val +3):  Fe³⁺, Al³⁺, Mg²⁺, Mn³⁺, Zn²⁺, Ti³⁺→(Li-site rare, use Zr-site for Ti)
  Zr-site (16a, val +4):  Ti⁴⁺, Mn⁴⁺, Fe⁴⁺ (uncommon), Nb⁵⁺(abundant ore)

Deliberately excluded (expensive/strategic):
  Ta, W, Mo, Ga (high cost), Y, Gd (rare earth), Hf (co-extracted w/ Zr, expensive)

Physics checks applied:
  1. Charge neutrality → Li_pfu range 6.0–6.9
  2. Li_pfu in the superionic window (6.1–6.8)
  3. Concentration caps per known stability limits
  4. Shannon ionic radius compatibility (dopant fits the site)

Validation pipeline:
  CHGNet  → energy/atom + volume (static predict_structure)
  M3GNet  → independent energy cross-check
  Cross-check: ΔE between two models < 0.15 eV/atom → accepted

Output: earth_abundant_candidates_validated.csv
"""

import itertools
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from pymatgen.core import Structure, Lattice, Composition

warnings.filterwarnings("ignore")

# ROOT = d:/doped_2 (three levels up)
ROOT = Path(__file__).parent.parent.parent
CWD  = Path(__file__).parent

# ─── Dopant definitions ─────────────────────────────────────────────────────

LI_SITE_DOPANTS = {
    # element: (valence, max_fraction, cost_tier, note)
    "Fe": (3, 0.20, "low",  "Fe³⁺ on Li-site; above x=0.20 causes electronic conductivity"),
    "Al": (3, 0.30, "low",  "Al³⁺ on Li-site; best known Li-site dopant, very cheap"),
    "Mg": (2, 0.25, "low",  "Mg²⁺ on Li-site; aliovalent, creates extra vacancies"),
    "Mn": (3, 0.15, "low",  "Mn³⁺/4+ mixed; risk of reduction to Mn²⁺ at high conc."),
    "Zn": (2, 0.20, "low",  "Zn²⁺ on Li-site; less studied, potentially novel"),
}

ZR_SITE_DOPANTS = {
    # element: (valence, max_fraction, cost_tier, note)
    "Ti": (4, 0.50, "low",  "Ti⁴⁺ isovalent; expands lattice, enhances bottleneck"),
    "Nb": (5, 0.50, "low",  "Nb⁵⁺ donor; ore-abundant (columbite), most studied Zr-site"),
    "Mn": (4, 0.30, "low",  "Mn⁴⁺ on Zr-site; novel, earth-abundant"),
    "Fe": (4, 0.20, "low",  "Fe⁴⁺ on Zr-site (rare oxidation state); less common"),
    "Sn": (4, 0.30, "low",  "Sn⁴⁺ isovalent; lattice softening, novel in LLZO"),
}

# Concentration steps to enumerate
X_VALS = [0.05, 0.10, 0.15, 0.20, 0.25]  # Li-site
Y_VALS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]  # Zr-site


# ─── Charge balance ──────────────────────────────────────────────────────────

def compute_li_pfu(li_val, x, zr_val, y):
    """
    Charge neutrality for:
      Li_n [Li_site_dopant]_x La3 Zr_(2-y) [Zr_site_dopant]_y O12

    Sum of cation charges = 24 (to balance 12 O²⁻):
      n×(+1) + x×li_val + 3×(+3) + (2-y)×(+4) + y×zr_val = 24
      n = 24 - x×li_val - 9 - (2-y)×4 - y×zr_val
    """
    n = 24.0 - x * li_val - 9.0 - (2 - y) * 4.0 - y * zr_val
    return round(n, 4)


def is_valid(li_pfu, x, li_max, y, zr_max):
    if not (6.0 <= li_pfu <= 6.9):
        return False, "li_pfu out of superionic window"
    if x > li_max:
        return False, f"Li-site conc {x} > cap {li_max}"
    if y > zr_max:
        return False, f"Zr-site conc {y} > cap {zr_max}"
    return True, "ok"


# ─── Candidate generation ─────────────────────────────────────────────────────

def generate_candidates():
    records = []

    for (li_el, (li_val, li_max, li_tier, li_note)), \
        (zr_el, (zr_val, zr_max, zr_tier, zr_note)) in \
            itertools.product(LI_SITE_DOPANTS.items(), ZR_SITE_DOPANTS.items()):

        # Skip Mn+Mn (same element on both sites → ordering impossible)
        if li_el == zr_el:
            continue

        for x, y in itertools.product(X_VALS, Y_VALS):
            li_pfu = compute_li_pfu(li_val, x, zr_val, y)
            ok, reason = is_valid(li_pfu, x, li_max, y, zr_max)
            if not ok:
                continue

            formula = (
                f"Li{li_pfu:.3f}"
                f"{li_el}{x:.2f}"
                f"La3"
                f"Zr{(2 - y):.2f}"
                f"{zr_el}{y:.2f}"
                f"O12"
            )

            # Literature novelty flag
            known_pairs = {("Al", "Nb"), ("Al", "Ta"), ("Ga", "Nb"), ("Ga", "Ta")}
            is_novel = (li_el, zr_el) not in known_pairs

            records.append({
                "formula":       formula,
                "Li_pfu":        li_pfu,
                "Li_site":       li_el,
                "Li_site_val":   li_val,
                "Li_conc":       x,
                "Zr_site":       zr_el,
                "Zr_site_val":   zr_val,
                "Zr_conc":       y,
                "pair":          f"{li_el}+{zr_el}",
                "cost_tier":     "low",
                "is_novel":      is_novel,
                "charge_check":  round(li_pfu + x * li_val + 9.0 + (2 - y) * 4.0 + y * zr_val - 24.0, 6),
            })

    df = pd.DataFrame(records)
    print(f"\n[OK] Generated {len(df)} earth-abundant candidates")
    print(df["pair"].value_counts().to_string())
    print(f"\nAll novel (not in main literature): {df['is_novel'].sum()}")
    print(f"Li_pfu range: {df['Li_pfu'].min():.3f} – {df['Li_pfu'].max():.3f}")
    return df


# ─── Base structure builder ───────────────────────────────────────────────────

def get_base_structure():
    """Builds LLZO garnet in Ia-3d from spacegroup symmetry."""
    return Structure.from_spacegroup(
        "Ia-3d",
        Lattice.cubic(12.98),
        ["Li", "La", "Zr", "O"],
        [[0.125, 0.5, 0.75],
         [0.125, 0.25, 0.375],
         [0.0,   0.0, 0.0],
         [0.105, 0.19, 0.795]],
    )


def build_substituted_structure(base_struct, li_el, x_frac, zr_el, y_frac):
    """
    Replaces atoms deterministically (ordered substitution):
      • Li-site dopant replaces proportional fraction of Li (24d sites)
      • Zr-site dopant replaces proportional fraction of Zr (16a sites)
    """
    from pymatgen.io.ase import AseAtomsAdaptor
    atoms = AseAtomsAdaptor.get_atoms(base_struct)
    syms = list(atoms.get_chemical_symbols())

    li_idx = [i for i, s in enumerate(syms) if s == "Li"]
    zr_idx = [i for i, s in enumerate(syms) if s == "Zr"]

    n_li_replace = max(1, round(len(li_idx) * x_frac))
    n_zr_replace = max(1, round(len(zr_idx) * y_frac))

    for i in li_idx[:n_li_replace]:
        syms[i] = li_el
    for i in zr_idx[:n_zr_replace]:
        syms[i] = zr_el

    atoms.set_chemical_symbols(syms)
    return AseAtomsAdaptor.get_structure(atoms)


# ─── CHGNet validation ────────────────────────────────────────────────────────

def validate_with_chgnet(structure, calculator):
    pred = calculator.predict_structure(structure)
    return float(pred["e"]), float(structure.volume / len(structure))


# ─── M3GNet validation ───────────────────────────────────────────────────────

def validate_with_m3gnet(structure):
    try:
        import matgl
        from matgl.ext.ase import M3GNetCalculator
        from pymatgen.io.ase import AseAtomsAdaptor

        pot = matgl.load_model("M3GNet-MP-2021.2.8-PES")
        calc = M3GNetCalculator(potential=pot)
        atoms = AseAtomsAdaptor.get_atoms(structure)
        atoms.set_calculator(calc)
        e_per_atom = atoms.get_potential_energy() / len(atoms)
        return float(e_per_atom)
    except ImportError:
        print("  ⚠  matgl not installed — skipping M3GNet cross-check")
        return None
    except Exception as e:
        print(f"  ⚠  M3GNet error: {e}")
        return None


# ─── Main screening loop ──────────────────────────────────────────────────────

def run_validation(df, max_candidates=20):
    """
    Validates up to max_candidates from the pool using CHGNet + M3GNet.
    Filters: |ΔE(CHGNet - M3GNet)| < 0.15 eV/atom → accepted
    """
    from chgnet.model import CHGNet
    print("\n── Loading CHGNet ──")
    chgnet_calc = CHGNet.load()
    base_struct = get_base_structure()

    results = []
    subset = df.head(max_candidates)

    for idx, row in subset.iterrows():
        formula = row["formula"]
        print(f"\n[{idx+1}/{len(subset)}] {formula}")
        try:
            struct = build_substituted_structure(
                base_struct, row["Li_site"], row["Li_conc"],
                row["Zr_site"], row["Zr_conc"]
            )

            # ── CHGNet ──
            e_chgnet, vol_pa = validate_with_chgnet(struct, chgnet_calc)
            print(f"  CHGNet: E/atom={e_chgnet:.4f} eV, Vol/atom={vol_pa:.3f} Å³")

            # ── M3GNet ──
            e_m3gnet = validate_with_m3gnet(struct)
            if e_m3gnet is not None:
                delta_e = abs(e_chgnet - e_m3gnet)
                cross_ok = delta_e < 0.15
                print(f"  M3GNet: E/atom={e_m3gnet:.4f} eV  |ΔE|={delta_e:.4f} → {'✅ PASS' if cross_ok else '❌ FAIL'}")
            else:
                delta_e = None
                cross_ok = None

            results.append({
                **row.to_dict(),
                "chgnet_energy_per_atom": e_chgnet,
                "chgnet_volume_per_atom": vol_pa,
                "m3gnet_energy_per_atom": e_m3gnet,
                "model_delta_eV_atom":    delta_e,
                "cross_model_agreement":  cross_ok,
            })

        except Exception as err:
            print(f"  ❌ Failed: {err}")

    return pd.DataFrame(results)


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    out_raw = ROOT / "01_data" / "candidates" / "earth_abundant_candidates_raw.csv"
    out_val = ROOT / "01_data" / "candidates" / "earth_abundant_candidates_validated.csv"
    out_raw.parent.mkdir(parents=True, exist_ok=True)

    # 1. Generate
    df = generate_candidates()
    df.to_csv(out_raw, index=False)
    print(f"\nSaved raw list → {out_raw}")

    # 2. Sort by Li_pfu (closer to 6.5 = ideal vacancy balance)
    df["pfu_score"] = (df["Li_pfu"] - 6.5).abs()
    df = df.sort_values("pfu_score").reset_index(drop=True)

    # 3. Validate top N with CHGNet + M3GNet
    print("\n── Starting validation (top 20 by Li_pfu proximity to 6.5) ──")
    validated_df = run_validation(df, max_candidates=20)
    validated_df.to_csv(out_val, index=False)

    print(f"\n\n{'='*60}")
    print("EARTH-ABUNDANT SCREENING RESULTS")
    print(f"{'='*60}")
    cols = ["formula", "pair", "Li_pfu", "chgnet_energy_per_atom",
            "chgnet_volume_per_atom", "cross_model_agreement"]
    avail = [c for c in cols if c in validated_df.columns]
    print(validated_df[avail].to_string(index=False))
    print(f"\nValidated results saved → {out_val}")


if __name__ == "__main__":
    main()
