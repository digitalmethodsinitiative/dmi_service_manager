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

# Whisper
if config_data.get('4CAT_DATASETS_PATH', False):
    fourcat_path = Path(config_data.get('4CAT_DATASETS_PATH'))
    shell2http.register_command(endpoint="whisper_local", command_name=f"docker run -v {fourcat_path}:/app/data/ {'--gpus all ' if config_data.get('WHISPER_GPU', False) else ''}whisper whisper")
else:
    app.logger.warning("4CAT_DATASETS_PATH not set; whisper_local endpoint not available")

if config_data.get('UPLOAD_FOLDER_PATH', False):
    uploads_path = Path(config_data.get('UPLOAD_FOLDER_PATH'))
    shell2http.register_command(endpoint="whisper_remote", command_name=f"docker run -v {uploads_path}:/app/data/ {'--gpus all ' if config_data.get('WHISPER_GPU', False) else ''}whisper whisper")
else:
    app.logger.warning("UPLOAD_FOLDER_PATH not set; whisper_remote endpoint not available")
