# run_ea_pipeline.ps1
# ══════════════════════════════════════════════════════════════════════════════
# EARTH-ABUNDANT PIPELINE — One-click runner
# ══════════════════════════════════════════════════════════════════════════════
#
# Pipeline: Fe/Mg/Mn/Zn-doped LLZO  +  Ti/Nb/Mn/Fe/Sn on Zr-site
# Focus:    Low-cost, earth-abundant dopants only (excludes Ta/W/Ga/Hf/Y/Gd)
# Candidates: 535 charge-balanced compositions
# Output:     earth_abundant/data/results/ea_finalresults.csv
#
# Usage:
#   $env:MP_API_KEY = "your_key_here"   # required for Step 5 only
#   .\run_ea_pipeline.ps1
#
# Steps:
#   1  ea_step1_feature_extraction.py → earth_abundant/data/results/ea_gpr_features.csv
#   2  ea_step2_model_training.py     → earth_abundant/data/models/ea_gpr_model.pkl
#   3  ea_step3_candidates.py         → earth_abundant/data/candidates/earth_abundant_candidates_raw.csv
#   4  ea_step4_validate.py           → earth_abundant/data/results/ea_validated_candidates.csv + CIFs
#   5  ea_step5_stability.py          → earth_abundant/data/results/ea_thermodynamic_stability.csv
#   6  ea_step6_md_validation.py      → earth_abundant/data/results/ea_finalresults.csv
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
Write-Host "║   EARTH-ABUNDANT PIPELINE — LLZO (Fe/Mg/Mn/Zn + Ti/Nb/Sn)  ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow

# Check MP_API_KEY (optional — only needed for Step 5)
if (-not $env:MP_API_KEY) {
    Write-Host ""
    Write-Host "WARNING: MP_API_KEY not set — Step 5 (thermodynamic hull) will be skipped." -ForegroundColor Yellow
    Write-Host "  Set it with: `$env:MP_API_KEY = 'your_key_here'" -ForegroundColor Yellow
}

Run-Step "Step 1 — EA Feature Extraction (Compositional features on 679 samples)" `
    "earth_abundant/scripts/ea_step1_feature_extraction.py"

Run-Step "Step 2 — EA GPR Model Training (5-fold CV, RF Baseline, ea_gpr_model.pkl)" `
    "earth_abundant/scripts/ea_step2_model_training.py"

Run-Step "Step 3 — EA Candidate Generation (535 charge-balanced compositions)" `
    "earth_abundant/scripts/ea_step3_candidates.py"

Run-Step "Step 4 — EA Validation (CHGNet staged relax + M3GNet + GPR)" `
    "earth_abundant/scripts/ea_step4_validate.py"

if ($env:MP_API_KEY) {
    Run-Step "Step 5 — EA Thermodynamic Stability (Materials Project hull)" `
        "earth_abundant/scripts/ea_step5_stability.py"
} else {
    Write-Host ""
    Write-Host "  [SKIP] Step 5 — Thermodynamic Stability (MP_API_KEY not set)" -ForegroundColor DarkYellow
}

Run-Step "Step 6 — EA MD Arrhenius Validation (top 5 stable, 1 ns NVT)" `
    "earth_abundant/scripts/ea_step6_md_validation.py"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Earth-Abundant Pipeline Complete!                           ║" -ForegroundColor Green
Write-Host "║  Results → earth_abundant/data/results/ea_finalresults.csv  ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
