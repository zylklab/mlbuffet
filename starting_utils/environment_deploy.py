import sys

n = int(sys.argv[1])

f = open('../FractalMLServer-Lite/deploy/.env', 'w')

cab = '### GLOBAL ###\n' \
      'FRACTALMLSERVER_SUBNET=172.24.0.0/16\n' \
      'FRACTALMLSERVER_GATEWAY=172.24.0.1\n' \
      '\n ' \
      '### PROMETHEUS ###\n' \
      'PROMETHEUS_IP=172.24.0.9\n' \
      'PROMETHEUS_PORT=9090\n' \
      'FLASK_PORT=8443\n' \
      '\n ' \
      '\n ' \
      '### FRACTALMLSERVER_INFERRER ###\n' \
      'INFERRER_IP=172.24.0.2\n' \
      'INFERRER_API_BIND_TO_PORT=8002\n' \
      '#TODO #INFER_MODE=PARALLEL/FEDERATED ?\n' \
      '\n ' \
      '\n ' \
      '### LOAD BALANCER ###\n' \
      'LOAD_BALANCER_IP=172.24.0.4\n' \
      'LOAD_BALANCER_PORT=80\n' \
      'LOAD_BALANCER_ENDPOINT=${LOAD_BALANCER_IP}:${LOAD_BALANCER_PORT}\n' \
      '\n ' \
      '\n ' \
      '### FRACTALMLSERVER_MODELHOST ###\n' \
      '    #MODELHOST_N_IP=<NODE_N_IP>\n' \
      '    #MODELHOST_N_API_BIND_TO_PORT=<NODE_N_PORT>\n' \
      '    # if adding more instances, changes should be done on\n' \
      '    # - nginx: ./service-configurations/nginx-config/project.conf adding a server line\n' \
      '    # - docker-compose: adding a service instance with Nth IP/PORT params\n' \
      '    #TODO this could be done by config-file initialization script (array of nodes)\n\n' \
      'NUMBER_MODELHOST_NODES=' + str(n) + '\n\n'
f.write(cab)
for i in range(n):
    j = i + 1
    modelhost = 'MODELHOST_' + str(j) + '_IP=172.24.0.' + str(11 +i) + '\n' \
                'MODELHOST_' + str(j) + '_API_BIND_TO_PORT=' + str(8004 + i) + '\n\n'
    f.write(modelhost)
