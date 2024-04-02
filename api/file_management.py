import os
import uuid
from pathlib import Path

from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename


from api import app, config_data
from api.lib.helpers import allowed_file, count_lines


def get_folder_from_request(request):
    """
    Get folder name from request
    """
    if request.form['folder_name']:
        folder_name = request.form['folder_name']
    else:
        # New randomly assigned folder_name
        folder_name = uuid.uuid4().hex
        while os.path.isdir(os.path.join(config_data.get("UPLOAD_FOLDER_PATH"), folder_name)):
            # Taken; try again
            folder_name = uuid.uuid4().hex

    return folder_name


@app.route("/api/linecount/", methods=["GET"])
def get_linecount():
    """
    Get line count for a file in the upload folder

    This is useful for tracking progress for services that write one line per
    item to the results file.
    """
    folder_name = request.args.get("folder")
    file_name = request.args.get("file")

    if not folder_name or not file_name:
        app.logger.warning('No file path provided')
        return jsonify({'reason': 'Must provide file path (with ?folder and ?file)'}), 400

    data_folder = Path(config_data.get("UPLOAD_FOLDER_PATH")).resolve()
    file_path = data_folder.joinpath(folder_name).joinpath(file_name).resolve()

    # no shenanigans!
    is_good_path = (os.path.commonprefix((data_folder, file_path)) == str(data_folder))

    if not file_path.exists() or not is_good_path:
        return jsonify({'reason': 'file_path %s does not exist' % file_path}), 404

    return jsonify({"lines": count_lines(file_path)})


@app.route('/api/list_filenames/<path:folder_name>', methods=['GET'])
def list_filenames(folder_name):
    """
    Get request to list all filenames in a particular folder
    ?folder_name=your_folder_name

    Note: due to import using secure_filename, it is possible that some filenames will appear changed from upload
    """
    if not config_data.get("UPLOAD_FOLDER_PATH"):
        return jsonify({'reason': 'This instance of DMI Service Manager not configured for remote file management'}), 405

    if not folder_name:
        app.logger.warning('No folder_name provided')
        return jsonify({'reason': 'Must provide folder_name (e.g., /api/list_filenames/folder_name)'}), 400
    else:
        folder_path = os.path.join(config_data.get("UPLOAD_FOLDER_PATH"), folder_name)
        app.logger.debug(f"folder_path: {folder_path}")
        # check if folder exists
        if not os.path.exists(folder_path):
            return jsonify({'reason': 'folder_name %s does not exist' % folder_name}), 404

        files_uploaded = {}
        for path, subdirs, files in os.walk(folder_path):
            rel_path = os.path.relpath(path, folder_path)
            for name in files:
                if rel_path not in files_uploaded:
                    files_uploaded[rel_path] = [name]
                else:
                    files_uploaded[rel_path].append(name)

        return jsonify({
                        **files_uploaded
                       }), 200


@app.route('/api/send_files', methods=['POST'])
def upload_files_api():
    """
    Upload multiple files to folder as ('file_type', open(filename, 'rb')). This creates a directory structure with
    files stored by filetype.
    If no folder_name provided, a random unique ID will be generated that will be needed to retrieve or add to the
    files.

    Example:
    files = [
        ('metadata', open('metadata.csv', 'rb')),
        ('images', open('image_1.jpg', 'rb')),
        ('images', open('image_2.jpg', 'rb')),
    ]
    Optional:
    data = {'folder_name' : 'desired_name'}
    """
    if not config_data.get("UPLOAD_FOLDER_PATH"):
        return jsonify({'reason': 'This instance of DMI Service Manager not configured to allow uploads'}), 400

    if not request.files:
        # No files received
        app.logger.debug('No files received')
        return {'reason': 'No files received; check request formatting'}, 400

    folder_name = get_folder_from_request(request)

    folder_path = os.path.join(config_data.get("UPLOAD_FOLDER_PATH"), folder_name)
    if not os.path.isdir(folder_path):  # Make folder if it does not exist
        os.mkdir(folder_path)

    files_uploaded = {}
    for file_type in request.files:
        if file_type not in files_uploaded:
            files_uploaded[file_type] = []
        file_type_path = os.path.join(folder_path, file_type)
        if not os.path.isdir(file_type_path):  # Make folder if it does not exist
            os.mkdir(file_type_path)

        files = request.files.getlist(file_type)
        for file in files:
            if file and allowed_file(file.filename, config_data.get("ALLOWED_EXTENSIONS")):
                filename = secure_filename(file.filename)
                app.logger.debug(f"Uploading {file_type} file: {str(file)} as {filename}")
                file.save(os.path.join(file_type_path, filename))
                files_uploaded[file_type].append(file.filename)
            else:
                app.logger.debug(f"Skipping uploaded {file_type} file: {str(file)}")

    response = {
        'folder_name': folder_name,
        **files_uploaded,
    }

    return jsonify(response), 200


@app.route('/api/download/<path:filepath>', methods=['GET'])
def get_result(filepath):
    """
    Get uploaded file

    :return:  Result file
    """
    path = Path(config_data.get("UPLOAD_FOLDER_PATH")).joinpath(filepath)
    return send_from_directory(directory=path.parent, path=path.name)

