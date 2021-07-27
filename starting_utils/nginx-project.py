import sys

n = int(sys.argv[1])

f = open('../FractalMLServer-Lite/deploy/service-configurations/nginx-config/project.conf', 'w')
cab = '\nupstream mlbuffet_kitchen_cluster {\n'
f.write(cab)
for i in range(n):
    server = '    server 172.24.0.' + str(11 + i) + ':8000;\n'
    f.write(server)
f.write('}\n\n')
cluster = 'server {\n' \
          '    listen 80;\n' \
          '\n' \
          '    location / {\n' \
          '        proxy_pass http://mlbuffet_kitchen_cluster;\n' \
          '    }\n' \
          '}'
f.write(cluster)
