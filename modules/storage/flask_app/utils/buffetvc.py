import os
import json
import shutil
import werkzeug.datastructures as ds
from flask import send_file
from os.path import exists
from os import makedirs
from os.path import join
from time import time, strftime, localtime
from utils.storage_pojos import HttpJsonResponse, ModelList, ML_Library
from utils.utils import HISTORY, DEFAULT, FILES_DIRECTORY


def save_file(file: ds.FileStorage, tag: str, file_name: str, description: str, ml_library: str):
    MODEL_ROOT_DIR = os.path.join(FILES_DIRECTORY, tag)
    history_file = os.path.join(MODEL_ROOT_DIR, HISTORY)
    default_file = os.path.join(MODEL_ROOT_DIR, DEFAULT)

    # Create a new model directory
    create_model_directory(MODEL_ROOT_DIR, history_file, default_file)

    # Check the default file to find the version of the new file
    new_directory_version, model_path = new_default_file(MODEL_ROOT_DIR, default_file, history_file)

    # Check the existence of the version directory and save it
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    model_location = os.path.join(model_path, file_name)
    file.save(model_location)

    # Update history file
    update_history_file(history_file=history_file,
                        new_version=new_directory_version,
                        model_path=model_path,
                        file_name=file_name,
                        description=description,
                        default_file=default_file,
                        ml_library=ml_library)


def delete_tag(tag: str):
    tag_directory = os.path.join(FILES_DIRECTORY, tag)
    shutil.rmtree(tag_directory)


def delete_file(tag: str, version: str):
    default_file = os.path.join(FILES_DIRECTORY, tag, DEFAULT)
    history_file = os.path.join(FILES_DIRECTORY, tag, HISTORY)

    try:
        # Clean the history file deleting the information
        directories, data_history = clean_history(history_file=history_file,
                                                  default_file=default_file,
                                                  version=version)
    # Check if the directory will be empty

    if len(directories) == 0:
        delete_tag(tag=tag)
    else:
            # If not is empty, set a new default number
            last_default, new_default = new_default_number(default_file=default_file,
                                                           history_file=history_file)
        # Rewrite the default file with the last version available
        if version == 'default':
            with open(default_file, 'w') as lf:
                new_default = directories[-1]
                lf.write(str(new_default))
                lf.close()

        # Rewrite the history file without the information of the removed file
        with open(history_file, 'w') as hf:
            hf.write(json.dumps(data_history,
                                sort_keys=True))
            hf.close()
        # Remove the file

        if version == 'default':
            version = last_default

        directory_file = os.path.join(FILES_DIRECTORY, tag, str(version))
        shutil.rmtree(directory_file)


def download_file(name: str, version: str):
    # Return the file
    try:
        # Check default file
        if version == 'default':
            with open(os.path.join(FILES_DIRECTORY, name, DEFAULT), 'r') as df:
                version = df.read()
                df.close()
        directory_path = os.path.join(FILES_DIRECTORY, name, version)

        file_name = os.listdir(directory_path)[0]
        file = os.path.join(directory_path, file_name)
        return send_file(path_or_file=file,
                         mimetype='application/octet-stream',
                         as_attachment=True)
    except FileNotFoundError:
        return HttpJsonResponse(
            422,
            http_status_description='File not found, please check the model name is correct!').get_response()


def get_directory_file(tag: str):
    with open(os.path.join(FILES_DIRECTORY, tag, DEFAULT), 'r') as df:
        version = df.read()
        df.close()
    directory_path = os.path.join(FILES_DIRECTORY, tag, version)
    file_name = os.listdir(directory_path)[0].__str__()
    path_file = os.path.join(directory_path, file_name)
    return path_file


def update_default(name: str, version: str):
    version = str(version)
    directory_path = os.path.join(FILES_DIRECTORY, name)

    try:
        os.listdir(os.path.join(directory_path, version))[0]
    except FileNotFoundError:
        return HttpJsonResponse(
            422,
            http_status_description='Version not found, please check the version!').get_response()

    try:
        # Rewrite .default file with the new default tag
        with open(os.path.join(directory_path, DEFAULT), 'w') as lf:
            lf.write(version)
            lf.close()

        response = HttpJsonResponse(
            200,
            http_status_description=f'The tag {name} with the version {version} has been set as default').get_response()

    except FileNotFoundError:
        response = HttpJsonResponse(
            422,
            http_status_description='File not found, please check the model name!').get_response()

    return response


def get_information(name: str):
    directory_path = os.path.join(FILES_DIRECTORY, name)

    # Read the history file
    with open(os.path.join(directory_path, HISTORY), 'r') as hf:
        data = hf.read()
        output = json.loads(data)
        return output


def get_model_list():
    model_list = []

    for model_directory in os.listdir(FILES_DIRECTORY):

        with open(os.path.join(FILES_DIRECTORY, model_directory, DEFAULT), 'r') as df:
            version = df.read()
            df.close()

        directory_path = os.path.join(
            FILES_DIRECTORY, model_directory, version)

        file_name = os.listdir(directory_path)[0]

        if file_name is not None:
            model_list.append(file_name)
        else:
            pass

    return ModelList(200,
                     http_status_description='Model list provided',
                     model_list=model_list).get_response()


def get_ml_library(tag: str):
    default_file = os.path.join(FILES_DIRECTORY, tag, DEFAULT)
    history_file = os.path.join(FILES_DIRECTORY, tag, HISTORY)
    with open(default_file, 'r') as default:
        last_version = int(default.read())
    with open(history_file, 'r') as hf:
        history = json.loads(hf.read())
        ml_library = history[str(last_version)]['ml_library']
        print(ml_library)
    return ML_Library(200,
                      http_status_description=f'ML Library from tag {tag} provided',
                      ml_library=ml_library).get_response()


def create_model_directory(MODEL_ROOT_DIR: str, history_file: str, default_file: str):
    # If not exist, create the root path for the tag. Then, create the default and history files.
    if not exists(MODEL_ROOT_DIR):
        makedirs(MODEL_ROOT_DIR)
        with open(history_file, "w") as hf:
            hf.write('{}')
        with open(default_file, "w") as lf:
            lf.write('0')


def new_default_file(MODEL_ROOT_DIR: str, default_file: str, history_file: str):
    """
    This method gives the new version number and the path of that version.
    :param MODEL_ROOT_DIR: The root of the tag
    :param default_file: The path of the default file tag
    :param history_file: The path of the history file tag
    """
    # Reads the history file
    with open(history_file, 'r') as hf:
        hf_json = json.loads(hf.read())
    # Open the default file
    with open(default_file, 'r') as default:
        last_directory = int(default.read())
        new_directory_version = last_directory + 1
        # With the history file loaded, searches the next version available
        for i in hf_json:
            if new_directory_version <= int(i):
                new_directory_version = int(i) + 1
        new_directory_version = str(new_directory_version)
        model_path = join(MODEL_ROOT_DIR, new_directory_version)
    # Returns the new version and his path
    return new_directory_version, model_path


def update_history_file(history_file: str, new_version: str, model_path: str, file_name: str,
                        description: str, default_file: str, ml_library: str):
    """
    Method to updatte the history file with new information and the default version
    :param history_file: Path of the history file
    :param new_version: Number of the new version
    :param model_path: Path of the new file
    :param file_name: Name of the file
    :param description: Description of the file
    :param default_file: Default version
    :param ml_library: Library which the model is build
    """
    # Update history file with the new information
    with open(history_file, 'r+') as fh:
        data = json.load(fh)
        ts = time()
        time_string = strftime('%H:%M:%S %d/%m/%Y', localtime(ts))
        data[new_version] = {"path": model_path,
                                       "file": file_name,
                                       "time": time_string,
                                       "description": description,
                                       "ml_library": ml_library}
        fh.seek(0)
        fh.write(json.dumps(data, sort_keys=True))
        fh.close()

    # Rewrite the default file with the new version
    with open(default_file, 'w') as fl:
        fl.write(new_version)


def clean_history(history_file: str, default_file: str, version):
    """
    Method to remove required version of a specified tag
    :param history_file: Path of the history file
    :param default_file: Path of the default file
    :param version: Version to delete
    """
    directories = []
    # Open the history file
    with open(history_file, 'r') as hf:
        data_history = json.load(hf)
        for i in data_history:
            i = int(i)
            directories.append(i)
        directories.sort()
        if version == 'default':
            with open(default_file, 'r') as default:
                version = int(default.read())

        directories.remove(int(version))
        del data_history[str(version)]
    directories.sort()
    return directories, data_history


def new_default_number(default_file, history_file):
    """
    This method sets a new default number
    :param default_file: Path of the default file
    :param history_file: Path of the history file
    """
    # Open the history file
    with open(history_file, 'r') as hf:
        hf_json = json.loads(hf.read())
    # Open the default file
    with open(default_file, 'r') as default:
        # Reads the last default version
        last_version = int(default.read())
        new_version = last_version
        # Search the new default version with the information taken by the history file
        for i in hf_json:
            if new_version <= int(i):
                new_version = int(i)
    # Return both the old and new default versions
    return last_version, new_version
