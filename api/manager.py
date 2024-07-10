from datetime import datetime

from flask import request, jsonify

from api import app, db


@app.route('/status_update/', methods=['POST'])
def status_update():
    """
    Update the status of a service
    :param key:
    :param value:
    :return:
    """
    key = request.args.get("key")
    status = request.args.get("status")
    if not key or not status:
        return jsonify({"status": "error", "message": "status_update must include both 'key' and 'status'"}), 400

    message = request.args.get("message")
    if "status" == "complete":
        db.insert("UPDATE jobs SET status = ?, completed_at = ? WHERE id = ?", (status, int(datetime.now().timestamp()), key))
    elif message:
        db.insert("UPDATE jobs SET status = ?, message = ? WHERE id = ?", (status, message, key))
    else:
        db.insert("UPDATE jobs SET status = ? WHERE id = ?", (status, key))

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