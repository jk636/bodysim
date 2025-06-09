import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import tempfile
import numpy as np

# Adjust import path if necessary. This assumes 'body_simulator' is on PYTHONPATH
# or pytest can find it (e.g. by running pytest from project root)
from body_simulator.src.models.human_body import Organ, HumanBody
# We will also need to mock trimesh, so no direct import of it here in tests unless for type hinting
# import trimesh

class TestOrgan(unittest.TestCase):

    def test_organ_creation(self):
        organ = Organ(name="Heart")
        self.assertEqual(organ.name, "Heart")
        self.assertIsNone(organ.mesh)
        self.assertIsNone(organ.mesh_file)
        self.assertEqual(organ.magnetic_susceptibility, 0.0)
        self.assertEqual(organ.voxel_resolution, 1.0)
        self.assertEqual(len(organ.sub_organs), 0)

    @patch('os.path.isfile')
    @patch('trimesh.load') # Mocking trimesh.load directly
    def test_load_mesh_success(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True # Simulate file exists

        dummy_mesh = MagicMock(spec=trimesh.Trimesh) # Create a MagicMock that acts like a Trimesh object
        dummy_mesh.is_empty = False
        dummy_mesh.vertices = [1,2,3] # Give it some dummy vertices to make it not "empty" in a general sense
        mock_trimesh_load.return_value = dummy_mesh

        organ = Organ(name="Liver")
        mesh_path = "dummy/path/liver.obj"
        organ.load_mesh(mesh_path)

        mock_isfile.assert_called_once_with(mesh_path)
        mock_trimesh_load.assert_called_once_with(mesh_path)
        self.assertEqual(organ.mesh_file, mesh_path)
        self.assertIsNotNone(organ.mesh)
        self.assertEqual(organ.mesh, dummy_mesh)

    @patch('os.path.isfile')
    def test_load_mesh_file_not_found(self, mock_isfile):
        mock_isfile.return_value = False # Simulate file does NOT exist
        organ = Organ(name="Kidney")
        mesh_path = "nonexistent/kidney.obj"
        organ.load_mesh(mesh_path)

        mock_isfile.assert_called_once_with(mesh_path)
        self.assertIsNone(organ.mesh)
        self.assertEqual(organ.mesh_file, mesh_path) # mesh_file path should still be set

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_empty_mesh(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True

        empty_mesh = MagicMock(spec=trimesh.Trimesh)
        empty_mesh.is_empty = True
        mock_trimesh_load.return_value = empty_mesh

        organ = Organ(name="Spleen")
        mesh_path = "dummy/spleen.obj"
        organ.load_mesh(mesh_path)

        self.assertIsNone(organ.mesh, "Mesh should be None if trimesh loads an empty mesh.")

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_trimesh_exception(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True
        mock_trimesh_load.side_effect = Exception("Trimesh load error")

        organ = Organ(name="Pancreas")
        mesh_path = "dummy/pancreas.obj"
        organ.load_mesh(mesh_path)
        self.assertIsNone(organ.mesh)


    def test_set_properties(self):
        organ = Organ(name="Brain")
        organ.conductivity = 0.8
        organ.density = 1050.0
        organ.voxel_resolution = 0.5

        self.assertEqual(organ.conductivity, 0.8)
        self.assertEqual(organ.density, 1050.0)
        self.assertEqual(organ.voxel_resolution, 0.5)

    def test_voxelize_mesh_no_mesh(self):
        organ = Organ(name="Lung")
        organ.voxelize_mesh() # Should not crash
        self.assertIsNone(organ.voxel_grid)

    @patch('body_simulator.src.models.human_body.voxelize_mesh') # Mock the imported utility function
    def test_voxelize_mesh_success(self, mock_util_voxelize_mesh):
        organ = Organ(name="Stomach")
        # Give it a dummy mesh object; it doesn't need to be a full trimesh mock for this test
        # as voxelize_mesh method in Organ class primarily checks its existence.
        # The actual call to the utility function is what we are mocking.
        organ.mesh = MagicMock(spec=trimesh.Trimesh)
        organ.mesh.is_empty = False # Make it seem like a valid mesh

        dummy_grid = np.array([[[True]]])
        mock_util_voxelize_mesh.return_value = dummy_grid

        organ.voxel_resolution = 2.0
        organ.voxelize_mesh()

        mock_util_voxelize_mesh.assert_called_once_with(organ.mesh, pitch=2.0)
        self.assertIsNotNone(organ.voxel_grid)
        self.assertTrue(np.array_equal(organ.voxel_grid, dummy_grid))

    def test_interpolate_properties(self):
        organ = Organ(name="Gallbladder")
        organ.conductivity = 0.1
        organ.density = 1020
        expected_props = {
            "magnetic_susceptibility": 0.0,
            "permeability": 1.0,
            "permittivity": 1.0,
            "conductivity": 0.1,
            "elasticity": 0.0,
            "density": 1020.0, # Ensure float
        }
        self.assertEqual(organ.interpolate_properties(), expected_props)

    def test_add_remove_sub_organ(self):
        main_organ = Organ(name="Liver")
        sub_organ1 = Organ(name="Lobule1")
        sub_organ2 = Organ(name="Lobule2")

        main_organ.add_sub_organ(sub_organ1)
        self.assertIn("Lobule1", main_organ.sub_organs)
        self.assertEqual(main_organ.sub_organs["Lobule1"], sub_organ1)

        main_organ.add_sub_organ(sub_organ2)
        self.assertIn("Lobule2", main_organ.sub_organs)

        main_organ.remove_sub_organ("Lobule1")
        self.assertNotIn("Lobule1", main_organ.sub_organs)
        self.assertIn("Lobule2", main_organ.sub_organs)

    @patch('os.path.isfile', MagicMock(return_value=True)) # Assume mesh files exist for simplicity
    @patch('trimesh.load', MagicMock(return_value=MagicMock(spec=trimesh.Trimesh, is_empty=False)))
    def test_to_dict_from_dict_equivalence(self):
        organ = Organ(name="Heart", mesh_file="heart.obj")
        organ.conductivity = 0.7
        organ.voxel_resolution = 1.5

        sub_organ = Organ(name="Ventricle", mesh_file="ventricle.obj")
        sub_organ.density = 1060
        organ.add_sub_organ(sub_organ)

        organ_dict = organ.to_dict()

        # Ensure JSON serializability (basic check)
        try:
            json.dumps(organ_dict)
        except TypeError:
            self.fail("Organ.to_dict() output is not JSON serializable")

        new_organ = Organ.from_dict(organ_dict)

        self.assertEqual(new_organ.name, organ.name)
        self.assertEqual(new_organ.mesh_file, organ.mesh_file)
        self.assertEqual(new_organ.conductivity, organ.conductivity)
        self.assertEqual(new_organ.voxel_resolution, organ.voxel_resolution)
        self.assertEqual(len(new_organ.sub_organs), len(organ.sub_organs))
        self.assertIn("Ventricle", new_organ.sub_organs)
        self.assertEqual(new_organ.sub_organs["Ventricle"].name, sub_organ.name)
        self.assertEqual(new_organ.sub_organs["Ventricle"].mesh_file, sub_organ.mesh_file)
        self.assertEqual(new_organ.sub_organs["Ventricle"].density, sub_organ.density)


class TestHumanBody(unittest.TestCase):

    def test_add_remove_organ(self):
        body = HumanBody()
        heart = Organ(name="Heart")
        liver = Organ(name="Liver")

        body.add_organ(heart)
        self.assertIn("Heart", body.organs)
        self.assertEqual(body.organs["Heart"], heart)

        body.add_organ(liver)
        self.assertIn("Liver", body.organs)

        body.remove_organ("Heart")
        self.assertNotIn("Heart", body.organs)
        self.assertIn("Liver", body.organs)

    @patch('os.path.isfile', MagicMock(return_value=True))
    @patch('trimesh.load', MagicMock(return_value=MagicMock(spec=trimesh.Trimesh, is_empty=False)))
    def test_save_load_human_body(self):
        body = HumanBody()

        heart = Organ(name="Heart", mesh_file="heart.obj")
        heart.conductivity = 0.7
        ventricle = Organ(name="Ventricle", mesh_file="ventricle.obj")
        heart.add_sub_organ(ventricle)
        body.add_organ(heart)

        liver = Organ(name="Liver", mesh_file="liver.obj")
        liver.density = 1050
        body.add_organ(liver)

        # Use a temporary file for saving and loading
        # tempfile.NamedTemporaryFile creates and opens a file.
        # We need the name to pass to save_to_file and load_from_file.
        # It's better to close it immediately if writing/reading is done by the methods themselves.

        # Create a temporary file that is deleted when closed
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp_file:
            temp_filename = tmp_file.name
            # File is open, so our methods can write to it if they expect a file object.
            # However, our methods expect a filename string. So, close it first.

        try:
            body.save_to_file(temp_filename)

            new_body = HumanBody()
            new_body.load_from_file(temp_filename)

            self.assertEqual(len(new_body.organs), len(body.organs))
            self.assertIn("Heart", new_body.organs)
            self.assertIn("Liver", new_body.organs)

            loaded_heart = new_body.organs["Heart"]
            self.assertEqual(loaded_heart.name, heart.name)
            self.assertEqual(loaded_heart.mesh_file, heart.mesh_file)
            self.assertEqual(loaded_heart.conductivity, heart.conductivity)
            self.assertEqual(len(loaded_heart.sub_organs), 1)
            self.assertIn("Ventricle", loaded_heart.sub_organs)
            self.assertEqual(loaded_heart.sub_organs["Ventricle"].mesh_file, ventricle.mesh_file)

            loaded_liver = new_body.organs["Liver"]
            self.assertEqual(loaded_liver.density, liver.density)

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    @patch('builtins.open', new_callable=mock_open) # Mock open to simulate IOErrors
    def test_save_human_body_io_error(self, mock_file_open):
        mock_file_open.side_effect = IOError("Failed to write")
        body = HumanBody()
        heart = Organ(name="Heart")
        body.add_organ(heart)
        # Expecting a print message to stderr/stdout, not an exception to be raised by save_to_file
        # This test mainly checks if it handles the error gracefully (e.g., doesn't crash).
        # To assert print, you'd need to redirect stdout/stderr. For now, just check for no crash.
        try:
            body.save_to_file("test_save_fail.json")
        except Exception as e:
            self.fail(f"save_to_file raised an unexpected exception on IOError: {e}")


    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_human_body_json_error(self, mock_file_open):
        body = HumanBody()
        # As above, mainly checking for graceful handling rather than specific error message content here.
        try:
            body.load_from_file("test_load_fail.json")
            self.assertEqual(len(body.organs), 0) # Organs should be empty after failed load
        except Exception as e:
            self.fail(f"load_from_file raised an unexpected exception on JSONDecodeError: {e}")

    @patch('os.path.isfile', return_value=False)
    def test_load_human_body_file_not_found(self, mock_isfile):
        body = HumanBody()
        body.load_from_file("non_existent.json")
        mock_isfile.assert_called_once_with("non_existent.json")
        self.assertEqual(len(body.organs),0) # Ensure organs list is empty


if __name__ == '__main__':
    unittest.main()
