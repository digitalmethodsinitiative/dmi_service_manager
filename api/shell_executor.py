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
    shell2http.register_command(endpoint="whisper", command_name=f"docker run -v {fourcat_path}:/app/data/ --gpus all -it whisper whisper")
else:
    app.log.warning("4CAT_DATASETS_PATH not set; whisper endpoint not available")

if config_data.get('WHISPER_LIVE', False):
    shell2http.register_command(endpoint="whisper_live", command_name=f"docker exec -it whisper whisper")


