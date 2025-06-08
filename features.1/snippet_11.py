import os
from flask import Flask, request, render_template, send_file, jsonify
import trimesh
import pyvista as pv
import tempfile
import numpy as np

app = Flask(__name__)
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Keep last loaded mesh globally (for simplicity)
loaded_mesh = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_mesh():
    global loaded_mesh
    if 'mesh' not in request.files:
        return jsonify({"error": "No mesh file provided"}), 400

    file = request.files['mesh']
    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)

    try:
        loaded_mesh = trimesh.load(filename)
        if loaded_mesh.is_empty:
            return jsonify({"error": "Empty mesh loaded"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to load mesh: {e}"}), 500

    return jsonify({"message": f"Loaded mesh '{file.filename}'", "vertices": len(loaded_mesh.vertices)})

@app.route('/visualize')
def visualize():
    global loaded_mesh
    if loaded_mesh is None:
        return "No mesh loaded.", 400

    # Create PyVista plotter and export screenshot
    pv_mesh = pv.wrap(loaded_mesh)
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(pv_mesh, color='lightblue')
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], 'mesh_visualization.png')
    plotter.show(screenshot=img_path, auto_close=True)

    return send_file(img_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
