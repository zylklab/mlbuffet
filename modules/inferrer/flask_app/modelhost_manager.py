from os import path, getenv
from tkinter import E
from kubernetes import client as kclient, config
import requests

from utils.inferer_pojos import HttpJsonResponse

# Request constants
URI_SCHEME = 'http://'


def _url(resource):
    #    return URI_SCHEME + LOAD_BALANCER_ENDPOINT + resource
    return URI_SCHEME + 'modelhost:8000' + resource


def _is_ok(code):
    return str(code).startswith('2')


def _get(resource):
    return requests.get(_url(resource)).json()


def _post(resource, json_data):
    response = requests.post(_url(resource), json=json_data).json()
    return response


def _put(resource, files):
    response = requests.put(_url(resource), files=files).json()
    return response


def make_a_prediction(tag, model_input):
    resource = f'/modelhost/models/{tag}/prediction'
    return _post(resource, {'values': model_input})


def delete_modelhost(tag):
    # DELETE POD FROM K8S API

    return 'MODELHOST DELETED'


def create_modelhost(tag, ml_library):
    # Train in K8S environments
    config.load_incluster_config()
    v1 = kclient.CoreV1Api()


#####################################################
#####################################################
# apiVersion: apps/v1
# kind: Deployment
# metadata:
#   name: modelhost
#   namespace: mlbuffet
#   labels:
#     app: mlbuffet_modelhost
# spec:
#   replicas: 1
#   selector:
#     matchLabels:
#       app: mlbuffet_modelhost
#   template:
#     metadata:
#       labels:
#         app: mlbuffet_modelhost
#     spec:
#       containers:
#         - name: modelhost
#           image: IMAGE_MLBUFFET_MODELHOST
#           imagePullPolicy: Always
#           ports:
#             - containerPort: 8000
# ---
# apiVersion: v1
# kind: Service
# metadata:
#   name: modelhost
#   namespace: mlbuffet
# spec:
#   selector:
#     app: mlbuffet_modelhost
#   ports:
#   - protocol: TCP
#     port: 8000
#     targetPort: 8000
#   type: ClusterIP
#   internalTrafficPolicy: Cluster
#####################################################
#####################################################

    NAMESPACE = 'mlbuffet'
    NAME = f'modelhost_{tag}'
    IMAGE = getenv('IMAGE_MLBUFFET_MODELHOST')

    # Fill the environment variables list
    ENV_LIST = []
    ENV1 = kclient.V1EnvVar(name='ML_LIBRARY', value=f'{ml_library}')
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
        service_account_name='pod-scheduler', containers=CONTAINER_LIST, restart_policy='Never')

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
