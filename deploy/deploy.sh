#!/bin/bash

default_value=2  # default number of Modelhosts
echo "Welcome to MLBuffet Swarm deployment helper."

# ask for user input
while true; do
  # read user input
  echo "How many Modelhost replicas do you want to build? [$default_value]"
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
echo "Creating deploy environment with $num Modelhost replicas..."

# Run
exec docker stack deploy -c swarmdeploy.yaml mlbuffet

sleep 5

exec docker service update modelhost --replicas=$num
