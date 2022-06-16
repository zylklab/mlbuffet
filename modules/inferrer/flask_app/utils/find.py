import glob
from sys import argv
from os import getenv, path
import requests
from zipfile import ZipFile
import shutil

#######################################################################
# The ALLOWED EXTENSIONS and get_file_extension function should not be
# extracted to /utils, because find.py is thought to be executed in
# secondary trainer containers/Pods which don't have the utils dir

ALLOWED_EXTENSIONS = [".h5", ".onnx", ".pkl",
                      ".pt", ".pmml", ".pb", ".zip", ".mlmodel"]


def get_file_extension(file_name):
    return path.splitext(file_name)[1]
#######################################################################


# Get what trining library has been used
# In case not supported deployment library, set it as null
library = ""

# Import libraries and in case it works, set library value
try:
    import onnxruntime
    library = 'onnxruntime'
except Exception as e:
    try:
        import tensorflow as tf
        library = 'tensorflow==' + tf.__version__
    except Exception as e:
        pass


def search_and_send():
    for file in glob.glob(f'/home/trainer/**/{FILENAME}', recursive=True):
        if file is not None and get_file_extension(file) in ALLOWED_EXTENSIONS:

            # For TensorFlow models, compress .pb directory into .zip and send it to Inferrer
            if get_file_extension(file) == '.pb':
                shutil.make_archive(
                    base_name=f'{file}', base_dir=f'{file}', format='zip')

                sendfile = open(f'{file}'+'.zip', 'rb')

            # The rest of formats should be single files, so open them to be sent via HTTP request
            else:
                sendfile = open(f'{file}', 'rb')

            # For K8S Environments, call the Inferrer service
            if getenv('ORCHESTRATOR') == 'KUBERNETES':
                response = requests.post(
                    f'http://inferrer:8000/api/v1/models/{TAG}', files={"path": sendfile, "library_version": library})

            # For other environments, call the standard Docker daemon endpoint
            else:
                response = requests.post(
                    f'http://172.17.0.1:8002/api/v1/models/{TAG}', files={"path": sendfile})


# Both Docker or K8S training containers should have this information
FILENAME = getenv('MODEL_NAME')
TAG = getenv('TAG')

search_and_send()
