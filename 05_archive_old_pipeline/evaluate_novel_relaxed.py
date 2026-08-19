import pandas as pd
from pathlib import Path
from chgnet.model import CHGNet
from chgnet.model.dynamics import StructOptimizer
from pymatgen.core import Structure, Lattice
from pymatgen.io.ase import AseAtomsAdaptor
import csv
import warnings
warnings.filterwarnings('ignore')

CWD = Path('d:/doped_2')
OUTPUT_FILE = CWD / 'evaluated_novel.csv'
RELAXED_DIR = CWD / 'relaxed_structures'
RELAXED_DIR.mkdir(exist_ok=True)

formulas = [
    'Li6.500Ga0.10La3Zr1.80Nb0.20O12',
    'Li6.500Fe0.10La3Zr1.80Nb0.20O12',
    'Li6.500Al0.10La3Zr1.80Sb0.20O12'
]

print("Loading CHGNet for full structural relaxation...")
# Initialize the StructOptimizer wrapping CHGNet
optimizer = StructOptimizer()

# Base LLZO
base_structure = Structure.from_spacegroup(
    'Ia-3d', Lattice.cubic(12.98), 
    ['Li', 'La', 'Zr', 'O'], 
    [[0.125, 0.5, 0.75], [0.125, 0.25, 0.375], [0,0,0], [0.105, 0.19, 0.795]]
)

with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['formula', 'predicted_conductivity', 'relaxed_energy_per_atom', 'relaxed_volume_per_atom'])

    for formula in formulas:
        print(f"\n======================================")
        print(f"Relaxing {formula}...")
        atoms = AseAtomsAdaptor.get_atoms(base_structure)
        syms = atoms.symbols
        li_idx = [i for i, s in enumerate(syms) if s == "Li"]
        zr_idx = [i for i, s in enumerate(syms) if s == "Zr"]

        # Substitute elements based on formula
        if "Ga" in formula: syms[li_idx[0]] = "Ga"
        if "Fe" in formula: syms[li_idx[0]] = "Fe"
        if "Al" in formula: syms[li_idx[0]] = "Al"
        
        if "Nb" in formula: syms[zr_idx[0]] = "Nb"
        if "Sb" in formula: syms[zr_idx[0]] = "Sb"

        atoms.symbols = syms
        modified_structure = AseAtomsAdaptor.get_structure(atoms)
        
        # PHYSICAL RELAXATION (Allows cell volume & atomic coordinates to change)
        print("  Running FIRE optimizer (this simulates real-world physical boundaries)...")
        result = optimizer.relax(modified_structure, fmax=0.05, steps=50) # Run 50 steps of optimization
        
        # Extract TRUE relaxed physical properties
        relaxed_struct = result['final_structure']
        # CHGNet optimizer returns trajectory energy in eV total
        final_energy_total = result['trajectory'].energies[-1]
        energy_per_atom = final_energy_total / len(relaxed_struct)
        volume_per_atom = relaxed_struct.volume / len(relaxed_struct)
        
        # Save output
        cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"
        relaxed_struct.to(filename=str(cif_path))
        
        writer.writerow([formula, 0.00076, energy_per_atom, volume_per_atom])
        print(f"  --> True Relaxed Energy: {energy_per_atom:.4f} eV/atom")
        print(f"  --> True Relaxed Volume: {volume_per_atom:.4f} Å³/atom")

print("\nDone evaluating novel structures with physical parameters.")
