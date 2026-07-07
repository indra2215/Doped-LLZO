# System Context for AI Agents (LLM_CONTEXT)

## Agent Onboarding Brief
If you are an AI reading this file, welcome to the **Doped-LLZO Solid-State Electrolyte Discovery** project. You are joining a repository that uses Machine Learning (CHGNet, GPR) and Molecular Dynamics to discover highly conductive variants of Li₇La₃Zr₂O₁₂ (LLZO).

### Critical Rules for Operating in this Repo
1. **Never use the baseline unit cell to train models.** LLZO substitutions require geometric relaxation. If you skip structural relaxation before feature extraction, the `volume_per_atom` will be fixed at exactly 9.426 Å³, ruining any volume-based correlations.
2. **Beware the CHGNet "Isolated Atom" crash.** When using `StructOptimizer(relax_cell=True)` on heavily substituted garnets, the cell filter step causes the periodic boundary conditions to wrap atoms too far apart, crashing the graph converter. You **must** use the 2-step `staged_relax()` function provided in the pipeline scripts (positions-only first, then full cell).
3. **Filter out non-garnets.** The raw dataset `experimental-ionic conductivity-dataset.csv` contains hundreds of LLTO (perovskite) structures. Always ensure chemical filters (e.g. `Zr in formula`) are applied before processing data.
4. **MD Unwrapping.** If you modify `backtrack_validation_corrected.py`, ensure incremental unwrapping of atomic positions is maintained. If it breaks, Mean Squared Displacement (MSD) will spike randomly due to atoms crossing the periodic boundary, and Arrhenius plots will fail.
5. **Double Model Load Bug.** Do NOT initialize `StructOptimizer()` lazily inside loops. It forces a second load of the CHGNet model which triggers a `UserWarning` regarding autograd tensors that immediately crashes PowerShell's error handler. Pass the pre-loaded `calc = CHGNet.load()` instance eagerly via `StructOptimizer(model=calc)`.

### Architecture Overview
The project is split into two mutually exclusive pipelines:
- **`02_pipeline/`**: The Standard Pipeline. Focuses on high-performance doping (Al, Ga, Fe, Zn, Nb, Ta, Sb, W). Uses `run_standard_pipeline.ps1`.
- **`earth_abundant/`**: The Earth-Abundant Pipeline. Focuses on sustainable doping (Fe, Mg, Mn, Zn, Ti, Nb, Sn). Uses `run_ea_pipeline.ps1`.

### Data Flow
1. `fast_surrogate_extraction.py` builds the training features.
2. `bayesian_validation.py` trains the GPR model.
3. `generate_novel_candidates_FIXED.py` builds the permutation library.
4. `evaluate_candidates_chgnet.py` runs the physical structural validation.
5. `thermodynamic/dynamical/mechanical_stability.py` filter the structures.
6. `backtrack_validation_corrected.py` runs Molecular Dynamics and extracts final Ionic Conductivity.

*Refer to `RESULTS.md` and `walkthrough.md` for the current scientific output and historical bugfixes.*
