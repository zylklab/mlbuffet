import nmap


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
