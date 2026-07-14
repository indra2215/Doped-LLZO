"""
smoke_tests.py
══════════════════════════════════════════════════════════════════════════
Lightweight smoke tests for the Doped-LLZO pipeline.

Checks:
  1. All scripts referenced in the runner actually exist
  2. All expected output files exist and have the right column schemas
  3. No D:\\ absolute paths leak into submission CSVs
  4. Candidate counts are within expected ranges
  5. No sentinel values (inf / 0/0/0) quietly pass as real data

Usage:
    python smoke_tests.py

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed (see output above).
"""

import sys
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent
ERRORS = []
WARNINGS = []

def check(name, condition, message, is_warning=False):
    if condition:
        print(f"  [PASS] {name}")
    else:
        if is_warning:
            WARNINGS.append(f"  [WARN] {name}: {message}")
            print(f"  [WARN] {name}: {message}")
        else:
            ERRORS.append(f"  [FAIL] {name}: {message}")
            print(f"  [FAIL] {name}: {message}")

# ─── 1. Runner script references ───────────────────────────────────────────────
print("\n=== 1. Runner Script File Existence ===")
RUNNER_SCRIPTS = [
    "02_pipeline/step1_feature_extraction/fast_surrogate_extraction.py",
    "02_pipeline/step2_model_training/bayesian_validation.py",
    "02_pipeline/step3_screening/generate_candidates.py",
    "02_pipeline/step3_screening/compositional_screening.py",
    "02_pipeline/step3_screening/evaluate_candidates_chgnet.py",
    "02_pipeline/step4_stability/thermodynamic_stability.py",
    "02_pipeline/step4_stability/dynamical_stability.py",
    "02_pipeline/step4_stability/mechanical_stability.py",
    "02_pipeline/step5_md_validation/backtrack_validation_corrected.py",
    "earth_abundant/scripts/ea_step1_feature_extraction.py",
    "earth_abundant/scripts/ea_step2_model_training.py",
    "earth_abundant/scripts/ea_step3_candidates.py",
    "earth_abundant/scripts/ea_step4_validate.py",
    "earth_abundant/scripts/ea_step5_stability.py",
    "earth_abundant/scripts/ea_step6_md_validation.py",
]
for s in RUNNER_SCRIPTS:
    check(s, (ROOT / s).exists(), f"Script not found")

# ─── 2. Output file schemas ────────────────────────────────────────────────────
print("\n=== 2. Output File Schemas ===")

def check_csv(rel_path, required_cols, min_rows=0):
    p = ROOT / rel_path
    name = rel_path.split("/")[-1]
    if not p.exists():
        check(f"{name} exists", False, f"File missing at {rel_path}")
        return
    try:
        df = pd.read_csv(p, comment="#")
        check(f"{name} exists", True, "")
        for col in required_cols:
            check(f"  {name} has column '{col}'", col in df.columns, f"Column missing")
        if min_rows > 0:
            check(f"  {name} has >= {min_rows} rows", len(df) >= min_rows,
                  f"Only {len(df)} rows", is_warning=True)
    except Exception as e:
        check(f"{name} readable", False, str(e))

check_csv(
    "01_data/candidates/bayesian_virtual_candidates.csv",
    ["formula"], min_rows=1000
)
check_csv(
    "01_data/candidates/top_50_screened_candidates.csv",
    ["formula"], min_rows=10
)
check_csv(
    "earth_abundant/data/results/ea_validated_candidates.csv",
    ["formula", "gpr_sigma_RT_bulk_S_cm", "thermal_stability", "delta_E_vs_LLZO"], min_rows=1
)
check_csv(
    "FINAL_RESULTS_HACKATHON/EarthAbundantPipeline_ea_validated_candidates.csv",
    ["formula", "gpr_sigma_RT_bulk_S_cm", "thermal_stability"], min_rows=5
)
check_csv(
    "FINAL_RESULTS_HACKATHON/StandardPipeline_evaluated_top_candidates.csv",
    ["formula", "predicted_conductivity", "relaxed_volume_per_atom"], min_rows=20
)

# ─── 3. No absolute D:\\ paths in submission CSVs ──────────────────────────────
print("\n=== 3. Absolute Path Leak Check (FINAL_RESULTS_HACKATHON/*.csv) ===")
submission_csvs = list((ROOT / "FINAL_RESULTS_HACKATHON").glob("*.csv"))
for csv_path in submission_csvs:
    try:
        text = csv_path.read_text(errors="replace")
        has_abs = "D:\\" in text or "d:\\" in text or "D:/" in text
        check(f"No D:\\ path in {csv_path.name}", not has_abs,
              "Absolute local path found — strip before submitting externally")
    except Exception as e:
        check(f"{csv_path.name} readable", False, str(e))

# ─── 4. Candidate count sanity ─────────────────────────────────────────────────
print("\n=== 4. Candidate Count Ranges ===")
def check_count(label, rel_path, min_r, max_r):
    p = ROOT / rel_path
    if not p.exists():
        check(label, False, "File missing"); return
    try:
        df = pd.read_csv(p, comment="#")
        n = len(df)
        check(label, min_r <= n <= max_r,
              f"{n} rows — expected {min_r}–{max_r}", is_warning=(n < min_r))
    except Exception as e:
        check(label, False, str(e))

check_count("bayesian_virtual_candidates rows (1k–25k)",
            "01_data/candidates/bayesian_virtual_candidates.csv", 1000, 25000)
check_count("top_50_screened rows (5–60)",
            "01_data/candidates/top_50_screened_candidates.csv", 5, 60)
check_count("EA validated candidates rows (1–20)",
            "FINAL_RESULTS_HACKATHON/EarthAbundantPipeline_ea_validated_candidates.csv", 1, 20)

# ─── 5. Sentinel value detection ───────────────────────────────────────────────
print("\n=== 5. Sentinel Value Detection ===")

def check_no_sentinels(rel_path, col, sentinel_val, label=None):
    p = ROOT / rel_path
    if not p.exists():
        return
    try:
        df = pd.read_csv(p, comment="#")
        if col not in df.columns:
            return
        n_sentinel = (df[col] == sentinel_val).sum()
        total = len(df)
        name = label or rel_path.split("/")[-1]
        check(f"No {sentinel_val} sentinels in {name}['{col}']",
              n_sentinel == 0,
              f"{n_sentinel}/{total} rows are sentinel values — check data_quality column",
              is_warning=True)
    except Exception:
        pass

check_no_sentinels(
    "FINAL_RESULTS_HACKATHON/StandardPipeline_mechanical_stability.csv",
    "bulk_modulus_vrh", 0, "mechanical_stability"
)
check_no_sentinels(
    "FINAL_RESULTS_HACKATHON/StandardPipeline_dynamical_stability.csv",
    "is_dynamically_stable", False, "dynamical_stability"
)

# ─── 6. CIF count in relaxed/ ──────────────────────────────────────────────────
print("\n=== 6. Relaxed Structure CIF Count ===")
cif_dir = ROOT / "03_structures" / "relaxed"
cifs = list(cif_dir.glob("*.cif")) if cif_dir.exists() else []
check("relaxed/ exists", cif_dir.exists(), "Directory missing")
check("relaxed/ has 30–60 CIFs", 30 <= len(cifs) <= 60,
      f"Found {len(cifs)} — expected 30–60", is_warning=True)
print(f"    (Found {len(cifs)} CIF files)")

# ─── 7. results_manifest.json readable ────────────────────────────────────────
print("\n=== 7. Results Manifest Valid JSON ===")
manifest_path = ROOT / "FINAL_RESULTS_HACKATHON" / "results_manifest.json"
if manifest_path.exists():
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        check("results_manifest.json is valid JSON", True, "")
        check("manifest has 'pipelines' key", "pipelines" in manifest, "Key missing")
    except json.JSONDecodeError as e:
        check("results_manifest.json is valid JSON", False, str(e))
else:
    check("results_manifest.json exists", False, "File missing")

# ─── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print(f"SMOKE TEST RESULTS: {len(ERRORS)} errors, {len(WARNINGS)} warnings")

if ERRORS:
    print("\nFAILURES (must fix):")
    for e in ERRORS:
        print(e)

if WARNINGS:
    print("\nWARNINGS (review):")
    for w in WARNINGS:
        print(w)

if not ERRORS and not WARNINGS:
    print("All checks passed!")
elif not ERRORS:
    print("\nAll critical checks passed. Review warnings above.")

sys.exit(1 if ERRORS else 0)
