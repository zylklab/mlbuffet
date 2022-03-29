import glob
import requests
import os
from sys import argv

FILENAME = argv[1]

TAG = argv[2]


def get_file_extension(file_name):
    return os.path.splitext(file_name)[1]


allowed_extensions = [".h5", ".onnx", ".pkl",
                      ".pt", ".pmml", ".pb", ".zip", ".mlmodel"]

for file in glob.glob(f'/home/trainer/**/{FILENAME}', recursive=True):
    if file is not None and get_file_extension(os.path.basename(file)) in allowed_extensions:

        response = requests.put(
            f'http://172.17.0.1:8002/api/v1/models/{TAG}', files={"path": open(file, 'rb')})
