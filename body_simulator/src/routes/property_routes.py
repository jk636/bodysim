from flask import Blueprint, request, jsonify

# Define the blueprint with URL prefix
property_bp = Blueprint('property_bp', __name__, url_prefix='/properties')

@property_bp.route('/<string:organ_name>', methods=['GET'])
def get_organ_properties(organ_name: str):
    """
    Placeholder route to get properties for a given organ.
    In a real application, this would interact with a loaded model or database.
    """
    print(f"[INFO] Request to GET properties for organ: {organ_name}")
    # Placeholder properties
    mock_properties = {
        "conductivity": 0.5,
        "permittivity": 10.0,
        "density": 1040.0,
        "magnetic_susceptibility": -9e-6,
        "example_source": "placeholder_get_route"
    }
    return jsonify({
        "message": f"Properties for {organ_name} (placeholder)",
        "organ_name": organ_name,
        "properties": mock_properties
    }), 200

@property_bp.route('/<string:organ_name>', methods=['POST'])
def set_organ_properties(organ_name: str):
    """
    Placeholder route to set properties for a given organ.
    In a real application, this would update a loaded model or database.
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "No JSON data provided or invalid content type. Make sure Content-Type is application/json."}), 400

    print(f"[INFO] Request to SET properties for organ: {organ_name} with data: {data}")
    # In a real app, you would:
    # 1. Validate the organ_name.
    # 2. Validate the received data structure and values.
    # 3. Update the properties of the specified organ in your backend model/database.
    #    Example: human_body_model.get_organ(organ_name).set_properties(data)

    return jsonify({
        "message": f"Properties for {organ_name} updated with received data (placeholder)",
        "organ_name": organ_name,
        "received_data": data,
        "status": "success_placeholder"
    }), 200

# Example of how to test with curl:
# GET:
# curl http://localhost:5000/properties/Heart
#
# POST:
# curl -X POST -H "Content-Type: application/json" \
#      -d '{"conductivity": 0.6, "permittivity": 11.0}' \
#      http://localhost:5000/properties/Heart
