from os import path, getcwd
import shutil


def unzip_models(file_name):
    shutil.unpack_archive(file_name, getcwd())
    return 'Unzipped'


def get_model_library(file_name):

    # Check filename extension
    extension = path.splitext(file_name)[1]

    if extension == '.onnx':
        ML_LIBRARY = 'onnx'
    elif extension == '.pb' or '.h5' or '.zip':
        ML_LIBRARY = 'tf'

        if extension == '.zip':
            unzip_models(file_name)

    # elif add new supported libraries
    else:
        ML_LIBRARY = 'UNSUPPORTED'

    return ML_LIBRARY
