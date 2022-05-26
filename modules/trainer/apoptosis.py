from importlib.resources import path
from kubernetes import client as kclient
from kubernetes import config

config.load_incluster_config()
v1 = kclient.CoreV1Api()

try:
    api_response = v1.connect_delete_namespaced_pod_proxy(
        name='trainer', namespace='mlbuffet')
    print(api_response)
except Exception as e:
    print("Exception when calling CoreV1Api->connect_delete_namespaced_pod_proxy: %s\n" % e)
