# Historical Design Document & Idea Repository

**Note:** This document serves as a historical record of the design process, initial ideas, and brainstorming for the polygonal human body model project. Many features and concepts discussed herein have been implemented or superseded.

For a list of current actionable TODO items, please see `todo.md`.
For a list of planned future enhancements and larger work items, please see `future.md`.

---

Got it! Here’s a **comprehensive design plan, pseudocode, and TODOs** for a polygonal human body model designed for future FDTD (Finite-Difference Time-Domain) electromagnetic and physical simulations. The architecture supports multiple organs as classes, each with customizable physical and electromagnetic properties.

---

# Polygonal Human Body Modeling for FDTD & Multi-Physics Simulations

## Design Goals

* Represent the human body as a composition of polygonal meshes (3D geometry).
* Each organ as a class with physical & electromagnetic properties.
* Properties include: magnetic susceptibility, permeability, permittivity, elasticity, density, conductivity, etc.
* Modular for future expansion (PET/CT/MRI tissue properties, mechanical simulations).
* Support property getters/setters for simulation parameters.
* Allow hierarchy: Body → Organs → Substructures.
* Placeholder methods for mesh loading, FDTD grid mapping, property interpolation.
* Extendable for visualization and integration with solvers.

---

## High-Level Class Structure
> ARCHIVED: The high-level class structure has evolved. Refer to the current code in `body_simulator/src/models/human_body.py` for the actual implementation.
(Refer to original explanation.md for any diagrams if they were present)

---

## Pseudocode with TODOs / Placeholders
> ARCHIVED: Specific pseudocode and placeholders here are likely outdated. Refer to `todo.md` for current pending items and the codebase for implementation details.
(Refer to original explanation.md for any specific pseudocode if present)

---

## TODO / Implementation Plan
> ARCHIVED: These items have been partially addressed or moved. Refer to `todo.md` for current specific tasks and `future.md` for longer-term goals related to this area.

### Mesh Handling
> ARCHIVED: These items have been partially addressed or moved. Refer to `todo.md` for current specific tasks and `future.md` for longer-term goals related to this area.

* [ ] Implement polygon mesh loading (OBJ/STL support) for organs.
* [ ] Implement polygon mesh voxelization/discretization to FDTD grid.
* [ ] Support mesh simplification and hierarchy (e.g., substructures within organs).

### Organ Properties
> ARCHIVED: These items have been partially addressed or moved. Refer to `todo.md` for current specific tasks and `future.md` for longer-term goals related to this area.

* [ ] Collect literature values for EM and mechanical properties for all organs.
* [ ] Implement property interpolation inside organ volume for heterogenous tissues.
* [ ] Support temperature or physiological state-dependent property variations.

### Simulation Integration
> ARCHIVED: These items have been partially addressed or moved. Refer to `todo.md` for current specific tasks and `future.md` for longer-term goals related to this area.

* [ ] Design FDTD grid class and coordinate system to interact with organ voxel data.
* [ ] Map organ properties onto simulation grid with spatial resolution control.
* [ ] Interface with EM solvers or PET/CT simulators.

### Visualization
> ARCHIVED: These items have been partially addressed or moved. Refer to `todo.md` for current specific tasks and `future.md` for longer-term goals related to this area.

* [ ] Create 3D mesh visualizer (e.g., with PyVista, VTK, or Open3D).
* [ ] Enable overlay of properties on meshes with color maps.
* [ ] Support export to formats readable by physics simulation tools.

### Advanced Features (Future)
> MOVED: These items are now tracked in `future.md` if still relevant.

* [ ] Time-dependent properties (e.g., elasticity during pulse).
* [ ] Coupling with fluid dynamics (blood flow) and mechanics (organ deformation).
* [ ] PET tracer distribution and metabolic activity mapping.
* [ ] MRI simulation with relaxation times per organ.

---

## Initial Python Implementation Notes (from explanation.md)
> ARCHIVED: These notes reflect early implementation stages. The current implementation in `body_simulator.src.models.human_body` and related utility files show the developed features like `trimesh` usage, PyVista for visualization, etc.

* **`trimesh`** for mesh loading and basic 3D mesh manipulation (works well with OBJ/STL).
* **`pyvista`** for visualization (it’s a friendly wrapper around VTK).
* Mesh loading: Uses `trimesh.load()` to load OBJ/STL files.
* Visualization: Converts trimesh meshes into `pyvista` meshes and renders them in interactive windows.
* The `HumanBody.visualize()` shows all added organs together with transparency and labels.

---

## Expanded Code Scaffold Features (from explanation.md)
> ARCHIVED: Many of these scaffold features (error handling, voxelization placeholders, substructures, property interpolation stubs, JSON save/load, DICOM placeholders) have been implemented or evolved in the current codebase (see `human_body.py`). Refer to `todo.md` for any remaining specific tasks.

* Robust error handling for mesh loading.
* A voxelization method placeholder to map meshes to grids (e.g., for FDTD).
* Support for organ substructures/hierarchies.
* Property interpolation stub (e.g., spatial interpolation across mesh).
* Placeholder to load DICOM data (conceptual).
* Basic PyQt UI scaffold for organ selection and property editing.
* Save/load full human body model configurations to JSON.
* Placeholder hooks for physics solver integration.

---

## Flask App and UI Features (from explanation.md)
> MOVED/ARCHIVED: Some basic Flask UI for mesh upload and visualization exists. More advanced UI features are tracked in `todo.md` or `future.md` if still relevant.

* Flask UI to upload OBJ meshes and visualize them as PNG snapshots.
* `voxelize_mesh()` converts a trimesh mesh to a voxel grid (boolean numpy array).
* DICOM pipeline reads slices, stacks to volume, applies marching cubes, and exports a mesh.

---

## Detailed Feature TODOs (from explanation.md)
> MOVED/ARCHIVED: These detailed TODOs have been reviewed. Actionable items are in `todo.md`, broader concepts in `future.md`. Many of these, like basic voxelization integration or Three.js visualization, might be future tasks.

# 1. Integrate voxelization into Flask app with live previews
* Implement `encode_image_to_png()` helper
* Add slider/input in UI to select voxel pitch
* Show live preview PNG of voxel projection after voxelization

# 2. Add WebGL 3D visualization for client-side interactive models (Three.js)
* Serve uploaded OBJ files for Three.js to load
* Add controls (orbit, zoom) with `OrbitControls.js`
* Add UI buttons to toggle wireframe, shading, etc.
* Optionally visualize voxel grid with Three.js cubes or point clouds

# 3. Full DICOM uploader and automatic mesh conversion in UI
* Implement multi-file DICOM uploader (e.g., with drag-drop)
* Show progress during upload + conversion
* Load resulting mesh in Three.js viewer dynamically

# 4. Advanced UI with property editing & saving
* Form/UI to select organs from list or 3D model
* Editable fields for physical properties (density, susceptibility, elasticity)
* Save/load model configurations locally or server-side
* Visual feedback showing property impact (e.g., color maps on mesh)

# 5. Run FDTD or other physics simulation using voxel grids
* Implement or integrate FDTD solver (or other physics engines)
* Provide progress updates (WebSocket or polling)
* Visualize simulation output on UI (animated heatmaps, vector fields)
* Allow parameter tweaking & re-run simulation
* Store simulation runs for later analysis

---

## Additional Notes from explanation.md
> ARCHIVED: These are general development notes. Refer to current code structure and `requirements.txt` for module organization and dependencies.

* Use Flask-SocketIO for real-time updates during voxelization or simulation
* Separate modules: `mesh_io.py`, `voxelizer.py`, `simulation.py`, `ui_routes.py`
* Store data efficiently, consider caching or DB for large volumes
* Security: sanitize uploads, control resource usage

---
## Further Implementation Details (from snippet_12.txt)
> ARCHIVED: These notes on key code features and next steps reflect a snapshot in development. The codebase (e.g., `human_body.py`) shows the current state of these features. Remaining next steps are in `todo.md` or `future.md` if applicable.

### Key Code Features Discussed:

- **Mesh loading with file existence and emptiness checks.**
- **Voxelization stub:** creates a placeholder numpy 3D grid; you should implement real voxelization.
- **Sub-organ support:** organs can contain sub-organs hierarchically.
- **Interpolate properties stub:** to calculate spatially varying physics properties.
- **Save/load human body as JSON** including organ hierarchies and properties.
- **DICOM import stub:** notes that pydicom is needed, and this will require volume segmentation + meshing.
- **Physics solver placeholder class** for future integration.
- **PyQt5 UI scaffold:** lets you select organs and edit physical properties live.

### Next Steps from snippet_12.txt:
> ARCHIVED: These notes on key code features and next steps reflect a snapshot in development. The codebase (e.g., `human_body.py`) shows the current state of these features. Remaining next steps are in `todo.md` or `future.md` if applicable.

- Implement real mesh voxelization (e.g., using `trimesh.voxel` or marching cubes).
- Implement mesh/volume segmentation and DICOM conversion pipeline.
- Integrate a physics solver (e.g., openEMS, MEEP) using the voxel grids.
- Add organ-specific meshes & realistic properties.
- Expand UI with visualization controls & multi-organ editing.
- Support exporting/importing more formats and configurations.

---

## Phased Implementation Approach (from snippet_12.txt)
> ARCHIVED: This describes an initial rollout. The current system has implemented parts of these phases. Refer to `todo.md` for immediate next steps.

# 1️⃣ Simple Flask UI to upload, load, and visualize OBJ meshes
(using `trimesh` + `pyvista` backend visualization, streamed to the client)

# 2️⃣ Voxelization algorithm to convert meshes into 3D voxel grids

# 3️⃣ Basic DICOM-to-mesh pipeline skeleton using `pydicom` and `skimage.measure.marching_cubes`

**Requirements mentioned:**
pip install flask trimesh pyvista flask-cors pydicom scikit-image
(Note: some of these are already in the main requirements.txt)

---
