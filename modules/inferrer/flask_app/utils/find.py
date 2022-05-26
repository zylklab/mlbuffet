import glob
from sys import argv
from os import getenv, path
import requests

ALLOWED_EXTENSIONS = [".h5", ".onnx", ".pkl",
                      ".pt", ".pmml", ".pb", ".zip", ".mlmodel"]


def get_file_extension(file_name):
    return path.splitext(file_name)[1]


FILENAME = getenv('MODEL_NAME')
TAG = getenv('TAG')

for file in glob.glob(f'/home/trainer/**/{FILENAME}', recursive=True):
    if file is not None and get_file_extension(file) in ALLOWED_EXTENSIONS:

        if getenv('ORCHESTRATOR') == 'KUBERNETES':
            response = requests.put(
                f'http://inferrer:8000/api/v1/models/{TAG}', files={"path": open(file, 'rb')})
        else:
            response = requests.put(
                f'http://172.17.0.1:8002/api/v1/models/{TAG}', files={"path": open(file, 'rb')})
