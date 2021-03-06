from os import getenv
from utils.ipscan import DeploymentNameScan, PodNameScan
from kubernetes import client as kclient, config
import requests

import datetime

from utils.inferer_pojos import HttpJsonResponse

# Request constants
URI_SCHEME = 'http://'
NAMESPACE = 'mlbuffet'


def _url(tag, resource):
    #    return URI_SCHEME + LOAD_BALANCER_ENDPOINT + resource
    return URI_SCHEME + f'modelhost-{tag}:8000' + resource


def _is_ok(code):
    return str(code).startswith('2')


def _get(tag, resource):
    return requests.get(_url(tag, resource)).json()


def _post(tag, resource, json_data):
    response = requests.post(_url(tag, resource), json=json_data).json()
    return response


def _put(tag, resource, files):
    response = requests.put(_url(tag, resource), files=files).json()
    return response


def make_a_prediction(tag, model_input):
    resource = f'/modelhost/predict'
    return _post(tag, resource, {'values': model_input})


def delete_modelhost(tag):
    # Delete Modelhost Deployment from the K8S cluster

    # Load K8S Cluster config
    config.load_incluster_config()
    appsv1 = kclient.AppsV1Api()
    v1 = kclient.CoreV1Api()

    # Make the API requests to delete the Modelhost Deployment and Service
    try:
        appsv1.delete_namespaced_deployment(
            name=f'modelhost-{tag}', namespace='mlbuffet')

    except Exception as e:
        print("Exception when calling AppsV1Api->delete_namespaced_deployment: %s\n" % e)

    try:
        api_response = v1.delete_namespaced_service(
            name=f'modelhost-{tag}', namespace='mlbuffet')

    except Exception as e:
        print("Exception when calling CoreV1Api->delete_namespaced_service: %s\n" % e)


def _create_body_deployment(tag: str):
    # Define constants

    NAME = f'modelhost-{tag}'

    ############################################
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
    #############################################

    IMAGE = getenv('IMAGE_MLBUFFET_MODELHOST')

    # Fill the environment variables list
    ENV_LIST = []
    ENV = kclient.V1EnvVar(name='TAG', value=tag)
    ENV_LIST.append(ENV)

    ################# Fill the container list that goes into V1PodSpec #############################
    CONTAINER_LIST = []
    mlbuffet_container = kclient.V1Container(
        name=NAME, image=IMAGE, image_pull_policy='Always', env=ENV_LIST, ports=[kclient.V1ContainerPort(container_port=8000)])

    CONTAINER_LIST.append(mlbuffet_container)
    ################################################################################################
    # |
    # V
    ################# Create the Pod Spec which goes into V1PodTemplateSpec ########################
    V1PodSpec = kclient.V1PodSpec(containers=CONTAINER_LIST)
    ################################################################################################
    # |
    # V
    ################ These two go into V1Deployment ################################################
    # Create the Metadata of the Deployment and Pod
    V1ObjectMeta = kclient.V1ObjectMeta(name=NAME, namespace=NAMESPACE, labels={
        "app": f"mlbuffet_modelhost_{tag}"})

    # Create the Pod Template Spec
    V1PodTemplateSpec = kclient.V1PodTemplateSpec(
        metadata=kclient.V1ObjectMeta(labels={"app": f"mlbuffet_modelhost_{tag}"}), spec=V1PodSpec)

    # Create the Deployment Spec
    V1DeploymentSpec = kclient.V1DeploymentSpec(
        replicas=1, template=V1PodTemplateSpec,
        selector=kclient.V1LabelSelector(match_labels={"app": f"mlbuffet_modelhost_{tag}"}))
    ################################################################################################
    # |
    # V
    ################ This one goes into create_namespaced_deployment ###############################
    # Create Deployment body
    V1Deployment = kclient.V1Deployment(
        api_version='apps/v1', kind='Deployment', metadata=V1ObjectMeta, spec=V1DeploymentSpec)
    ################################################################################################
    # |
    # V

    return V1Deployment


def _create_body_service(tag):
    NAME = f'modelhost-{tag}'
    # Now create a K8S Service to access the Modelhost Pod
    ###################################
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
    ###################################

    ################ This goes in Service Spec ######################################################
    # Create Service Ports
    servicePorts = [kclient.V1ServicePort(
        protocol='TCP', port=8000, target_port=8000)]
    #################################################################################################
    # |
    # V
    ################ These two go in Service Body ###################################################
    v1ServiceMeta = kclient.V1ObjectMeta(name=NAME, namespace=NAMESPACE)
    v1ServiceSpec = kclient.V1ServiceSpec(selector={"app": f"mlbuffet_modelhost_{tag}"},
                                          ports=servicePorts, type='ClusterIP',
                                          internal_traffic_policy='Cluster')
    #################################################################################################
    # |
    # V
    ################ Body goes in the API call ######################################################
    v1ServiceBody = kclient.V1Service(api_version='v1',
                                      kind='Service',
                                      metadata=v1ServiceMeta,
                                      spec=v1ServiceSpec)
    #################################################################################################
    # |
    # V
    #################################################################################################
    return v1ServiceBody


def create_modelhost(tag):
    # Load K8S Cluster config
    config.load_incluster_config()
    v1 = kclient.CoreV1Api()
    api_instance = kclient.AppsV1Api()

    """
    This function first checks that the Deployment name does not already exist for a given tag.
    If the Deployment exists, it performs a rollout restart that will restart the Modelhost Pod, 
    forcing it to download the correct version of the model from Storage.
    If the deployment does not exist, it creates a new Deployment and binds it to a new Service.
    """

    if f'modelhost-{tag}' in DeploymentNameScan('modelhost', tag):

        """
        https://github.com/kubernetes-client/python/issues/1378
        'kubectl rollout restart deployment' command does not exists out of the box in the Python API.
        This issue describes how to do it with the Python Client, by sending the same API call as the Kubectl.
        """

        try:
            now = datetime.datetime.utcnow()
            now = str(now.isoformat("T") + "Z")

            restart_body = {
                'spec': {
                    'template': {
                        'metadata': {
                            'annotations': {
                                'kubectl.kubernetes.io/restartedAt': now
                            }
                        }
                    }
                }
            }

            api_instance.patch_namespaced_deployment(
                namespace=NAMESPACE, name=f'modelhost-{tag}', body=restart_body)
        except Exception as e:
            print(
                "Exception when calling AppsV1Api->patch_namespaced_deployment: %s\n" % e)

    else:
        # Create the Deployment and Service if it does not previously exist

        # Deployment creation
        try:
            V1Deployment = _create_body_deployment(tag)
            api_instance.create_namespaced_deployment(namespace=NAMESPACE,
                                                      body=V1Deployment)
        except Exception as e:
            print(
                "Exception when calling AppsV1Api->create_namespaced_deployment: %s\n" % e)

        # Service creation
        try:
            v1ServiceBody = _create_body_service(tag)
            v1.create_namespaced_service(namespace=NAMESPACE,
                                             body=v1ServiceBody)
        except Exception as e:
            print(
                "Exception when calling CoreV1Api->create_namespaced_service: %s\n" % e)

