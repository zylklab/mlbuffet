from importlib.resources import path
from kubernetes import client as kclient
from kubernetes import config

config.load_incluster_config()
v1 = kclient.CoreV1Api()

# Trainer Pod deletes itself
try:
    api_response = v1.delete_namespaced_pod(
        name='trainer', namespace='mlbuffet')

except Exception as e:
    print("Exception when calling CoreV1Api->connect_delete_namespaced_pod_proxy: %s\n" % e)
