import os
import json
import shutil
import werkzeug.datastructures as ds
from flask import send_file
import utils.buffetvc_utils as bvc_utils
from utils.storage_pojos import HttpJsonResponse, ModelList
from utils.utils import HISTORY, DEFAULT, FILES_DIRECTORY


def save_file(file: ds.FileStorage, tag: str, file_name: str, description: str):
    MODEL_ROOT_DIR = os.path.join(FILES_DIRECTORY, tag)
    history_file = os.path.join(MODEL_ROOT_DIR, HISTORY)
    default_file = os.path.join(MODEL_ROOT_DIR, DEFAULT)

    # Create a new model storage directory
    bvc_utils.create_model_directory(MODEL_ROOT_DIR, history_file, default_file)

    # Check the default file to find the version of the new file
    new_directory_version, model_path = bvc_utils.new_default_file(MODEL_ROOT_DIR, default_file, history_file)

    # Check the existence of the version directory and save it
    if not os.path.exists(model_path):
        os.makedirs(model_path)

    model_location = os.path.join(model_path, file_name)
    file.save(model_location)

    # Update history file

    bvc_utils.update_history_file(history_file=history_file,
                                  new_directory_version=new_directory_version,
                                  model_path=model_path,
                                  file_name=file_name,
                                  description=description,
                                  default_file=default_file)


def delete_tag(tag: str):
    tag_directory = os.path.join(FILES_DIRECTORY, tag)
    shutil.rmtree(tag_directory)


def delete_file(tag: str, version: str):
    default_file = os.path.join(FILES_DIRECTORY, tag, DEFAULT)
    history_file = os.path.join(FILES_DIRECTORY, tag, HISTORY)

    # Clean the history file
    directories, data_history = bvc_utils.clean_history(history_file=history_file,default_file = default_file, version=version)
    # Check if the directory will be empty

    if len(directories) == 0:
        delete_tag(tag=tag)
    else:
        last_default, new_default = bvc_utils.new_default_number(default_file=default_file, history_file=history_file)
        # Rewrite the default file with the last version available
        if version == 'default':
            with open(default_file, 'w') as lf:
                new_default = directories[-1]
                lf.write(str(new_default))
                lf.close()

        # Rewrite the history file without the information of the removed file
        with open(history_file, 'w') as hf:
            hf.write(json.dumps(data_history, sort_keys=True))
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
            422, http_status_description='File not found, please check the model name is correct!').get_response()


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
        new_default_file = os.listdir(
            os.path.join(directory_path, version))[0]
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

    return ModelList(
        200, http_status_description='Model list provided', model_list=model_list).get_response()
