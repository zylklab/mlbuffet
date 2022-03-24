import os
import time
import json
import shutil
import werkzeug.datastructures as ds
from flask import Response, send_file
from utils.storage_pojos import HttpJsonResponse

HISTORY = '.history'
DEFAULT = '.default'

archivos_folder = "files"
extern_folder = 'modelhostfiles'


def save_file(file: ds.FileStorage, tag: str, file_name: str, description: str):
    model_folder = os.path.join(archivos_folder, tag)
    # Creation of the name folder to the model and the history/default files
    if not os.path.exists(model_folder):
        os.makedirs(model_folder)
        history_file = os.path.join(model_folder, HISTORY)
        latest_file = os.path.join(model_folder, DEFAULT)
        open(history_file, 'x')
        open(latest_file, 'x')
        with open(history_file, "w") as hf:
            hf.write('{}')
        with open(latest_file, "w") as hf:
            hf.write('0')

    # Check the default file to find the version of the new file
    with open(os.path.join(model_folder, DEFAULT), 'r') as fl:
        last_folder = int(fl.read())
        new_folder = str(last_folder + 1)
        folder_dir = os.path.join(model_folder, new_folder)

    # Check the existence of the version folder
    if not os.path.exists(folder_dir):
        os.makedirs(folder_dir)

    # Save the file
    intern_path = os.path.join(folder_dir, file_name)
    file.save(intern_path)

    # Rewrite the history file with the new data
    with open(os.path.join(model_folder, HISTORY), 'r+') as fh:
        data = json.load(fh)
        ts = time.time()
        time_string = time.strftime('%H:%M:%S %d/%m/%Y', time.localtime(ts))
        data[new_folder] = {"folder": folder_dir, "file": file_name, "time": time_string, "description": description}
        fh.seek(0)
        fh.write(json.dumps(data, sort_keys=True))
        fh.close()

    # Rewrite the default file with the new version
    with open(os.path.join(model_folder, DEFAULT), 'w') as fl:
        fl.write(new_folder)

    # Save the file into the bind volume shared with the modelhosts
    extern_model_folder = os.path.join(extern_folder, tag)
    if not os.path.exists(extern_model_folder):
        os.makedirs(extern_model_folder)
    extern_path = os.path.join(extern_model_folder, file_name)

    # Check if extern_path is empty, if not, remove the file inside
    if len(os.listdir(extern_model_folder)) != 0:
        for file_to_remove in os.listdir(extern_model_folder):
            filer = os.path.join(extern_model_folder, file_to_remove)
            os.remove(filer)

    shutil.copy(intern_path, extern_path)


def remove_file(name: str, version: str):
    default_file = os.path.join(archivos_folder, name, DEFAULT)
    history_file = os.path.join(archivos_folder, name, HISTORY)

    folders = []

    # Open the history file and removes the data of the file
    with open(history_file, 'r') as hf:
        data_history = json.load(hf)
        for i in data_history:
            i = int(i)
            folders.append(i)
        if version == 'latest':
            version = folders[-1]
        del data_history[str(version)]

    no_files = False

    # Check if the folder will be empty
    try:
        new_default_file = folders[-2]
    except IndexError:
        no_files = True

    # If the folder is empty: remove. Else: manage the versions
    if no_files:
        tag_folder = os.path.join(archivos_folder, name)
        shutil.rmtree(tag_folder)
        extern_tagged_folder = os.path.join(extern_folder, name)
        shutil.rmtree(extern_tagged_folder)
    else:
        # Open the default file and checks the version of the file
        with open(default_file, 'r') as lf:
            data_default = lf.read()
            if data_default == version or version == 'default':
                version = data_default
            lf.close()

        # Rewrite the default file with the last version available
        with open(default_file, 'w') as lf:
            if int(data_default) == int(version):
                lf.write(str(new_default_file))
            else:
                lf.write(data_default)
            lf.close()

        # Rewrite the history file without the information of the removed file
        with open(history_file, 'w') as hf:
            hf.write(json.dumps(data_history, sort_keys=True))
            hf.close()

        # Remove the file
        folder_file = os.path.join(archivos_folder, name, str(version))
        shutil.rmtree(folder_file)

        # Put the default versioned file in the extern folder
        with open(default_file, 'r') as lf:
            data_default = lf.read()
            print(data_default)
            new_default_path = os.path.join(archivos_folder, name, str(data_default))
        extern_path = os.path.join(extern_folder, name)

        # Check if the extern_path is empty. If not, remove the file
        files_extern_path = os.listdir(extern_path)
        if len(files_extern_path) != 0:
            for file_extern in files_extern_path:
                os.remove(os.path.join(extern_path, file_extern))

        shutil.copytree(new_default_path, extern_path, dirs_exist_ok=True)


def download_file(name: str, version: str):
    # Check default file
    if version == 'default':
        with open(os.path.join(archivos_folder, name, DEFAULT), 'r') as lf:
            version = lf.read()
            lf.close()
    folder_path = os.path.join(archivos_folder, name, version)

    # Return the file
    try:
        file_name = os.listdir(folder_path)[0]
        file = os.path.join(folder_path, file_name)
        return send_file(path_or_file=file, as_attachment=True)
    except FileNotFoundError:
        return Response('File not found, please check the name introduced')


def update_default(name: str, version: str):
    folder_path = os.path.join(archivos_folder, name)
    extern_folder_path = os.path.join(extern_folder, name)

    try:
        # Rewrite .default file with the new default tag
        with open(os.path.join(folder_path, DEFAULT), 'w') as lf:
            lf.write(version)
            lf.close()

        # Remove the file in the external path
        file_to_remove = os.listdir(os.path.join(extern_folder, name))[0]
        os.remove(os.path.join(extern_folder_path, file_to_remove))

        # Copy the new default file into the external path
        new_default_file = os.listdir(os.path.join(folder_path, version))[0]
        path_to_default = os.path.join(extern_folder_path, new_default_file)
        shutil.copy(new_default_file, path_to_default)
        return Response(f'The file {name} with the version {version} has been set as default\n')
    except FileNotFoundError:
        return Response('File not found, please check the name introduced\n')


def get_information(name: str):
    folder_path = os.path.join(archivos_folder, name)

    # Read the history file
    try:
        with open(os.path.join(folder_path, HISTORY), 'r') as hf:
            data = hf.read()
            return data
    except FileNotFoundError:
        return Response('File not found, please check the name introduced\n')
