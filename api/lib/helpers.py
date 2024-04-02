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


def count_lines(path):
    """
    Get the amount of (new)lines in a file.

    Thanks to https://stackoverflow.com/a/27517681!

    :param path:  File to read
    :return int:  Amount of lines
    """
    def _make_gen(reader):
        b = reader(1024 * 1024)
        while b:
            yield b
            b = reader(1024 * 1024)

    with open(path, "rb") as f:
        f_gen = _make_gen(f.raw.read)

        return sum(buf.count(b"\n") for buf in f_gen)
