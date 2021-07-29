#!/bin/bash
echo 'Welcome to FractalMLServer-Lite'
echo "This is the installing configuration helper"
echo 'How many modelhosts do you want to build'
read num

echo "$num modelhosts will be built"
cd starting_utils
echo 'Creating deploy environment:'
python3 environment_deploy.py $num
python3 compose_deploy.py $num

echo 'Creating Nginx environment'
python3 nginx-project.py $num

echo 'Building FractalMLServer-Lite'
cd ../FractalMLServer-Lite/deploy
exec docker-compose up --build
