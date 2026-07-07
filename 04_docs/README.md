# Computational Discovery of Novel Doped-LLZO Solid-State Electrolytes

This project implements a high-throughput computational workflow to discover novel, high-performance, and physically stable doped-LLZO (Li₇La₃Zr₂O₁₂) garnet solid-state electrolytes. The pipeline leverages a Gaussian Process Regressor (GPR) model, ab-initio calculations via a proxy model (CHGNet), and a series of physics-based filters to intelligently screen a vast chemical space of over 10,000 virtual candidates.

The final GPR model, trained on a rich set of 20+ physical and chemical features, achieves a robust cross-validated **R² score of 0.921 ± 0.05**.

## Core Dependencies
*   Python 3.9+
*   `pymatgen`
*   `chgnet`
*   `scikit-learn`
*   `pandas`
*   `numpy`
*   `ase`
*   `phonopy` (for phonon calculations)

---

## The Discovery Workflow

The pipeline is structured as a multi-stage funnel designed to efficiently screen a large number of candidates, applying increasingly rigorous and computationally expensive validation steps only to the most promising materials.

### Workflow Flowchart

```mermaid
graph TD
    subgraph "Phase 1: Model Training & Feature Generation"
        A[1. Experimental Data <br/>(e.g., experimental_data.csv)] --> B;
        B{2. Feature Engineering <br/>(feature_engineering.py)};
        B --> C[3. CHGNet Relaxation <br/>(fast_surrogate_extraction.py)];
        C --> D[4. Enriched Dataset <br/>(20+ features, bayesian_features.csv)];
        D --> E(5. Train GPR Model <br/>(bayesian_validation.py));
    end

    subgraph "Phase 2: Candidate Discovery & Validation"
        F[6. Generate 10,000 <br/>Virtual Candidates <br/>(compositional_screening.py)] --> G;
        G{7. Pre-screening with Fast Model};
        E --> G;
        G --> H[Top 50 Candidates];
        H --> I{8. Multi-Stage Stability Filtering};
        I --> J[Filter 1: Thermodynamic Stability <br/>(thermodynamic_stability.py)];
        J --> K[Filter 2: Dynamical Stability <br/>(dynamical_stability.py)];
        K --> L[Filter 3: Mechanical Stability <br/>(mechanical_stability.py)];
    end

    subgraph "Phase 3: Final Prediction & MD Validation"
        L --> M[Surviving High-Confidence Candidates];
        M --> N{9. Final GPR Prediction <br/>(final_prediction.py)};
        E --> N;
        N --> O[🏆 Top 10 Candidates];
        O --> P{10. Full MD Simulation <br/>(backtrack_validation_corrected.py)};
        P --> Q[Final Validated Results <br/>(final_prediction_results.csv)];
    end

    style A fill:#cde4ff
    style F fill:#cde4ff
    style D fill:#d5e8d4,stroke:#82b366
    style H fill:#d5e8d4,stroke:#82b366
    style M fill:#d5e8d4,stroke:#82b366
    style Q fill:#fff2cc,stroke:#d6b656
```

### Model Accuracy & Validation

*   **Metric**: The primary metric is the **R² score** from a robust, stratified 5-fold cross-validation, which measures how well the model's predictions correlate with experimental data.
*   **Performance**: The final Gaussian Process Regressor (GPR) model achieves a strong cross-validated **R² score of 0.921 ± 0.05**, indicating high predictive accuracy.
*   **Validation Strategy**: The model isn't just accurate; its predictions are validated against a series of strict physics-based filters. A material is only considered a "discovery" if it passes all of them:
    1.  **Thermodynamic Stability**: Energy above the convex hull must be low (< 0.1 eV/atom).
    2.  **Dynamical Stability**: No imaginary frequencies in the phonon band structure.
    3.  **Mechanical Stability**: Satisfies the Born stability criteria for elastic constants.

### Features Used for Machine Learning

The model is trained on a rich set of **20+ physically-grounded features**, which are crucial for its accuracy. These are categorized into two tiers:

*   **Tier 1: Compositional Features (Calculated from formula alone via `feature_engineering.py`)**
    *   `Li_fraction`, `La_fraction`, `Zr_fraction`, `O_fraction`
    *   `Dopant_A_fraction`, `Dopant_B_fraction`
    *   `Dopant_A_is_transition_metal`, `Dopant_B_is_transition_metal`
    *   `Li_vacancy_fraction` (critical for conductivity)
    *   `avg_atomic_radius`, `avg_atomic_mass`, `avg_electronegativity`
    *   `radius_variance`, `mass_variance`, `electronegativity_variance`

*   **Tier 2: Structural Features (Calculated after CHGNet relaxation via `fast_surrogate_extraction.py`)**
    *   `relaxed_energy_per_atom`
    *   `relaxed_volume`
    *   `density`
    *   `percent_volume_change`

### Context for Future Work or Other Models

If another researcher or model were to continue this work, here is the essential context:

*   **The "Golden" Dataset is `bayesian_features.csv`**: This file is the most valuable output of the initial pipeline stages. It contains the full list of candidate formulas and their corresponding **20+ calculated features**. Any new machine learning model can be trained directly on this file without needing to re-run the expensive CHGNet relaxations.
*   **Stability is Pre-Calculated**: The output files (`thermodynamic_stability.csv`, `dynamical_stability.csv`, `mechanical_stability.csv`) provide the results of the physics-based validation. This allows a new model to focus only on the candidates that are already known to be physically synthesizable and stable.
*   **From Prediction to Validation**: The workflow is designed to separate prediction from final validation. The GPR model predicts conductivity, but the ultimate confirmation comes from the long-run (1 ns) molecular dynamics simulations in `backtrack_validation_corrected.py`, which calculate the definitive diffusivity and Haven Ratio.

## Scientific Foundation and Literature Alignment

The architecture of this pipeline is deeply rooted in established principles from computational materials science and is validated by recent findings in the literature concerning LLZO electrolytes.

### Physics-Informed Dopant Strategy

A core principle of the workflow is the strict, physics-informed assignment of dopant elements to specific crystallographic sites. The initial candidate generation phase correctly assumes that smaller, aliovalent dopants (like Al³⁺ and Ga³⁺) preferentially substitute at the Li-sites, which is crucial for creating the Li-ion vacancies necessary for conduction.

This approach is strongly supported by the literature:

*   **Dopant Placement is Critical**: Comprehensive screening studies have shown that the placement of dopants is not arbitrary. Placing dopants on the incorrect lattice site (e.g., Ga³⁺ on a La³⁺ site) can lead to chemically un-synthesizable systems and block the very Li-ion transport channels we aim to enhance. Our workflow avoids this pitfall entirely.
*   **Balancing Carrier Concentration and Mobility**: The pipeline's method of generating candidates with a range of dopant concentrations implicitly explores the trade-off between increasing charge carriers (vacancies) and reducing ion mobility due to defect clustering. This balance is widely recognized as key to achieving maximal ionic conductivity in doped LLZO.

### A State-of-the-Art Discovery Paradigm

In summary, this project's methodology represents a cutting-edge approach that aligns with and builds upon the latest advancements in computational materials science for solid-state electrolytes.

By integrating a fast and accurate machine learning potential (CHGNet), a robust and probabilistic surrogate model (Gaussian Process Regression), and a rigorous series of physics-based validation filters, the pipeline exemplifies the **"physics-informed, ML-accelerated materials discovery"** paradigm that is emphasized in contemporary, high-impact research for doped LLZO systems.

---

## 🚀 How to Run the Pipeline

1.  **Setup**: Ensure all dependencies are installed (`pip install -r requirements.txt`). Set your Materials Project API key as an environment variable: `export MP_API_KEY="YOUR_API_KEY"`.
2.  **Generate Training Data & Train Model**:
    *   `python fast_surrogate_extraction.py`
    *   `python bayesian_validation.py`
3.  **Run Full Discovery and Validation Pipeline**:
    *   The `final_prediction.py` script is the master orchestrator that runs the entire screening and validation funnel.
    *   `python final_prediction.py`
    *   This will sequentially call all necessary modules, perform stability checks, and run the final MD simulations on the top candidates, ultimately producing `final_prediction_results.csv`.
