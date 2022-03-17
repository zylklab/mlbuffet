from distutils.command.upload import upload
import re
import tarfile as tar
from os import path
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

    dockerfile.write(
        'FROM python:3.8.1\n' +
        'COPY ' + upload_path('requirements.txt') + ' requirements.txt\n' +
        'COPY ' + upload_path('train.py') + ' train.py\n' +
        'COPY ' + upload_path('dataset.csv') + ' dataset.csv\n' +
        'RUN pip install -r requirements.txt\n'
        'ENTRYPOINT python3 train.py\n'
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


def build_image():

    client = create_client()

    context = open(upload_path('environment.tar'), "r")

    ## Pasar un filtro de encoding para que todos los ficheros dentro de context sean ascii

    # Build the images sending the context to the external Docker daemon
    client.images.build(fileobj=context, rm=True, pull=True, custom_context=True,
                        tag="trainer", dockerfile='Dockerfile')

    # client.api.build(fileobj=context, rm=True, pull=True,
    #                     tag="trainer")
    context.close()


def run_training(train_script, requirements, dataset):
    save_files(train_script, requirements, dataset)

    # Create Dockerfile with the files in it
    create_dockerfile()

    # Build the image
    build_image()
    print("Image built!")

    # Run the image
    client = create_client()  # TODO: do not create client again
    container = client.containers.run(image="trainer")
    print("Training started!")

    # >> CREATE DOCKERFILE
    # >> CREATE IMAGE
    # >> RUN Container
    # >> CHECK CONTAINER header_length
    # >> REMOVE FILES

# TODO: def check_logs():
