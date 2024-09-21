from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import ssl
import os

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# VMware vCenter connection details
VCENTER_HOST = "your_vcenter_host"
VCENTER_USER = "your_vcenter_username"
VCENTER_PASSWORD = "your_vcenter_password"

def get_vcenter_connection():
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE
    return SmartConnect(host=VCENTER_HOST, user=VCENTER_USER, pwd=VCENTER_PASSWORD, sslContext=context)

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
        vms.append({
            'name': child.name,
            'power_state': child.runtime.powerState,
            'cpu': child.config.hardware.numCPU,
            'memory': child.config.hardware.memoryMB
        })
    
    Disconnect(si)
    return jsonify(vms)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
