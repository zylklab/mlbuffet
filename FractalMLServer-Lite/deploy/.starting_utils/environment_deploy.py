import sys

"""Script for generating .env file based on desired number of Modelhosts"""

file_part1 = """\
### GLOBAL ###
FRACTALMLSERVER_SUBNET=172.24.0.0/16
FRACTALMLSERVER_GATEWAY=172.24.0.1
FLASK_PORT=8443


### PROMETHEUS ###
PROMETHEUS_IP=172.24.0.9
PROMETHEUS_PORT=9090


### FRACTALMLSERVER_INFERRER ###
INFERRER_IP=172.24.0.2
INFERRER_API_BIND_TO_PORT=8002
#TODO #INFER_MODE=PARALLEL/FEDERATED ?


### LOAD BALANCER ###
LOAD_BALANCER_IP=172.24.0.4
LOAD_BALANCER_PORT=80
LOAD_BALANCER_ENDPOINT=${LOAD_BALANCER_IP}:${LOAD_BALANCER_PORT}


### FRACTALMLSERVER_MODELHOST ###
    #MODELHOST_N_IP=<NODE_N_IP>
    #MODELHOST_N_API_BIND_TO_PORT=<NODE_N_PORT>
    # if adding more instances, changes should be done on
    # - nginx: ./service-configurations/nginx-config/project.conf adding a server line
    # - docker-compose: adding a service instance with Nth IP/PORT params

"""

# dynamic part
file_part2 = """\
NUMBER_MODELHOST_NODES={0}

"""

# dynamic part
file_part3 = """\
MODELHOST_{0}_IP=172.24.0.{1}
MODELHOST_{0}_API_BIND_TO_PORT={2}

"""

with open('./.env', 'w') as f:
    # write file part 1
    f.write(file_part1)

    num_modelhosts = int(sys.argv[1])

    # write file part 2
    f.write(file_part2.format(num_modelhosts))

    # write for each Modelhost
    for i in range(num_modelhosts):
        f.write(file_part3.format(i + 1,
                                  i + 11,
                                  i + 8004))
