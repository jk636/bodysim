import trimesh
import pyvista as pv
import json
import os
import numpy as np
from typing import Dict, List, Optional

# For DICOM (conceptual placeholder)
try:
    import pydicom
except ImportError:
    pydicom = None

# -- Organ class with error handling, voxelization, interpolation, substructures --

class Organ:
    def __init__(self, name: str, mesh_file: Optional[str] = None):
        self.name = name
        self.mesh_file = mesh_file
        self.mesh: Optional[trimesh.Trimesh] = None

        self.sub_organs: Dict[str, 'Organ'] = {}

        # EM and mechanical properties
        self.magnetic_susceptibility = 0.0
        self.permeability = 1.0
        self.permittivity = 1.0
        self.conductivity = 0.0
        self.elasticity = 0.0
        self.density = 1000

        # Mesh voxel grid (placeholder for FDTD mapping)
        self.voxel_grid: Optional[np.ndarray] = None
        self.voxel_resolution = 1.0  # mm per voxel, placeholder

        if mesh_file:
            self.load_mesh(mesh_file)

    def load_mesh(self, mesh_file: str):
        if not os.path.isfile(mesh_file):
            print(f"[ERROR] Mesh file not found: {mesh_file}")
            return
        try:
            self.mesh = trimesh.load(mesh_file)
            if self.mesh.is_empty:
                print(f"[ERROR] Mesh loaded but empty: {mesh_file}")
                self.mesh = None
            else:
                print(f"[INFO] Successfully loaded mesh for {self.name} from {mesh_file}")
        except Exception as e:
            print(f"[ERROR] Exception loading mesh {mesh_file}: {e}")
            self.mesh = None

    def add_sub_organ(self, sub_organ: 'Organ'):
        self.sub_organs[sub_organ.name] = sub_organ

    def remove_sub_organ(self, name: str):
        if name in self.sub_organs:
            del self.sub_organs[name]

    def voxelize_mesh(self):
        """
        Convert the mesh into a 3D voxel grid for FDTD or physics simulation.
        This is a stub, real implementation should convert the mesh geometry into a numpy 3D array,
        marking which voxels are inside the organ.

        Returns:
            None - sets self.voxel_grid
        """
        if self.mesh is None:
            print(f"[WARN] Cannot voxelize {self.name}: no mesh loaded.")
            return

        # Example stub:
        bounds = self.mesh.bounds  # min and max XYZ
        shape = (100, 100, 100)  # Placeholder voxel grid shape

        print(f"[INFO] Voxelizing mesh for {self.name} with shape {shape}")

        # A real implementation would rasterize mesh into voxels here.
        self.voxel_grid = np.zeros(shape, dtype=bool)
        # ... complex voxelization logic goes here ...

    def interpolate_properties(self, point_xyz):
        """
        Interpolate physical properties at a given 3D point based on the mesh and substructures.
        This is a stub to show future capability.

        Args:
            point_xyz (tuple): Coordinates (x, y, z)

        Returns:
            dict: interpolated properties at that point
        """
        # TODO: spatial interpolation based on mesh & sub-organs
        return {
            "magnetic_susceptibility": self.magnetic_susceptibility,
            "permeability": self.permeability,
            "permittivity": self.permittivity,
            "conductivity": self.conductivity,
            "elasticity": self.elasticity,
            "density": self.density,
        }

    def visualize(self, show_suborgans=True):
        if self.mesh is None:
            print(f"[WARN] No mesh for {self.name} to visualize.")
            return

        plotter = pv.Plotter(title=f"{self.name} Visualization")
        pv_mesh = pv.wrap(self.mesh)
        plotter.add_mesh(pv_mesh, color="lightcoral", opacity=0.7)

        if show_suborgans:
            for sub in self.sub_organs.values():
                if sub.mesh:
                    plotter.add_mesh(pv.wrap(sub.mesh), color="lightblue", opacity=0.5)

        plotter.show()

    def to_dict(self):
        return {
            "name": self.name,
            "mesh_file": self.mesh_file,
            "properties": {
                "magnetic_susceptibility": self.magnetic_susceptibility,
                "permeability": self.permeability,
                "permittivity": self.permittivity,
                "conductivity": self.conductivity,
                "elasticity": self.elasticity,
                "density": self.density,
            },
            "sub_organs": {name: sub.to_dict() for name, sub in self.sub_organs.items()},
        }

    @classmethod
    def from_dict(cls, data):
        organ = cls(data["name"], data.get("mesh_file"))
        props = data.get("properties", {})
        for k, v in props.items():
            setattr(organ, k, v)
        for sub_name, sub_data in data.get("sub_organs", {}).items():
            organ.add_sub_organ(Organ.from_dict(sub_data))
        return organ


# -- HumanBody class extended --

class HumanBody:
    def __init__(self):
        self.organs: Dict[str, Organ] = {}

    def add_organ(self, organ: Organ):
        self.organs[organ.name] = organ

    def remove_organ(self, name: str):
        if name in self.organs:
            del self.organs[name]

    def visualize(self):
        plotter = pv.Plotter(title="Human Body Visualization")
        if not self.organs:
            print("[WARN] No organs to visualize.")
            return

        for organ in self.organs.values():
            if organ.mesh:
                plotter.add_mesh(pv.wrap(organ.mesh), opacity=0.5, label=organ.name)

            for sub in organ.sub_organs.values():
                if sub.mesh:
                    plotter.add_mesh(pv.wrap(sub.mesh), opacity=0.3, label=f"{organ.name} - {sub.name}")

        plotter.add_legend()
        plotter.show()

    def save_to_file(self, filename: str):
        data = {name: organ.to_dict() for name, organ in self.organs.items()}
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[INFO] Saved human body model to {filename}")

    def load_from_file(self, filename: str):
        if not os.path.isfile(filename):
            print(f"[ERROR] Model file not found: {filename}")
            return

        with open(filename, "r") as f:
            data = json.load(f)
        self.organs = {name: Organ.from_dict(o) for name, o in data.items()}
        print(f"[INFO] Loaded human body model from {filename}")


# -- DICOM import stub --

def load_dicom_as_mesh(dicom_folder: str) -> Optional[trimesh.Trimesh]:
    if pydicom is None:
        print("[ERROR] pydicom is not installed.")
        return None

    # TODO: Implement actual DICOM volume to mesh conversion here
    print(f"[INFO] Loading DICOM from folder: {dicom_folder}")
    # This might involve segmenting volumes, marching cubes, etc.
    return None


# -- Physics solver integration placeholder --

class PhysicsSolverInterface:
    def __init__(self, human_body: HumanBody):
        self.body = human_body

    def run_fdtd_simulation(self):
        """
        Run FDTD or other physics simulation using voxelized meshes.
        TODO: Implement integration with FDTD solver.
        """
        print("[INFO] Running physics simulation... (stub)")


# -- PyQt5 UI scaffold for organ selection and editing --

try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QPushButton,
        QListWidget, QLabel, QFormLayout, QLineEdit, QMessageBox
    )
except ImportError:
    print("[WARN] PyQt5 is not installed. UI will not work.")


class OrganEditorUI(QWidget):
    def __init__(self, human_body: HumanBody):
        super().__init__()
        self.body = human_body
        self.selected_organ: Optional[Organ] = None

        self.setWindowTitle("Human Body Organ Editor")
        self.resize(600, 400)

        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.organ_selected)
        layout.addWidget(QLabel("Organs:"))
        layout.addWidget(self.list_widget)

        self.form_layout = QFormLayout()
        self.prop_edits = {}
        for prop in ["magnetic_susceptibility", "permeability", "permittivity",
                     "conductivity", "elasticity", "density"]:
            line_edit = QLineEdit()
            self.prop_edits[prop] = line_edit
            self.form_layout.addRow(QLabel(prop.replace("_", " ").title()), line_edit)

        layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
        self.refresh_organ_list()

    def refresh_organ_list(self):
        self.list_widget.clear()
        for organ_name in self.body.organs:
            self.list_widget.addItem(organ_name)

    def organ_selected(self, item):
        name = item.text()
        self.selected_organ = self.body.organs.get(name)
        if not self.selected_organ:
            return

        for prop, editor in self.prop_edits.items():
            val = getattr(self.selected_organ, prop, "")
            editor.setText(str(val))

    def save_changes(self):
        if not self.selected_organ:
            QMessageBox.warning(self, "No organ selected", "Please select an organ first.")
            return
        try:
            for prop, editor in self.prop_edits.items():
                val = float(editor.text())
                setattr(self.selected_organ, prop, val)
            QMessageBox.information(self, "Saved", f"Changes saved for {self.selected_organ.name}.")
        except ValueError:
            QMessageBox.warning(self, "Invalid input", "Please enter valid numeric values.")


if __name__ == "__main__":
