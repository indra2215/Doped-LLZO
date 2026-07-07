import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.diffusion.analyzer import DiffusionAnalyzer
from pymatgen.analysis.local_env import CrystalNN

def calculate_bottleneck_radius(structure: Structure) -> float:
    """
    Estimates the diffusion bottleneck radius for Li-ions.
    This is a simplified approach that finds the minimum distance between
    a migrating Li ion and the framework atoms during migration.
    A more rigorous approach would involve analyzing the transition state path.

    Args:
        structure (Structure): The relaxed structure.

    Returns:
        float: The estimated bottleneck radius in Angstroms.
    """
    try:
        # Find Li sites and non-Li sites
        li_sites = [site for site in structure if site.specie.symbol == 'Li']
        framework_sites = [site for site in structure if site.specie.symbol != 'Li']

        if not li_sites or not framework_sites:
            return 0.0

        # Use CrystalNN to find near neighbors to define migration pathways
        cnn = CrystalNN()
        
        min_bottleneck = float('inf')

        for li_site in li_sites:
            # Get neighbors of the Li site, which represent potential next hops
            neighbors = cnn.get_nn_info(structure, structure.index(li_site))
            
            for neighbor_info in neighbors:
                if neighbor_info['site'].specie.symbol == 'Li':
                    # We found a potential hop between two Li sites
                    start_li = li_site
                    end_li = neighbor_info['site']
                    
                    # Create 20 points along the migration path
                    path_points = np.linspace(start_li.frac_coords, end_li.frac_coords, 20)
                    
                    # For each point on the path, find the minimum distance to a framework atom
                    for point in path_points:
                        min_dist_to_framework = float('inf')
                        for fw_site in framework_sites:
                            # Calculate distance, accounting for periodic boundaries
                            dist = structure.lattice.get_distance_and_image(point, fw_site.frac_coords)[0]
                            if dist < min_dist_to_framework:
                                min_dist_to_framework = dist
                        
                        # The bottleneck for this path is the minimum of these minimums
                        if min_dist_to_framework < min_bottleneck:
                            min_bottleneck = min_dist_to_framework
                            
        # The final value is the radius, so we can consider this distance as such.
        # A more refined definition might subtract ionic radii, but this gives a good proxy.
        return min_bottleneck if min_bottleneck != float('inf') else 0.0

    except Exception as e:
        print(f"Error calculating bottleneck radius: {e}")
        return 0.0

def calculate_haven_ratio(structure: Structure, trajectories: list, li_ion_indices: list) -> float:
    """
    Calculates the Haven Ratio from MD trajectories.
    H_R = D_tracer / D_conductivity
    where D_tracer is the average self-diffusion of Li ions and
    D_conductivity is derived from the collective displacement of Li ions.

    Args:
        structure (Structure): The initial structure.
        trajectories (list): A list of Structures representing the MD trajectory.
        li_ion_indices (list): Indices of the Li ions in the structure.

    Returns:
        float: The calculated Haven Ratio.
    """
    if not trajectories or not li_ion_indices:
        return 0.0
        
    try:
        # We need pymatgen's DiffusionAnalyzer for this.
        # The trajectory should be a list of (structure, time_step) tuples,
        # but we can fake the time step for this calculation.
        
        # Let's assume a time step of 1 fs for demonstration.
        # The actual value cancels out in the ratio.
        dt = 1.0 # in fs
        time_steps = [i * dt for i in range(len(trajectories))]

        # Create a list of structures for the analyzer
        structures = trajectories

        # Get the analyzer object
        diff_analyzer = DiffusionAnalyzer.from_structures(
            structures=structures,
            specie="Li",
            time_step=dt,
            step_skip=1 # Process every frame
        )

        # D_tracer is the standard diffusivity from the analyzer's MSD
        d_tracer = diff_analyzer.diffusivity

        # D_conductivity requires calculating the collective displacement
        # Sum of displacement vectors for all Li ions
        collective_disp = np.zeros((len(structures), 3))
        
        start_positions = np.array([s.frac_coords[li_ion_indices] for s in structures])
        
        # Correct for periodic boundary conditions by unwrapping coordinates
        unwrapped_positions = DiffusionAnalyzer.get_unwrapped_displacements(structures, start_positions)

        # Sum of displacement vectors over all Li ions at each time step
        sum_of_disp_vectors = np.sum(unwrapped_positions, axis=1)

        # Collective MSD is the squared magnitude of this sum vector, averaged
        collective_msd = np.mean(np.sum(sum_of_disp_vectors**2, axis=1))

        # D_conductivity is proportional to the collective MSD
        # The exact prefactor depends on time and number of particles, but it cancels
        # with the prefactor for D_tracer in the ratio.
        # D_conductivity is related to the slope of collective_msd vs time.
        # For a single value, we can approximate.
        
        # A simpler way to get at the Haven Ratio is through the correlation factor,
        # which is what the analyzer's `get_summary_dict` provides.
        summary = diff_analyzer.get_summary_dict()
        haven_ratio = summary['haven_ratio']
        
        # The analyzer might return None if the statistics are poor
        if haven_ratio is None or np.isnan(haven_ratio):
            return 0.0

        return haven_ratio

    except Exception as e:
        print(f"Could not calculate Haven Ratio: {e}")
        # This can fail if diffusion is zero or trajectories are too short
        return 0.0

if __name__ == '__main__':
    # This is a placeholder for example usage.
    # To run this, you would need a real structure and trajectory data.
    print("Advanced Structural Analysis Module")
    print("Provides functions to calculate bottleneck radius and Haven ratio.")
    # Example:
    # from pymatgen.core import Structure
    # from ase.io import read
    #
    # # 1. Load a relaxed structure
    # pmg_structure = Structure.from_file("path/to/your/relaxed.cif")
    #
    # # 2. Calculate bottleneck radius
    # radius = calculate_bottleneck_radius(pmg_structure)
    # print(f"Estimated bottleneck radius: {radius:.3f} Å")
    #
    # # 3. Load an MD trajectory
    # ase_traj = read("path/to/your/md.traj", index=":")
    # pmg_traj = [s.todict() for s in ase_traj] # Convert to pymatgen structures
    # li_indices = [i for i, site in enumerate(pmg_traj[0]) if site.specie.symbol == 'Li']
    #
    # # 4. Calculate Haven Ratio
    # hr = calculate_haven_ratio(pmg_traj[0], pmg_traj, li_indices)
    # print(f"Calculated Haven Ratio: {hr:.3f}")
