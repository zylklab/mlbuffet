#!/bin/bash
echo 'Welcome to FractalMLServer-Lite'
echo "This is the installing configuration helper"
echo 'Please, how many modelhosts do you want build'

read num

echo "$num modelhosts will be builded"
cd starting_utils
echo 'creating environment on deploy:'
python3 environment_deploy.py $num
python3 compose_deploy.py $num
echo 'environment on deploy done'
echo 'creating environment on nginx'
python3 nginx-project.py $num
echo 'environment on nginx done'
echo 'growing FractalMLServer-Lite'
pwd
cd ../FractalMLServer-Lite/deploy
exec docker-compose up --build