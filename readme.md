# DMI Service Manager
The Digital Methods Service Manager is an API built to run Docker containers and handle file management. Primarily
it is to run GPU intensive tasks in a containerized environment and provide the result files to the user. The DMI Service
Manager was built to work with the [4CAT Capture and Analysis Toolkit](https://github.com/digitalmethodsinitiative/4cat?tab=readme-ov-file#-4cat-capture-and-analysis-toolkit)
as a way to offload certain analyses to a more capable server. A number of services are available to run on the DMI 
Service Manager and some examples can be found in the [DMI Dockerized Services repository](https://github.com/digitalmethodsinitiative/dmi_dockerized_services/tree/main?tab=readme-ov-file#dmi-dockerized-services).

The DMI Service Manager will have access to specific endpoints as defined in `config.yml`. It will create a Docker 
container from the image specified by `image_name` and run the command specified by `command` with the arguments 
provided.

[Navigate here for information and examples of 4CAT analyses using the DMI Service Manager](https://docs.google.com/document/d/1hrzxsQVE0bDeVgKZFBJ3UIrkmAEcKdNTm2mT8fiwsuM/edit).

# Installation
Setting up the DMI Service Manager requires two main steps: installation of the DMI Service Manager itself and building
(or downloading) the Docker images for the services you want to run. You will also need to have [Docker itself installed](https://docs.docker.com/engine/install/).

## DMI Service Manager installation

1. Clone this repository
    - `git clone https://github.com/digitalmethodsinitiative/dmi_service_manager.git`
2. Set up and activate python venv
    - `python3 -m venv ./venv/`
    - `source venv/bin/activate`
3. Install setup.py
    - `python3 setup.py install`
4. Copy the `config.yml.example` file to `config.yml` and set the necessary values
    - `cp config.yml.example config.yml`
    - `nano config.yml`
### Configuration
- `UPLOAD_FOLDER_PATH`: The path to the folder where files will be uploaded to; only necessary if you want to use the file manager
- `4CAT_DATASETS_PATH`: The path to the folder where 4CAT datasets are stored; only necessary if 4CAT is installed on the same server
  - This is a useful feature as it avoids the need to upload and download files
- `SECRET_KEY`: Neede for Flask sessions
- `ALLOWED_EXTENSIONS`: A list of allowed file extensions for the file manager
- `GPU_ENABLED`: If you have a GPU available, set this to `True` otherwise set to `False`
- `DOCKER_ENDPOINTS`: A list of Docker image that the DMI Service Manager can run
  -  `image_name`: the name of the Docker image
  -  `local`: an endpoint to use the local `4CAT_DATASETS_PATH`
  -  `remote`: an endpoint to use the `UPLOAD_FOLDER_PATH`
  -  `command`: the command to run in the Docker container (you can add arguments to the command in the request)
  -  `data_path`: the path to the data folder inside the Docker container
- `IP_WHITELIST`: It is recommended that you use the `IP_WHITELIST` to restrict access to the DMI Service Manager if your server is accessible to the wider world
- `TRUSTED_PROXIES`: If you are using a reverse proxy, you may need to set the `TRUSTED_PROXIES` variable to the IP of the reverse proxy, only used in conjunction with the `IP_WHITELIST`

The local and remote endpoints are used to specify the location where the volumes are mounted and result files can be
obtained.

## Docker images setup
Example Docker images can be found in the [DMI Dockerized Services repository](https//github.com/digitalmethodsinitiative/dmi_dockerized_services/tree/main?tab=readme-ov-file#dmi-dockerized-services).
Essentially, any image can be used with the idea that you can first upload relevant files to the server and then run the
container which should save any results to the `data_path` folder. These can then be retrieved by the user.

You will need to have the Docker images available on the server where the DMI Service Manager is running. You can either build 
them or download them from a repository (such as Docker Hub). The images we have built are quite large as they contain 
various ML models and their dependencies. We thus have not uploaded them to Docker Hub, and they will need to be built 
following the instructions in the DMI Dockerized Services repository.

### Example setup for Whisper container
1. Clone DMI Dockerized Services repository
   -  `git clone https://github.com/digitalmethodsinitiative/dmi_dockerized_services.git`
2. Navigate into the Whisper folder containing its `Dockerfile` and build the Docker image
   -  `cd openai_whisper`
   -  `docker build -t whisper .`
   -  You can read the README.md file in this folder for additional information on the container
3. Update your DMI Service Manager config.yml `DOCKER_ENDPOINTS` to activate this image
   ```
   whisper: 
    image_name: whisper
    local: True  # Set to True if 4CAT is running locally
    remote: False  # Set to True if 4CAT is running remotely
    command: whisper
    data_path: /app/data/
   ```
   - `image_name` matches the `-t` tag given in the `docker build` command
   - `local` or `remote` should be set depending on where you wish to access the Whisper container from (or where your 4CAT server is running)
   - `command` can be found in the README.md file in the openai_whisper folder (arguments following the command will be added to your API request)
   - `data_path` is flexible, but may have restrictions in the README.md file; it is where the Whisper container expects data to be uploaded and/or results saved
4. Run your server!
   - see next section

## Run server
Once the DMI Service Manager is set up and your Docker images are ready, you can run the server using the following 
example Gunicorn command:
`python3 -m gunicorn --worker-tmp-dir /dev/shm --workers=1 --threads=12 --worker-class=gthread --log-level=debug --reload --bind 0.0.0.0:4000 api:app`

Note: `--workers=1` is recommended as Flask will otherwise lose track of the running services and you will be unable 
to collect their statuses (though they will still complete as normal). 

# 4CAT Integration
All of the DMI Dockerized Services are built to work with 4CAT. Once the DMI Service Manager is set up, you (or rather
your 4CAT admin) can add the processors to 4CAT via `Control Panel -> Settings -> DMI Service Manager`. You will need to
set the `DMI Service Manager server/URL` to the server where the DMI Service Manager is running 
(e.g. `http://localhost:4000`) and `DMI Services Local or Remote` to either `local` or `remote` depending on whether 
4CAT and the DMI Service Manager are on the same server. You can then enable the individual services you want to use and
adjust any relevant settings.

![image](https://github.com/digitalmethodsinitiative/dmi_service_manager/assets/32108944/856e75c2-af59-4d39-b099-3b54bf2b4608)

You are now good to go!

# DMI Service Manager API
If you would like to use these services directly without 4CAT, you can use the endpoints directly. All endpoints can 
found at `http://servername/api/` (e.g. `http://localhost:4000/api/` in the example above).

### Manage files
The DMI Service Manager has a file manager to help you upload and download files on the server.
- `/api/list_files?folder_name=your_folder_name`: List all files in `your_folder_name` found in the `UPLOAD_FOLDER_PATH` directory
- `/api/send_files`: Upload files to the `UPLOAD_FOLDER_PATH` directory
- `/api/uploads/<string:folder_name>/<string:file_type>/<string:filename>'`: Download files from the `UPLOAD_FOLDER_PATH` directory

See `api/lib/file_manager.py` for more details.

### Usage example using OpenAI's Whisper model to convert audio to text
Whisper requires the [DMI Whisper Docker image](https://github.com/digitalmethodsinitiative/dmi_dockerized_services/tree/main/openai_whisper) to be available with the tag `whisper`.

Endpoints:
- `whisper_remote`: Used with files uploaded to the directory (set `UPLOAD_FOLDER_PATH` in config.yml)
- `whisper_local`: Used with a local directory linked to a 4CAT instance (set `4CAT_DATASETS_PATH` in config.yml)

Post via curl or python requests commands to DMI Service Manager endpoint: '/api/whisper_local' or '/api/whisper_remote'
```
import requests
# Note, the `data` folder in the container is mapped to your `4CAT_DATASETS_PATH` or `UPLOAD_FOLDER_PATH` in config.yml
data = {"args" : ['--output_dir', "data/text/", '--output_format', "json", "--model", "medium", "data/audio/audio_file.wav"]}
resp = requests.post("http://localhost:4000/api/whisper_local", json=data)
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

Once the service is complete, all the result text files will be in the relevant directory on the server.
