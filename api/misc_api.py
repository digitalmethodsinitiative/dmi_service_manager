from flask import jsonify
import subprocess
import shlex
import json

from api import app, config_data


@app.route('/api/', methods=['GET'])
def list_endpoints():
    endpoints = {
        'endpoints': [
            'check_gpu_mem'
        ]
    }
    return jsonify(endpoints), 200

@app.route('/api/check_gpu_mem/<string:service_id>', methods=['GET'])
def check_gpu_mem(service_id):
    """
    Check GPU memory usage for a service

    Runs the container with a command that returns the GPU memory usage; assumes torch is installed
    """
    if not config_data.get('GPU_ENABLED', False):
        return jsonify({'reason': 'GPU not enabled on this instance of DMI Service Manager'}), 400

    if service_id not in config_data.get("DOCKER_ENDPOINTS").keys():
        return jsonify({'reason': 'Service not found'}), 404

    command = shlex.split("docker run --rm --gpus all %s python3 -c \"import torch; import json; current_mem=torch.cuda.mem_get_info(); print(json.dumps({'gpu_total_mem': current_mem[1], 'gpu_free_mem': current_mem[0]}))\"" % service_id)
    remote = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if remote.stderr:
        return jsonify({'reason': remote.stderr}), 500

    if remote.stdout:
        results = json.loads(remote.stdout.split("\n")[-2])
        if results['gpu_free_mem'] == 0:
            return jsonify({'reason': 'GPU not available; unable to use %s' % service_id, 'memory': results}), 503
        else:
            return jsonify({'reason': 'GPU available', 'memory': results}), 200

    return jsonify({'reason': 'Unknown error'}), 500
