import sys

"""Script for generating docker-compose.yml file based on desired number of Modelhosts"""

file_part1 = """\
version: '3'
services:

  inferrer:
    container_name: inferrer
    restart: always
    build: ../inferrer/flask_app
    ports:
    - ${INFERRER_API_BIND_TO_PORT}:8000
    networks:
      fractalmlserver_network:
        ipv4_address: ${INFERRER_IP}
    volumes:
      - ../inferrer/logs:/home/logs
      - ./.env:/home/.env

"""

# dynamic part
file_part2 = """\
  modelhost_{0}:
    container_name: modelhost_{0}
    restart: always
    build: ../modelhost/flask_app
    ports:
    - ${{MODELHOST_{0}_API_BIND_TO_PORT}}:8000
    networks:
      fractalmlserver_network:
        ipv4_address: ${{MODELHOST_{0}_IP}}
    volumes:
      - ../modelhost/logs:/home/logs
      - .env:/home/.env
      - ../modelhost/flask_app/models:/usr/src/flask_app/models

"""

file_part3 = """\
  prometheus:
    container_name: prometheus-fractal
    restart: always
    build: ../metrics/prometheus
    ports:
      - ${PROMETHEUS_PORT}:9090
    networks:
      fractalmlserver_network:
        ipv4_address: ${PROMETHEUS_IP}

  nginx:
    container_name: nginx-fractal
    restart: always
    build: ../inferrer/nginx
    ports:
      - "80:80"
    depends_on:
      - inferrer
    networks:
      fractalmlserver_network:
        ipv4_address: ${LOAD_BALANCER_IP}
    volumes:
      - ./service-configurations/nginx-config/:/etc/nginx/conf.d/

networks:
  fractalmlserver_network:
    driver: bridge
    ipam:
      config:
        - subnet: ${FRACTALMLSERVER_SUBNET}
          gateway: ${FRACTALMLSERVER_GATEWAY}

"""

with open('./docker-compose.yml', 'w') as f:
    # write file part 1
    f.write(file_part1)

    # write for each Modelhost
    num_modelhosts = int(sys.argv[1])
    for i in range(num_modelhosts):
        f.write(file_part2.format(i + 1))

    # write file part 3
    f.write(file_part3)
