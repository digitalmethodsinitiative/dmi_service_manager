from datetime import datetime

from flask import request, jsonify

from api import app, db


@app.route('/status_update/', methods=['POST'])
def status_update():
    """
    Update the status of a service. Optionally provide a status message and/or the number of processed records.

    :param int key:
    :param str status:
    :param str message:
    :param int processed_records:
    :return:
    """
    key = request.args.get("key")
    status = request.args.get("status")
    if not key or not status:
        return jsonify({"status": "error", "message": "status_update must include both 'key' and 'status'"}), 400

    message = request.args.get("message", False)
    processed_records = request.args.get("processed_records", False)
    # Update the job
    db.insert(f"UPDATE jobs SET status = ?{', message = ?' if message else ''}{', processed_records = ?' if processed_records else ''}{', completed_at = ?' if status == 'complete' else ''} WHERE id = ?",
                  [status] + ([message] if message else []) + ([processed_records] if processed_records else []) + ([int(datetime.now().timestamp())] if status == 'complete' else []) + [key])

    app.logger.info(f"Updated job {key}: {status}{' - '+ message if message else ''}")
    return jsonify({"status": "success"}), 200

@app.route('/jobs/', methods=['GET'])
def list_jobs():
    """
    List all jobs
    """
    current = request.args.get("current", False)
    if current:
        jobs = [dict(row) for row in db.select("SELECT * FROM jobs WHERE status != 'complete'")]
    else:
        jobs = [dict(row) for row in db.select("SELECT * FROM jobs")]

    app.logger.info(f"Collected {'current' if current else 'all'} ({len(jobs)}) jobs")
    return jsonify({"status": "success", "jobs": jobs}), 200

@app.route('/api/jobs/<string:database_key>', methods=['GET'])
def job_status(database_key):
    """
    List all jobs
    """
    if not database_key:
        return jsonify({"status": "error", "message": "job_status must include 'database_key'"}), 400

    job = dict(db.select("SELECT * FROM jobs WHERE id = ?", (database_key,)).__next__())

    return jsonify({"status": "success", "job": job}), 200

@app.route('/api/jobs/details_query/', methods=['GET'])
def job_query_details():
    """
    Find job by details JSON key-value pair
    """
    details_key = request.json.get("details_key")
    details_value = request.json.get("details_value")
    if not details_key or not details_value:
        return jsonify({"status": "error", "message": "job_query_details must include 'details_key' and 'details_value'"}), 400

    jobs = [dict(job) for job in db.select("SELECT * FROM jobs WHERE json_extract(details, ?) = ?", (details_key, details_value))]

    return jsonify({"status": "success", "jobs": jobs}), 200