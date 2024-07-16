"""
Allow controlled command line access to certain API endpoints
"""
import json
from datetime import datetime
from flask_executor import Executor
from flask_executor.futures import Future
from flask_shell2http import Shell2HTTP
from pathlib import Path
import functools
from flask import request, url_for

from api import app, config_data, db

active_endpoints = config_data.get('DOCKER_ENDPOINTS', False)
base_url_prefix = "/api/"

def create_job_record(f):
    @functools.wraps(f)
    def decorator(*args, **kwargs):
        # Insert into database
        job_data = {"request_args": request.args, "request_json": request.json}
        app.logger.info(f"Creating job record for {request.path}: {job_data}")
        key = db.insert("INSERT INTO jobs (created_at, jobtype, status, details) VALUES (?, ?, ?, ?)",
                        (int(datetime.now().timestamp()), request.path, "created", json.dumps(job_data)))

        # Add database key to callback in order to pick up when service is complete
        if "callback_context" not in request.json:
            request.json["callback_context"] = {}
        request.json["callback_context"].update({"db_key": key})

        # Pass key and server address to service if requested
        #NOTE: request.json["args"] is a list of arguments for the shell command; we can add the job key here for services able to utilize and update status
        if request.json.get("pass_key", False):
            # TODO We could also add the key to known services that expect it
            # Request knows to pass key
            if "args" not in request.json:
                request.json["args"] = []
            request.json.get("args", []).extend(["--database_key", str(key), "--dmi_sm_server", config_data.get("DMI_SM_SERVER", "http://localhost:5000")])

        # Run the route
        response = f(*args, **kwargs)

        # Collect results and update database
        response_json = response.get_json()
        job_data.update({
            # This key is unfortunately only accessible by the Flask/Gunicorn worker that creates the service
            "service_key": response_json.get("key", "unknown")
        })
        status = response_json.get("status", "unknown")
        db.insert("UPDATE jobs SET status = ?, details = ? WHERE id = ?", (status, json.dumps(job_data), key))

        # Update response with job key and result_url
        # prior result_url is only available to current worker; use route to collect results from database
        response_json["key"] = key
        response_json["result_url"] = request.url_root + url_for("job_status", database_key=key)
        response.data = json.dumps(response_json)

        return response
    return decorator

def finish_service(extra_callback_context, future: Future):
    """
    Will be invoked on every service completion
    """
    db_key = extra_callback_context.get("db_key")
    if db_key and future.done():
        returncode = future.result().get("returncode", None)
        status = "complete" if returncode == 0 else "error"
        db.insert("UPDATE jobs SET status = ?, completed_at = ?, results = ? WHERE id = ?", (status, int(datetime.now().timestamp()), json.dumps(future.result()), db_key))
        app.logger.info(f"Service complete: job {db_key} - {status}")
        return
    message = (
            f"{'*' * 64}\n"
            f"ERROR w/ service db_key: {db_key}\n"
            f"[i] Process running ?: {future.running()}\n"
            f"[i] Process completed ?: {future.done()}\n"
            # future.result() has our key
            f"[+] Result: {future.result()}\n"
            f"[+] Context: {extra_callback_context}\n"
            f"{'*' * 64}"
            )
    app.logger.error(message)

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
            # Docker ENV variable? Could add status pingback route to ENV variable
            shell2http.register_command(endpoint=f"{endpoint}_local",
                                        command_name=f"docker run --rm --network host -v {fourcat_path}:{endpoint_data['data_path']} {'--gpus all ' if config_data.get('GPU_ENABLED', False) else ''}{endpoint_data['image_name']} {endpoint_data['command']}",
                                        decorators=[create_job_record], callback_fn=finish_service)
            app.config["endpoints"].add(f"{base_url_prefix}{endpoint}_local")
        if uploads_path and endpoint_data['remote']:
            shell2http.register_command(endpoint=f"{endpoint}_remote",
                                        command_name=f"docker run --rm --network host -v {uploads_path}:{endpoint_data['data_path']} {'--gpus all ' if config_data.get('GPU_ENABLED', False) else ''}{endpoint_data['image_name']} {endpoint_data['command']}",
                                        decorators=[create_job_record], callback_fn=finish_service)
            app.config["endpoints"].add(f"{base_url_prefix}{endpoint}_remote")

