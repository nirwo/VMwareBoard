"""
VMware vCenter Management API

This Flask application provides a RESTful API for managing VMware vCenter environments.
It allows users to connect to a vCenter server, manage virtual machines, and perform
various operations such as power management and snapshot creation.

Author: Your Name
Date: September 21, 2024
"""

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import ssl
import os
from dotenv import load_dotenv
from datetime import datetime
import atexit
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__, static_folder='../frontend')
app.config['MAX_PARALLEL_TASKS'] = 5  # Default value, can be changed
executor = ThreadPoolExecutor(max_workers=app.config['MAX_PARALLEL_TASKS'])
CORS(app)
app.secret_key = os.urandom(24)  # Set a secret key for session management

# Load environment variables
load_dotenv()

def get_vcenter_connection():
    """
    Retrieve or create a connection to the vCenter server.
    
    Returns:
        ServiceInstance: A connection to the vCenter server, or None if connection fails.
    """
    if 'vcenter_connection' not in session:
        return None
    
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    try:
        si = SmartConnect(
            host=session['vcenter_connection']['host'],
            user=session['vcenter_connection']['user'],
            pwd=session['vcenter_connection']['password'],
            sslContext=context
        )
        atexit.register(Disconnect, si)
        return si
    except Exception as e:
        print(f"Error connecting to vCenter: {str(e)}")
        return None

@app.route('/api/vcconnect', methods=['POST'])
def vcconnect():
    """
    Connect to a vCenter server.
    
    Expects JSON payload with 'host', 'user', and 'password' fields.
    
    Returns:
        JSON: Status of the connection attempt.
    """
    data = request.json
    host = data.get('host')
    user = data.get('user')
    password = data.get('password')
    
    if not all([host, user, password]):
        return jsonify({'status': 'error', 'message': 'Missing connection details'}), 400
    
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    try:
        si = SmartConnect(host=host, user=user, pwd=password, sslContext=context)
        atexit.register(Disconnect, si)
        session['vcenter_connection'] = {'host': host, 'user': user, 'password': password}
        return jsonify({'status': 'success', 'message': 'Connected to vCenter successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to connect to vCenter: {str(e)}'}), 400

@app.route('/api/vcdisconnect', methods=['POST'])
def vcdisconnect():
    """
    Disconnect from the vCenter server.
    
    Returns:
        JSON: Status of the disconnection.
    """
    if 'vcenter_connection' in session:
        del session['vcenter_connection']
    return jsonify({'status': 'success', 'message': 'Disconnected from vCenter'})

@app.route('/api/vcstatus', methods=['GET'])
def vcstatus():
    """
    Get the current vCenter connection status.
    
    Returns:
        JSON: Current connection status and host (if connected).
    """
    if 'vcenter_connection' in session:
        return jsonify({'status': 'connected', 'host': session['vcenter_connection']['host']})
    else:
        return jsonify({'status': 'disconnected'})

def get_vm_by_name(si, vm_name):
    """
    Retrieve a virtual machine object by its name.
    
    Args:
        si (ServiceInstance): vCenter connection instance.
        vm_name (str): Name of the virtual machine.
    
    Returns:
        vim.VirtualMachine: The virtual machine object, or None if not found.
    """
    content = si.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = content.viewManager.CreateContainerView(container, view_type, recursive)
    children = container_view.view
    for child in children:
        if child.name == vm_name:
            return child
    return None

def get_vm_snapshots(vm):
    snapshots = []
    if vm.snapshot:
        for snap in vm.snapshot.rootSnapshotList:
            snapshots.append({
                'name': snap.name,
                'description': snap.description,
                'creation_time': snap.createTime.isoformat(),
                'id': snap.id,
                'state': snap.state
            })
    return snapshots

def get_vm_networks(vm):
    networks = []
    for network in vm.network:
        networks.append({
            'name': network.name,
            'accessible': network.summary.accessible
        })
    return networks

def get_vm_datastores(vm):
    datastores = []
    for datastore in vm.datastore:
        datastores.append({
            'name': datastore.name,
            'capacity': datastore.summary.capacity,
            'freeSpace': datastore.summary.freeSpace
        })
    return datastores

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/vms', methods=['GET'])
def get_vms():
    """
    Retrieve information about all virtual machines in the vCenter inventory.
    
    Returns:
        JSON: List of virtual machines with their details.
    """
    si = get_vcenter_connection()
    content = si.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = content.viewManager.CreateContainerView(container, view_type, recursive)
    children = container_view.view
    
    vms = []
    for child in children:
        vm_info = {
            'name': child.name,
            'power_state': child.runtime.powerState,
            'cpu': child.config.hardware.numCPU,
            'memory': child.config.hardware.memoryMB,
            'guest_os': child.config.guestFullName,
            'ip_address': child.guest.ipAddress,
            'snapshots': get_vm_snapshots(child),
            'networks': get_vm_networks(child),
            'datastores': get_vm_datastores(child),
            'tools_status': child.guest.toolsStatus,
            'tools_version': child.guest.toolsVersion,
            'uuid': child.config.uuid
        }
        vms.append(vm_info)
    
    return jsonify(vms)

@app.route('/api/vm/<string:vm_name>/power', methods=['POST'])
def power_vm(vm_name):
    """
    Power on or off a virtual machine.
    
    Args:
        vm_name (str): Name of the virtual machine.
    
    Returns:
        JSON: Status of the power operation.
    """
    action = request.json.get('action')
    si = get_vcenter_connection()
    content = si.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = content.viewManager.CreateContainerView(container, view_type, recursive)
    children = container_view.view
    
    for child in children:
        if child.name == vm_name:
            if action == 'on' and child.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                child.PowerOn()
            elif action == 'off' and child.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                child.PowerOff()
            break
    
    Disconnect(si)
    return jsonify({'status': 'success', 'message': f'VM {vm_name} power {action} initiated'})

@app.route('/api/vm/<string:vm_name>/snapshot', methods=['POST'])
def create_snapshot(vm_name):
    """
    Create a snapshot of a virtual machine.
    
    Args:
        vm_name (str): Name of the virtual machine.
    
    Returns:
        JSON: Status of the snapshot creation operation.
    """
    si = get_vcenter_connection()
    vm = get_vm_by_name(si, vm_name)
    if not vm:
        Disconnect(si)
        return jsonify({'status': 'error', 'message': 'VM not found'}), 404

    snapshot_name = request.json.get('name', f'Snapshot-{datetime.now().isoformat()}')
    description = request.json.get('description', '')

    task = vm.CreateSnapshot_Task(name=snapshot_name, description=description, memory=True, quiesce=False)
    Disconnect(si)
    return jsonify({'status': 'success', 'message': f'Snapshot creation initiated for VM {vm_name}'})

@app.route('/api/vm/<string:vm_name>/snapshot/<string:snapshot_id>/revert', methods=['POST'])
def revert_snapshot(vm_name, snapshot_id):
    """
    Revert a virtual machine to a specific snapshot.
    
    Args:
        vm_name (str): Name of the virtual machine.
        snapshot_id (str): ID of the snapshot to revert to.
    
    Returns:
        JSON: Status of the revert operation.
    """
    si = get_vcenter_connection()
    vm = get_vm_by_name(si, vm_name)
    if not vm:
        Disconnect(si)
        return jsonify({'status': 'error', 'message': 'VM not found'}), 404

    snapshot = next((snap for snap in vm.snapshot.rootSnapshotList if snap.id == snapshot_id), None)
    if not snapshot:
        Disconnect(si)
        return jsonify({'status': 'error', 'message': 'Snapshot not found'}), 404

    task = snapshot.snapshot.RevertToSnapshot_Task()
    Disconnect(si)
    return jsonify({'status': 'success', 'message': f'Revert to snapshot initiated for VM {vm_name}'})

@app.route('/api/vm/<string:vm_name>/snapshot/<string:snapshot_id>', methods=['DELETE'])
def delete_snapshot(vm_name, snapshot_id):
    """
    Delete a specific snapshot of a virtual machine.
    
    Args:
        vm_name (str): Name of the virtual machine.
        snapshot_id (str): ID of the snapshot to delete.
    
    Returns:
        JSON: Status of the delete operation.
    """
    si = get_vcenter_connection()
    vm = get_vm_by_name(si, vm_name)
    if not vm:
        Disconnect(si)
        return jsonify({'status': 'error', 'message': 'VM not found'}), 404

    snapshot = next((snap for snap in vm.snapshot.rootSnapshotList if snap.id == snapshot_id), None)
    if not snapshot:
        Disconnect(si)
        return jsonify({'status': 'error', 'message': 'Snapshot not found'}), 404

    task = snapshot.snapshot.RemoveSnapshot_Task(removeChildren=False)
    Disconnect(si)
    return jsonify({'status': 'success', 'message': f'Snapshot deletion initiated for VM {vm_name}'})

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """
    Retrieve all VM templates from vCenter.
    
    Returns:
        JSON: List of available VM templates.
    """
    si = get_vcenter_connection()
    content = si.RetrieveContent()
    container = content.rootFolder
    view_type = [vim.VirtualMachine]
    recursive = True
    container_view = content.viewManager.CreateContainerView(container, view_type, recursive)
    children = container_view.view
    
    templates = [child.name for child in children if child.config.template]
    Disconnect(si)
    return jsonify(templates)

@app.route('/api/customizations', methods=['GET'])
def get_customizations():
    """
    Retrieve all VMware customization specifications from vCenter.
    
    Returns:
        JSON: List of available customization specifications.
    """
    si = get_vcenter_connection()
    content = si.RetrieveContent()
    customization_spec_manager = content.customizationSpecManager
    
    customizations = [spec.name for spec in customization_spec_manager.info]
    Disconnect(si)
    return jsonify(customizations)

@app.route('/api/provision', methods=['POST'])
def provision_vms():
    """
    Provision multiple VMs based on the provided specifications.
    
    Expects JSON payload with:
    - template_name: Name of the template to use
    - customization_spec: Name of the customization specification to use
    - vm_count: Number of VMs to provision
    - vm_name_prefix: Prefix for the VM names
    
    Returns:
        JSON: Status of the provisioning operation.
    """
    data = request.json
    template_name = data.get('template_name')
    customization_spec = data.get('customization_spec')
    vm_count = data.get('vm_count', 1)
    vm_name_prefix = data.get('vm_name_prefix', 'NewVM')
    
    si = get_vcenter_connection()
    content = si.RetrieveContent()
    
    # Get the template
    template = get_vm_by_name(si, template_name)
    if not template:
        Disconnect(si)
        return jsonify({'status': 'error', 'message': 'Template not found'}), 404
    
    # Get the customization specification
    customization_spec_manager = content.customizationSpecManager
    customization = customization_spec_manager.GetCustomizationSpec(customization_spec)
    if not customization:
        Disconnect(si)
        return jsonify({'status': 'error', 'message': 'Customization specification not found'}), 404
    
    # Get the first datastore and resource pool (you might want to make this configurable)
    datastore = content.rootFolder.childEntity[0].datastore[0]
    resource_pool = content.rootFolder.childEntity[0].hostFolder.childEntity[0].resourcePool
    
    def clone_vm(i):
        vm_name = f"{vm_name_prefix}-{i+1}"
        clonespec = vim.vm.CloneSpec()
        clonespec.location = vim.vm.RelocateSpec(datastore=datastore, pool=resource_pool)
        clonespec.customization = customization.spec
        clonespec.powerOn = True
        
        task = template.Clone(folder=template.parent, name=vm_name, spec=clonespec)
        return task
    
    # Submit tasks to the executor
    futures = [executor.submit(clone_vm, i) for i in range(vm_count)]
    
    Disconnect(si)
    return jsonify({'status': 'success', 'message': f'Provisioning of {vm_count} VMs initiated'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5079)
