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
        # Mesh is already watertight
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = False
        mock_mesh_input.is_watertight = True # Initially watertight

        # Mock the voxelization chain: mesh.voxelized(pitch).fill().matrix
        mock_voxel_grid_obj = MagicMock()
        mock_filled_voxel_grid_obj = MagicMock()
        expected_matrix = np.array([[[True, False], [False, True]]], dtype=bool)
        mock_filled_voxel_grid_obj.matrix = expected_matrix
        mock_voxel_grid_obj.fill.return_value = mock_filled_voxel_grid_obj
        mock_mesh_input.voxelized.return_value = mock_voxel_grid_obj

        mock_mesh_input.fill_holes = MagicMock() # To check it's NOT called

        pitch = 0.5
        result_matrix = voxelize_mesh(mock_mesh_input, pitch=pitch)

        mock_mesh_input.fill_holes.assert_not_called()
        mock_mesh_input.voxelized.assert_called_once_with(pitch)
        mock_voxel_grid_obj.fill.assert_called_once()
        self.assertIsNotNone(result_matrix)
        self.assertTrue(np.array_equal(result_matrix, expected_matrix))

    def test_voxelize_mesh_not_watertight_repairable(self):
        # Mesh is initially not watertight, but fill_holes fixes it
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = False
        mock_mesh_input.is_watertight = MagicMock(side_effect=[False, True]) # False then True
        mock_mesh_input.fill_holes = MagicMock()

        # Mock the voxelization chain
        mock_voxel_grid_obj = MagicMock()
        mock_filled_voxel_grid_obj = MagicMock()
        expected_matrix = np.array([[[True, True], [True, True]]], dtype=bool)
        mock_filled_voxel_grid_obj.matrix = expected_matrix
        mock_voxel_grid_obj.fill.return_value = mock_filled_voxel_grid_obj
        mock_mesh_input.voxelized.return_value = mock_voxel_grid_obj

        pitch = 0.5
        result_matrix = voxelize_mesh(mock_mesh_input, pitch=pitch)

        mock_mesh_input.is_watertight.assert_any_call() # Called multiple times
        mock_mesh_input.fill_holes.assert_called_once()
        mock_mesh_input.voxelized.assert_called_once_with(pitch)
        mock_voxel_grid_obj.fill.assert_called_once()
        self.assertIsNotNone(result_matrix)
        self.assertTrue(np.array_equal(result_matrix, expected_matrix))

    def test_voxelize_mesh_not_watertight_unrepairable(self):
        # Mesh is not watertight and fill_holes doesn't fix it
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = False
        # is_watertight will be called before and after fill_holes
        mock_mesh_input.is_watertight = MagicMock(side_effect=[False, False])
        mock_mesh_input.fill_holes = MagicMock()

        # Mock the voxelization chain
        mock_voxel_grid_obj = MagicMock()
        mock_filled_voxel_grid_obj = MagicMock()
        expected_matrix = np.array([[[False, False], [False, True]]], dtype=bool) # Example matrix
        mock_filled_voxel_grid_obj.matrix = expected_matrix
        mock_voxel_grid_obj.fill.return_value = mock_filled_voxel_grid_obj
        mock_mesh_input.voxelized.return_value = mock_voxel_grid_obj

        pitch = 0.75
        result_matrix = voxelize_mesh(mock_mesh_input, pitch=pitch)

        mock_mesh_input.is_watertight.assert_any_call()
        mock_mesh_input.fill_holes.assert_called_once()
        mock_mesh_input.voxelized.assert_called_once_with(pitch)
        mock_voxel_grid_obj.fill.assert_called_once()
        self.assertIsNotNone(result_matrix)
        self.assertTrue(np.array_equal(result_matrix, expected_matrix))

    def test_voxelize_mesh_empty_input_mesh(self):
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = True
        # Add is_watertight mock for completeness, though it might not be reached
        mock_mesh_input.is_watertight = True
        result = voxelize_mesh(mock_mesh_input, pitch=1.0)
        self.assertIsNone(result)

    def test_voxelize_mesh_invalid_pitch(self):
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = False
        # Add is_watertight mock for completeness
        mock_mesh_input.is_watertight = True
        result_zero_pitch = voxelize_mesh(mock_mesh_input, pitch=0)
        self.assertIsNone(result_zero_pitch)
        result_negative_pitch = voxelize_mesh(mock_mesh_input, pitch=-1.0)
        self.assertIsNone(result_negative_pitch)


    # Removed @patch('trimesh.Trimesh') as we are passing a mock mesh directly
    def test_voxelize_mesh_trimesh_api_error_on_voxelized(self):
        # This tests if mesh.voxelized itself raises an error
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = False
        mock_mesh_input.is_watertight = True # Assume watertight for this specific error test
        mock_mesh_input.voxelized.side_effect = Exception("Trimesh voxelization failed")
        # fill_holes should not be called if voxelized fails before it.
        mock_mesh_input.fill_holes = MagicMock()


        result = voxelize_mesh(mock_mesh_input, pitch=1.0)
        mock_mesh_input.fill_holes.assert_not_called() # Because is_watertight is True
        self.assertIsNone(result)

    def test_voxelize_mesh_trimesh_api_error_on_fill(self):
        # This tests if voxel_grid_object.fill() raises an error
        mock_mesh_input = MagicMock(spec=trimesh.Trimesh)
        mock_mesh_input.is_empty = False
        mock_mesh_input.is_watertight = True

        mock_voxel_grid_obj = MagicMock()
        mock_voxel_grid_obj.fill.side_effect = Exception("VoxelGrid fill failed")
        mock_mesh_input.voxelized.return_value = mock_voxel_grid_obj
        mock_mesh_input.fill_holes = MagicMock()

        result = voxelize_mesh(mock_mesh_input, pitch=1.0)

        mock_mesh_input.fill_holes.assert_not_called()
        mock_mesh_input.voxelized.assert_called_once_with(1.0)
        mock_voxel_grid_obj.fill.assert_called_once()
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
