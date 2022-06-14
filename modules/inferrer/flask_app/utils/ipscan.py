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
