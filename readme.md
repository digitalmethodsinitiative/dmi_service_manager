# Start DMI Service Manager

### Install package
1. Set up and activate python venv
    - `python3 -m venv ./venv/`
    - `source venv/bin/activate`
2. Install setup.py
    - `python3 setup.py install`

### Run server
Gunicorn command example
`python3 -m gunicorn --worker-tmp-dir /dev/shm --workers=4 --threads=4 --worker-class=gthread --log-level=debug --reload --bind 0.0.0.0:4000 api:app`

# Use Services
All endpoints found at `http://servername/api/`

### Manage files
The DMI Service Manager has a file manager to help you upload and download files on the server.
- `/api/list_files?folder_name=your_folder_name`: List all files in `your_folder_name` found in the `UPLOAD_FOLDER_PATH` directory
- `/api/send_files`: Upload files to the `UPLOAD_FOLDER_PATH` directory
- `/api/uploads/<string:folder_name>/<string:file_type>/<string:filename>'`: Download files from the `UPLOAD_FOLDER_PATH` directory

See `api/lib/file_manager.py` for more details.

### Whisper
Whisper requires the [DMI Whisper Docker image](https://github.com/digitalmethodsinitiative/dmi_dockerized_services/tree/main/openai_whisper) to be available with the tag `whisper`.

Endpoints:
- `whisper_remote`: Used with files uploaded to the directory (set `UPLOAD_FOLDER_PATH` in config.yml)
- `whisper_local`: Used with a local directory linked to a 4CAT instance (set `4CAT_DATASETS_PATH` in config.yml)

Post via curl or python requests commands to DMI Service Manager endpoint: '/api/whisper_local' or '/api/whisper_remote'
```
import requests
# Note, the `data` folder in the container is mapped to your `4CAT_DATASETS_PATH` or `UPLOAD_FOLDER_PATH` in config.yml
data = {"args" : ['--output_dir', "data/text/", '--output_format', "json", "--model", "medium", "data/audio/audio_file.wav"]}
resp = requests.post("http://localhost:4000/api/whisper_new", json=data)
```
  - You can check the status of your command like so:
```
result = requests.get(resp.json()['result_url'])
print(result.json())
```

This endpoint does not accept glob arguments (e.g. `data/audio/*`) as it does not have access to the shell. For multiple
files, you can provide them like so:
```
import os
audio_files = os.listdir("./audio") # path to the audio files
data = {"args" : ['--output_dir', "/app/data/text/", '--output_format', "json", "--model", "medium"] +[f"/app/data/audio/{filename}" for filename in audio_files]}
```

