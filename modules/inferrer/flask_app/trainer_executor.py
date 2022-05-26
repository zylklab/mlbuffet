from lib2to3.pgen2.token import NAME
from zipfile import ZipFile
from os import environ, path, remove
import docker
from os import getenv
from kubernetes import config
from kubernetes import client as kclient


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
    remove(upload_path('Dockerfile'))
    remove(upload_path('requirements.txt'))
    remove(upload_path('train.py'))
    if getenv('ORCHESTRATOR') == 'KUBERNETES':
        remove(upload_path('environment.sh'))
    try:
        remove(upload_path("dataset.csv"))
    except Exception as e:
        print(e)
        remove(upload_path("dataset.zip"))

    if getenv('ORCHESTRATOR') == 'KUBERNETES':
        remove(upload_path("environment.zip"))


def create_dockerfile(model_name, tag):
    dockerfile = open(upload_path('Dockerfile'), 'w')

    dockerfile.write(
        'FROM python:3.8.1\n' +
        'RUN useradd -s /bin/bash trainer\n' +
        'RUN mkdir /home/trainer\n' +
        'RUN chown -R trainer:trainer /home/trainer\n' +
        'USER trainer\n' +
        'WORKDIR /home/trainer\n' +
        'RUN pip install requests\n' +
        'RUN curl 172.17.0.1:8002/api/v1/train/download_buildenv --output environment.zip\n'
        'RUN unzip environment.zip\n' +
        'WORKDIR /home/trainer/trainerfiles\n' +
        'RUN pip install -r requirements.txt\n' +
        f'ENTRYPOINT python3 train.py && python3 find.py {model_name} {tag}\n'
    )

    dockerfile.close()


def create_client():
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

    # Create Dockerfile with the files in it
    if not getenv('ORCHESTRATOR') == 'KUBERNETES':
        create_dockerfile(model_name, tag)

        client = create_client()
        # Build the image
        build_image(client)

        # TODO: Do this in a thread so the user gets back the control of his terminal
        # Run the image
        container = client.containers.run(image="trainer", detach=True)
        # >> CHECK CONTAINER header_length

    else:
        config.load_incluster_config()
        v1 = kclient.CoreV1Api()

        # apiVersion: apps/v1
        # kind: Pod
        # metadata:
        #   name: trainer
        #   namespace: mlbuffet
        # spec:
        #   replicas: 1
        #   selector:
        #     matchLabels:
        #       app: mlbuffet_trainer
        #   template:
        #     metadata:
        #       labels:
        #         app: mlbuffet_trainer
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
        # All this must be parsed into Python objects

        NAMESPACE = 'mlbuffet'
        NAME = 'trainer'
        IMAGE = 'localhost:5000/mlbuffet_trainer'

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
            service_account_name='pod-scheduler', containers=CONTAINER_LIST)

        # Create the Metadata of the Pod
        V1ObjectMeta = kclient.V1ObjectMeta(
            name=NAME, namespace=NAMESPACE)

        # Create Pod body
        V1Pod = kclient.V1Pod(api_version='v1', kind='Pod',
                              metadata=V1ObjectMeta, spec=V1PodSpec)  # V1Pod |

        # str | fieldValidation determines how the server should respond to unknown/duplicate fields in the object in the request.
        # Introduced as alpha in 1.23, older servers or servers with the `ServerSideFieldValidation` feature disabled will discard
        # valid values specified in  this param and not perform any server side field validation. Valid values are:
        # - Ignore: ignores unknown/duplicate fields.
        # - Warn: responds with a warning for each unknown/duplicate field, but successfully serves the request.
        # - Strict: fails the request on unknown/duplicate fields. (optional)
        field_validation = 'Ignore'

        try:
            api_response = v1.create_namespaced_pod(
                NAMESPACE, body=V1Pod)
            print(api_response)
        except Exception as e:
            print("Exception when calling CoreV1Api->create_namespaced_pod: %s\n" % e)

        # trainerPod.

        # STEPS TO FOLLOW:
        # 1.- Create Pod from trainer image
        # 2.- Get download_buildenv call
        # 3.- Execute train.py
        # 4.- Execute find.py
        # 5.- Receive the model back
        #

# TODO: def check_logs():
