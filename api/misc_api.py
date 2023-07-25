from flask import jsonify
import subprocess
import shlex
import json

from api import app, config_data


@app.route('/api/check_gpu_mem/<string:service_id>', methods=['POST'])
def check_gpu_mem(service_id):
    """
    Check GPU memory usage for a service

    Runs the container with a command that returns the GPU memory usage; assumes torch is installed
    """
    if not config_data.get('GPU_ENABLED', False):
        return jsonify({'reason': 'GPU not enabled on this instance of DMI Service Manager'}), 400

    if service_id not in ['whisper', 'clip']:
        # TODO: manage services interactively
        return jsonify({'reason': 'Service not found'}), 404

    command = shlex.split("docker run --rm --gpus all %s python3 -c \"import torch; import json; print(json.dumps({'gpu_total_mem': torch.cuda.get_device_properties(0).total_memory, 'gpu_reserved_mem': torch.cuda.memory_reserved(0), 'gpu_free_mem': torch.cuda.memory_reserved(0) - torch.cuda.memory_allocated(0)}))\"" % service_id)
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
