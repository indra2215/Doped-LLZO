# Further Improvements & Pending Tasks

## 1. High-Performance Pipeline (Current Focus)
The following tasks require significant computational power and are currently being monitored or are scheduled next:

### A. Known Computational Issues & Hardware Limits
- **Memory Allocation Crashes (OOM)**: Running Langevin dynamics via CHGNet and calculating Phonon force constants is causing the local machine to repeatedly crash with `A realloc of memory failed!` and exit code 1. This occurs because tracking gradient tensors across thousands of 100-atom supercell displacements exceeds standard local RAM.
- **PyTorch Gradient Constraints**: Disabling `torch.set_grad_enabled(False)` prevented OOM crashes but fundamentally broke the CHGNet physics engine (which relies on autograd to compute forces). Thus, gradients *must* remain enabled, demanding high RAM.
- **Extremely Slow Runtimes**: Local processing of `dynamical_stability.py` is taking ~15+ minutes per candidate, rendering the full 35-candidate batch practically unfeasible on a local CPU.

### B. Action Plan for Pending Tasks
**Required Action:** Manually submit the following pending tasks to the High-Performance Compute (PBS/HPC) cluster system to leverage higher memory and parallel processing:
- **Molecular Dynamics (MD) Validation** (`step5_md_validation/backtrack_validation_corrected.py`): Simulate Li-ion diffusion over 5,000 steps without memory caps.
- **Dynamical Stability** (`step4_stability/dynamical_stability.py`): Extract phonon DOS using Phonopy + CHGNet forces to verify no imaginary frequencies exist.
- **Mechanical Stability** (`step4_stability/mechanical_stability.py`): Calculate the full elastic tensor ($C_{ij}$) to ensure structural integrity under shear.
- **Thermodynamic Hull Distance**: Validating phase stability against the Materials Project database.

## 2. Streamlining Process
- **Cleaned Data Folders**: Removed old/partial data related to the Earth-Abundant pipeline from the `FINAL_Results` directory to strictly isolate and streamline the High-Performance generation pipeline.
- **Removed Redundant Scripts**: Cleaned up deprecated and irrelevant files in the `02_pipeline` directory.

## 3. Future Work: Earth-Abundant Materials (Pipeline 2)
Once the high-end generation pipeline is fully executed and validated, we will transition to the Earth-Abundant (Real Estate / Scalability) aspects.
- Re-run `ea_step4_validate.py` (M3GNet / CHGNet cross-validation).
- Conduct stability and MD simulations strictly constrained to low-cost dopants (Fe, Al, Mg, Mn, Zn, Ti, Nb, Sn).
