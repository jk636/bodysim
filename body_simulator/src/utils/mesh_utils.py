import trimesh
import numpy as np
from typing import Optional, Union
from PIL import Image # For image encoding
import io # For byte stream

def voxelize_mesh(mesh: trimesh.Trimesh, pitch: float = 1.0) -> Optional[np.ndarray]:
    """
    Voxelizes a trimesh.Trimesh object into a 3D boolean numpy array.

    Args:
        mesh (trimesh.Trimesh): The input mesh to voxelize.
        pitch (float): The edge length of a single voxel. It determines the resolution
                       of the voxelization. Units should be consistent with mesh coordinates.

    Returns:
        Optional[np.ndarray]: A 3D NumPy array of booleans where True indicates a voxel
                              is occupied by the mesh. Returns None if voxelization fails
                              or the input mesh is invalid.
    """
    if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
        print(f"[ERROR] Invalid or empty mesh provided for voxelization. Mesh: {mesh}")
        return None

    if not isinstance(pitch, (int, float)) or pitch <= 0:
        print(f"[ERROR] Invalid pitch value for voxelization: {pitch}. Must be a positive number.")
        return None

    print(f"[INFO] Starting voxelization for mesh with {len(mesh.vertices)} vertices, pitch={pitch}...")
    try:
        # mesh.voxelized(pitch) creates a VoxelGrid object.
        # .matrix accesses the boolean numpy array representation.
        voxel_grid_matrix = mesh.voxelized(pitch).matrix.astype(bool)

        if voxel_grid_matrix.ndim != 3 or voxel_grid_matrix.size == 0:
            print(f"[WARN] Voxelization resulted in an empty or non-3D grid. Shape: {voxel_grid_matrix.shape}")
            # Depending on requirements, this might be an error or an expected outcome for certain meshes/pitches.
            # For now, returning it as is, but could return None if an empty grid is considered an error.

        print(f"[INFO] Voxelization successful. Grid shape: {voxel_grid_matrix.shape}")
        return voxel_grid_matrix
    except AttributeError as e: # e.g. if mesh is not a Trimesh object due to an earlier error
        print(f"[ERROR] Voxelization failed due to attribute error (possibly invalid mesh object): {str(e)}")
        return None
    except Exception as e: # Catch other potential trimesh or numpy errors
        print(f"[ERROR] An unexpected error occurred during voxelization: {str(e)}")
        return None

def encode_image_to_png(numpy_array: np.ndarray) -> Optional[io.BytesIO]:
    """
    Encodes a 2D NumPy array representing an image into PNG format stored in an io.BytesIO buffer.

    The function handles basic normalization (scaling to 0-255) if the input array
    is not already of type uint8. It assumes a grayscale image.

    Args:
        numpy_array (np.ndarray): A 2D NumPy array representing the image.

    Returns:
        Optional[io.BytesIO]: An io.BytesIO buffer containing the PNG image bytes if successful,
                              None otherwise.
    """
    if not isinstance(numpy_array, np.ndarray) or numpy_array.ndim != 2:
        print(f"[ERROR] Invalid input for PNG encoding: Expected a 2D NumPy array, got {type(numpy_array)} with ndim={getattr(numpy_array, 'ndim', 'N/A')}.")
        return None

    print(f"[INFO] Encoding NumPy array of shape {numpy_array.shape} to PNG...")
    try:
        # Handle data type and scaling for image conversion
        if numpy_array.dtype != np.uint8:
            print(f"[INFO] Input array dtype is {numpy_array.dtype}. Normalizing and converting to uint8.")
            if np.issubdtype(numpy_array.dtype, np.floating):
                # Scale float arrays (assuming range 0.0 to 1.0 or needs normalization)
                # Simple min-max normalization if not 0-1
                min_val, max_val = np.min(numpy_array), np.max(numpy_array)
                if max_val > min_val: # Avoid division by zero
                    normalized_array = 255 * (numpy_array - min_val) / (max_val - min_val)
                else:
                    normalized_array = np.zeros_like(numpy_array) # Or set to min_val if appropriate
                image_array_uint8 = normalized_array.astype(np.uint8)
            elif np.issubdtype(numpy_array.dtype, np.integer):
                # For integer types, scale based on current range or assume direct conversion if appropriate
                # This part might need adjustment based on expected input range of integer arrays
                # For simplicity, if not uint8, attempt direct cast, but this could be lossy.
                # A more robust solution would check min/max and scale.
                if np.min(numpy_array) < 0 or np.max(numpy_array) > 255:
                     print(f"[WARN] Integer array values are outside 0-255 range. Clamping/scaling might be needed for proper PNG.")
                     # Simple clamp and cast for now
                     numpy_array = np.clip(numpy_array, 0, 255)
                image_array_uint8 = numpy_array.astype(np.uint8)
            else: # boolean or other types
                 image_array_uint8 = (numpy_array * 255).astype(np.uint8)

        else: # Already uint8
            image_array_uint8 = numpy_array

        # Create a PIL Image from the NumPy array
        # 'L' mode is for grayscale images
        image = Image.fromarray(image_array_uint8, mode='L')

        # Save the image to a BytesIO buffer in PNG format
        png_buffer = io.BytesIO()
        image.save(png_buffer, format="PNG")
        png_buffer.seek(0) # Reset buffer position to the beginning for reading

        print(f"[INFO] Successfully encoded image to PNG buffer.")
        return png_buffer
    except ImportError: # Should not happen if PIL is installed, but as a safeguard
        print(f"[ERROR] Pillow (PIL) library is not installed. Cannot encode image to PNG.")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to encode NumPy array to PNG: {str(e)}")
        return None

# Example usage (kept for reference):
# if __name__ == "__main__":
#     # Example for voxelize_mesh
#     # Create a simple mesh (e.g., a box)
#     box_mesh = trimesh.creation.box(extents=(10, 10, 10))
#     voxels = voxelize_mesh(box_mesh, pitch=1.0)
#     if voxels is not None:
#         print(f"Voxelized box shape: {voxels.shape}")
#         # print(voxels)

#         # Example for encode_image_to_png
#         # Create a sample 2D numpy array (e.g., a projection of the voxels)
#         if voxels.ndim == 3 and voxels.shape[0] > 0:
#             projection = np.max(voxels, axis=0).astype(np.uint8) * 255 # Simple max projection
#             png_data_buffer = encode_image_to_png(projection)

#             if png_data_buffer:
#                 try:
#                     with open("test_projection.png", "wb") as f:
#                         f.write(png_data_buffer.getvalue())
#                     print("Saved test_projection.png successfully.")
#                 except Exception as e:
#                     print(f"Error saving test_projection.png: {e}")
#                 finally:
#                     png_data_buffer.close()
#             else:
#                 print("Failed to encode projection to PNG.")
#         else:
#             print("Voxel grid is not suitable for creating a projection.")
#     else:
#         print("Failed to voxelize box mesh.")

#     # Test encode_image_to_png with a float array
#     float_array = np.random.rand(50, 50) * 100.0 # Values between 0 and 100
#     png_float_buffer = encode_image_to_png(float_array)
#     if png_float_buffer:
#         try:
#             with open("test_float_array.png", "wb") as f:
#                 f.write(png_float_buffer.getvalue())
#             print("Saved test_float_array.png successfully.")
#         except Exception as e:
#             print(f"Error saving test_float_array.png: {e}")
#         finally:
#             png_float_buffer.close()
#     else:
#         print("Failed to encode float array to PNG.")
