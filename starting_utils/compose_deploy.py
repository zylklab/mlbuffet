import sys

n = int(sys.argv[1])

f = open('../FractalMLServer-Lite/deploy/docker-compose.yml', 'w')

services = 'version: \'3\' \n' \
           'services:\n'
inferrer = '  inferrer:\n ' \
           '    container_name: inferrer\n ' \
           '    restart: always\n ' \
           '    build: ../inferrer/flask_app\n ' \
           '    ports:\n ' \
           '    - ${INFERRER_API_BIND_TO_PORT}:8000\n ' \
           '    networks:\n ' \
           '      fractalmlserver_network:\n ' \
           '        ipv4_address: ${INFERRER_IP}\n ' \
           '    volumes:\n ' \
           '      - ../inferrer/logs:/home/logs\n ' \
           '      - ./.env:/home/.env\n\n'
prometheus = '  prometheus:\n ' \
             '    container_name: prometheus-fractal\n ' \
             '    restart: always\n ' \
             '    build: ../metrics/prometheus\n ' \
             '    ports:\n ' \
             '      - ${PROMETHEUS_PORT}:9090\n ' \
             '    networks:\n ' \
             '      fractalmlserver_network:\n ' \
             '        ipv4_address: ${PROMETHEUS_IP}\n\n'
nginx = '  nginx:\n ' \
        '      container_name: nginx-fractal\n ' \
        '      restart: always\n ' \
        '      build: ../inferrer/nginx\n ' \
        '      ports:\n ' \
        '        - "80:80"\n ' \
        '      depends_on:\n ' \
        '        - inferrer\n ' \
        '      networks:\n ' \
        '        fractalmlserver_network:\n ' \
        '          ipv4_address: ${LOAD_BALANCER_IP}\n ' \
        '      volumes:\n ' \
        '        - ./service-configurations/nginx-config/:/etc/nginx/conf.d/\n\n'
networks = 'networks:\n ' \
           '  fractalmlserver_network:\n ' \
           '    driver: bridge\n ' \
           '    ipam:\n ' \
           '     config:\n ' \
           '       - subnet: ${FRACTALMLSERVER_SUBNET}\n ' \
           '         gateway: ${FRACTALMLSERVER_GATEWAY}\n\n'
f.write(services)
f.write(inferrer)
for i in range(n):
    j = i+1
    modelhost = '  modelhost_' + str(j) + ':\n ' \
                '    container_name: modelhost_' + str(j) +'\n ' \
                '    restart: always\n ' \
                '    build: ../modelhost/flask_app\n ' \
                '    ports:\n ' \
                '    - ${MODELHOST_' + str(j) +'_API_BIND_TO_PORT}:8000\n ' \
                '    networks:\n ' \
                '      fractalmlserver_network:\n ' \
                '        ipv4_address: ${MODELHOST_' + str(j) +'_IP}\n ' \
                '    volumes:\n ' \
                '        - ../modelhost/logs:/home/logs\n ' \
                '        - .env:/home/.env\n ' \
                '        - ../modelhost/flask_app/models:/usr/src/flask_app/models\n\n'

    f.write(modelhost)
f.write(prometheus)
f.write(nginx)
f.write(networks)
