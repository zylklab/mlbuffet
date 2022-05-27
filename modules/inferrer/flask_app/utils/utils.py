from os import path

ALLOWED_EXTENSIONS = ['.h5', '.onnx', '.pkl',
                      '.pt', '.pmml', '.pb', '.mlmodel', '.zip']


def get_file_extension(file_name):
    return path.splitext(file_name)[1]


def is_ok(code):
    return str(code).startswith('2')
