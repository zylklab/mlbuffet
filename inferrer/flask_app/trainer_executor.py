import tarfile as tar
from os import path

import docker

UPLOADS_DIR = '/dockerinferrer/'


def save_files(train_script, requirements, dataset):
    train_script.save(path.join(UPLOADS_DIR, train_script.filename))
    requirements.save(path.join(UPLOADS_DIR, requirements.filename))
    dataset.save(path.join(UPLOADS_DIR, dataset.filename))

    print("Data have been saved!")


def create_dockerfile():
    dockerfile = open(UPLOADS_DIR + 'Dockerfile', 'w')

    dockerfile.write(
        'FROM python:3.8.1\n'
        f'COPY {UPLOADS_DIR}requirements.txt requirements.txt\n'
        f'COPY {UPLOADS_DIR}train.py train.py\n'
        f'COPY {UPLOADS_DIR}dataset.csv dataset.csv\n'
        'RUN pip install -r requirements.txt\n'
        'ENTRYPOINT python3 train.py\n'
    )
    dockerfile.close()

    # Create a tar file with the docker environment

    buildenv = tar.open(name=UPLOADS_DIR + "environment.tar", mode="x")
    buildenv.add(name=UPLOADS_DIR + "Dockerfile")
    buildenv.add(name=UPLOADS_DIR + "train.py")
    buildenv.add(name=UPLOADS_DIR + "requirements.txt")
    buildenv.add(name=UPLOADS_DIR + "dataset.csv")
    buildenv.close()


def set_client():
    # Configure the Docker Client of the external machine.
    tlsconfig = docker.TLSConfig(client_cert=("./utils/client/cert.pem", "./utils/client/key.pem"),
                                 ca_cert="./utils/client/ca.pem")
    client = docker.DockerClient(base_url="tcp://172.17.0.1:2376", tls=tlsconfig)

    return client


def build_image():
    client = set_client()

    context = open(UPLOADS_DIR + "environment.tar")

    # Build the images sending the context to the external Docker daemon
    client.images.build(fileobj=context, rm=True, pull=True, custom_context=True, dockerfile=UPLOADS_DIR + "Dockerfile",
                        tag="trainer")

    context.close()


def run_training():
    client = set_client()

    container = client.containers.run(image="trainer")

    # >> CREATE DOCKERFILE
    # >> CREATE IMAGE
    # >> RUN Container
    # >> CHECK CONTAINER header_length
    # >> REMOVE FILES

# TODO: def check_logs():
