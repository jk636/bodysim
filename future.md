# Future Enhancements & Complex Features

## Advanced Organ Properties
- [ ] Implement property interpolation inside organ volumes for heterogeneous tissues.
- [ ] Support temperature-dependent or physiological state-dependent property variations.

## Advanced Simulation Integration
- [ ] Interface with external EM solvers (e.g., openEMS, MEEP) or PET/CT simulators.
- [ ] Implement or integrate a full FASTM (or other physics) solver.
- [ ] Develop capabilities to run physics simulations using the generated voxel grids.
    - [ ] Provide progress updates for simulations (e.g., via WebSocket or polling).
    - [ ] Visualize simulation outputs on the UI (e.g., animated heatmaps, vector fields).
    - [ ] Allow parameter tweaking and re-running simulations.
    - [ ] Store simulation run data for later analysis and comparison.

## Advanced Features
- [ ] Model time-dependent properties (e.g., tissue elasticity changes during a cardiac cycle).
- [ ] Couple simulations with fluid dynamics (e.g., blood flow modeling).
- [ ] Couple simulations with structural mechanics (e.g., organ deformation).
- [ ] Implement PET tracer distribution and metabolic activity mapping.
- [ ] Enable MRI simulation capabilities, including relaxation times (T1, T2) per organ.

## Web UI/UX Overhaul (Client-Side Rendering & Interactivity)
- [ ] Transition to WebGL-based 3D visualization for client-side interactive models (e.g., using Three.js).
    - [ ] Serve uploaded/generated OBJ/3D model files for Three.js to load directly.
    - [ ] Implement standard 3D view controls (orbit, zoom, pan) using libraries like `OrbitControls.js`.
    - [ ] Add UI buttons/controls to toggle wireframe rendering, surface shading, transparency, etc.
    - [ ] Optionally, visualize the voxel grid directly in Three.js using cubes or point clouds for detailed inspection.

## Comprehensive DICOM Workflow in UI
- [ ] Implement a multi-file DICOM series uploader (e.g., with drag-and-drop support).
- [ ] Show user-friendly progress indicators during DICOM upload, processing, and mesh conversion.
- [ ] Dynamically load and display the resulting 3D mesh (from DICOM) in the WebGL/Three.js viewer.

## Advanced UI for Model Configuration & Property Editing
- [ ] Develop a UI form/system to select organs from a list or directly by clicking on the 3D model.
- [ ] Provide editable fields for all relevant physical and EM properties (e.g., density, susceptibility, permittivity, elasticity).
- [ ] Implement functionality to save and load complete human body model configurations (including geometries, properties, hierarchies) locally (browser) or server-side (user accounts/database).
- [ ] Give visual feedback in the UI showing the impact of property changes (e.g., dynamic color maps on the 3D mesh).

## Architectural & Infrastructure
- [ ] Implement real-time updates using Flask-SocketIO (or similar) for long processes like voxelization or simulation.
- [ ] Refactor codebase into more clearly defined modules (e.g., `mesh_io.py`, `voxelizer.py`, `simulation.py`, `ui_routes.py`) if not already optimal.
- [ ] Implement efficient data storage strategies, possibly including caching or a database for large datasets or user configurations.
- [ ] Enhance security: sanitize all user uploads, implement rate limiting or resource usage controls for computationally intensive tasks.
