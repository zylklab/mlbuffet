import tarfile as tar
from os import path

import docker

UPLOADS_DIR = '/dockerinferrer/'


def get_path(file):
    return path.join(UPLOADS_DIR, file)


def save_files(train_script, requirements, dataset):
    train_script.save(get_path(train_script.filename))
    requirements.save(get_path(requirements.filename))
    dataset.save(get_path(dataset.filename))

    print("Data have been saved!")


def create_dockerfile():
    dockerfile = open(get_path('Dockerfile'), 'w')

    dockerfile.write(
        'FROM python:3.8.1\n' +
        'COPY ' + get_path('requirements.txt') + ' requirements.txt\n' +
        'COPY ' + get_path('train.py') + ' train.py\n' +
        'COPY ' + get_path('dataset.csv') + ' dataset.csv\n' +
        'RUN pip install -r requirements.txt\n'
        'ENTRYPOINT python3 train.py\n'
    )
    dockerfile.close()

    # Create a tar file with the docker environment

    buildenv = tar.open(name=get_path('environment.tar'), mode='x')
    buildenv.add(name=get_path('Dockerfile'))
    buildenv.add(name=get_path('train.py'))
    buildenv.add(name=get_path('requirements.txt'))
    buildenv.add(name=get_path('dataset.csv'))
    buildenv.close()


def create_client():
    # Configure the Docker Client to connect to the external machine
    tlsconfig = docker.TLSConfig(client_cert=("./utils/client/cert.pem", "./utils/client/key.pem"),
                                 ca_cert="./utils/client/ca.pem")
    return docker.DockerClient(base_url='tcp://172.17.0.1:2376', tls=tlsconfig)


def build_image():
    client = create_client()

    context = open(get_path('environment.tar'))

    # Build the images sending the context to the external Docker daemon
    client.images.build(fileobj=context, rm=True, pull=True, custom_context=True, dockerfile=get_path('Dockerfile'),
                        tag="trainer")

    context.close()


def run_training(train_script, requirements, dataset):
    save_files(train_script, requirements, dataset)

    # Create Dockerfile with the files in it
    create_dockerfile()

    # Build the image
    build_image()

    # Run the image
    client = create_client()  # TODO: do not create client again
    container = client.containers.run(image="trainer")

    # >> CREATE DOCKERFILE
    # >> CREATE IMAGE
    # >> RUN Container
    # >> CHECK CONTAINER header_length
    # >> REMOVE FILES

# TODO: def check_logs():
