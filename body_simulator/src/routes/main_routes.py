from flask import Blueprint, render_template

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    """Serves the main index page."""
    # This assumes 'index.html' is in a 'templates' folder configured for the Flask app.
    return render_template('index.html')

@main_bp.route('/hello') # Example route to test blueprint
def hello():
    return "Hello from main_bp!"
