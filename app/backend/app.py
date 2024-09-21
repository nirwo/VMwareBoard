from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import ssl
import os
from dotenv import load_dotenv
from datetime import datetime
import atexit

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Load environment variables
load_dotenv()

# VMware vCenter connection details
VCENTER_HOST = os.getenv('VCENTER_HOST')
VCENTER_USER = os.getenv('VCENTER_USER')
VCENTER_PASSWORD = os.getenv('VCENTER_PASSWORD')

def get_vcenter_connection():
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    si = SmartConnect(host=VCENTER_HOST, user=VCENTER_USER, pwd=VCENTER_PASSWORD, sslContext=context)
    atexit.register(Disconnect, si)
    return si

def get_vm_by_name(si, vm_name):
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5079)
