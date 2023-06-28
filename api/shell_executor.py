"""
Allow controlled command line access to certain API endpoints
"""
from flask_executor import Executor
from flask_shell2http import Shell2HTTP
from pathlib import Path

from api import app, config_data

# Setup Executor
executor = Executor(app)
shell2http = Shell2HTTP(app=app, executor=executor, base_url_prefix="/api/")

# Register commands

# Local Endpoints
if config_data.get('4CAT_DATASETS_PATH', False):
    fourcat_path = Path(config_data.get('4CAT_DATASETS_PATH'))

    # Whisper
    shell2http.register_command(endpoint="whisper_local", command_name=f"docker run --rm -v {fourcat_path}:/app/data/ {'--gpus all ' if config_data.get('GPU_ENABLED', False) else ''}whisper whisper")
    # CLIP
    shell2http.register_command(endpoint="clip_local", command_name=f"docker run --rm -v {fourcat_path}:/app/data/ {'--gpus all ' if config_data.get('GPU_ENABLED', False) else ''}clip python3 clip_interface.py")
else:
    app.logger.warning("4CAT_DATASETS_PATH not set; local endpoints not available")

# Remote Endpoints
if config_data.get('UPLOAD_FOLDER_PATH', False):
    uploads_path = Path(config_data.get('UPLOAD_FOLDER_PATH'))
    shell2http.register_command(endpoint="whisper_remote", command_name=f"docker run --rm -v {uploads_path}:/app/data/ {'--gpus all ' if config_data.get('GPU_ENABLED', False) else ''}whisper whisper")
    # CLIP
    shell2http.register_command(endpoint="clip_remote",
                                command_name=f"docker run --rm -v {uploads_path}:/app/data/ {'--gpus all ' if config_data.get('GPU_ENABLED', False) else ''}clip python3 clip_interface.py")
else:
    app.logger.warning("UPLOAD_FOLDER_PATH not set; whisper_remote endpoint not available")
