"""
feature_engineering.py
──────────────────────
This module handles the extraction of compositional features from a given 
chemical formula (e.g. fractional compositions, average mass, atomic radius, 
and electronegativity). 

Outputs are structured into dictionaries used by downstream machine learning 
models (e.g. Gaussian Process Regressor) for fast initial screening of conductivity.
"""
import pandas as pd
from pymatgen.core import Composition

def get_feature_names():
    """Returns the list of all feature names."""
    return [
        'Li_fraction', 'La_fraction', 'Zr_fraction', 'O_fraction',
        'Dopant_A_fraction', 'Dopant_B_fraction',
        'Dopant_A_is_transition_metal', 'Dopant_B_is_transition_metal',
        'Li_vacancy_fraction',
        'avg_atomic_radius', 'avg_atomic_mass', 'avg_electronegativity',
        'radius_variance', 'mass_variance', 'electronegativity_variance'
    ]

def calculate_compositional_features(formula: str) -> dict:
    """
    Calculates a suite of compositional features for a given chemical formula.

    Args:
        formula (str): The chemical formula of the material.

    Returns:
        dict: A dictionary containing the calculated features.
    """
    try:
        comp = Composition(formula)
        elements = comp.elements
        el_dict = comp.get_el_amt_dict()

        # Base LLZO fractions
        li_frac = el_dict.get("Li", 0) / comp.num_atoms
        la_frac = el_dict.get("La", 0) / comp.num_atoms
        zr_frac = el_dict.get("Zr", 0) / comp.num_atoms
        o_frac = el_dict.get("O", 0) / comp.num_atoms

        # Identify dopants (assuming they are not Li, La, Zr, O)
        dopants = [el for el in elements if el.symbol not in ["Li", "La", "Zr", "O"]]
        dopant_A = dopants[0] if len(dopants) > 0 else None
        dopant_B = dopants[1] if len(dopants) > 1 else None

        dopant_A_frac = el_dict.get(dopant_A.symbol, 0) / comp.num_atoms if dopant_A else 0
        dopant_B_frac = el_dict.get(dopant_B.symbol, 0) / comp.num_atoms if dopant_B else 0

        # Dopant properties
        dopant_A_is_tm = dopant_A.is_transition_metal if dopant_A else 0
        dopant_B_is_tm = dopant_B.is_transition_metal if dopant_B else 0

        # Vacancy calculation (relative to ideal Li7La3Zr2O12)
        # Ideal formula has 7 Li atoms.
        ideal_li_per_fu = 7
        actual_li_per_fu = el_dict.get("Li", 0)
        li_vacancy_frac = max(0, (ideal_li_per_fu - actual_li_per_fu)) / ideal_li_per_fu

        # Weighted average properties
        total_atoms = comp.num_atoms
        avg_radius = sum(el.atomic_radius * el_dict[el.symbol] for el in elements) / total_atoms if all(el.atomic_radius is not None for el in elements) else 0
        avg_mass = sum(el.atomic_mass * el_dict[el.symbol] for el in elements) / total_atoms
        avg_en = sum(el.X * el_dict[el.symbol] for el in elements) / total_atoms if all(el.X is not None for el in elements) else 0
        
        # Weighted variance/difference features
        radius_variance = sum(el_dict[el.symbol] * (el.atomic_radius - avg_radius)**2 for el in elements) / total_atoms if all(el.atomic_radius is not None for el in elements) and avg_radius > 0 else 0
        mass_variance = sum(el_dict[el.symbol] * (el.atomic_mass - avg_mass)**2 for el in elements) / total_atoms
        en_variance = sum(el_dict[el.symbol] * (el.X - avg_en)**2 for el in elements) / total_atoms if all(el.X is not None for el in elements) and avg_en > 0 else 0


        features = {
            'formula': formula,
            'Li_fraction': li_frac,
            'La_fraction': la_frac,
            'Zr_fraction': zr_frac,
            'O_fraction': o_frac,
            'Dopant_A_fraction': dopant_A_frac,
            'Dopant_B_fraction': dopant_B_frac,
            'Dopant_A_is_transition_metal': 1 if dopant_A_is_tm else 0,
            'Dopant_B_is_transition_metal': 1 if dopant_B_is_tm else 0,
            'Li_vacancy_fraction': li_vacancy_frac,
            'avg_atomic_radius': avg_radius,
            'avg_atomic_mass': avg_mass,
            'avg_electronegativity': avg_en,
            'radius_variance': radius_variance,
            'mass_variance': mass_variance,
            'electronegativity_variance': en_variance,
        }
        return features

    except Exception as e:
        print(f"Could not process formula {formula}: {e}")
        return {key: 0 for key in get_feature_names()}

if __name__ == '__main__':
    # Example usage:
    formulas = ["Li6.5La3Zr1.5Ta0.5O12", "Li7La3Zr2O12", "Li6.25Ga0.25La3Zr2O12"]
    
    # Create a list to hold the feature dictionaries
    all_features = []

    # Process each formula
    for f in formulas:
        features = calculate_compositional_features(f)
        all_features.append(features)

    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(all_features)

    # Set the formula as the index
    df.set_index('formula', inplace=True)

    print("Calculated Compositional Features:")
    print(df)

    # Example of how to use this in another script:
    # from feature_engineering import calculate_compositional_features
    #
    # new_formula = "Li6.75Al0.25La3Zr1.75Nb0.25O12"
    # features = calculate_compositional_features(new_formula)
    # print(f"\nFeatures for {new_formula}:")
    # print(features)
