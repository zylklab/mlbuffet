import json
from os.path import exists
from os import makedirs
from os.path import join
from time import time, strftime, localtime


def create_model_directory(MODEL_ROOT_DIR: str, history_file: str, default_file: str):
    if not exists(MODEL_ROOT_DIR):
        makedirs(MODEL_ROOT_DIR)
        with open(history_file, "w") as hf:
            hf.write('{}')
        with open(default_file, "w") as lf:
            lf.write('0')


def new_default_file(MODEL_ROOT_DIR: str, default_file: str, history_file: str):
    with open(history_file, 'r') as hf:
        hf_json = json.loads(hf.read())
    with open(default_file, 'r') as default:
        last_directory = int(default.read())
        new_directory_version = last_directory + 1
        for i in hf_json:
            if new_directory_version <= int(i):
                new_directory_version = int(i) + 1
        new_directory_version = str(new_directory_version)
        model_path = join(MODEL_ROOT_DIR, new_directory_version)

    return new_directory_version, model_path


def update_history_file(history_file: str, new_directory_version: str, model_path: str, file_name: str,
                        description: str, default_file: str, ml_library: str):
    # Update history file
    with open(history_file, 'r+') as fh:
        data = json.load(fh)
        ts = time()
        time_string = strftime('%H:%M:%S %d/%m/%Y', localtime(ts))
        data[new_directory_version] = {"path": model_path,
                                       "file": file_name,
                                       "time": time_string,
                                       "description": description,
                                       "ml_library": ml_library}
        fh.seek(0)
        fh.write(json.dumps(data, sort_keys=True))
        fh.close()

    # Rewrite the default file with the new version
    with open(default_file, 'w') as fl:
        fl.write(new_directory_version)


def clean_history(history_file: str, default_file: str, version):
    directories = []

    with open(history_file, 'r') as hf:
        data_history = json.load(hf)
        for i in data_history:
            i = int(i)
            directories.append(i)
        directories.sort()
        if version == 'default':
            with open(default_file, 'r') as default:
                version = int(default.read())
            # version = directories[-1]

        directories.remove(int(version))
        del data_history[str(version)]
    directories.sort()
    return directories, data_history


def new_default_number(default_file, history_file):
    with open(history_file, 'r') as hf:
        hf_json = json.loads(hf.read())
    with open(default_file, 'r') as default:
        last_version = int(default.read())
        new_version = last_version
        for i in hf_json:
            if new_version <= int(i):
                new_version = int(i)

    return last_version, new_version
