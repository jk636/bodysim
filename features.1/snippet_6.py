# Flask route to voxelize uploaded mesh and return voxel data preview (e.g., slice or volume summary)
@app.route('/voxelize', methods=['POST'])
def voxelize_mesh_endpoint():
    global loaded_mesh
    if loaded_mesh is None:
        return jsonify({"error": "No mesh loaded"}), 400

    pitch = float(request.form.get('pitch', 1.0))
    
    try:
        voxels = voxelize_mesh(loaded_mesh, pitch=pitch)  # from previous voxelize_mesh function
        # Create a 2D projection image for preview, e.g., max projection along z-axis
        voxel_projection = np.max(voxels, axis=2).astype(np.uint8) * 255
        # Convert voxel_projection to PNG bytes for sending
        png_bytes = encode_image_to_png(voxel_projection)  # implement with PIL or cv2

        return send_file(io.BytesIO(png_bytes), mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
