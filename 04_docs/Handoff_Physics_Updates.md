# PHYSICS UPDATE HANDOFF 

**Reviewer Feedback Addressed:** 13 peer-reviewed critiques incorporated into the code architecture without interrupting the live Bayesian Extraction phase.

## 1. Structural Corrections to `generate_candidates.py`
**Literature Source:** *Anderson et al. (2024)* & *Ma et al. (2024)*
- **Old Assumption:** Aliovalent elements (Fe, Ga, Al) were placed as La/Zr-site dopants.
- **Physical Reality:** These elements substitute the Li-site (24d). Placing them on the La/Zr network results in chemically un-synthesizable systems, false vacancy generations, and severe transport channel blockage. 
- **Code Fix:** We explicitly rewrote the dopant assignments. The candidate matrix generator now assigns `li_dopants = {'Fe': 3, 'Ga': 3, 'Al': 3}` directly substituting the Li+ site.

## 2. Conductivity Limits to `generate_candidates.py`
**Literature Source:** *Anderson et al. (2024)*
- **Old Assumption:** Li concentration (pfu) was permitted between 5.0 and 8.0, and charge balancing calculated naive positive targets blindly.
- **Physical Reality:** The highest RT ionic conductivities strictly lie within a window of 6.1 - 6.8 formula units of Li. Dropping below 6.1 destabilizes the cubic phase; going above 6.8 provides insufficient vacancy concentration for hopping.
- **Code Fix:** Added an exact conditional filter enforcing `6.1 <= (n_li_actual + z) <= 6.8`. Non-compliant structures are skipped.

## 3. Lattice Parameter Checks (Surrogate Validation)
**Literature Source:** *Luo et al. (2025 corr.)*
- **Old Assumption:** Bayesian Optimization was mapping just primitive Energy to Conductivity regardless of unit cell distortion.
- **Physical Reality:** High ionic conductivity is strongly localized in Garnets exhibiting a macroscopic lattice parameter (a) between **12.91 - 12.98 Angstrom**.
- **Code Fix:** Added a = (2 * V_primitive)^(1/3) calculation inside `bayesian_validation.py`. The updated GP regressor now flags all validated data points mapping outside the Anderson target metric stringently as FAIL/PASS within the ML prediction phase.

## Process Status:
All updates have been made to the validation, model, and generation code blocks without stopping the active `fast_surrogate_extraction.py` terminal context.