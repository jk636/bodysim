import trimesh
import pyvista as pv


class Organ:
    def __init__(self, name, mesh_file=None):
        self.name = name
        self.mesh_file = mesh_file
        self.mesh = None

        # Electromagnetic properties (placeholders)
        self.magnetic_susceptibility = 0.0
        self.permeability = 1.0
        self.permittivity = 1.0
        self.conductivity = 0.0

        # Mechanical properties (placeholders)
        self.elasticity = 0.0
        self.density = 1000

        if mesh_file:
            self.load_mesh(mesh_file)

    def load_mesh(self, mesh_file):
        try:
            self.mesh = trimesh.load(mesh_file)
            print(f"[INFO] Loaded mesh for {self.name} from {mesh_file}")
        except Exception as e:
            print(f"[ERROR] Failed to load mesh {mesh_file}: {e}")
            self.mesh = None

    def get_properties(self):
        return {
            "magnetic_susceptibility": self.magnetic_susceptibility,
            "permeability": self.permeability,
            "permittivity": self.permittivity,
            "conductivity": self.conductivity,
            "elasticity": self.elasticity,
            "density": self.density,
        }

    def visualize(self):
        if self.mesh is None:
            print(f"[WARN] No mesh loaded for {self.name}, cannot visualize.")
            return

        # Convert trimesh mesh to pyvista mesh
        pv_mesh = pv.wrap(self.mesh)

        plotter = pv.Plotter(title=f"{self.name} Visualization")
        plotter.add_mesh(pv_mesh, color="lightcoral", opacity=0.7)
        plotter.show()


class Brain(Organ):
    def __init__(self, mesh_file=None):
        super().__init__("Brain", mesh_file)
        self.magnetic_susceptibility = -9e-6
        self.permeability = 1.00001
        self.permittivity = 50
        self.conductivity = 0.7
        self.elasticity = 2000
        self.density = 1040


class HumanBody:
    def __init__(self):
        self.organs = {}

    def add_organ(self, organ: Organ):
        self.organs[organ.name] = organ

    def remove_organ(self, organ_name: str):
        if organ_name in self.organs:
            del self.organs[organ_name]

    def visualize(self):
        plotter = pv.Plotter(title="Human Body Visualization")

        added = False
        for organ in self.organs.values():
            if organ.mesh is not None:
                pv_mesh = pv.wrap(organ.mesh)
                plotter.add_mesh(pv_mesh, opacity=0.5, label=organ.name)
                added = True

        if not added:
            print("[WARN] No organ meshes to display!")
            return

        plotter.add_legend()
        plotter.show()


if __name__ == "__main__":
    # Example usage
    body = HumanBody()

    # Path to example mesh files (replace with your own)
    brain_mesh_path = "example_meshes/brain.obj"

    brain = Brain(brain_mesh_path)
    body.add_organ(brain)

    # Visualize individual organ
    brain.visualize()

    # Visualize entire body (currently only brain)
    body.visualize()
