This repo contains the work for the DEMO of the FRACTAL project, which will take place at the beggining of October 2021.

The DEMO is initially based on the Model Server developed by Zylk, during the research of this project.

Please, for making commits use always 'develop' branch. Changes will then be merged to 'master' by the repo admin and reviewers.



# Project Description:

## Overview

This Project is a Machine Learning Model Server based on Docker Containers.  Fractal - ML Server has 4 main modules, each being responsible of a task as described in the table below:

|Module Name| Description |      
|-----------|-------------|
|Deploy| This is where the docker-compose.yaml file is and this directory should be used as the deploy directory. |
|Inferrer| Once the services are up and running, the Inferrer is the module to which HTTP calls must be made. Balances calls and loads between Modelhost modules. |
|Modelhost| This service does all the workloads related to model deployment, model inference and model management. Communicates to Inferrer only, so no HTTP calls might me bade to this module except for developing purposes. |
|Metrics| Manages information about performance. Metrics scraped by Prometheus from the rest of the services can be accesed. |


# Quickstart

## Build & Deploy the services.

First make sure that you have Docker-Engine and Docker-Compose installed. Some TCP and UDP ports must be available before deploying:

-TCP 80
-TCP 8001
-TCP 8002
-TCP 9090

Go to the deploy directory and run the following command: `docker-compose up -d`
Docker-Compose will begin building the images of the containers to be created. Once it is done building (usually takes around 3-4 minutes), containers will be created and services will be deployed. Make sure that services are up and running by running `docker ps`. In case any of the services are not available, run `docker logs <container_name>` to see the possible reason.

Once you are over, run `docker-compose down` to remove the containers. `docker-compose down --rm all --remove-orphans` will also remove the images in case you don't need them anymore (they can be rebuilt).

## Service description


## Test the API and welcome.

The module used to communicate with and the one to which the HTTP requests must be made is the Inferrer, with an associated container called inferrer and its 8000 port binded to localhost:8081. HTTP requests can be done through the localhost port or the internal Docker network, but the first method is preferred.

To get welcomed by the API, use `curl http://localhost:8001/`

The welcome message should be displayed.
