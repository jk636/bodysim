import unittest
from unittest.mock import patch, MagicMock, mock_open, call
import os
import numpy as np
import pydicom # For pydicom.FileDataset and pydicom.errors.InvalidDicomError
from pydicom.errors import InvalidDicomError
# Assuming trimesh is a dependency for type hinting if needed, but it's mocked for behavior.
# import trimesh

# Import functions to be tested
from body_simulator.src.utils.dicom_utils import load_dicom_volume, volume_to_mesh

class TestDicomUtils(unittest.TestCase):

    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('pydicom.dcmread')
    def test_load_dicom_volume_success(self, mock_dcmread, mock_listdir, mock_isdir):
        mock_isdir.return_value = True
        mock_listdir.return_value = ['slice1.dcm', 'slice0.dcm'] # Unsorted

        # Create mock DICOM datasets
        dcm_slice0 = MagicMock(spec=pydicom.FileDataset)
        dcm_slice0.ImagePositionPatient = [0, 0, 0.0] # Z-position for sorting
        dcm_slice0.PixelData = np.array([[1, 2], [3, 4]], dtype=np.uint16).tobytes()
        dcm_slice0.pixel_array = np.array([[1, 2], [3, 4]], dtype=np.uint16)
        dcm_slice0.filename = 'slice0.dcm'


        dcm_slice1 = MagicMock(spec=pydicom.FileDataset)
        dcm_slice1.ImagePositionPatient = [0, 0, 1.0]
        dcm_slice1.PixelData = np.array([[5, 6], [7, 8]], dtype=np.uint16).tobytes()
        dcm_slice1.pixel_array = np.array([[5, 6], [7, 8]], dtype=np.uint16)
        dcm_slice1.filename = 'slice1.dcm'

        # Define the side_effect for dcmread based on the filename
        def dcmread_side_effect(filepath):
            if filepath.endswith('slice0.dcm'):
                return dcm_slice0
            elif filepath.endswith('slice1.dcm'):
                return dcm_slice1
            raise FileNotFoundError(f"Unexpected file path {filepath}")

        mock_dcmread.side_effect = dcmread_side_effect

        dicom_folder = "dummy_dicom_folder"
        volume = load_dicom_volume(dicom_folder)

        mock_isdir.assert_called_once_with(dicom_folder)
        mock_listdir.assert_called_once_with(dicom_folder)
        # Calls are made to os.path.join(dicom_folder, filename)
        expected_dcmread_calls = [
            call(os.path.join(dicom_folder, 'slice0.dcm')),
            call(os.path.join(dicom_folder, 'slice1.dcm'))
        ]
        mock_dcmread.assert_has_calls(expected_dcmread_calls, any_order=True)


        self.assertIsNotNone(volume)
        self.assertEqual(volume.shape, (2, 2, 2)) # (rows, cols, num_slices)
        # Check correct sorting and stacking: slice0 should be first
        self.assertTrue(np.array_equal(volume[:, :, 0], dcm_slice0.pixel_array))
        self.assertTrue(np.array_equal(volume[:, :, 1], dcm_slice1.pixel_array))

    @patch('os.path.isdir', return_value=True)
    @patch('os.listdir', return_value=[]) # No files in directory
    def test_load_dicom_volume_no_files(self, mock_listdir, mock_isdir):
        volume = load_dicom_volume("empty_folder")
        self.assertIsNone(volume)

    @patch('os.path.isdir', return_value=False) # Directory does not exist
    def test_load_dicom_volume_folder_not_found(self, mock_isdir):
        volume = load_dicom_volume("nonexistent_folder")
        self.assertIsNone(volume)

    @patch('os.path.isdir', return_value=True)
    @patch('os.listdir', return_value=['bad_slice.dcm'])
    @patch('pydicom.dcmread', side_effect=InvalidDicomError("Bad DICOM"))
    def test_load_dicom_volume_pydicom_error(self, mock_dcmread, mock_listdir, mock_isdir):
        volume = load_dicom_volume("bad_dicom_folder")
        self.assertIsNone(volume)

    @patch('os.path.isdir', return_value=True)
    @patch('os.listdir', return_value=['slice_no_pos.dcm'])
    @patch('pydicom.dcmread')
    def test_load_dicom_volume_missing_tags(self, mock_dcmread, mock_listdir, mock_isdir):
        dcm_slice_no_pos = MagicMock(spec=pydicom.FileDataset)
        # Missing ImagePositionPatient
        dcm_slice_no_pos.PixelData = np.array([[1,2],[3,4]]).tobytes()
        dcm_slice_no_pos.pixel_array = np.array([[1,2],[3,4]])
        mock_dcmread.return_value = dcm_slice_no_pos

        volume = load_dicom_volume("dicom_missing_tags")
        self.assertIsNone(volume) # Should fail because ImagePositionPatient is needed for sorting

    @patch('skimage.measure.marching_cubes')
    @patch('trimesh.Trimesh') # Mock the Trimesh class constructor
    def test_volume_to_mesh_success(self, mock_Trimesh_constructor, mock_marching_cubes):
        dummy_volume = np.random.rand(10, 10, 10)
        mock_verts = np.array([[0,0,0], [1,0,0], [0,1,0]])
        mock_faces = np.array([[0,1,2]])
        mock_normals = np.array([[0,0,1], [0,0,1], [0,0,1]])
        mock_marching_cubes.return_value = (mock_verts, mock_faces, mock_normals, MagicMock()) # Last value is "values"

        # Mock the Trimesh instance methods that might be called
        mock_trimesh_instance = MagicMock(spec=trimesh.Trimesh)
        mock_trimesh_instance.is_empty = False
        mock_trimesh_instance.vertices = mock_verts # for the print statement and potential checks
        mock_trimesh_instance.faces = mock_faces
        mock_Trimesh_constructor.return_value = mock_trimesh_instance

        threshold = 0.5
        spacing = (1.0, 1.0, 2.0)
        mesh = volume_to_mesh(dummy_volume, threshold=threshold, spacing=spacing)

        mock_marching_cubes.assert_called_once_with(dummy_volume, level=threshold, spacing=spacing)
        mock_Trimesh_constructor.assert_called_once_with(vertices=mock_verts, faces=mock_faces, vertex_normals=mock_normals)
        mock_trimesh_instance.remove_unreferenced_vertices.assert_called_once()
        mock_trimesh_instance.remove_degenerate_faces.assert_called_once()

        self.assertIsNotNone(mesh)
        self.assertEqual(mesh, mock_trimesh_instance)

    @patch('skimage.measure.marching_cubes', side_effect=RuntimeError("Marching cubes failed"))
    def test_volume_to_mesh_marching_cubes_error(self, mock_marching_cubes):
        dummy_volume = np.random.rand(10, 10, 10)
        mesh = volume_to_mesh(dummy_volume)
        self.assertIsNone(mesh)

    def test_volume_to_mesh_invalid_volume(self):
        mesh = volume_to_mesh(np.random.rand(10,10)) # 2D array
        self.assertIsNone(mesh)
        mesh = volume_to_mesh(None)
        self.assertIsNone(mesh)

    @patch('skimage.measure.marching_cubes')
    def test_volume_to_mesh_no_surface_generated(self, mock_marching_cubes):
        dummy_volume = np.zeros((10, 10, 10)) # Volume that might not generate a surface at a given threshold
        # Simulate marching_cubes returning empty vertices/faces
        mock_marching_cubes.return_value = (np.array([]), np.array([]), np.array([]), np.array([]))

        mesh = volume_to_mesh(dummy_volume, threshold=0.5)
        self.assertIsNone(mesh)

if __name__ == '__main__':
    unittest.main()
