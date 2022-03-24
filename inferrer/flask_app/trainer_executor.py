from distutils.command.upload import upload
import re
import tarfile as tar
from os import path, remove
import docker

UPLOADS_DIR = '/trainerfiles/'


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

def create_dockerfile(model_name):
    dockerfile = open(upload_path('Dockerfile'), 'w')

    # TODO: USE GLOB LIBRARY TO SEARCH THE MODEL IN THE TRAINER CONTAINER
    MODEL_PATH = path.join("./", model_name)
    
    dockerfile.write(
        'FROM python:3.8.1\n' +
        'RUN useradd -s /bin/bash trainer\n' +
        'RUN mkdir /home/trainer\n' +
        'RUN chown -R trainer:trainer /home/trainer\n' +
        'USER trainer\n' + 
        'WORKDIR /home/trainer\n' +
        'RUN pip install requests\n' + 
        'COPY --chown=trainer ' + upload_path('requirements.txt') + ' requirements.txt\n' +
        'COPY --chown=trainer ' + upload_path('train.py') + ' train.py\n' +
        'COPY --chown=trainer ' + upload_path('dataset.csv') + ' dataset.csv\n' +
        'COPY --chown=trainer ' + upload_path('find.py') + ' find.py\n' + 
        'RUN pip install -r requirements.txt\n' + 
        f'ENTRYPOINT python3 train.py && python3 find.py {model_name}\n'
    )
    
    dockerfile.close()

    # Create a tar file with the docker environment
    buildenv = tar.open(name=upload_path('environment.tar'), mode='x')
    buildenv.add(name=upload_path('Dockerfile'), arcname='Dockerfile')
    buildenv.add(name=upload_path('train.py'))
    buildenv.add(name=upload_path('requirements.txt'))
    buildenv.add(name=upload_path('dataset.csv'))
    buildenv.add(name=upload_path('find.py'))
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

    remove(upload_path("Dockerfile"))
    remove(upload_path("requirements.txt"))
    remove(upload_path("train.py"))
    remove(upload_path("dataset.csv"))
    remove(upload_path("environment.tar"))


def run_training(train_script, requirements, dataset, model_name):
    save_files(train_script, requirements, dataset)

    # Create Dockerfile with the files in it
    create_dockerfile(model_name)

    client = create_client()

    # Build the image
    build_image(client)

    # TODO: Do this in a thread so the user gets back the control of his terminal
    # Run the image
    container = client.containers.run(image="trainer", detach=True)


    # >> CHECK CONTAINER header_length

# TODO: def check_logs():
