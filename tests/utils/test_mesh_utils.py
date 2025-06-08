import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import io

# Import functions to be tested
from body_simulator.src.utils.mesh_utils import voxelize_mesh, encode_image_to_png

# We need to mock trimesh.Trimesh for some tests, so no direct import unless for type hinting
# import trimesh
# from PIL import Image # Will be mocked

class TestMeshUtils(unittest.TestCase):

    def test_voxelize_mesh_success(self):
        # Create a mock trimesh.Trimesh object
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = False

        # Mock the 'voxelized' method and its 'matrix' attribute
        mock_voxel_grid = MagicMock()
        mock_voxel_grid.matrix = np.array([[[True, False], [False, True]]], dtype=bool)
        mock_mesh_input.voxelized.return_value = mock_voxel_grid

        pitch = 0.5
        result_matrix = voxelize_mesh(mock_mesh_input, pitch=pitch)

        mock_mesh_input.voxelized.assert_called_once_with(pitch)
        self.assertIsNotNone(result_matrix)
        self.assertTrue(np.array_equal(result_matrix, mock_voxel_grid.matrix))

    def test_voxelize_mesh_empty_input_mesh(self):
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = True
        result = voxelize_mesh(mock_mesh_input, pitch=1.0)
        self.assertIsNone(result)

    def test_voxelize_mesh_invalid_pitch(self):
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = False
        result_zero_pitch = voxelize_mesh(mock_mesh_input, pitch=0)
        self.assertIsNone(result_zero_pitch)
        result_negative_pitch = voxelize_mesh(mock_mesh_input, pitch=-1.0)
        self.assertIsNone(result_negative_pitch)


    @patch('trimesh.Trimesh') # If we were passing a path and loading inside
    def test_voxelize_mesh_trimesh_api_error(self, MockTrimesh): # Renamed for clarity
        # This tests if mesh.voxelized itself raises an error
        mock_mesh_instance = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_instance.is_empty = False
        mock_mesh_instance.voxelized.side_effect = Exception("Trimesh voxelization failed")

        result = voxelize_mesh(mock_mesh_instance, pitch=1.0)
        self.assertIsNone(result)

    def test_voxelize_mesh_non_trimesh_object(self):
        not_a_mesh = "this is a string"
        result = voxelize_mesh(not_a_mesh, pitch=1.0)
        self.assertIsNone(result)

    @patch('PIL.Image.fromarray') # Mocking PIL.Image.fromarray
    def test_encode_image_to_png_success_uint8(self, mock_fromarray):
        dummy_array = np.array([[0, 128], [255, 0]], dtype=np.uint8)

        # Mock the image object and its save method
        mock_image_instance = MagicMock()
        mock_fromarray.return_value = mock_image_instance

        # The save method will write to the BytesIO buffer passed to it
        def mock_save_method(buffer, format):
            self.assertEqual(format, "PNG")
            buffer.write(b"dummy_png_bytes") # Simulate writing PNG data
        mock_image_instance.save = mock_save_method

        result_buffer = encode_image_to_png(dummy_array)

        mock_fromarray.assert_called_once()
        # Check if the first argument to fromarray is the numpy_array (or a version of it)
        # We can't directly compare numpy arrays with '==' in assert_called_with,
        # so we check its properties or use np.array_equal with the actual call argument.
        self.assertTrue(np.array_equal(mock_fromarray.call_args[0][0], dummy_array))
        self.assertEqual(mock_fromarray.call_args[1]['mode'], 'L') # mode='L' for grayscale

        self.assertIsNotNone(result_buffer)
        self.assertIsInstance(result_buffer, io.BytesIO)
        self.assertEqual(result_buffer.getvalue(), b"dummy_png_bytes")

    @patch('PIL.Image.fromarray')
    def test_encode_image_to_png_float_normalization(self, mock_fromarray):
        dummy_float_array = np.array([[0.0, 0.5], [1.0, 0.25]])
        expected_uint8_array = (dummy_float_array * 255).astype(np.uint8)

        mock_image_instance = MagicMock()
        mock_fromarray.return_value = mock_image_instance
        mock_image_instance.save = MagicMock() # Simple mock for save

        encode_image_to_png(dummy_float_array)

        mock_fromarray.assert_called_once()
        called_array = mock_fromarray.call_args[0][0]
        self.assertTrue(np.array_equal(called_array, expected_uint8_array))
        self.assertEqual(called_array.dtype, np.uint8)

    @patch('PIL.Image.fromarray')
    def test_encode_image_to_png_bool_conversion(self, mock_fromarray):
        dummy_bool_array = np.array([[True, False], [False, True]])
        expected_uint8_array = (dummy_bool_array * 255).astype(np.uint8)

        mock_image_instance = MagicMock()
        mock_fromarray.return_value = mock_image_instance
        mock_image_instance.save = MagicMock()

        encode_image_to_png(dummy_bool_array)

        mock_fromarray.assert_called_once()
        called_array = mock_fromarray.call_args[0][0]
        self.assertTrue(np.array_equal(called_array, expected_uint8_array))
        self.assertEqual(called_array.dtype, np.uint8)


    @patch('PIL.Image.fromarray', side_effect=Exception("PIL error"))
    def test_encode_image_to_png_pil_error(self, mock_fromarray):
        dummy_array = np.array([[0, 0], [0, 0]], dtype=np.uint8)
        result_buffer = encode_image_to_png(dummy_array)
        self.assertIsNone(result_buffer)

    def test_encode_image_to_png_invalid_input(self):
        result_1d = encode_image_to_png(np.array([1,2,3]))
        self.assertIsNone(result_1d)

        result_3d = encode_image_to_png(np.random.rand(5,5,3))
        self.assertIsNone(result_3d)

        result_none = encode_image_to_png(None)
        self.assertIsNone(result_none)

if __name__ == '__main__':
    unittest.main()
