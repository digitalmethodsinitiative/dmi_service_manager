# Start DMI Service Manager

### Install package
1. Set up and activate python venv
    - `python3 -m venv ./venv/`
    - `source venv/bin/activate`
2. Install setup.py
    - `python3 setup.py install`

### Run server
Gunicorn command example
`python3 -m gunicorn --worker-tmp-dir /dev/shm --workers=1 --threads=4 --worker-class=gthread --log-level=debug --reload --bind 0.0.0.0:4000 api:app`

# Use Services
All endpoints found at `http://servername/api/`

### Whisper

Endpoints:
- `whisper`: Creates a new Docker container from the whisper image
- `whisper_live`: Can be used if a running Whisper Docker container is live (setting in config.yml; this is necessary if server does not have GPU) 

Post via curl or python requests commands to DMI Service Manager endpoint: '/api/whisper'
```
import requests
# Note, the `data` folder in the container is mapped to your `4CAT_DATASETS_PATH` in config.yml
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

