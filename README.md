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


# Service description

The Inferrer and Modelhost modules expose REST APIs built on Flask for inter-communication. The Modelhost API will handle the user requests from the available resources, i.e. uploading a model, asking for a prediction... and will send them as jobs to the Inferrer module who will do the workloads in the background in an asynchronous way.

When a prediction is requested, the Modelhost will first check if the requested model is already deployed. If it is, then it will pass the http request as an input to the ONNX session running in the background, and the answer is sent back to the user through Inferrer.

# Quickstart

## Build & Deploy the services.

First make sure that you have Docker-Engine and Docker-Compose installed. Some TCP and UDP ports must be available before deploying:

-TCP 80

-TCP 8001

-TCP 8002

-TCP 9090

Then, execute the file `start_FractalMLServer-Lite.sh` (if you cannot execute that file, change the permissions of the file). The installing file will ask how many hodelhosts nodes you want to build, and then, it will build the server.

If you do not want to execute the file `start_FractalMLServer-Lite`, go to the deploy directory and run the following command: `docker-compose up -d`
Docker-Compose will begin building the images of the containers to be created. Once it is done building (usually takes around 3-4 minutes), containers will be created and services will be deployed. Make sure that services are up and running by running `docker ps`. In case any of the services are not available, run `docker logs <container_name>` to see the possible reason.

Once you are over, run `docker-compose down` to remove the containers. `docker-compose down --rm all --remove-orphans` will also remove the images in case you don't need them anymore (they can be rebuilt).





## Test the API and welcome.

The module used to communicate with and the one to which the HTTP requests must be made is the Inferrer, with an associated container called inferrer and its 8000 port binded to localhost:8081. HTTP requests can be done through the localhost port or the internal Docker network, but the first method is preferred.

To get welcomed by the API, use `curl http://localhost:8001/`

The welcome message should be displayed.

## Test the inferrer API and rebalance queries to modelhost nodes.

To test the inferrer API, there are some methods with the '_test_' prefix that are used to show the comunication between the inferrer, the load balancer and the modelhost nodes.

The following query can be used to call inferrer node
`curl -X GET -H "Content-Type: application/json" --data '{"data": ["ONE", "TWO", "THREE", "FOUR"]}'  http://172.24.0.2:8000/api/test/sendtomodelhost/`

The communication flow includes:
- the query HTTP query is send to the inferrer API REST <INFERRER_IP:8000>
- the API method uses ModelHostClientManager class to make the queries to the modelhost nodes.
This is done by calling the LOAD BALANCER, which is in charge of redirecting the queries to the modelhost nodes.
- in te modelhost method responds with a ping message, incluiding an unique ID for each of the modelhost nodes, which allows to distinguish which modelhost node has executed the query.
- results are gatherer by the ModelHostClientManager and presented on the inferrer API.

To add or remove modelhost nodes to the architecture, the following files have to be updated:
- on the deploy module, add the new endpoint properties to the `.env` file, on the modelhost sectioon
     `MODELHOST_N_IP=<NODE_N_IP>` and
      `MODELHOST_N_API_BIND_TO_PORT=<NODE_N_PORT>`
- then on the deploy module, add to the `docker-compose` the new service instance:
         ```docker
           modelhost_N:
            container_name: modelhost_N
            restart: always
            build: ../modelhost/flask_app
            ports:
            - ${MODELHOST_N_API_BIND_TO_PORT}:8000
            networks:
              fractalmlserver_network:
                ipv4_address: ${MODELHOST_N_IP}
            volumes:
              - ../modelhost/logs:/home/logs
              - .env:/home/.env```
- finally, on the deploy module, add update the nginx configuration on `service-configurations/nginx-config/project.conf`:
  add the line `server MODELHOST_N_IP:8000;` for example  `server 172.24.0.5:8000;`



## Model Handling

Some pre-trained models are already uploaded and can be updated manually through the inferrer/models/ directory. However, model handling is supported by Fractal - ML Server. Several methods for model handling can be used from the API:

**Get model information**

`curl -X GET http://localhost:8001/api/v1/models/iris.onnx/information`


**Update model information**

The information you got is in Spanish. You can update a model's description with the POST method:

`curl -X POST -H "Content-Type: application/json" --data '{"model_description":"This model classifies a 4 element array input between different species of Iris flowers."}' http://localhost:8001/api/v1/updateinfo/iris.onnx`

**Upload a new model**

You can upload your own .onnx models to the server by using the /upload<model_name> method.

`curl -X POST -F "path=@/path/to/directory/<model_name>.onnx" http://localhost:8002/api/v1/models/upload_<model_name>.onnx`

**Delete a model**

To be done

**Deploy a new model**

## Model Predictions
**Get a prediction!**

Once models have been correctly uploaded, deployed and described, the server is ready for inference. Requests must be done with an input in json format.

`curl -X GET -H "Content-Type: application/json" --data '{"values":[2, 5, 1, 5]}' http://localhost:8001/api/v1/models/iris.onnx/prediction`

This command will send an HTTP request to the server asking for a prediction on a given flower.
