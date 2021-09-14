import nmap

def IPScan():
    nm = nmap.PortScanner()
    nm.scan(hosts="10.0.13.0/24", arguments="-sn")

    listaddr = nm.all_hosts()
    modelhostlist = []

    for addr in listaddr:
        print(nm[addr].hostname())

        if 'modelhost' in nm[addr].hostname():
            modelhostlist.append(addr)

    return listaddr


