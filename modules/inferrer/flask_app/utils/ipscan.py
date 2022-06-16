from kubernetes import client, config


def IPScan(service: str):
    """
    IPScan search the IPs of the services deployed in K8S.
    """
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    servicelist = []
    service_name = 'mlbuffet_' + service
    ret = v1.list_namespaced_pod('mlbuffet')
    for item in ret.items:
        try:
            if item.metadata.labels['app'] == service_name:
                servicelist.append(item.status.pod_ip)
        except:
            pass

    return servicelist


def PodNameScan(service: str, tag: str):
    """
    IPScan search the IPs of the services deployed in K8S.
    """
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    PodList = []
    service_name = 'mlbuffet_' + service + '_' + tag
    ret = v1.list_namespaced_pod('mlbuffet')
    for item in ret.items:
        if item.metadata.labels['app'] == service_name:
            PodList.append(item.metadata.name)

    return PodList


def DeploymentNameScan(service: str, tag: str):
    """
    Search the Deployments deployed in K8S.
    """
    config.load_incluster_config()
    appsv1 = client.AppsV1Api()
    DeploymentList = []
    service_name = 'mlbuffet_' + service + '_' + tag

    ret = appsv1.list_namespaced_deployment('mlbuffet')

    for item in ret.items:
        if item.metadata.labels is not None:
            if item.metadata.labels['app'] == service_name:
                DeploymentList.append(item.metadata.name)

    return DeploymentList
