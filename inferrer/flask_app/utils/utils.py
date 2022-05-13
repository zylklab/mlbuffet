from os import path


def get_file_extension(file_name):
    return path.splitext(file_name)[1]
