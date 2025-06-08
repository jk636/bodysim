import os
import numpy as np
import pydicom
from skimage import measure
import trimesh

def load_dicom_volume(dicom_folder: str) -> np.ndarray:
    """
    Load a DICOM series from a folder and return a 3D numpy array volume.
    Assumes all slices in the folder belong to the same volume.
    """
    files = [pydicom.dcmread(os.path.join(dicom_folder, f)) 
             for f in sorted(os.listdir(dicom_folder)) if f.endswith('.dcm')]
    
    slices = sorted(files, key=lambda s: float(s.ImagePositionPatient[2]))
    volume = np.stack([s.pixel_array for s in slices], axis=-1)
    print(f"Loaded DICOM volume with shape {volume.shape}")
    return volume

def volume_to_mesh(volume: np.ndarray, threshold=300):
    """
    Convert volume to mesh using marching cubes.
    threshold controls isosurface level (depends on modality).
    """
    verts, faces, normals, values = measure.marching_cubes(volume, level=threshold)
    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    print(f"Created mesh from volume: verts={len(verts)}, faces={len(faces)}")
    return mesh

# Example usage:
# volume = load_dicom_volume('/path/to/dicom_folder')
# mesh = volume_to_mesh(volume, threshold=300)
# mesh.export('output_mesh.obj')
