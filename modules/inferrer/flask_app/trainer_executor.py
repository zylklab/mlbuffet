from zipfile import ZipFile
import docker
from os import getenv, listdir, path, remove
from kubernetes import client as kclient, config


UPLOADS_DIR = '/trainerfiles/'


def upload_path(file):
    return path.join(UPLOADS_DIR, file)


def save_files(train_script, requirements, dataset, model_name, tag):
    files = [train_script, requirements, dataset]

    with ZipFile(upload_path('environment.zip'), 'w') as zipfile:
        zipfile.write(upload_path('find.py'))

        for file in files:
            # Save the file in /trainerfiles/filename path
            file.save(upload_path(file.filename))

            # Add file to environment.zip
            zipfile.write(upload_path(file.filename))


def remove_buildenv():

    for file in listdir(UPLOADS_DIR):
        if file != 'find.py':
            remove(upload_path(file))


def create_dockerfile(model_name, tag):
    dockerfile = open(upload_path('Dockerfile'), 'w')

    dockerfile.write(
        'FROM python:3.8.1\n' +
        'RUN useradd -s /bin/bash trainer\n' +
        'RUN mkdir /home/trainer\n' +
        'RUN chown -R trainer:trainer /home/trainer\n' +
        'USER trainer\n' +
        f'ENV MODEL_NAME={model_name}\n' +
        f'ENV TAG={tag}\n' +
        'WORKDIR /home/trainer\n' +
        'RUN pip install requests\n' +
        'RUN curl 172.17.0.1:8002/api/v1/train/download_buildenv --output environment.zip\n'
        'RUN unzip environment.zip\n' +
        'WORKDIR /home/trainer/trainerfiles\n' +
        'RUN pip install -r requirements.txt\n' +
        f'ENTRYPOINT python3 train.py && python3 find.py\n'
    )

    dockerfile.close()


def create_docker_client():
    # Configure the Docker Client to connect to the external machine
    tlsconfig = docker.TLSConfig(client_cert=("./utils/client/cert.pem", "./utils/client/key.pem"),
                                 ca_cert="./utils/client/ca.pem")
    return docker.DockerClient(base_url='tcp://172.17.0.1:2376', tls=tlsconfig)


def build_image(client):
    # Build the images sending the context to the external Docker daemon
    client.images.build(path=UPLOADS_DIR, rm=True,
                        pull=True, tag='trainer')


def run_training(train_script, requirements, dataset, model_name, tag):
    save_files(train_script, requirements, dataset, model_name, tag)

    if getenv('TRAINER_MANAGER') == 'KUBERNETES':
        # Train in K8S environments
        config.load_incluster_config()
        v1 = kclient.CoreV1Api()

        #####################################################
        # apiVersion: apps/v1
        # kind: Pod
        # metadata:
        #   name: trainer
        #   namespace: mlbuffet
        # spec:
        #   replicas: 1
        #   template:
        #     spec:
        #      serviceAccountName: pod-scheduler
        #      containers:
        #         - name: trainer
        #           image: localhost:5000/mlbuffet_trainer
        #           imagePullPolicy: Always
        #           env:
        #             - name: ORCHESTRATOR
        #               value: "KUBERNETES"
        #             - name: MODEL_NAME
        #               value: "model_name"
        #             - name: TAG
        #               value: "tag"
        # This YAML must be parsed into Python objects
        #####################################################

        NAMESPACE = 'mlbuffet'
        NAME = 'trainer'
        IMAGE = getenv('IMAGE_MLBUFFET_TRAINER')

        # Fill the environment variables list
        ENV_LIST = []
        ENV1 = kclient.V1EnvVar(name='ORCHESTRATOR', value='KUBERNETES')
        ENV2 = kclient.V1EnvVar(name='MODEL_NAME', value=model_name)
        ENV3 = kclient.V1EnvVar(name='TAG', value=tag)
        ENV_LIST.append(ENV1)
        ENV_LIST.append(ENV2)
        ENV_LIST.append(ENV3)

        # Fill the container list
        CONTAINER_LIST = []
        trainer_container = kclient.V1Container(
            name=NAME, image=IMAGE, image_pull_policy='Always', env=ENV_LIST)
        CONTAINER_LIST.append(trainer_container)

        # Create the Pod Spec
        V1PodSpec = kclient.V1PodSpec(
            service_account_name='trainer-sa', containers=CONTAINER_LIST, restart_policy='Never')

        # Create the Metadata of the Pod
        V1ObjectMeta = kclient.V1ObjectMeta(
            name=NAME, namespace=NAMESPACE)

        # Create Pod body
        V1Pod = kclient.V1Pod(api_version='v1', kind='Pod',
                              metadata=V1ObjectMeta, spec=V1PodSpec)

        try:
            api_response = v1.create_namespaced_pod(
                NAMESPACE, body=V1Pod)

        except Exception as e:
            print("Exception when calling CoreV1Api->create_namespaced_pod: %s\n" % e)

    else:
        # Train in Docker environments
        # Create Dockerfile
        create_dockerfile(model_name, tag)

        client = create_docker_client()
        # Build the image
        build_image(client)

        # Run the image
        container = client.containers.run(image="trainer", detach=True)
