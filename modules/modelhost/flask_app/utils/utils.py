from os import path


def get_model_library(file_name):

    # Check filename extension
    extension = path.splitext(file_name)[1]

    if extension == '.onnx':
        ML_LIBRARY = 'onnx'
    elif extension == '.pb':
        ML_LIBRARY = 'tf'
    # elif add new supported libraries
    else:
        ML_LIBRARY = 'UNSUPPORTED'

    return ML_LIBRARY
