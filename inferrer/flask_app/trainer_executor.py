from distutils.command.upload import upload
import re
import tarfile as tar
from os import path, remove
import docker

UPLOADS_DIR = '/dockerinferrer/'


def upload_path(file):
    return path.join(UPLOADS_DIR, file)


def save_files(train_script, requirements, dataset):

    files = [train_script, requirements, dataset]

    for file in files:
        file.save(upload_path(file.filename))

        with open(upload_path(file.filename),'rb') as source_file:
            contents = source_file.read()
            asciiinfo = contents.decode(encoding='utf-8').encode(encoding='ascii',errors='replace')

        with open(upload_path(file.filename), 'w+b') as dest_file:
            dest_file.write(asciiinfo)

def create_dockerfile():
    dockerfile = open(upload_path('Dockerfile'), 'w')

    # TODO: HTTP CALL TO INFERRER TO UPLOAD MODEL
    dockerfile.write(
        'FROM python:3.8.1\n' +
        'COPY ' + upload_path('requirements.txt') + ' requirements.txt\n' +
        'COPY ' + upload_path('train.py') + ' train.py\n' +
        'COPY ' + upload_path('dataset.csv') + ' dataset.csv\n' +
        'RUN pip install -r requirements.txt\n'
        'ENTRYPOINT python3 train.py && curl -X PUT -F "path=@/path/to/model" http://172.17.0.1:8002/api/v1/models/lstm.onnx'
    )
    dockerfile.close()

    # Create a tar file with the docker environment
    buildenv = tar.open(name=upload_path('environment.tar'), mode='x')
    buildenv.add(name=upload_path('Dockerfile'), arcname='Dockerfile')
    buildenv.add(name=upload_path('train.py'))
    buildenv.add(name=upload_path('requirements.txt'))
    buildenv.add(name=upload_path('dataset.csv'))
    buildenv.close()


def create_client():
    # Configure the Docker Client to connect to the external machine
    tlsconfig = docker.TLSConfig(client_cert=("./utils/client/cert.pem", "./utils/client/key.pem"),
                                 ca_cert="./utils/client/ca.pem")
    return docker.DockerClient(base_url='tcp://172.17.0.1:2376', tls=tlsconfig)


def build_image(client):

    context = open(upload_path('environment.tar'), "r")

    # Build the images sending the context to the external Docker daemon
    client.images.build(fileobj=context, rm=True, pull=True, custom_context=True,
                        tag="trainer", dockerfile='Dockerfile')

    context.close()


def run_training(train_script, requirements, dataset):
    save_files(train_script, requirements, dataset)

    # Create Dockerfile with the files in it
    create_dockerfile()

    client = create_client()

    # Build the image
    build_image(client)

    # Run the image
    container = client.containers.run(image="trainer")

    remove(upload_path("Dockerfile"))
    remove(upload_path("requirements.txt"))
    remove(upload_path("train.py"))
    remove(upload_path("dataset.csv"))
    remove(upload_path("environment.tar"))
    # >> CREATE DOCKERFILE
    # >> CREATE IMAGE
    # >> RUN Container
    # >> CHECK CONTAINER header_length
    # >> REMOVE FILES

# TODO: def check_logs():
