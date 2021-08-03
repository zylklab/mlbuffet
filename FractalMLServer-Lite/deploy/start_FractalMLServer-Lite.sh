#!/bin/bash
echo 'Welcome to FractalMLServer-Lite'
echo "This is the installing configuration helper"
echo 'How many modelhosts do you want to build'
read num

echo "$num modelhosts will be built"
echo 'Creating deploy environment:'

python3 .starting_utils/environment_deploy.py $num
python3 .starting_utils/compose_deploy.py $num

echo 'Done.'

echo 'Creating Nginx environment'
python3 .starting_utils/nginx-project.py $num

echo 'Done.'


echo 'Building FractalMLServer-Lite'

exec docker-compose up --build
