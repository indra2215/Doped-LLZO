import os
import sys
import glob
from pathlib import Path
from pymatgen.core import Structure, Lattice
from pymatgen.io.ase import AseAtomsAdaptor
from chgnet.model import CHGNet
from chgnet.model.dynamics import StructOptimizer
from ase.io import read
import random
import warnings

warnings.filterwarnings('ignore')

def get_base_structure():
    s = Structure.from_spacegroup(
        'Ia-3d',
        Lattice.cubic(12.98),
        ['Li', 'Li', 'La', 'Zr', 'O'],
        [
            [0.375, 0.0, 0.25],
            [0.098, 0.686, 0.577],
            [0.125, 0.0, 0.25],
            [0, 0, 0],
            [0.282, 0.096, 0.194]
        ]
    )
    li_indices = [i for i, site in enumerate(s) if site.species_string == 'Li']
    li_96h_indices = li_indices[24:]
    random.seed(42)
    to_delete = random.sample(li_96h_indices, 64)
    s.remove_sites(to_delete)
    return s

def build_substituted_structure(base_structure, formula):
    atoms = AseAtomsAdaptor.get_atoms(base_structure)
    syms  = list(atoms.get_chemical_symbols())
    li_idx = [i for i, s in enumerate(syms) if s == "Li"]
    la_idx = [i for i, s in enumerate(syms) if s == "La"]
    zr_idx = [i for i, s in enumerate(syms) if s == "Zr"]

    dopants = formula
    if "Al" in dopants and len(li_idx) > 0: syms[li_idx[0]] = "Al"
    if "Ga" in dopants and len(li_idx) > 1: syms[li_idx[1]] = "Ga"
    if "Nb" in dopants and len(zr_idx) > 0: syms[zr_idx[0]] = "Nb"
    if "Ta" in dopants and len(zr_idx) > 1: syms[zr_idx[1]] = "Ta"
    if "Gd" in dopants and len(la_idx) > 0: syms[la_idx[0]] = "Gd"
    if "Mg" in dopants and len(li_idx) > 2: syms[li_idx[2]] = "Mg"
    if "Sr" in dopants and len(la_idx) > 1: syms[la_idx[1]] = "Sr"
    if "Y"  in dopants and "Yb" not in dopants and len(la_idx) > 3: syms[la_idx[3]] = "Y"
    if "Hf" in dopants and len(zr_idx) > 2: syms[zr_idx[2]] = "Hf"
    if "W"  in dopants and len(zr_idx) > 3: syms[zr_idx[3]] = "W"
    if "Sb" in dopants and len(zr_idx) > 4: syms[zr_idx[4]] = "Sb"
    if "Fe" in dopants and len(li_idx) > 4: syms[li_idx[4]] = "Fe"
    if "Zn" in dopants and len(li_idx) > 5: syms[li_idx[5]] = "Zn"
    if "Ti" in dopants and len(zr_idx) > 5: syms[zr_idx[5]] = "Ti"
    if "Sn" in dopants and len(zr_idx) > 6: syms[zr_idx[6]] = "Sn"
    
    # Missing from original evaluate_candidates_chgnet.py substitution logic!
    if "Ba" in dopants and len(la_idx) > 2: syms[la_idx[2]] = "Ba"
    if "Ca" in dopants and len(la_idx) > 3: syms[la_idx[3]] = "Ca"

    atoms.set_chemical_symbols(syms)
    return AseAtomsAdaptor.get_structure(atoms)

def main():
    repo_path = Path("d:/doped_2")
    all_cifs = list(repo_path.rglob("*.cif"))
    
    incorrect_cifs = []
    
    print("Scanning repository for corrupted CIFs...")
    for cif in all_cifs:
        try:
            atoms = read(str(cif))
            num_atoms = len(atoms)
            if num_atoms == 0:
                continue
            vol = atoms.get_volume()
            vol_per_atom = vol / num_atoms
            if not (9.0 <= vol_per_atom <= 16.0):
                incorrect_cifs.append((cif, vol_per_atom))
        except Exception:
            pass
            
    if not incorrect_cifs:
        print("No corrupted CIFs found! Everything looks good.")
        return
        
    print(f"Found {len(incorrect_cifs)} corrupted CIFs. Rebuilding...")
    
    print("Loading CHGNet...", flush=True)
    try:
        calculator = CHGNet.load()
        optimizer = StructOptimizer(model=calculator)
    except Exception as e:
        print(f"Error loading CHGNet: {e}")
        return

    print("Building base structure...", flush=True)
    base_structure = get_base_structure()
    
    fixed_count = 0
    for cif_path, old_vpa in incorrect_cifs:
        formula = cif_path.name.replace("_evaluated.cif", "").replace(".cif", "")
        print(f"\n[{fixed_count+1}/{len(incorrect_cifs)}] Fixing {cif_path.name} (was {old_vpa:.2f} A^3/atom)...", flush=True)
        
        try:
            modified_struct = build_substituted_structure(base_structure, formula)
            
            # Short relaxation (10 steps) to avoid memory crash
            res1 = optimizer.relax(modified_struct, relax_cell=False, fmax=0.5, steps=10, verbose=False)
            pos_relaxed = res1['final_structure']
            
            res2 = optimizer.relax(pos_relaxed, relax_cell=True, fmax=0.5, steps=10, verbose=False)
            final_struct = res2['final_structure']
            
            vol_per_atom = final_struct.volume / len(final_struct)
            print(f"  -> Fixed vol/atom: {vol_per_atom:.2f} A^3", flush=True)
            
            final_struct.to(fmt="cif", filename=str(cif_path))
            fixed_count += 1
            
        except Exception as e:
            print(f"Error processing {formula}: {e}", flush=True)
            
    print(f"\nDone! Successfully fixed {fixed_count}/{len(incorrect_cifs)} corrupted CIFs.")

if __name__ == "__main__":
    main()
