import pytest
import tempfile
import os
import io
from unittest.mock import patch, MagicMock

# Import the Flask app instance
# The conftest.py should allow this import to work if tests are run with pytest from root
from body_simulator.src.main.app import app as flask_app

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    # Create a temporary directory for UPLOAD_FOLDER for the duration of the test
    with tempfile.TemporaryDirectory(prefix="flask_test_uploads_") as tmpdir:
        original_upload_folder = flask_app.config['UPLOAD_FOLDER']
        flask_app.config['UPLOAD_FOLDER'] = tmpdir
        with flask_app.test_client() as client:
            yield client
        # Restore original UPLOAD_FOLDER if necessary, though for testing it's usually fine
        flask_app.config['UPLOAD_FOLDER'] = original_upload_folder


def test_main_index_route(client):
    """Test the main index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"<h1>Body Simulator Interface</h1>" in response.data # Check for a key element

def test_mesh_index_route(client):
    """Test the mesh blueprint index route."""
    response = client.get('/mesh/')
    assert response.status_code == 200
    assert b"Mesh processing routes" in response.data

# --- OBJ Upload Tests ---
def test_upload_obj_success(client):
    """Test successful OBJ file upload."""
    # Create a dummy OBJ file content
    dummy_obj_content = b"v 0.0 0.0 0.0\nv 1.0 0.0 0.0\nv 0.0 1.0 0.0\nf 1 2 3\n"
    data = {
        'mesh': (io.BytesIO(dummy_obj_content), 'test_cube.obj')
    }
    response = client.post('/mesh/upload_obj', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == "OBJ file uploaded successfully"
    assert json_data['filename'] == "test_cube.obj"
    # Check if file exists in the temporary UPLOAD_FOLDER
    assert os.path.exists(os.path.join(flask_app.config['UPLOAD_FOLDER'], "test_cube.obj"))

def test_upload_obj_no_file_part(client):
    """Test OBJ upload with no 'mesh' file part."""
    response = client.post('/mesh/upload_obj', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert "No mesh file part" in json_data['error']

def test_upload_obj_no_selected_file(client):
    """Test OBJ upload with an empty filename."""
    data = {'mesh': (io.BytesIO(b''), '')} # Empty filename
    response = client.post('/mesh/upload_obj', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert "No selected file" in json_data['error']

def test_upload_obj_invalid_extension(client):
    """Test OBJ upload with an invalid file extension."""
    data = {'mesh': (io.BytesIO(b'dummy data'), 'test.txt')}
    response = client.post('/mesh/upload_obj', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert "Invalid file type" in json_data['error']

# --- PyVista Visualization Route Test ---
@patch('trimesh.load_mesh') # Mock the actual mesh loading
@patch('pyvista.Plotter')    # Mock the PyVista Plotter
def test_visualize_obj_success(mock_Plotter, mock_trimesh_load, client):
    """Test successful OBJ visualization (PyVista screenshot)."""
    # Setup: Ensure a dummy file exists in the UPLOAD_FOLDER
    dummy_filename = "test_pv_viz.obj"
    dummy_filepath = os.path.join(flask_app.config['UPLOAD_FOLDER'], dummy_filename)
    with open(dummy_filepath, 'w') as f:
        f.write("v 0 0 0\nv 1 1 1") # Minimal valid OBJ content

    # Mock trimesh.load_mesh to return a mock mesh object
    mock_mesh = MagicMock(spec=trimesh.Trimesh)
    mock_mesh.is_empty = False
    mock_trimesh_load.return_value = mock_mesh

    # Mock PyVista Plotter instance and its methods
    mock_plotter_instance = MagicMock()
    mock_Plotter.return_value = mock_plotter_instance

    response = client.get(f'/mesh/visualize_uploaded_obj?filename={dummy_filename}')

    assert response.status_code == 200
    assert response.mimetype == 'image/png'
    mock_trimesh_load.assert_called_once_with(dummy_filepath)
    mock_Plotter.assert_called_once_with(off_screen=True)
    mock_plotter_instance.add_mesh.assert_called_once()
    mock_plotter_instance.screenshot.assert_called_once()
    mock_plotter_instance.close.assert_called_once()


def test_visualize_obj_file_not_found(client):
    """Test visualization when the OBJ file does not exist."""
    response = client.get('/mesh/visualize_uploaded_obj?filename=nonexistent.obj')
    assert response.status_code == 404 # Not Found (due to abort(404))

# --- DICOM Upload Route Test ---
@patch('body_simulator.src.routes.mesh_routes.load_dicom_volume')
@patch('body_simulator.src.routes.mesh_routes.volume_to_mesh')
@patch('trimesh.Trimesh.export') # Mock the export method of the mesh object
def test_upload_dicom_success(mock_mesh_export, mock_volume_to_mesh, mock_load_dicom_volume, client):
    # Mock return values
    mock_load_dicom_volume.return_value = np.array([[[1]]]) # Dummy volume
    mock_trimesh_mesh = MagicMock(spec=trimesh.Trimesh)
    mock_trimesh_mesh.is_empty = False
    mock_volume_to_mesh.return_value = mock_trimesh_mesh

    # Create dummy DICOM files
    dicom_files_data = []
    for i in range(3):
        dicom_files_data.append(
            (io.BytesIO(f"dummy dicom content {i}".encode('utf-8')), f'slice{i}.dcm')
        )

    data = {'dicom_files': dicom_files_data}
    response = client.post('/mesh/upload_dicom', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['message'] == "DICOM files processed and mesh generated successfully."
    assert json_data['filename'] == "dicom_converted_mesh.obj"

    # Check if the generated OBJ file exists in UPLOAD_FOLDER (it should after export)
    # and then it's cleaned up by the test framework's temp dir for UPLOAD_FOLDER
    expected_mesh_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], "dicom_converted_mesh.obj")
    mock_mesh_export.assert_called_once_with(expected_mesh_path)
    # The temp subdir for DICOMs should have been cleaned up by shutil.rmtree in the route

def test_upload_dicom_no_files(client):
    response = client.post('/mesh/upload_dicom', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    assert "No 'dicom_files' part" in response.get_json()['error']

# --- Voxelize Route Test ---
@patch('trimesh.load_mesh')
@patch('body_simulator.src.routes.mesh_routes.voxelize_mesh') # Target where it's imported in routes
@patch('body_simulator.src.routes.mesh_routes.encode_image_to_png')
def test_voxelize_mesh_success(mock_encode_png, mock_util_voxelize, mock_trimesh_load, client):
    dummy_filename = "test_for_voxel.obj"
    dummy_filepath = os.path.join(flask_app.config['UPLOAD_FOLDER'], dummy_filename)
    with open(dummy_filepath, 'w') as f:
        f.write("v 0 0 0\nv 1 1 1") # Minimal OBJ

    mock_mesh_obj = MagicMock(spec=trimesh.Trimesh)
    mock_mesh_obj.is_empty = False
    mock_trimesh_load.return_value = mock_mesh_obj

    mock_voxel_grid = np.ones((5,5,5), dtype=bool) # Dummy voxel grid
    mock_util_voxelize.return_value = mock_voxel_grid

    mock_png_bytes = io.BytesIO(b"dummy_png_data")
    mock_encode_png.return_value = mock_png_bytes

    response = client.post('/mesh/voxelize', json={'filename': dummy_filename, 'pitch': 1.0})

    assert response.status_code == 200
    assert response.mimetype == 'image/png'
    assert response.data == b"dummy_png_data"

    mock_trimesh_load.assert_called_once_with(dummy_filepath)
    mock_util_voxelize.assert_called_once_with(mock_mesh_obj, pitch=1.0)
    # Check that encode_image_to_png was called with a 2D projection
    # The actual projection logic is np.max(voxels, axis=2)
    expected_projection = np.max(mock_voxel_grid, axis=2)
    # np.array_equal(mock_encode_png.call_args[0][0], expected_projection)
    assert mock_encode_png.call_args is not None
    assert np.array_equal(mock_encode_png.call_args[0][0], expected_projection)


# --- Placeholder Property and Simulation Routes ---
def test_get_organ_properties_placeholder(client):
    response = client.get('/properties/Heart')
    assert response.status_code == 200
    json_data = response.get_json()
    assert "Properties for Heart (placeholder)" in json_data['message']
    assert "conductivity" in json_data['properties']

def test_set_organ_properties_placeholder(client):
    response = client.post('/properties/Heart', json={"conductivity": 0.6})
    assert response.status_code == 200
    json_data = response.get_json()
    assert "updated with received data (placeholder)" in json_data['message']
    assert json_data['received_data']['conductivity'] == 0.6

def test_run_fdtd_simulation_placeholder(client):
    response = client.post('/simulation/run_fdtd', json={"param1": "value1"})
    assert response.status_code == 200
    json_data = response.get_json()
    assert "FDTD simulation run initiated (placeholder)" in json_data['message']
    assert json_data['received_params']['param1'] == "value1"

# --- Test /mesh/get_model/<filename> route ---
def test_get_model_file_success(client):
    dummy_filename = "test_serve.obj"
    dummy_filepath = os.path.join(flask_app.config['UPLOAD_FOLDER'], dummy_filename)
    dummy_content = b"v 0 0 0\nv 1 0 0"
    with open(dummy_filepath, 'wb') as f:
        f.write(dummy_content)

    response = client.get(f'/mesh/get_model/{dummy_filename}')
    assert response.status_code == 200
    assert response.mimetype == 'model/obj'
    assert response.data == dummy_content

def test_get_model_file_not_found(client):
    response = client.get('/mesh/get_model/nonexistent_model.obj')
    assert response.status_code == 404

# Add more tests for error conditions in routes as needed.
# For example, what happens if trimesh.load_mesh fails in a route?
# Or if pydicom processing fails? Many of these are handled by abort() or jsonify(error),
# which can be checked.
