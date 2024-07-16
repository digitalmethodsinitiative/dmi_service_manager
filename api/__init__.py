import os

from flask import Flask
import logging
import sys

from api.lib.database import Database
from api.lib.helpers import update_config

# Flask application instance
app = Flask(__name__)

if "gunicorn" in os.environ.get("SERVER_SOFTWARE", ""):
    # Add gunicorn logger to Flask logger
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Log file
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
# create add stream handler to logger
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(logFormatter)
# create add file handler to logger
file_handler = logging.FileHandler("dmi_service_manager.log")
file_handler.setFormatter(logFormatter)
for logger in [app.logger, logging.getLogger("flask_shell2http")]:
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

# Config app
config_data = update_config("config.yml")
app.secret_key = config_data.get('SECRET_KEY')
app.config["endpoints"] = set()

# Database
db = Database()

# Import api modules
import api.access
import api.shell_executor
import api.file_management
import api.misc_api
import api.manager

app.logger.info('Starting server...')
# Run API
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
