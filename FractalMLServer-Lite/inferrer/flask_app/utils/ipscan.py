import nmap

def IPScan(network):
    nm = nmap.PortScanner()
    nm.scan(hosts=network, arguments="-sn")

    listaddr = nm.all_hosts()
    modelhostlist = []

    for addr in listaddr:
        print(nm[addr].hostname())

        if 'modelhost' in nm[addr].hostname():
            modelhostlist.append(addr)

    return listaddr


