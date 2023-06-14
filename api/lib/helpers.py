import os
import yaml


def update_config(config_filepath='config.yml'):
    # Import config options
    if not os.path.exists(config_filepath):
        raise Exception("No config.yml file exists! Update and rename the config-example.yml file.")

    with open(config_filepath) as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
    return config_data


def allowed_file(filename, extensions):
    """
    Check filenames to ensure they are an allowed extension
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions
