"""
Allow controlled command line access to certain API endpoints
"""
from flask_executor import Executor
from flask_shell2http import Shell2HTTP
from pathlib import Path

from api import app, config_data

active_endpoints = config_data.get('DOCKER_ENDPOINTS', False)
base_url_prefix = "/api/"

if not active_endpoints:
    app.logger.warning("DOCKER_ENDPOINTS not set; no endpoints available")
else:
    # Setup Executor
    executor = Executor(app)
    shell2http = Shell2HTTP(app=app, executor=executor, base_url_prefix=base_url_prefix)

    # Local path
    if config_data.get('4CAT_DATASETS_PATH', False):
        fourcat_path = Path(config_data.get('4CAT_DATASETS_PATH'))
    else:
        app.logger.warning("4CAT_DATASETS_PATH not set; local endpoints not available")
        fourcat_path = None

    # Remote path
    if config_data.get('UPLOAD_FOLDER_PATH', False):
        uploads_path = Path(config_data.get('UPLOAD_FOLDER_PATH'))
    else:
        app.logger.warning("UPLOAD_FOLDER_PATH not set; remote endpoints not available")
        uploads_path = None

    # Register endpoints
    for endpoint, endpoint_data in active_endpoints.items():
        if fourcat_path and endpoint_data['local']:
            shell2http.register_command(endpoint=f"{endpoint}_local",
                                        command_name=f"docker run --rm -v {fourcat_path}:{endpoint_data['data_path']} {'--gpus all ' if config_data.get('GPU_ENABLED', False) else ''}{endpoint_data['image_name']} {endpoint_data['command']}")
            app.config["endpoints"].add(f"{base_url_prefix}{endpoint}_local")
        if uploads_path and endpoint_data['remote']:
            shell2http.register_command(endpoint=f"{endpoint}_remote",
                                        command_name=f"docker run --rm -v {uploads_path}:{endpoint_data['data_path']} {'--gpus all ' if config_data.get('GPU_ENABLED', False) else ''}{endpoint_data['image_name']} {endpoint_data['command']}")
            app.config["endpoints"].add(f"{base_url_prefix}{endpoint}_remote")

