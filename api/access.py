from flask import abort, request

from api import app
from api.lib.helpers import update_config

@app.before_request
def limit_remote_addr():
    """
    Checks the incoming IP address and compares with whitelist
    """
    config_data = update_config()
    trusted_proxies = config_data.get('TRUSTED_PROXIES')
    ip_whitelist = config_data.get('IP_WHITELIST')

    if ip_whitelist:
        # Check that whitelist exists
        route = request.access_route + [request.remote_addr]
        remote_addr = next((addr for addr in reversed(route) if addr not in trusted_proxies), request.remote_addr)
        app.logger.debug('remote_address: '+str(remote_addr))
        if remote_addr not in ip_whitelist:
            abort(403)  # Forbidden
    else:
        # No whitelist = access for all
        return