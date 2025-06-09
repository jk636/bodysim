import trimesh
import pyvista as pv # Keep for visualization methods
import json
import os
import numpy as np
from typing import Dict, List, Optional, Any # Added Any

# Removed pydicom import, should be in utils or services
from ..utils.mesh_utils import voxelize_mesh # Integrated voxelization

# -- Organ class with error handling, voxelization, interpolation, substructures --

class Organ:
    def __init__(self, name: str, mesh_file: Optional[str] = None):
        self.name = name
        self.mesh_file: Optional[str] = mesh_file # Explicitly typing mesh_file
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
        self.mesh_file = mesh_file  # Store/update the mesh file path
        self.mesh = None # Initialize mesh to None

        if not os.path.isfile(mesh_file):
            print(f"[ERROR] Organ {self.name}: Mesh file not found: {mesh_file}")
            return

        try:
            mesh_candidate = trimesh.load(mesh_file)

            # Handle trimesh.Scene by attempting to consolidate it
            if isinstance(mesh_candidate, trimesh.Scene):
                print(f"[INFO] Organ {self.name}: Loaded a trimesh.Scene from {mesh_file}.")
                if not mesh_candidate.geometry: # Check if scene has any geometries
                    print(f"[ERROR] Organ {self.name}: Scene from {mesh_file} contains no geometries. No mesh loaded.")
                    return
                try:
                    # Consolidate all geometries in the scene into a single Trimesh object
                    mesh_candidate = mesh_candidate.dump(concatenate=True)
                    if not isinstance(mesh_candidate, trimesh.Trimesh):
                        # This case might happen if dump results in an empty scene or some other non-Trimesh object
                        print(f"[ERROR] Organ {self.name}: Failed to consolidate scene from {mesh_file} into a single Trimesh object. Result type: {type(mesh_candidate)}.")
                        return
                    print(f"[INFO] Organ {self.name}: Scene consolidated into a single mesh.")
                except Exception as e_scene:
                    print(f"[ERROR] Organ {self.name}: Error consolidating scene from {mesh_file}: {str(e_scene)}")
                    return

            # Check if the loaded or consolidated mesh_candidate is a valid Trimesh and not empty
            if not isinstance(mesh_candidate, trimesh.Trimesh) or mesh_candidate.is_empty:
                is_empty_val = getattr(mesh_candidate, 'is_empty', 'N/A (not a Trimesh object or no is_empty attr)')
                if isinstance(mesh_candidate, trimesh.Trimesh): # If it's Trimesh, is_empty is reliable
                    is_empty_val = mesh_candidate.is_empty
                print(f"[ERROR] Organ {self.name}: Loaded content from {mesh_file} is not a valid non-empty mesh (Type: {type(mesh_candidate)}, Empty: {is_empty_val}). No mesh loaded.")
                return

            # Process the mesh (e.g., to ensure manifold, fix normals, etc.)
            # trimesh.process() returns a new mesh object
            print(f"[INFO] Organ {self.name}: Attempting to process mesh (original from {mesh_file})...")
            processed_mesh = mesh_candidate.process()

            if not isinstance(processed_mesh, trimesh.Trimesh) or processed_mesh.is_empty:
                # Log details of the original mesh_candidate if processing fails to produce a valid mesh
                orig_type = type(mesh_candidate)
                orig_empty = mesh_candidate.is_empty if isinstance(mesh_candidate, trimesh.Trimesh) else 'N/A'
                orig_verts = len(mesh_candidate.vertices) if hasattr(mesh_candidate, 'vertices') else 'N/A'
                orig_faces = len(mesh_candidate.faces) if hasattr(mesh_candidate, 'faces') else 'N/A'
                print(f"[WARN] Organ {self.name}: Processing mesh from {mesh_file} resulted in an invalid or empty mesh. Original (pre-process) mesh was (Type: {orig_type}, Empty: {orig_empty}, Vertices: {orig_verts}, Faces: {orig_faces}). Setting mesh to None as processed version is unusable.")
                return # self.mesh remains None as initialized or set previously

            self.mesh = processed_mesh
            print(f"[INFO] Organ {self.name}: Successfully loaded and processed mesh from {mesh_file}.")
            print(f"[INFO] Organ {self.name}: Mesh details: Vertices={len(self.mesh.vertices)}, Faces={len(self.mesh.faces)}, Watertight={self.mesh.is_watertight}")

        except Exception as e:
            # Catch any other exceptions during loading or initial processing
            print(f"[ERROR] Organ {self.name}: Exception loading/processing mesh {mesh_file}: {str(e)}")
            self.mesh = None # Ensure mesh is None on any error during this process

    def add_sub_organ(self, sub_organ: 'Organ'):
        self.sub_organs[sub_organ.name] = sub_organ

    def remove_sub_organ(self, name: str):
        if name in self.sub_organs:
            del self.sub_organs[name]

    def voxelize_mesh(self):
        """
        Convert the mesh into a 3D voxel grid using the utility function.
        Stores the result in self.voxel_grid.
        """
        if self.mesh is None:
            print(f"[WARN] Cannot voxelize {self.name}: no mesh loaded.")
            self.voxel_grid = None
            return

        print(f"[INFO] Voxelizing mesh for {self.name} with resolution {self.voxel_resolution}...")
        try:
            # Assuming voxelize_mesh from mesh_utils takes mesh and pitch (resolution)
            self.voxel_grid = voxelize_mesh(self.mesh, pitch=self.voxel_resolution)
            if self.voxel_grid is not None:
                print(f"[INFO] Voxelization complete for {self.name}. Grid shape: {self.voxel_grid.shape}")
            else:
                # Voxelize_mesh might return None on failure
                print(f"[ERROR] Voxelization failed for {self.name} (returned None).")
        except Exception as e:
            print(f"[ERROR] Exception during voxelization for {self.name}: {str(e)}")
            self.voxel_grid = None

    def simplify_mesh(self, target_face_count: int) -> bool:
        # Ensure self.mesh exists and is a trimesh.Trimesh object
        if not isinstance(self.mesh, trimesh.Trimesh) or self.mesh.is_empty:
            print(f"[WARN] Organ {self.name}: No valid mesh to simplify.")
            return False

        # Validate target_face_count
        if not isinstance(target_face_count, int) or target_face_count <= 0:
            print(f"[ERROR] Organ {self.name}: target_face_count must be a positive integer. Got {target_face_count}.")
            return False

        original_face_count = len(self.mesh.faces)
        print(f"[INFO] Organ {self.name}: Attempting to simplify mesh from {original_face_count} faces to {target_face_count} faces.")

        # If target is same or more than current, no simplification needed
        if target_face_count >= original_face_count:
            print(f"[INFO] Organ {self.name}: Target face count ({target_face_count}) is >= current face count ({original_face_count}). No simplification performed.")
            return True

        try:
            # trimesh.Trimesh.simplify_quadric_decimation returns a new mesh
            simplified_mesh = self.mesh.simplify_quadric_decimation(face_count=target_face_count)

            if simplified_mesh is None or simplified_mesh.is_empty: # Check if simplification failed or resulted in empty
                print(f"[WARN] Organ {self.name}: Simplification to {target_face_count} faces resulted in an empty or None mesh. Original mesh retained.")
                return False # Simplification technically failed to produce a valid result

            self.mesh = simplified_mesh # Update the organ's mesh
            new_face_count = len(self.mesh.faces) # Should be close to target_face_count
            print(f"[INFO] Organ {self.name}: Mesh simplified successfully. New face count: {new_face_count} (Target was {target_face_count}).")
            return True
        except Exception as e:
            # Log the error, self.mesh remains the original mesh
            print(f"[ERROR] Organ {self.name}: Error during mesh simplification using trimesh: {str(e)}")
            return False

    def interpolate_properties(self, point_xyz: Optional[Any] = None) -> Dict[str, float]:
        """
        Returns the global physical properties of the organ.
        The 'point_xyz' argument is ignored in this simplified version.

        Args:
            point_xyz (Any, optional): Coordinates (x, y, z). Currently unused.

        Returns:
            dict: A dictionary of the organ's physical properties.
        """
        # In a future implementation, this could use point_xyz to return
        # spatially varying properties or properties of sub-organs.
        # For now, ensure properties are float for consistency.
        return {
            "magnetic_susceptibility": float(self.magnetic_susceptibility),
            "permeability": float(self.permeability),
            "permittivity": float(self.permittivity),
            "conductivity": float(self.conductivity),
            "elasticity": float(self.elasticity),
            "density": float(self.density),
        }

    def visualize(self, show_suborgans: bool = True):
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "mesh_file": self.mesh_file,
            "voxel_resolution": self.voxel_resolution,
            "properties": self.interpolate_properties(), # Uses the method to get all props
            "sub_organs": {name: sub.to_dict() for name, sub in self.sub_organs.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Organ':
        organ = cls(data["name"], data.get("mesh_file")) # mesh_file can be None

        # Set properties directly using dictionary get for safety
        props = data.get("properties", {})
        organ.magnetic_susceptibility = float(props.get("magnetic_susceptibility", 0.0))
        organ.permeability = float(props.get("permeability", 1.0))
        organ.permittivity = float(props.get("permittivity", 1.0))
        organ.conductivity = float(props.get("conductivity", 0.0))
        organ.elasticity = float(props.get("elasticity", 0.0))
        organ.density = float(props.get("density", 1000.0)) # Ensure float

        organ.voxel_resolution = float(data.get("voxel_resolution", 1.0))

        # Recursively add sub-organs
        for sub_name, sub_data in data.get("sub_organs", {}).items():
            if isinstance(sub_data, dict): # Basic check for valid sub_organ data
                organ.add_sub_organ(Organ.from_dict(sub_data))
            else:
                print(f"[WARN] Invalid sub_organ data for {sub_name} in {data['name']}. Expected dict, got {type(sub_data)}.")
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
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[INFO] Saved human body model to {filename}")
        except IOError as e:
            print(f"[ERROR] Could not write to file {filename}: {str(e)}")
        except Exception as e: # Catch any other unexpected errors during save
            print(f"[ERROR] An unexpected error occurred while saving to {filename}: {str(e)}")

    def load_from_file(self, filename: str):
        if not os.path.isfile(filename):
            print(f"[ERROR] Model file not found: {filename}")
            self.organs = {} # Ensure organs is empty if file not found
            return
        try:
            with open(filename, "r") as f:
                data = json.load(f)
            self.organs = {} # Clear existing organs before loading
            for name, organ_data in data.items():
                if isinstance(organ_data, dict): # Basic check for valid organ data
                    self.organs[name] = Organ.from_dict(organ_data)
                else:
                    print(f"[WARN] Invalid data for organ {name} in {filename}. Expected dict, got {type(organ_data)}.")
            print(f"[INFO] Loaded human body model from {filename}")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in model file {filename}: {str(e)}")
            self.organs = {} # Ensure organs is empty on error
        except IOError as e:
            print(f"[ERROR] Could not read file {filename}: {str(e)}")
            self.organs = {} # Ensure organs is empty on error
        except Exception as e: # Catch any other unexpected errors during load
            print(f"[ERROR] An unexpected error occurred while loading from {filename}: {str(e)}")
            self.organs = {}


# -- DICOM import stub removed from here --
# This functionality should reside in `utils/dicom_utils.py` or a dedicated service.


# -- Physics solver integration placeholder --

class PhysicsSolverInterface: # This can stay as a conceptual placeholder
    def __init__(self, human_body: HumanBody):
        self.body = human_body

    def run_fdtd_simulation(self):
        """
        Run FDTD or other physics simulation using voxelized meshes.
        TODO: Implement integration with FDTD solver.
        """
        print("[INFO] Running physics simulation... (stub)")

# Removed PyQt5 UI scaffold (OrganEditorUI and related imports)
# Removed __main__ block that used the UI.

# Example Usage (Optional - can be added for testing if needed, kept minimal for now)
# if __name__ == "__main__":
#     # Create a dummy mesh file for testing if it doesn't exist
#     dummy_mesh_path = "dummy_heart.obj"
#     if not os.path.exists(dummy_mesh_path):
#         try:
#             # Create a simple cube mesh and save it
#             mesh = trimesh.creation.box(extents=(1, 1, 1))
#             mesh.export(dummy_mesh_path)
#             print(f"Created dummy mesh file: {dummy_mesh_path}")
#         except Exception as e:
#             print(f"Could not create dummy mesh file: {e}")

#     heart = Organ(name="Heart", mesh_file=dummy_mesh_path if os.path.exists(dummy_mesh_path) else None)
#     if heart.mesh_file:
#         heart.load_mesh(heart.mesh_file)

#     heart.magnetic_susceptibility = -9.05e-6
#     heart.voxel_resolution = 0.5 # mm

#     if heart.mesh:
#         heart.voxelize_mesh()
#         if heart.voxel_grid is not None:
#             print(f"Heart voxel grid shape: {heart.voxel_grid.shape}")
#     else:
#         print(f"Skipping voxelization for {heart.name} as mesh is not loaded.")

#     print(f"Heart properties: {heart.interpolate_properties()}")

#     body = HumanBody()
#     body.add_organ(heart)
#     model_path = "test_human_body_model.json"
#     body.save_to_file(model_path)
#     new_body = HumanBody()
#     new_body.load_from_file(model_path)
#     if "Heart" in new_body.organs:
#         print(f"Loaded {new_body.organs['Heart'].name} from file.")
#     if os.path.exists(dummy_mesh_path):
#         os.remove(dummy_mesh_path)
#     if os.path.exists(model_path):
#         os.remove(model_path)
