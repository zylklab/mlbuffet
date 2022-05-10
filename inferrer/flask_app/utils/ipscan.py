import nmap
from kubernetes import client, config

# IPScan for Docker Swarm

def IPScan(service: str):
    """
    IPScan search the IPs of the service nodes. The way of how IPScan tries to do it, is different if MLBuffet is
    deployed on Kubernetes or Docker Swarm.
    """

    listaddr = nm.all_hosts()
    modelhostlist = []

    key = 'ORCHESTRATOR'

        if 'modelhost' in is_host:
            modelhostlist.append(addr)

    if getenv(key) == 'KUBERNETES':
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        servicelist = []
        service_name = 'mlbuffet_' + service
        ret = v1.list_namespaced_pod('mlbuffet')
        for item in ret.items:
            if item.metadata.labels['app'] == service_name:
                servicelist.append(item.status.pod_ip)


    else:
        network = getenv('OVERLAY_NETWORK')
        nm = nmap.PortScanner()
        nm.scan(hosts=network, arguments="-sn")
        listaddr = nm.all_hosts()
        servicelist = []

        for addr in listaddr:
            try:
                is_host = nm[addr].get('hostnames')[0]['name']
            except IndexError:
                is_host = ''
            if service in is_host:
                servicelist.append(addr)

    return servicelist
