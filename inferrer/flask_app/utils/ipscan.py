import nmap
from kubernetes import client, config

# IPScan for Docker Swarm

def IPScan(network):
    nm = nmap.PortScanner()
    nm.scan(hosts=network, arguments="-sn")

    listaddr = nm.all_hosts()
    modelhostlist = []

    for addr in listaddr:
        try:
            is_host = nm[addr].get('hostnames')[0]['name']
        except IndexError:
            is_host = ''

        if 'modelhost' in is_host:
            modelhostlist.append(addr)

    return modelhostlist


# IPScan for Kubernetes

def KubeIPScan():
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    modelhostlist = []
    ret = v1.list_namespaced_pod('mlbuffet')
    for item in ret.items:
        if item.metadata.labels['app'] == 'mlbuffet_modelhost':
            modelhostlist.append(item.status.pod_ip)
        # print([item.status.pod_ip, item.metadata.name, item.metadata])
    return modelhostlist