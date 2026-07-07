# run_standard_pipeline.ps1
# ══════════════════════════════════════════════════════════════════════════════
# STANDARD PIPELINE — One-click runner
# ══════════════════════════════════════════════════════════════════════════════
#
# Pipeline: Li/Al/Ga/Fe-doped LLZO  +  Nb/Ta/Sb/W on Zr-site
# Candidates: 150 charge-balanced compositions (permutation_candidates.csv)
# Output:     finalresults.csv  (Arrhenius MD validated σ_RT + Ea)
#
# Usage:
#   $env:MP_API_KEY = "your_key_here"   # required for Step 4a only
#   .\run_standard_pipeline.ps1
#
# Steps:
#   1  fast_surrogate_extraction.py  → 01_data/results/bayesian_features.csv
#   2  bayesian_validation.py        → step2_model_training/trained_gpr_model.pkl
#   3a generate_novel_candidates_FIXED.py → 01_data/candidates/permutation_candidates.csv
#   3b screen_novel_candidates.py   → 01_data/candidates/novel_screened_candidates.csv
#   3c compositional_screening.py   → 01_data/candidates/top_50_screened_candidates.csv
#   3d evaluate_candidates_chgnet.py → 01_data/results/evaluated_top_candidates.csv + CIFs
#   4a thermodynamic_stability.py   → 01_data/results/thermodynamic_stability.csv
#   4b dynamical_stability.py       → 01_data/results/dynamical_stability.csv
#   4c mechanical_stability.py      → 01_data/results/mechanical_stability.csv
#   5  backtrack_validation_corrected.py → 01_data/results/finalresults.csv
# ══════════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING  = "utf-8"

function Run-Step {
    param([string]$Label, [string]$Script)
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host " $Label" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    python $Script
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: $Script (exit code $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "Done: $Label" -ForegroundColor Green
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║        STANDARD PIPELINE — LLZO (Al/Ga/Fe + Nb/Ta/Sb/W)    ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow

# Check MP_API_KEY (optional — only needed for Step 4a)
if (-not $env:MP_API_KEY) {
    Write-Host ""
    Write-Host "WARNING: MP_API_KEY not set — Step 4a (thermodynamic hull) will be skipped." -ForegroundColor Yellow
    Write-Host "  Set it with: `$env:MP_API_KEY = 'your_key_here'" -ForegroundColor Yellow
}

Run-Step "Step 1 — Feature Extraction (Compositional features on 679 samples)" `
    "02_pipeline/step1_feature_extraction/fast_surrogate_extraction.py"

Run-Step "Step 2 — GPR Model Training (5-fold CV, RF Baseline, trained_gpr_model.pkl)" `
    "02_pipeline/step2_model_training/bayesian_validation.py"

Run-Step "Step 3a — Generate Novel Candidates (charge-balanced permutations)" `
    "02_pipeline/step3_screening/generate_novel_candidates_FIXED.py"

Run-Step "Step 3b — Screen Novel Candidates (RF ranking)" `
    "02_pipeline/step3_screening/screen_novel_candidates.py"

Run-Step "Step 3c — Compositional Screening (top 50 from virtual library)" `
    "02_pipeline/step3_screening/compositional_screening.py"

Run-Step "Step 3d — CHGNet Staged Relax (top 50 candidates)" `
    "02_pipeline/step3_screening/evaluate_candidates_chgnet.py"

if ($env:MP_API_KEY) {
    Run-Step "Step 4a — Thermodynamic Stability (Materials Project hull)" `
        "02_pipeline/step4_stability/thermodynamic_stability.py"
} else {
    Write-Host ""
    Write-Host "  [SKIP] Step 4a — Thermodynamic Stability (MP_API_KEY not set)" -ForegroundColor DarkYellow
}

Run-Step "Step 4b — Dynamical Stability (phonons, top 5)" `
    "02_pipeline/step4_stability/dynamical_stability.py"

Run-Step "Step 4c — Mechanical Stability (elastic tensor)" `
    "02_pipeline/step4_stability/mechanical_stability.py"

Run-Step "Step 5  — MD Arrhenius Validation (1 ns NVT Langevin, σ_RT + Ea)" `
    "02_pipeline/step5_md_validation/backtrack_validation_corrected.py"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Standard Pipeline Complete!                                 ║" -ForegroundColor Green
Write-Host "║  Results → 01_data/results/finalresults.csv                 ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
