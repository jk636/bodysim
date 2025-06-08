import trimesh
import numpy as np

def voxelize_mesh(mesh: trimesh.Trimesh, pitch=1.0):
    """
    Voxelizes the mesh into a 3D boolean numpy array.
    pitch = voxel size in the same unit as mesh coordinates.
    """
    # Create voxelized mesh (using trimesh.voxel)
    try:
        voxelized = mesh.voxelized(pitch)
        matrix = voxelized.matrix.astype(bool)
        print(f"Voxelization complete: shape={matrix.shape}")
        return matrix
    except Exception as e:
        print(f"Voxelization failed: {e}")
        return None

# Example:
# mesh = trimesh.load('path/to/your_mesh.obj')
# voxels = voxelize_mesh(mesh, pitch=1.0)
# print(voxels.shape)
