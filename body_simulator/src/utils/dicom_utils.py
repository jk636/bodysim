import os
import numpy as np
import pydicom # For DICOM file reading
from pydicom.errors import InvalidDicomError # Specific pydicom error
from skimage import measure # For marching cubes
import trimesh # For mesh creation
from typing import Optional, List

def load_dicom_volume(dicom_folder: str) -> Optional[np.ndarray]:
    """
    Load a DICOM series from a specified folder and reconstruct a 3D numpy array volume.

    The function sorts slices based on the 'ImagePositionPatient[2]' tag, which represents
    the z-coordinate in the patient coordinate system.

    Args:
        dicom_folder (str): Path to the folder containing DICOM (.dcm) files.

    Returns:
        Optional[np.ndarray]: A 3D NumPy array representing the volume if successful,
                              None otherwise. Logs errors encountered during loading.
    """
    if not os.path.isdir(dicom_folder):
        print(f"[ERROR] DICOM folder not found: {dicom_folder}")
        return None

    dicom_files: List[pydicom.FileDataset] = []
    # List comprehension for initial file scan, converted to lowercase for case-insensitivity
    filenames = sorted([f for f in os.listdir(dicom_folder) if f.lower().endswith('.dcm')])

    if not filenames:
        print(f"[ERROR] No DICOM files (.dcm) found in folder: {dicom_folder}")
        return None

    print(f"[INFO] Found {len(filenames)} .dcm files in {dicom_folder}. Attempting to read...")

    for filename in filenames:
        filepath = os.path.join(dicom_folder, filename)
        try:
            dcm_file = pydicom.dcmread(filepath)
            # Basic check for essential DICOM attributes for volume reconstruction
            if not hasattr(dcm_file, 'ImagePositionPatient') or not hasattr(dcm_file, 'PixelData'):
                print(f"[WARN] Skipping file {filename}: missing required DICOM tags (e.g., ImagePositionPatient, PixelData).")
                continue
            dicom_files.append(dcm_file)
        except InvalidDicomError:
            print(f"[WARN] Invalid DICOM file: {filename}. Skipping.")
        except Exception as e:
            print(f"[WARN] Could not read DICOM file {filename} due to an unexpected error: {str(e)}. Skipping.")

    if not dicom_files:
        print(f"[ERROR] No valid DICOM files could be read from {dicom_folder}.")
        return None

    # Sort slices by the z-coordinate of ImagePositionPatient
    # This assumes slices are parallel and regularly spaced.
    try:
        # Ensure ImagePositionPatient is present and is a list/tuple of sufficient length
        valid_files_for_sorting = []
        for dcm in dicom_files:
            if hasattr(dcm, 'ImagePositionPatient') and isinstance(dcm.ImagePositionPatient, (list, tuple)) and len(dcm.ImagePositionPatient) >= 3:
                valid_files_for_sorting.append(dcm)
            else:
                filename_attr = dcm.filename if hasattr(dcm, 'filename') else 'Unknown'
                print(f"[WARN] File {filename_attr} is missing or has an invalid ImagePositionPatient tag. Excluding from sort.")

        if not valid_files_for_sorting:
            print("[ERROR] No files with valid ImagePositionPatient tag found for sorting.")
            return None

        valid_files_for_sorting.sort(key=lambda s: float(s.ImagePositionPatient[2]))
        dicom_files = valid_files_for_sorting

    except AttributeError: # Should be caught by the check above, but as a fallback
        print("[ERROR] Could not sort DICOM slices: 'ImagePositionPatient' tag missing or invalid in one or more files.")
        return None
    except ValueError as e: # Handles issues with converting ImagePositionPatient[2] to float
        print(f"[ERROR] Could not sort DICOM slices due to invalid value in ImagePositionPatient[2]: {str(e)}")
        return None
    except Exception as e: # Catch-all for other sorting errors
        print(f"[ERROR] Error sorting DICOM slices: {str(e)}")
        return None

    # Stack slices into a 3D volume
    # Ensure all pixel arrays have the same shape for stacking
    if not dicom_files: # Check again after filtering during sort validation
        print("[ERROR] No valid DICOM files remaining after attempting to sort.")
        return None

    first_slice_shape = dicom_files[0].pixel_array.shape
    for dcm_file in dicom_files[1:]: # Start from the second file for comparison
        if dcm_file.pixel_array.shape != first_slice_shape:
            slice_filename = dcm_file.filename if hasattr(dcm_file, 'filename') else 'Unknown'
            print(f"[ERROR] DICOM slices have inconsistent shapes. Expected {first_slice_shape}, got {dcm_file.pixel_array.shape} for {slice_filename}.")
            return None

    try:
        volume = np.stack([s.pixel_array for s in dicom_files], axis=-1)
        print(f"[INFO] Successfully loaded DICOM volume with shape {volume.shape} from {dicom_folder}")
        return volume
    except Exception as e:
        print(f"[ERROR] Failed to stack DICOM slices into volume: {str(e)}")
        return None

def volume_to_mesh(volume: np.ndarray, threshold: float = 300.0, spacing: tuple = (1.0, 1.0, 1.0)) -> Optional[trimesh.Trimesh]:
    """
    Convert a 3D numpy array (volume) to a 3D mesh using the marching cubes algorithm.

    Args:
        volume (np.ndarray): The 3D numpy array representing the image volume.
        threshold (float): The isosurface value to extract from the volume.
                           This value depends on the modality and image intensity range.
        spacing (tuple): Voxel spacing in (x, y, z) dimensions. Affects mesh scale.

    Returns:
        Optional[trimesh.Trimesh]: A trimesh.Trimesh object if successful, None otherwise.
                                   Logs errors encountered during mesh creation.
    """
    if not isinstance(volume, np.ndarray) or volume.ndim != 3:
        vol_ndim = volume.ndim if hasattr(volume, 'ndim') else 'N/A'
        print(f"[ERROR] Invalid input volume: Expected a 3D NumPy array, got {type(volume)} with {vol_ndim} dimensions.")
        return None

    print(f"[INFO] Attempting to create mesh from volume with shape {volume.shape}, threshold={threshold}, spacing={spacing}...")
    try:
        # Marching cubes algorithm to extract surface
        # The 'spacing' argument is crucial for correct mesh scaling if voxels are anisotropic.
        verts, faces, normals, _ = measure.marching_cubes(volume, level=threshold, spacing=spacing)
    except RuntimeError as e: # marching_cubes can raise RuntimeError for certain inputs
        print(f"[ERROR] Marching cubes algorithm failed: {str(e)}. This can happen if the volume is unsuitable (e.g., all flat or contains NaNs/Infs).")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error during marching cubes: {str(e)}")
        return None

    if not isinstance(verts, np.ndarray) or verts.shape[0] == 0 or not isinstance(faces, np.ndarray) or faces.shape[0] == 0 :
        print(f"[WARN] No surface generated from marching cubes (0 vertices or faces). Threshold might be too high/low or volume is empty/flat.")
        return None

    try:
        # Create a trimesh object
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals) # Include normals for better appearance

        # Basic mesh processing (optional, but can improve mesh quality)
        if mesh.vertices.shape[0] > 0 and mesh.faces.shape[0] > 0: # only process if mesh is not empty
            mesh.remove_unreferenced_vertices()
            mesh.remove_degenerate_faces()
        # mesh.fill_holes() # Can be computationally intensive and alter desired geometry
        # mesh.smooth()     # Can alter geometry significantly

        if mesh.is_empty:
             print(f"[WARN] Mesh is empty after basic processing.")
             return None

        print(f"[INFO] Successfully created mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces.")
        return mesh
    except Exception as e:
        print(f"[ERROR] Failed to create or process Trimesh object: {str(e)}")
        return None

# Example usage (kept for reference, ensure paths/thresholds are valid):
# if __name__ == "__main__":
#     # For robust testing, use actual anonymized DICOM data or well-formed dummy data.
#     # The following is a very basic dummy data creation and might not cover all edge cases.
#     dummy_folder = "temp_dicom_test_data"
#     if not os.path.exists(dummy_folder):
#         os.makedirs(dummy_folder)

#     # Create some dummy DICOM files
#     try:
#         slice_shape = (64, 64)
#         for i in range(5): # Create 5 slices
#             ds = pydicom.Dataset()
#             ds.file_meta = pydicom.Dataset() # Add file meta information
#             ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian # Common transfer syntax
#             ds.file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2' # Example: CT Image Storage
#             ds.file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid() # Unique UID for instance

#             ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
#             ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPInstanceUID

#             ds.PatientName = "Test^Patient"
#             ds.PatientID = "123456"
#             ds.Modality = "CT"
#             ds.SeriesInstanceUID = pydicom.uid.generate_uid()
#             ds.StudyInstanceUID = pydicom.uid.generate_uid()
#             ds.ImagePositionPatient = [0, 0, float(i * 2.5)] # Slice spacing of 2.5mm
#             ds.PixelSpacing = [0.5, 0.5] # Voxel spacing in x, y
#             ds.Rows, ds.Columns = slice_shape
#             ds.PhotometricInterpretation = "MONOCHROME2"
#             ds.SamplesPerPixel = 1
#             ds.BitsAllocated = 16
#             ds.BitsStored = 12
#             ds.HighBit = 11
#             ds.PixelRepresentation = 0 # Unsigned integer

#             # Create dummy pixel data (e.g., a sphere)
#             img = np.zeros(slice_shape, dtype=np.uint16)
#             center_x, center_y = slice_shape[1] // 2, slice_shape[0] // 2
#             radius = 20 - abs(i - 2) * 5 # Make sphere change size per slice
#             y, x = np.ogrid[-center_y:slice_shape[0]-center_y, -center_x:slice_shape[1]-center_x]
#             mask = x*x + y*y <= radius*radius
#             img[mask] = 300 # Intensity value for the sphere
#             ds.PixelData = img.tobytes()

#             # Set TransferSyntaxUID explicitly before writing for pydicom > 1.0
#             ds.is_little_endian = True
#             ds.is_implicit_VR = True

#             pydicom.dcmwrite(os.path.join(dummy_folder, f"slice{i:03d}.dcm"), ds, write_like_original=False)
#         print(f"Created dummy DICOM files in {dummy_folder}")
#     except Exception as e:
#         print(f"Error creating dummy DICOMs for testing: {e}")

#     test_volume = load_dicom_volume(dummy_folder)
#     if test_volume is not None:
#         # Use spacing from DICOM (PixelSpacing and slice difference) for more realistic mesh
#         # For this dummy data: spacing_z = 2.5, spacing_xy = 0.5
#         test_mesh = volume_to_mesh(test_volume, threshold=150.0, spacing=(0.5, 0.5, 2.5))
#         if test_mesh is not None and isinstance(test_mesh, trimesh.Trimesh) and not test_mesh.is_empty:
#             output_path = os.path.join(os.getcwd(), "dummy_dicom_output_mesh.obj")
#             try:
#                 test_mesh.export(output_path)
#                 print(f"Dummy mesh exported to {output_path} with {len(test_mesh.vertices)} vertices.")
#             except Exception as e:
#                 print(f"Error exporting dummy mesh: {e}")
#         else:
#             print("Failed to create or mesh is empty from dummy volume.")
#     else:
#         print("Failed to load dummy volume for testing.")

#     # Clean up dummy DICOM folder and mesh file
#     import shutil
#     if os.path.exists(dummy_folder):
#         try:
#             shutil.rmtree(dummy_folder)
#             print(f"Cleaned up dummy DICOM folder: {dummy_folder}")
#         except Exception as e:
#             print(f"Error cleaning up dummy folder {dummy_folder}: {e}")
#     if os.path.exists("dummy_dicom_output_mesh.obj"):
#         try:
#             os.remove("dummy_dicom_output_mesh.obj")
#             print(f"Cleaned up dummy_dicom_output_mesh.obj")
#         except Exception as e:
#             print(f"Error cleaning up dummy_dicom_output_mesh.obj: {e}")
