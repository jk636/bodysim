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
import trimesh # For spec=trimesh.Trimesh

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

        dummy_mesh = MagicMock(spec=trimesh.Trimesh, name="loaded_mesh")
        dummy_mesh.is_empty = False
        dummy_mesh.vertices = [1,2,3]
        dummy_mesh.faces = [[0,1,2]] # Add faces for len() checks in method

        mock_processed_mesh = MagicMock(spec=trimesh.Trimesh, name="processed_mesh")
        mock_processed_mesh.is_empty = False
        mock_processed_mesh.vertices = [4,5,6]
        mock_processed_mesh.faces = [[0,1,2]]
        dummy_mesh.process.return_value = mock_processed_mesh

        mock_trimesh_load.return_value = dummy_mesh

        organ = Organ(name="Liver")
        mesh_path = "dummy/path/liver.obj"
        organ.load_mesh(mesh_path)

        mock_isfile.assert_called_once_with(mesh_path)
        mock_trimesh_load.assert_called_once_with(mesh_path)
        dummy_mesh.process.assert_called_once()
        self.assertEqual(organ.mesh_file, mesh_path)
        self.assertIsNotNone(organ.mesh)
        self.assertIs(organ.mesh, mock_processed_mesh) # Should be the processed mesh

    @patch('os.path.isfile')
    def test_load_mesh_file_not_found(self, mock_isfile):
        mock_isfile.return_value = False # Simulate file does NOT exist
        organ = Organ(name="Kidney")
        mesh_path = "nonexistent/kidney.obj"

        # Mock trimesh.load to ensure it's not called if file not found
        with patch('trimesh.load') as mock_trimesh_load_local:
            organ.load_mesh(mesh_path)
            mock_trimesh_load_local.assert_not_called()

        mock_isfile.assert_called_once_with(mesh_path)
        self.assertIsNone(organ.mesh)
        self.assertEqual(organ.mesh_file, mesh_path) # mesh_file path should still be set

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_empty_mesh_loaded(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True

        empty_mesh = MagicMock(spec=trimesh.Trimesh, name="loaded_empty_mesh")
        empty_mesh.is_empty = True
        empty_mesh.process = MagicMock(name="process_on_empty_mesh") # Mock process method
        mock_trimesh_load.return_value = empty_mesh

        organ = Organ(name="Spleen")
        mesh_path = "dummy/spleen.obj"
        organ.load_mesh(mesh_path)

        self.assertIsNone(organ.mesh, "Mesh should be None if trimesh loads an empty mesh.")
        empty_mesh.process.assert_not_called() # Process should not be called on an empty mesh

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_trimesh_load_exception(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True
        mock_trimesh_load.side_effect = Exception("Trimesh load error")

        organ = Organ(name="Pancreas")
        mesh_path = "dummy/pancreas.obj"

        # To check .process() is not called, we'd need a mesh object, but load fails.
        # So, this test primarily ensures mesh is None after such an exception.
        organ.load_mesh(mesh_path)
        self.assertIsNone(organ.mesh)

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_handles_scene_successfully(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True

        mock_scene = MagicMock(spec=trimesh.Scene, name="scene_mock")
        mock_trimesh_geom = MagicMock(spec=trimesh.Trimesh, name="trimesh_in_scene", is_empty=False, vertices=[1], faces=[[0,0,0]])
        mock_scene.geometry = {'geom1': mock_trimesh_geom}

        mock_concatenated_mesh = MagicMock(spec=trimesh.Trimesh, name="concatenated_mesh", is_empty=False, vertices=[2], faces=[[0,0,0]])
        mock_scene.dump.return_value = mock_concatenated_mesh

        mock_processed_concat_mesh = MagicMock(spec=trimesh.Trimesh, name="processed_concatenated_mesh", is_empty=False, vertices=[3], faces=[[0,0,0]])
        mock_concatenated_mesh.process.return_value = mock_processed_concat_mesh

        mock_trimesh_load.return_value = mock_scene

        organ = Organ(name="SceneOrgan")
        organ.load_mesh("dummy_scene.glb")

        mock_scene.dump.assert_called_once_with(concatenate=True)
        mock_concatenated_mesh.process.assert_called_once()
        self.assertIs(organ.mesh, mock_processed_concat_mesh)

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_handles_empty_scene(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True

        mock_empty_scene = MagicMock(spec=trimesh.Scene, name="empty_scene_mock")
        mock_empty_scene.geometry = {} # Empty geometry dict
        mock_empty_scene.dump = MagicMock(name="dump_on_empty_scene") # Mock dump

        mock_trimesh_load.return_value = mock_empty_scene

        organ = Organ(name="EmptySceneOrgan")
        organ.load_mesh("empty_scene.glb")

        self.assertIsNone(organ.mesh)
        mock_empty_scene.dump.assert_not_called() # Dump should not be called if geometry is empty

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_scene_consolidation_fails_returns_non_trimesh(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True

        mock_scene = MagicMock(spec=trimesh.Scene, name="scene_mock_fail_dump")
        mock_scene.geometry = {'geom1': MagicMock(spec=trimesh.Trimesh)} # Non-empty geometry
        mock_scene.dump.return_value = "not_a_trimesh_object" # Simulate dump returning wrong type

        mock_trimesh_load.return_value = mock_scene

        organ = Organ(name="SceneFailDumpOrgan")
        organ.load_mesh("scene_fail_dump.glb")

        self.assertIsNone(organ.mesh)
        mock_scene.dump.assert_called_once_with(concatenate=True)

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_scene_consolidation_exception(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True

        mock_scene = MagicMock(spec=trimesh.Scene, name="scene_mock_exc_dump")
        mock_scene.geometry = {'geom1': MagicMock(spec=trimesh.Trimesh)} # Non-empty geometry
        mock_scene.dump.side_effect = Exception("Scene dump error")

        mock_trimesh_load.return_value = mock_scene

        organ = Organ(name="SceneExcDumpOrgan")
        organ.load_mesh("scene_exc_dump.glb")

        self.assertIsNone(organ.mesh)
        mock_scene.dump.assert_called_once_with(concatenate=True)

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_processing_fails_returns_empty(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True

        mock_loaded_mesh = MagicMock(spec=trimesh.Trimesh, name="loaded_mesh_for_proc_fail", is_empty=False, vertices=[1], faces=[[0,0,0]])
        mock_empty_processed_mesh = MagicMock(spec=trimesh.Trimesh, name="empty_processed_mesh", is_empty=True, faces=[]) # is_empty makes it fail
        mock_loaded_mesh.process.return_value = mock_empty_processed_mesh

        mock_trimesh_load.return_value = mock_loaded_mesh

        organ = Organ(name="ProcessFailOrgan")
        organ.load_mesh("process_fail.obj")

        self.assertIsNone(organ.mesh)
        mock_loaded_mesh.process.assert_called_once()

    @patch('os.path.isfile')
    @patch('trimesh.load')
    def test_load_mesh_processing_fails_returns_non_trimesh(self, mock_trimesh_load, mock_isfile):
        mock_isfile.return_value = True

        mock_loaded_mesh = MagicMock(spec=trimesh.Trimesh, name="loaded_mesh_for_proc_fail_type", is_empty=False, vertices=[1], faces=[[0,0,0]])
        mock_loaded_mesh.process.return_value = "not_a_trimesh_object_after_process" # process returns wrong type

        mock_trimesh_load.return_value = mock_loaded_mesh

        organ = Organ(name="ProcessFailTypeOrgan")
        organ.load_mesh("process_fail_type.obj")

        self.assertIsNone(organ.mesh)
        mock_loaded_mesh.process.assert_called_once()


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

    # --- Tests for simplify_mesh ---

    def test_simplify_mesh_success(self):
        organ = Organ(name="TestOrgan")
        organ.mesh = MagicMock(spec=trimesh.Trimesh)
        organ.mesh.is_empty = False
        organ.mesh.faces = [([0,0,0])] * 100 # Simulate 100 faces

        mock_simplified_mesh = MagicMock(spec=trimesh.Trimesh)
        mock_simplified_mesh.is_empty = False
        mock_simplified_mesh.faces = [([0,0,0])] * 50 # Simulate 50 faces
        organ.mesh.simplify_quadric_decimation.return_value = mock_simplified_mesh

        result = organ.simplify_mesh(target_face_count=50)

        self.assertTrue(result)
        organ.mesh.simplify_quadric_decimation.assert_called_once_with(face_count=50)
        self.assertIs(organ.mesh, mock_simplified_mesh)

    def test_simplify_mesh_no_mesh(self):
        organ = Organ(name="TestOrganNoMesh")
        # organ.mesh is None by default
        result = organ.simplify_mesh(target_face_count=50)
        self.assertFalse(result)

    def test_simplify_mesh_mesh_is_empty(self):
        organ = Organ(name="TestOrganEmptyMesh")
        organ.mesh = MagicMock(spec=trimesh.Trimesh)
        organ.mesh.is_empty = True

        result = organ.simplify_mesh(target_face_count=50)
        self.assertFalse(result)
        organ.mesh.simplify_quadric_decimation.assert_not_called()

    def test_simplify_mesh_invalid_target_face_count(self):
        organ = Organ(name="TestOrganInvalidTarget")
        organ.mesh = MagicMock(spec=trimesh.Trimesh)
        organ.mesh.is_empty = False
        organ.mesh.faces = [([0,0,0])] * 100

        # Store original mock simplify_quadric_decimation to check it's not called
        simplify_mock = organ.mesh.simplify_quadric_decimation

        result_zero = organ.simplify_mesh(target_face_count=0)
        self.assertFalse(result_zero)

        result_negative = organ.simplify_mesh(target_face_count=-10)
        self.assertFalse(result_negative)

        result_string = organ.simplify_mesh(target_face_count='abc')
        self.assertFalse(result_string)

        simplify_mock.assert_not_called()

    def test_simplify_mesh_target_gte_current_faces(self):
        organ = Organ(name="TestOrganNoSimplifyNeeded")
        organ.mesh = MagicMock(spec=trimesh.Trimesh)
        organ.mesh.is_empty = False
        organ.mesh.faces = [([0,0,0])] * 100
        original_mesh = organ.mesh

        simplify_mock = organ.mesh.simplify_quadric_decimation

        result_equal = organ.simplify_mesh(target_face_count=100)
        self.assertTrue(result_equal)

        result_greater = organ.simplify_mesh(target_face_count=150)
        self.assertTrue(result_greater)

        simplify_mock.assert_not_called()
        self.assertIs(organ.mesh, original_mesh) # Mesh should not have changed

    def test_simplify_mesh_results_in_empty_mesh(self):
        organ = Organ(name="TestOrganSimplifyToEmpty")
        organ.mesh = MagicMock(spec=trimesh.Trimesh)
        organ.mesh.is_empty = False
        organ.mesh.faces = [([0,0,0])] * 100
        original_mesh = organ.mesh

        mock_empty_simplified_mesh = MagicMock(spec=trimesh.Trimesh)
        mock_empty_simplified_mesh.is_empty = True
        # simulate that simplification results in 0 faces, which might make it empty
        mock_empty_simplified_mesh.faces = []
        organ.mesh.simplify_quadric_decimation.return_value = mock_empty_simplified_mesh

        result = organ.simplify_mesh(target_face_count=10)

        self.assertFalse(result)
        organ.mesh.simplify_quadric_decimation.assert_called_once_with(face_count=10)
        self.assertIs(organ.mesh, original_mesh) # Mesh should revert or stay as original

    def test_simplify_mesh_results_in_none_mesh(self): # Explicitly test for None return
        organ = Organ(name="TestOrganSimplifyToNone")
        organ.mesh = MagicMock(spec=trimesh.Trimesh)
        organ.mesh.is_empty = False
        organ.mesh.faces = [([0,0,0])] * 100
        original_mesh = organ.mesh

        organ.mesh.simplify_quadric_decimation.return_value = None # Simplification returns None

        result = organ.simplify_mesh(target_face_count=10)

        self.assertFalse(result)
        organ.mesh.simplify_quadric_decimation.assert_called_once_with(face_count=10)
        self.assertIs(organ.mesh, original_mesh)

    def test_simplify_mesh_trimesh_exception(self):
        organ = Organ(name="TestOrganSimplifyException")
        organ.mesh = MagicMock(spec=trimesh.Trimesh)
        organ.mesh.is_empty = False
        organ.mesh.faces = [([0,0,0])] * 100
        original_mesh = organ.mesh

        organ.mesh.simplify_quadric_decimation.side_effect = Exception("Trimesh simplify error")

        result = organ.simplify_mesh(target_face_count=50)

        self.assertFalse(result)
        organ.mesh.simplify_quadric_decimation.assert_called_once_with(face_count=50)
        self.assertIs(organ.mesh, original_mesh)


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
