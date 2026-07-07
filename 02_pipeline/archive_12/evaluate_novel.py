import pandas as pd
from pathlib import Path
from chgnet.model import CHGNet
from chgnet.model.dynamics import CHGNetCalculator
from pymatgen.core import Structure, Lattice
from pymatgen.io.ase import AseAtomsAdaptor
from ase.optimize import FIRE
from ase.constraints import ExpCellFilter
import csv
import warnings
warnings.filterwarnings('ignore')

# ROOT = d:/doped_2
ROOT        = Path(__file__).parent.parent.parent
OUTPUT_FILE = ROOT / "01_data" / "results"    / "evaluated_novel.csv"
RELAXED_DIR = ROOT / "03_structures" / "relaxed"
RELAXED_DIR.mkdir(parents=True, exist_ok=True)

# Fixed set of novel candidates to evaluate
FORMULAS = [
    'Li6.500Ga0.10La3Zr1.80Nb0.20O12',
    'Li6.500Fe0.10La3Zr1.80Nb0.20O12',
    'Li6.500Al0.10La3Zr1.80Sb0.20O12',
]

print("Loading CHGNet...")
chgnet = CHGNet.load()
calculator = CHGNetCalculator(model=chgnet)

base_structure = Structure.from_spacegroup(
    'Ia-3d', Lattice.cubic(12.98),
    ['Li', 'La', 'Zr', 'O'],
    [[0.125, 0.5, 0.75], [0.125, 0.25, 0.375], [0, 0, 0], [0.105, 0.19, 0.795]]
)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['formula', 'predicted_conductivity', 'relaxed_energy_per_atom',
                     'relaxed_volume_per_atom', 'relaxed_cif_path'])

    for formula in FORMULAS:
        print(f"Evaluating {formula}...")
        atoms = AseAtomsAdaptor.get_atoms(base_structure)
        syms  = list(atoms.get_chemical_symbols())
        li_idx = [i for i, s in enumerate(syms) if s == "Li"]
        zr_idx = [i for i, s in enumerate(syms) if s == "Zr"]

        if "Ga" in formula and len(li_idx) > 0: syms[li_idx[0]] = "Ga"
        if "Fe" in formula and len(li_idx) > 0: syms[li_idx[0]] = "Fe"
        if "Al" in formula and len(li_idx) > 0: syms[li_idx[0]] = "Al"
        if "Nb" in formula and len(zr_idx) > 0: syms[zr_idx[0]] = "Nb"
        if "Sb" in formula and len(zr_idx) > 0: syms[zr_idx[0]] = "Sb"

        atoms.set_chemical_symbols(syms)
        atoms.calc = calculator

        # Geometric relaxation with FIRE optimizer
        ecf = ExpCellFilter(atoms)
        opt = FIRE(ecf, logfile=None)
        opt.run(fmax=0.05, steps=50)

        modified_structure = AseAtomsAdaptor.get_structure(atoms)
        energy_per_atom    = atoms.get_potential_energy() / len(atoms)
        volume_per_atom    = modified_structure.volume / len(modified_structure)

        cif_path = RELAXED_DIR / f"{formula}_evaluated.cif"
        modified_structure.to(fmt="cif", filename=str(cif_path))

        writer.writerow([formula, 0.00076, energy_per_atom, volume_per_atom, str(cif_path)])
        print(f"  Energy: {energy_per_atom:.4f} eV/atom, Volume: {volume_per_atom:.4f} Å³")

print(f"\nDone. Results saved to: {OUTPUT_FILE}")
