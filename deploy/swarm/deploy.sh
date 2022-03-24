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

echo "Creating deploy environment with $num Modelhost replicas..."

# create network if it is not already created
docker network create -d overlay --subnet 10.0.13.0/24 mlbuffet_overlay

# start deployment and exit on any error
docker stack deploy -c swarm.yaml mlbuffet &&
sleep 5
docker service update mlbuffet_modelhost --replicas=$num
