import os
import tempfile # For creating temporary files for screenshots and DICOM subdirs
import shutil # For cleaning up DICOM subdirectories
import trimesh
import pyvista as pv
import numpy as np # For voxel projection
import io # For BytesIO stream for send_file

from flask import (
    Blueprint, request, jsonify, current_app, send_file, abort
)
from werkzeug.utils import secure_filename

from ..utils.dicom_utils import load_dicom_volume, volume_to_mesh
from ..utils.mesh_utils import voxelize_mesh, encode_image_to_png

# Define the blueprint
mesh_bp = Blueprint('mesh_bp', __name__, url_prefix='/mesh')

# Allowed extensions for mesh uploads
ALLOWED_MESH_EXTENSIONS = {'obj'}
ALLOWED_DICOM_EXTENSIONS = {'dcm', ''} # Allow files with no extension or .dcm

def _allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Checks if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def _allowed_dicom_file(filename: str) -> bool:
    """Checks if the file is a DICOM file (ends with .dcm or has no extension)."""
    if not filename: return False
    parts = filename.rsplit('.', 1)
    if len(parts) == 1: # No extension
        return True
    return parts[1].lower() == 'dcm'


@mesh_bp.route('/')
def index():
    """Basic index route for the mesh blueprint."""
    return "Mesh processing routes. Use /upload_obj, /upload_dicom, /visualize_uploaded_obj, /voxelize, /get_model/<filename>."

@mesh_bp.route('/get_model/<path:filename>')
def get_model_file(filename: str):
    """
    Serves an uploaded model file (e.g., OBJ) from the UPLOAD_FOLDER.
    The <path:filename> converter allows filenames to contain slashes,
    though secure_filename should prevent this from being an issue from uploads.
    For direct access, ensure 'filename' is not attempting path traversal.
    """
    # Validate filename to prevent path traversal outside UPLOAD_FOLDER
    # current_app.config['UPLOAD_FOLDER'] is an absolute path.
    # os.path.join will correctly join it with filename.
    # os.path.normpath will resolve any ".." or "." components.
    # Then, we check if the resulting path is still within UPLOAD_FOLDER.

    # Secure the filename part again, just in case, though it's mostly for uploads.
    # For serving, the main concern is path traversal.
    safe_filename = secure_filename(os.path.basename(filename)) # Get only the filename part
    if safe_filename != os.path.basename(filename): # if secure_filename changed it
        print(f"[WARN] Filename {os.path.basename(filename)} was modified by secure_filename to {safe_filename} before serving.")
        # Potentially abort or use the original if your use case trusts the input filename structure
        # For now, we'll proceed with the original basename if it's just for lookup from our controlled storage

    requested_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename) # filename might be just name or name with "folder/" prefix

    # Normalize the path to prevent directory traversal issues like ../../
    normalized_path = os.path.normpath(requested_path)

    # Check if the normalized path is within the UPLOAD_FOLDER
    # Common prefix check is a good way if UPLOAD_FOLDER is guaranteed to be absolute and normalized
    if not normalized_path.startswith(os.path.normpath(current_app.config['UPLOAD_FOLDER'] + os.sep)):
        print(f"[ERROR] Path traversal attempt: {filename} resolved to {normalized_path} which is outside UPLOAD_FOLDER.")
        abort(404, description="Invalid file path.")

    if not os.path.exists(normalized_path) or not os.path.isfile(normalized_path):
        print(f"[ERROR] Model file not found: {normalized_path}")
        abort(404, description=f"Model file '{filename}' not found.")

    print(f"[INFO] Serving model file: {normalized_path}")
    # Mimetype for OBJ files is often model/obj or application/octet-stream
    # application/octet-stream is a safe default for arbitrary binary data.
    return send_file(normalized_path, mimetype='model/obj', as_attachment=False) # as_attachment=False to allow browser rendering if possible


@mesh_bp.route('/upload_obj', methods=['POST'])
def upload_obj_file():
    """Handles OBJ file uploads."""
    if 'mesh' not in request.files:
        return jsonify({"error": "No mesh file part in the request"}), 400
    file = request.files['mesh']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and _allowed_file(file.filename, ALLOWED_MESH_EXTENSIONS):
        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(save_path)
            print(f"[INFO] Successfully saved uploaded OBJ file to: {save_path}")
            return jsonify({
                "message": "OBJ file uploaded successfully",
                "filename": filename,
                "view_url": f"/mesh/visualize_uploaded_obj?filename={filename}"
            }), 200
        except Exception as e:
            print(f"[ERROR] Failed to save uploaded file {filename}: {str(e)}")
            return jsonify({"error": f"Failed to save file: {str(e)}"}), 500
    else:
        disallowed_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else "N/A"
        print(f"[WARN] Disallowed file type uploaded for OBJ: {file.filename}, extension: {disallowed_ext}")
        return jsonify({"error": f"Invalid file type '{disallowed_ext}'. Only .obj files are allowed."}), 400

@mesh_bp.route('/upload_dicom', methods=['POST'])
def upload_dicom_files():
    """
    Handles DICOM file series uploads.
    Processes DICOMs, generates a mesh, saves it as OBJ, and cleans up.
    """
    if 'dicom_files' not in request.files:
        return jsonify({"error": "No 'dicom_files' part in the request"}), 400

    files = request.files.getlist('dicom_files')

    if not files or files[0].filename == '':
        return jsonify({"error": "No DICOM files selected"}), 400

    # Create a temporary subdirectory for this DICOM series
    dicom_temp_subdir_path = tempfile.mkdtemp(dir=current_app.config['UPLOAD_FOLDER'])
    print(f"[INFO] Created temporary DICOM subdirectory: {dicom_temp_subdir_path}")

    saved_files_count = 0
    for file in files:
        if file and _allowed_dicom_file(file.filename):
            # Secure filename is important but DICOM files might not have typical extensions
            # For DICOM, often the original name is less critical than for web-served content.
            # However, still good to pass through secure_filename.
            filename = secure_filename(file.filename if file.filename else "unnamed_dicom_slice")
            if not filename.lower().endswith('.dcm') and '.' not in filename : # Add .dcm if no ext
                 filename += ".dcm"

            save_path = os.path.join(dicom_temp_subdir_path, filename)
            try:
                file.save(save_path)
                saved_files_count += 1
            except Exception as e:
                print(f"[WARN] Failed to save one of the DICOM files ({file.filename}): {str(e)}")
                # Decide if one failure should abort all; for now, we continue

    if saved_files_count == 0:
        shutil.rmtree(dicom_temp_subdir_path)
        print(f"[ERROR] No DICOM files were successfully saved from the upload.")
        return jsonify({"error": "No valid DICOM files saved from upload"}), 400

    print(f"[INFO] Saved {saved_files_count} DICOM files to {dicom_temp_subdir_path}")

    # Process DICOM volume and convert to mesh
    generated_mesh_filename = "dicom_converted_mesh.obj"
    generated_mesh_save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], generated_mesh_filename)

    try:
        print(f"[INFO] Loading DICOM volume from: {dicom_temp_subdir_path}")
        volume = load_dicom_volume(dicom_temp_subdir_path)
        if volume is None:
            raise ValueError("Failed to load DICOM volume. load_dicom_volume returned None.")

        print(f"[INFO] Converting DICOM volume to mesh...")
        # Example threshold and spacing - these might need to be configurable
        mesh = volume_to_mesh(volume, threshold=300.0, spacing=(1.0, 1.0, 1.0))
        if mesh is None or mesh.is_empty:
            raise ValueError("Failed to convert volume to mesh or resulting mesh is empty.")

        print(f"[INFO] Exporting generated mesh to: {generated_mesh_save_path}")
        mesh.export(generated_mesh_save_path)

        return jsonify({
            "message": "DICOM files processed and mesh generated successfully.",
            "filename": generated_mesh_filename,
            "view_url": f"/mesh/visualize_uploaded_obj?filename={generated_mesh_filename}"
        }), 200

    except Exception as e:
        print(f"[ERROR] Error during DICOM processing or mesh generation: {str(e)}")
        # If a mesh file was partially created, remove it
        if os.path.exists(generated_mesh_save_path):
            os.remove(generated_mesh_save_path)
        return jsonify({"error": f"DICOM processing failed: {str(e)}"}), 500
    finally:
        # Clean up the temporary subdirectory with DICOM files
        try:
            shutil.rmtree(dicom_temp_subdir_path)
            print(f"[INFO] Cleaned up temporary DICOM subdirectory: {dicom_temp_subdir_path}")
        except Exception as e_clean:
            print(f"[ERROR] Failed to clean up DICOM subdirectory {dicom_temp_subdir_path}: {str(e_clean)}")


@mesh_bp.route('/visualize_uploaded_obj', methods=['GET'])
def visualize_uploaded_obj():
    """Visualizes an uploaded OBJ file using PyVista and returns a PNG screenshot."""
    filename = request.args.get('filename')
    if not filename:
        print("[WARN] 'filename' query parameter missing for /visualize_uploaded_obj.")
        return jsonify({"error": "Missing 'filename' query parameter"}), 400

    safe_filename = secure_filename(filename)
    if safe_filename != filename:
        print(f"[WARN] Potentially unsafe filename requested for visualization: {filename} (secured as {safe_filename})")
        abort(400, description="Filename may contain disallowed characters.")

    mesh_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)

    if not os.path.exists(mesh_path):
        print(f"[ERROR] Mesh file not found for visualization: {mesh_path}")
        abort(404, description=f"Mesh file '{safe_filename}' not found. Please upload it first.")

    loaded_mesh_data = None
    try:
        print(f"[INFO] Loading mesh for visualization: {mesh_path}")
        loaded_mesh_data = trimesh.load_mesh(mesh_path)
        # Handle Trimesh scenes by attempting to extract a single geometry
        if isinstance(loaded_mesh_data, trimesh.Scene):
            if len(loaded_mesh_data.geometry) == 1:
                loaded_mesh_data = list(loaded_mesh_data.geometry.values())[0]
            elif len(loaded_mesh_data.geometry) > 1:
                print(f"[WARN] Mesh file {safe_filename} contains a scene. Visualizing combined geometry.")
                # Combine all geometries in the scene into a single mesh
                loaded_mesh_data = trimesh.util.concatenate(list(loaded_mesh_data.geometry.values()))
            else:
                abort(400, description="Mesh scene is empty.")

        if not isinstance(loaded_mesh_data, trimesh.Trimesh) or loaded_mesh_data.is_empty:
            abort(400, description="Loaded mesh is empty or not a valid Trimesh object.")

    except Exception as e:
        print(f"[ERROR] Failed to load or process mesh from {mesh_path}: {str(e)}")
        abort(500, description=f"Failed to load or process mesh: {str(e)}")

    plotter = None
    screenshot_file_obj = None # To keep tempfile object for proper cleanup
    try:
        print(f"[INFO] Generating PyVista plot for {safe_filename}...")
        pv_mesh = pv.wrap(loaded_mesh_data)
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(pv_mesh, color='lightblue', show_edges=True, edge_color='gray')
        plotter.camera_position = 'iso'
        plotter.enable_anti_aliasing('ssaa')
        plotter.background_color = 'white'

        screenshot_file_obj = tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=current_app.config['UPLOAD_FOLDER'])
        screenshot_path = screenshot_file_obj.name
        screenshot_file_obj.close()

        plotter.screenshot(screenshot_path)
        print(f"[INFO] Screenshot saved temporarily to: {screenshot_path}")

        @request.call_on_close
        def cleanup_screenshot():
            try:
                if os.path.exists(screenshot_path):
                    os.remove(screenshot_path)
                    print(f"[INFO] Cleaned up temporary screenshot: {screenshot_path}")
            except Exception as e_clean:
                print(f"[ERROR] Error cleaning up temporary screenshot {screenshot_path}: {str(e_clean)}")

        return send_file(screenshot_path, mimetype='image/png')
    except Exception as e:
        print(f"[ERROR] Failed during PyVista plotting or screenshot for {safe_filename}: {str(e)}")
        if screenshot_file_obj and os.path.exists(screenshot_file_obj.name):
            os.remove(screenshot_file_obj.name)
        abort(500, description=f"Failed to generate mesh visualization: {str(e)}")
    finally:
        if plotter:
            plotter.close()
            del plotter
        pv.global_theme.restore_defaults()


@mesh_bp.route('/voxelize', methods=['POST'])
def voxelize_uploaded_mesh():
    """
    Voxelizes a specified mesh file and returns a PNG preview of a 2D projection.
    Expects JSON payload: {"filename": "uploaded_mesh.obj", "pitch": 1.0}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    filename = data.get('filename')
    pitch_str = data.get('pitch')

    if not filename:
        return jsonify({"error": "Missing 'filename' in JSON payload"}), 400
    if not pitch_str:
        return jsonify({"error": "Missing 'pitch' in JSON payload"}), 400

    try:
        pitch = float(pitch_str)
        if pitch <= 0:
            raise ValueError("Pitch must be a positive number.")
    except ValueError as e:
        return jsonify({"error": f"Invalid pitch value: {str(e)}"}), 400

    safe_filename = secure_filename(filename)
    mesh_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)

    if not os.path.exists(mesh_path):
        print(f"[ERROR] Mesh file not found for voxelization: {mesh_path}")
        abort(404, description=f"Mesh file '{safe_filename}' not found. Upload it first.")

    try:
        print(f"[INFO] Loading mesh for voxelization: {mesh_path}")
        mesh_to_voxelize = trimesh.load_mesh(mesh_path)
        # Handle scenes similar to visualization route
        if isinstance(mesh_to_voxelize, trimesh.Scene):
            if len(mesh_to_voxelize.geometry) == 1:
                mesh_to_voxelize = list(mesh_to_voxelize.geometry.values())[0]
            elif len(mesh_to_voxelize.geometry) > 1:
                mesh_to_voxelize = trimesh.util.concatenate(list(mesh_to_voxelize.geometry.values()))
            else:
                abort(400, description="Mesh scene is empty and cannot be voxelized.")

        if not isinstance(mesh_to_voxelize, trimesh.Trimesh) or mesh_to_voxelize.is_empty:
            abort(400, description="Loaded mesh is empty or not a valid Trimesh object for voxelization.")

        print(f"[INFO] Voxelizing mesh '{safe_filename}' with pitch {pitch}...")
        voxels = voxelize_mesh(mesh_to_voxelize, pitch=pitch)
        if voxels is None:
            raise ValueError("Voxelization failed or returned None.")

        # Create a 2D projection for preview (e.g., max projection along z-axis)
        if voxels.ndim != 3 or voxels.size == 0:
             raise ValueError(f"Voxel grid has unexpected shape {voxels.shape} or is empty.")

        # Ensure there's a Z-axis to project along, handle potential 2D or flat grids
        if voxels.shape[2] > 1: # If depth is more than 1
            projection = np.max(voxels, axis=2)
        elif voxels.shape[2] == 1: # If depth is 1, squeeze it
            projection = np.squeeze(voxels, axis=2)
        else: # Should not happen if voxels.ndim == 3 and voxels.size > 0
            raise ValueError("Voxel grid has no depth for Z-projection.")

        print(f"[INFO] Voxel projection shape: {projection.shape}")

        # Encode the 2D projection to PNG
        png_bytes_io = encode_image_to_png(projection) # Expects uint8 or will try to convert
        if png_bytes_io is None:
            raise ValueError("Failed to encode voxel projection to PNG.")

        return send_file(png_bytes_io, mimetype='image/png')

    except ValueError as e: # Catch specific ValueErrors from our logic
        print(f"[ERROR] ValueError during voxelization or PNG encoding for {safe_filename}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"[ERROR] Unexpected error during voxelization or PNG encoding for {safe_filename}: {str(e)}")
        abort(500, description=f"Processing error: {str(e)}")
