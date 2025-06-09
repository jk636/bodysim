# Human Body Simulator (BodySim)

## 1. Project Overview

BodySim is a Python-based web application designed for simulating aspects of the human body, with an initial focus on preparing models for FDTD (Finite-Difference Time-Domain) electromagnetic simulations and other physics applications.

**Core Capabilities:**

*   **Mesh Import:** Supports uploading 3D models in OBJ format.
*   **DICOM Processing:** Allows uploading series of DICOM files, which are then processed to reconstruct a 3D volume and convert it into an OBJ mesh.
*   **Voxelization:** Converts mesh models into a 3D voxel grid, with a 2D PNG projection available as a preview.
*   **3D Visualization:**
    *   Server-side rendering of static PNG images for quick model previews (using PyVista).
    *   Client-side interactive 3D rendering of OBJ models using Three.js in a separate viewer page.
*   **Property Management (Placeholder):** Includes API endpoints for getting and setting physical/electromagnetic properties of organs (currently placeholder functionality).
*   **Simulation (Placeholder):** Includes API endpoints for initiating simulations like FDTD (currently placeholder functionality).

## 2. Project Structure

The project is organized as follows:

*   `body_simulator/`: Main application package.
    *   `src/`: Source code.
        *   `main/`: Flask application setup (`app.py`).
        *   `models/`: Core data models, including `HumanBody` and `Organ` classes.
        *   `utils/`: Utility functions for DICOM processing (`dicom_utils.py`) and mesh operations (`mesh_utils.py`).
        *   `routes/`: Flask Blueprints defining API endpoints for different functionalities (e.g., `mesh_routes.py`, `property_routes.py`).
        *   `templates/`: HTML templates for the web interface (`index.html`, `visualize_mesh.html`).
*   `tests/`: Unit tests for models, utils, and routes.
    *   `models/`: Tests for data models.
    *   `utils/`: Tests for utility functions.
    *   `conftest.py`: Pytest configuration, including Python path adjustments.
*   `DESIGN.md`: Detailed design notes, future plans, and architectural considerations (consolidated from original planning documents).
*   `requirements.txt`: A list of Python dependencies required for the project.
*   `UT.MD`: Notes on the status and coverage of unit tests.
*   `README.md`: This file.

## 3. Setup and Installation

Follow these steps to set up and run the BodySim application locally.

**Prerequisites:**

*   Python 3.8 or newer.
*   `pip` (Python package installer).
*   `git` (for cloning the repository).

**Steps:**

1.  **Clone the Repository:**
    ```bash
    git clone https://your-repository-url-here/bodysim.git
    cd bodysim
    ```
    *(Replace `https://your-repository-url-here/bodysim.git` with the actual repository URL)*

2.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv venv
    ```
    Activate the environment:
    *   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```

3.  **Install Dependencies:**
    With the virtual environment activated, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## 4. Running the Application

Once the setup is complete, you can run the Flask development server:

```bash
python body_simulator/src/main/app.py
```

The application will start, and you should see output indicating it's running, typically including:
```
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Or, if host='0.0.0.0' is used: Running on all addresses (http://your-local-ip:5000/)
```
Open your web browser and navigate to `http://127.0.0.1:5000/` to access the application.

## 5. Available Features and API Endpoints

### Web Interface (`/`)

The main web page provides access to the following features:

*   **Upload OBJ Models:** Upload a `.obj` file. A static PNG preview is generated, and an option to view it in an interactive 3D viewer (Three.js) becomes available.
*   **Upload DICOM Series:** Upload a folder containing DICOM slices (`.dcm` or files with no extension). The server processes these into a 3D volume, converts it to an OBJ mesh, and provides static and interactive viewing options for the generated mesh.
*   **Voxelize Meshes:** After uploading an OBJ or generating a mesh from DICOMs, specify the filename and a voxel pitch. The server will voxelize the mesh and return a 2D PNG projection as a preview.

### Key API Endpoints

*   `GET /`: Serves the main HTML application page.
*   `POST /mesh/upload_obj`: Uploads a single OBJ mesh file.
    *   **Request:** `multipart/form-data` with a file part named `mesh`.
    *   **Response:** JSON confirming success/failure, including filename and URL for static visualization.
*   `POST /mesh/upload_dicom`: Uploads a series of DICOM files.
    *   **Request:** `multipart/form-data` with a file part named `dicom_files` (can be multiple files).
    *   **Response:** JSON confirming success/failure, including the filename of the generated OBJ mesh and its static visualization URL.
*   `GET /mesh/visualize_uploaded_obj?filename=<filename>`: Returns a server-side rendered PNG image of the specified OBJ model (located in the upload folder).
*   `GET /mesh/get_model/<filename>`: Serves the raw OBJ model file. Used by the client-side Three.js viewer.
*   `POST /mesh/voxelize`: Voxelizes a specified mesh file.
    *   **Request:** JSON payload like `{"filename": "uploaded_mesh.obj", "pitch": 1.0}`.
    *   **Response:** A PNG image (2D projection of the voxel grid).
*   `GET /properties/<organ_name>`: (Placeholder) Get properties for a specified organ.
*   `POST /properties/<organ_name>`: (Placeholder) Set properties for a specified organ.
*   `POST /simulation/run_fdtd`: (Placeholder) Initiate an FDTD simulation.

## 6. Running Tests

Unit tests are implemented using `pytest`. To run the tests:

1.  Ensure you have activated your virtual environment and installed all dependencies from `requirements.txt` (including `pytest` and `pytest-mock`).
2.  Navigate to the project root directory (the one containing the `tests/` and `body_simulator/` folders).
3.  Run `pytest`:
    ```bash
    pytest
    ```
    Or, for more verbose output:
    ```bash
    pytest -v
    ```
Test results will be displayed in the terminal. Test files are located in the `tests/` directory. Refer to `UT.MD` for notes on test status and coverage.

## 7. DESIGN.md Review Note

The `DESIGN.md` file contains detailed notes from the initial planning stages. While much of the described functionality has been implemented, some parts still represent future plans or alternative design considerations. A future task should involve reviewing `DESIGN.md` to:
*   Archive or clearly mark outdated design ideas.
*   Update it to reflect the current architecture accurately.
*   Extract any still-relevant future work into a proper issue tracking system or a dedicated "Future Work" section.
For now, `DESIGN.md` serves as a historical record and a source of ideas for further development.