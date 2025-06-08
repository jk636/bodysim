# Flask route for DICOM upload (multiple files)
@app.route('/upload_dicom', methods=['POST'])
def upload_dicom():
    files = request.files.getlist('dicom_files')
    temp_dir = tempfile.mkdtemp()

    for f in files:
        f.save(os.path.join(temp_dir, f.filename))

    # Load DICOM series & convert to mesh
    volume = load_dicom_volume(temp_dir)
    mesh = volume_to_mesh(volume, threshold=300)

    mesh_path = os.path.join(temp_dir, 'dicom_mesh.obj')
    mesh.export(mesh_path)

    # Store mesh path/session info for visualization
    session['dicom_mesh_path'] = mesh_path
    return jsonify({"message": "DICOM processed", "mesh_url": f"/download_mesh/{mesh_path}"})

# Route to serve mesh file for Three.js visualization
@app.route('/download_mesh/<path:filename>')
def download_mesh(filename):
    return send_file(filename, mimetype='application/octet-stream')
