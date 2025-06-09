import os
from flask import Flask, render_template # render_template will be used by main_routes
import tempfile

# Initialize Flask App
app = Flask(__name__)

# Configure Upload Folder
# Create a unique temporary directory for uploads for this app instance
# In a production scenario, you might want a more persistent or configurable location.
temp_dir_for_uploads = tempfile.mkdtemp(prefix="flask_body_sim_uploads_")
app.config['UPLOAD_FOLDER'] = temp_dir_for_uploads

# Ensure the upload folder exists (mkdtemp should create it, but good practice)
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

print(f"Uploads will be stored in: {app.config['UPLOAD_FOLDER']}")

# Blueprint registrations
from ..routes.main_routes import main_bp
from ..routes.mesh_routes import mesh_bp
# Import other blueprints here if you have them, e.g.:
from ..routes.simulation_routes import sim_bp
from ..routes.property_routes import property_bp

app.register_blueprint(main_bp)
app.register_blueprint(mesh_bp)
app.register_blueprint(sim_bp)
app.register_blueprint(property_bp)
# ...

# The main index route is now in main_routes.py
# For now, if you run this directly without registering main_bp,
# the root path '/' won't be defined yet.

if __name__ == '__main__':
    # Blueprints are registered above, so they will be active.
    print("Attempting to run Flask app with registered blueprints...")
    print(f"Registered blueprints: {[bp.name for bp in app.blueprints.values()]}")
    app.run(debug=True, host='0.0.0.0') # Host 0.0.0.0 to make it accessible
