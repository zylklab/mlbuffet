import sys

"""Script for generating nginx project.conf file based on desired number of Modelhosts"""

file_part1 = """\
upstream fractalmlserver_modelhost_cluster {
"""

# dynamic part
file_part2 = """\
    server 172.24.0.{0}:8000;
"""

file_part3 = """\
}

server {
    listen 80;

    location / {
        proxy_pass http://fractalmlserver_modelhost_cluster;
    }
}
"""

with open('./service-configurations/nginx-config/project.conf', 'w') as f:
    # write file part 1
    f.write(file_part1)

    # write for each Modelhost
    num_modelhosts = int(sys.argv[1])
    for i in range(num_modelhosts):
        f.write(file_part2.format(i + 11))

    # write file part 3
    f.write(file_part3)
