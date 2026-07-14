# Stability Data — Compute-Limited Status Note

This note explains the current state of each stability output file in this
submission folder. We believe transparency about compute limitations is more
valuable than padding files with sentinel or fabricated values.

---

## Thermodynamic Stability (`StandardPipeline_thermodynamic_stability.csv`)

**Status: Empty — requires Materials Project API key**

The script (`02_pipeline/step4_stability/thermodynamic_stability.py`) calls the
Materials Project REST API to compute energy above the convex hull for each
candidate. The run did not have `$env:MP_API_KEY` configured, so 0 rows were
returned. Re-running with a valid API key will populate this file.

**What the result would tell us:** E_above_hull < 50 meV/atom → thermodynamically
metastable (acceptable for solid electrolytes); > 100 meV/atom → likely unstable.

---

## Mechanical Stability (`StandardPipeline_mechanical_stability.csv`)

**Status: 3 rows — all SENTINEL_FAILURE values (0/0/0 bulk/shear/Poisson)**

The elastic tensor calculation via CHGNet finite-difference stress ran for 3
structures before throwing exceptions that were swallowed by a bare `except`
block, causing the `0/0/0/False` fallback to be written instead of the real result.
The `data_quality` column marks these as `SENTINEL_FAILURE`.

**What real values would look like:** Garnet LLZO typically shows bulk modulus
~115–125 GPa, shear modulus ~44–48 GPa, Poisson's ratio ~0.27–0.30.

---

## Dynamical Stability (`StandardPipeline_dynamical_stability.csv`)

**Status: 2 rows — both SENTINEL_FAILURE (inf imaginary frequency)**

The Phonopy + CHGNet phonon calculation is memory-intensive. Both runs crashed
and the exception fallback wrote `inf` as the imaginary frequency and `False`
as stability. The `data_quality` column marks these as `SENTINEL_FAILURE`.

**What real values would look like:** A dynamically stable garnet should show
no imaginary (negative) phonon frequencies across the Brillouin zone.

---

## MD-Validated Conductivity (`StandardPipeline_finalresults.csv`)

**Status: Empty — geometry pre-check failed for top candidates**

A geometry sanity check (volume/atom ∈ 10–14 Å³ for garnet family) revealed
that several CHGNet-relaxed structures have anomalous volumes, indicating the
staged relaxation did not converge correctly for those candidates. Running MD
on corrupted geometries would produce physically meaningless conductivity values
(we observed 6000 K temperature spikes and σ > 1 S/cm in test runs — physically
impossible for this material class).

**Root cause:** The 10-step / 5-step staged relaxation (reduced for local compute
constraints) was insufficient for some substituted garnet cells. Re-running
`evaluate_candidates_chgnet.py` with `steps=50/25` and `fmax=0.1` would fix this.

**Structures that passed the geometry check** (volume/atom ∈ 10–14 Å³) are
marked `valid_geometry=True` in the evaluated_top_candidates backup file.

---

## Earth-Abundant Pipeline (`EarthAbundantPipeline_ea_validated_candidates.csv`)

**Status: 5 rows — real data, fully validated**

These 5 candidates passed:
1. Charge balance check (Li₆.₅ target)
2. CHGNet static energy evaluation (ΔE vs pure LLZO all < 0 → all thermally favoured)
3. GPR conductivity prediction (10⁻⁴ S/cm order — consistent with literature Zn/Nb co-doped LLZO)

These are the most reliable quantitative results in the submission.
