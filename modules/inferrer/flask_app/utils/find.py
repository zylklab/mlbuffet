import glob
from os import getenv, path
import requests
import shutil

#######################################################################
# The ALLOWED EXTENSIONS and get_file_extension function should not be
# extracted to /utils, because find.py is thought to be executed in
# secondary trainer containers/Pods which don't have the utils dir

ALLOWED_EXTENSIONS = [".h5", ".onnx", ".pkl",
                      ".pt", ".pmml", ".pb", ".zip", ".mlmodel"]

# For new supported libraries, include them in this list
SUPPORTED_LIBRARIES = ['onnx', 'tensorflow']


def get_file_extension(file_name):
    return path.splitext(file_name)[1]


#######################################################################

# Get what training library has been used

# In case not supported deployment library, set it as null
library = ""

with open('./requirements.txt', 'r') as requirements:
    for line in requirements.readlines():
        for module in SUPPORTED_LIBRARIES:
            if module in line:
                # Set library value
                if module == 'onnx':
                    library = 'onnxruntime'
                elif module == 'tensorflow':
                    library = line


def search_and_send():
    for file in glob.glob(f'/home/trainer/**/{FILENAME}', recursive=True):
        if file is not None and get_file_extension(file) in ALLOWED_EXTENSIONS:

            file = path.basename(file)

            # For TensorFlow models, compress .pb directory into .zip and send it to Inferrer
            if get_file_extension(file) == '.pb' and path.isdir(file):

                shutil.make_archive(
                    base_name=f'{file}', base_dir=f'{file}', format='zip')

                sendfile = open(f'{file}'+'.zip', 'rb')

            # The rest of formats should be single files, so open them to be sent via HTTP request
            else:
                sendfile = open(f'{file}', 'rb')

            # For K8S Environments, call the Inferrer service
            if getenv('ORCHESTRATOR') == 'KUBERNETES':
                response = requests.post(
                    f'http://inferrer:8000/api/v1/models/{TAG}', files={"path": sendfile}, data={"library_version": library})

            # For other environments, call the standard Docker daemon endpoint
            else:
                response = requests.post(
                    f'http://172.17.0.1:8002/api/v1/models/{TAG}', files={"path": sendfile})


# Both Docker or K8S training containers should have this information
FILENAME = getenv('MODEL_NAME')
TAG = getenv('TAG')

search_and_send()
