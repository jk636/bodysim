import sys
import os

# Add the project root to the Python path to allow direct imports of body_simulator
# This assumes tests are run from the project root directory (where 'tests' and 'body_simulator' are)
# or that pytest otherwise correctly discovers the root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# If you need any global fixtures, they can be defined here.
# For example, a fixture to set up a temporary UPLOAD_FOLDER for all tests
# that might need it, though the current plan is to do it per test client fixture.
