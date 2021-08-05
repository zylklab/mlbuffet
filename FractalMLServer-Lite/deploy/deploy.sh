#!/bin/bash

default_value=2  # default number of Modelhosts
echo "Welcome to FractalMLServer-Lite installing helper."

# ask for user input
while true; do
  # read user input
  echo "How many Modelhosts do you want to build? [$default_value]"
  read -r num

  # if empty means default value
  if [ -z "$num" ] ; then
    num=$default_value
  fi

  # if the input is a number, then continue execution, otherwise ask for it again
  re='^[0-9]+$'
  if ! [[ $num =~ $re ]] ; then
    echo "Error: input is not a number"
  else
    break
  fi
done

# start deploying and exit on any error
echo "Creating deploy environment with $num Modelhosts..."
python3 .starting_utils/environment_deploy.py "$num" || { exit 1; }
python3 .starting_utils/compose_deploy.py "$num" || { exit 1; }
echo "Done."

echo "Creating Nginx environment..."
python3 .starting_utils/nginx-project.py "$num" || { exit 1; }
echo "Done."


echo "Building FractalMLServer-Lite..."

# Run in detached mode if the user prompts -d as parameter
if [ $1 == "-d" ]
then
  exec docker-compose up --build -d
else
  exec docker-compose up --build
fi
