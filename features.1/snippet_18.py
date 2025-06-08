# Create human body
body = HumanBody()

# Add brain with mesh
brain = Brain("meshes/brain.obj")
body.add_organ(brain)

# Add more organs similarly...

# Visualize human body
body.visualize()

# Prepare simulation grid (placeholder)
fdtd_grid = "3D simulation grid"

# Map organs to simulation grid
body.map_all_to_fdtd(fdtd_grid)
