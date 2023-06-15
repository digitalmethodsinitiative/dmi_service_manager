from flask import Flask
import logging
import sys

from api.lib.helpers import update_config

# Flask application instance
app = Flask(__name__)

# Set up logging if run by gunicorn
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Log file
logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
file_handler = logging.FileHandler("dmi_service_manager.log")
file_handler.setFormatter(logFormatter)
app.logger.addHandler(file_handler)

# Flask_shell2http logger
fs2h_logger = logging.getLogger("flask_shell2http")
# create new handler
handler = logging.StreamHandler(sys.stdout)
fs2h_logger.addHandler(handler)
fs2h_logger.addHandler(file_handler)
# log messages of severity DEBUG or lower to the console
fs2h_logger.setLevel(logging.DEBUG)  # this is really important!

# Config app
config_data = update_config("config.yml")
# trusted_proxies = config_data.get('TRUSTED_PROXIES')
# ip_whitelist = config_data.get('IP_WHITELIST')
app.secret_key = config_data.get('SECRET_KEY')

# Import api modules
import api.access
import api.shell_executor
import api.file_management

# Run API
if __name__ == "__main__":
    print('Starting server...')
    app.run(host='0.0.0.0', debug=True)
