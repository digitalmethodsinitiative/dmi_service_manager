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
import shlex

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
        request.json["callback_context"].update({"db_key": key, "route": request.path})

        # Set timeout from config if not already set in request
        # Flask-Shell2HTTP reads timeout from request.json, defaulting to 3600 seconds
        # Max timeout appears to be around 2147483 seconds (~24.8 days) due to system limits
        if "timeout" not in request.json:
            command_timeout = config_data.get('SHELL_COMMAND_TIMEOUT', 0)
            request.json["timeout"] = command_timeout if command_timeout > 0 else 2147483  # ~24.8 days

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
        result = future.result()
        returncode = result.get("returncode", None)
        status = "complete" if returncode == 0 else "error"
        db.insert("UPDATE jobs SET status = ?, completed_at = ?, results = ? WHERE id = ?", (status, int(datetime.now().timestamp()), json.dumps(result), db_key))
        error_message = " - " + result.get("error") if returncode != 0 else ""
        app.logger.info(f"Service complete: job {db_key} - {status}{error_message}")
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
    # Setup Executor with no timeout (or use config_data.get('EXECUTOR_TIMEOUT', None))
    app.config['EXECUTOR_TYPE'] = 'thread'
    app.config['EXECUTOR_MAX_WORKERS'] = config_data.get('EXECUTOR_MAX_WORKERS', 5)
    # Set to None for no timeout, or a specific value in seconds
    app.config['EXECUTOR_PROPAGATE_EXCEPTIONS'] = True
    
    executor = Executor(app)
    shell2http = Shell2HTTP(app=app, executor=executor, base_url_prefix=base_url_prefix)
    app.config["endpoint_meta"] = {}

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

    # User and group settings
    service_user = config_data.get('SERVICE_USER', None)
    service_group = config_data.get('SERVICE_GROUP', None)
    # Optional persistent home on host for containers (create it and chmod 0777)
    container_home_host = config_data.get('CONTAINER_HOME_HOST', None)  # e.g. /opt/dmi_service_manager/container-home

    def make_base_args(gpu=True):
        args = ['docker', 'run', '--rm', '--network', 'host']
        if config_data.get('GPU_ENABLED', False) and gpu:
            args += ['--gpus', 'all']
        return args

    # Register endpoints
    for endpoint, endpoint_data in active_endpoints.items():
        use_gpu = endpoint_data.get('gpu', True) # Default to True if not specified
        if fourcat_path and endpoint_data['local']:
            args = make_base_args(gpu=use_gpu)
            args += ['-v', f'{str(fourcat_path)}:{endpoint_data["data_path"]}']
            args += [endpoint_data['image_name']]
            args += shlex.split(endpoint_data['command'])
            route = f"{endpoint}_local"
            shell2http.register_command(
                endpoint=route,
                command_name=shlex.join(args),
                decorators=[create_job_record],
                callback_fn=finish_service
            )
            app.config["endpoints"].add(f"{base_url_prefix}{route}")
            app.config["endpoint_meta"][f"{base_url_prefix}{route}"] = {
                "mount_base": str(fourcat_path),
                "image_name": endpoint_data['image_name'],
            }

        if uploads_path and endpoint_data['remote']:
            args = make_base_args(gpu=use_gpu)
            args += ['-v', f'{str(uploads_path)}:{endpoint_data["data_path"]}']
            args += [endpoint_data['image_name']]
            args += shlex.split(endpoint_data['command'])
            route = f"{endpoint}_remote"
            shell2http.register_command(
                endpoint=route,
                command_name=shlex.join(args),
                decorators=[create_job_record],
                callback_fn=finish_service
            )
            app.config["endpoints"].add(f"{base_url_prefix}{route}")
            app.config["endpoint_meta"][f"{base_url_prefix}{route}"] = {
                "mount_base": str(uploads_path),
                "image_name": endpoint_data['image_name'],
            }

