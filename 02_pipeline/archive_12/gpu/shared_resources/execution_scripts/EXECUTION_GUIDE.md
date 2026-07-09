# Execution Guide — GPU/HPC Submission

**Script:** `run_remaining_steps.py` | **Location:** Project root `Doped-LLZO/`

---

## Critical: Always Run from Project Root

```powershell
# Windows — navigate to the Doped-LLZO root first
cd C:\Users\sahasra\Downloads\doped\Doped-LLZO

# NOT from inside the gpu/ folder — paths will break
```

---

## Most Common Commands

### Run Everything (Both Pipelines, Both MD Steps)
```bash
python run_remaining_steps.py --n-candidates 3 --md-steps 500
```

### EA Pipeline MD Only (Skip Standard)
```bash
python run_remaining_steps.py --skip-std-md --n-candidates 3 --md-steps 500
```

### Standard Pipeline MD Only (Skip EA)
```bash
python run_remaining_steps.py --skip-ea6 --n-candidates 3 --md-steps 500
```

### With Materials Project Hull Check
```bash
python run_remaining_steps.py --mp-key mp-YOUR_KEY_HERE --n-candidates 3 --md-steps 500
```

### CPU Fallback (No GPU)
```bash
python run_remaining_steps.py --use-cpu --n-candidates 3 --md-steps 200
```

### High-Accuracy Publication Run
```bash
python run_remaining_steps.py --mp-key mp-xxx --n-candidates 3 --md-steps 2000
```

---

## All CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--mp-key` | `""` | Materials Project API key |
| `--skip-ea4` | False | Skip EA CHGNet validation |
| `--skip-ea5` | False | Skip EA thermodynamic hull |
| `--skip-ea6` | False | Skip EA Arrhenius MD |
| `--skip-std-md` | False | Skip Standard MD |
| `--n-candidates` | 3 | How many candidates for MD |
| `--md-steps` | 500 | MD steps per temperature (×3 temps) |
| `--use-cpu` | False | Force CPU-only |
| `--vram-limit-mb` | 3500 | Min free VRAM to use GPU |

---

## VRAM Safety Guide

| `--md-steps` | Peak VRAM | Recommended GPU |
|-------------|-----------|----------------|
| 200 | ~2–3 GB | GTX 1660, RTX 3050 |
| 500 | ~4–6 GB | RTX 3050 6GB, RTX 3060 |
| 1000 | ~6–10 GB | RTX 3080, RTX 4070 |
| 2000+ | ~12–20 GB | A100, RTX 4090 |

---

## OOM Troubleshooting

```bash
# If you get: RuntimeError: CUDA out of memory

# Option 1: Reduce steps
python run_remaining_steps.py --md-steps 200

# Option 2: One candidate at a time
python run_remaining_steps.py --n-candidates 1 --md-steps 500

# Option 3: CPU only
python run_remaining_steps.py --use-cpu

# Option 4: Lower VRAM threshold (auto-fallback to CPU)
python run_remaining_steps.py --vram-limit-mb 2000
```

---

## HPC SLURM Script

```bash
#!/bin/bash
#SBATCH --job-name=llzo_md_full
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=8
#SBATCH --partition=gpu

module load cuda/12.1
conda activate llzo_gpu

cd /path/to/Doped-LLZO

python run_remaining_steps.py \
    --mp-key $MP_API_KEY \
    --n-candidates 3 \
    --md-steps 1000 \
    2>&1 | tee gpu_run_$(date +%Y%m%d_%H%M%S).log
```

---

## Output Files Location

| Step | Output File | Location |
|------|-------------|----------|
| EA Step 4 | `ea_validated_candidates.csv` | `earth_abundant/data/results/` |
| EA Step 5 | `ea_thermodynamic_stability.csv` | `earth_abundant/data/results/` |
| EA Step 6 | `ea_md_arrhenius_results.csv` | `earth_abundant/data/results/` |
| Std Step 5 | Updated `MASTER_RESULTS.csv` | `FINAL_Results/High_Performance_Pipeline/` |
