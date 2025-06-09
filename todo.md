# Actionable TODOs

## Mesh Handling
- [ ] Implement robust polygon mesh loading (OBJ/STL) for all organ scenarios.
- [x] Implement full polygon mesh voxelization/discretization to FDTD/voxel grid (was: current `voxelize_mesh` is a placeholder). Enhanced `mesh_utils.voxelize_mesh` with watertightness checks, hole filling, and explicit interior fill.
- [ ] Implement or enhance support for mesh simplification.

## Organ Properties
- [ ] Collect literature values for EM and mechanical properties for all relevant organs.

## Simulation Integration
- [ ] Design and implement FASTM grid class and coordinate system for organ voxel data interaction.
- [ ] Implement mapping of organ properties onto the simulation grid with spatial resolution control.

## Visualization
- [ ] Enable overlay of physical/EM properties on meshes using color maps in visualization.
- [ ] Support export of model/grid data to formats readable by common physics simulation tools.

## Flask App Enhancements
- [x] Integrate voxelization into Flask app with live previews:
    - [x] Implement `encode_image_to_png()` helper (confirmed present and used for snapshots/previews).
    - [x] Add UI controls (e.g., slider/input) to select voxel pitch/resolution (existing input used, dynamic updates implemented).
    - [x] Display a live preview PNG (or similar) of the voxel grid projection after voxelization (implemented via dynamic updates on upload and pitch change).

## DICOM Pipeline
- [ ] Implement a functional DICOM-to-mesh conversion pipeline (current one is a basic skeleton/stub). This includes robust volume segmentation from DICOM slices.

## General
- [ ] Add more organ-specific meshes with realistic geometries.
- [ ] Expand UI/API with more advanced visualization controls.
- [ ] Enhance support for exporting/importing various model and configuration formats.
