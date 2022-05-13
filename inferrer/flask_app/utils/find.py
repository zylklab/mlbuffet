import glob
from sys import argv

import requests

from utils import get_file_extension

FILENAME = argv[1]

TAG = argv[2]

allowed_extensions = [".h5", ".onnx", ".pkl",
                      ".pt", ".pmml", ".pb", ".zip", ".mlmodel"]

for file in glob.glob(f'/home/trainer/**/{FILENAME}', recursive=True):
    if file is not None and get_file_extension(file) in allowed_extensions:
        response = requests.put(f'http://172.17.0.1:8002/api/v1/models/{TAG}', files={"path": open(file, 'rb')})
