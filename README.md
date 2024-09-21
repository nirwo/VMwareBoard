# VMware vCenter Management Application

This application provides a web-based interface for managing VMware vCenter environments. It allows users to connect to a vCenter server, view and manage virtual machines, and perform various operations such as power management and snapshot creation.

## Features

- Connect to vCenter server
- View list of virtual machines
- Power on/off virtual machines
- Create, revert, and delete snapshots
- View VM details including networks and datastores
- Dark mode support

## Technology Stack

- Backend: Python with Flask
- Frontend: Vue.js
- API: RESTful
- vSphere SDK: pyVmomi

## Prerequisites

- Python 3.7+
- Node.js and npm
- VMware vCenter Server
- pyVmomi library

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/vmware-vcenter-management.git
   cd vmware-vcenter-management
   ```

2. Set up a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install backend dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install frontend dependencies:
   ```
   cd app/frontend
   npm install
   cd ../..
   ```

5. Deactivate the virtual environment when you're done:
   ```
   deactivate
   ```

Note: Always activate the virtual environment before running the application:
```
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

## Development

To update dependencies after making changes:

1. Update backend dependencies:
   ```
   pip freeze > requirements.txt
   ```

2. Update frontend dependencies:
   ```
   npm update
   ```

3. Install updated dependencies:
   ```
   pip install -r requirements.txt
   npm install
   ```

## Configuration

1. Create a `.env` file in the `app/backend` directory with the following content:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   ```

2. Update the vCenter server details in `app/frontend/app.js` if necessary.

## Running the Application

1. Start the backend server:
   ```
   cd app/backend
   flask run --port=5079
   ```

2. Open `app/frontend/index.html` in a web browser.

## Usage

1. Connect to your vCenter server using the login form.
2. Browse and manage your virtual machines using the web interface.
3. Use the various buttons and forms to perform actions on your VMs.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- VMware for providing the vSphere SDK
- The Vue.js team for the excellent frontend framework
- The Flask team for the lightweight WSGI web application framework
