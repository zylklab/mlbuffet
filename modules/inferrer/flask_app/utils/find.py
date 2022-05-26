import glob
from sys import argv

import requests

from utils import get_file_extension, ALLOWED_EXTENSIONS

FILENAME = argv[1]

TAG = argv[2]

for file in glob.glob(f'/home/trainer/**/{FILENAME}', recursive=True):
    if file is not None and get_file_extension(file) in ALLOWED_EXTENSIONS:
        response = requests.put(f'http://172.17.0.1:8002/api/v1/models/{TAG}', files={"path": open(file, 'rb')})
