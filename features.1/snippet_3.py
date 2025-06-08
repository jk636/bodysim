# Flask routes to get/set organ properties
@app.route('/get_properties/<organ_name>')
def get_properties(organ_name):
    # Load properties from database or JSON config
    properties = load_properties_for_organ(organ_name)
    return jsonify(properties)

@app.route('/set_properties/<organ_name>', methods=['POST'])
def set_properties(organ_name):
    new_props = request.json
    # Validate and save properties
    save_properties_for_organ(organ_name, new_props)
    return jsonify({"message": "Properties updated"})
