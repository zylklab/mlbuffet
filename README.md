This repo contains the work for the DEMO of the FRACTAL project, which will take place at the beginning of October 2021.

This project is based on the Model Server developed by Zylk, as part of research for FRACTAL.

Please, always use 'develop' branch to make commits. Changes will then be merged to 'master' branch by the repo admin
and reviewers.

# Overview

This project is a Machine Learning Model Server based on Docker containers. Fractal - ML Server consists of 4 main
modules, each of which is in charge of a task as described in the table below:

|Module|Description|
|-----------|-------------|
|Deploy| Contains the necessary files to deploy the project, such as docker-compose.yml.|
|Inferrer| Receives HTTP requests and balances the workload between Modelhost modules.|
|Modelhost| Worker for model deployment, inference and management. It only communicates with Inferrer module, so no HTTP calls should be made to this module except for developing purposes. There should be multiple instances of this module, each of whom takes over one or more ML models.|
|Metrics| Gathers and manages performance metrics from host system and services.|

# Service description

The Inferrer and Modelhost modules expose REST APIs built on Flask for intercommunication. The Inferrer will handle user
requests made to the available models, i.e., uploading a model, asking for a prediction... and will send them as
jobs to the Modelhost module, which will perform them in the background asynchronously.

When a prediction is requested, the Modelhost will first check if the requested model is already deployed. If it is, then it will pass the http request as an input to the ONNX session running in the background, and the answer is sent back to the user through Inferrer.

# Quickstart

## Build & Deploy the services

First make sure that you have Docker-Engine and Docker-Compose installed. Some TCP and UDP ports must be available before deploying:

-TCP 80

-TCP 8001

-TCP 8002

-TCP 9090

Go to the deploy directory and run the following command: `docker-compose up -d`
Docker-Compose will begin building the images of the containers to be created. Once it is done building (usually takes around 3-4 minutes), containers will be created and services will be deployed. Make sure that services are up and running by running `docker ps`. In case any of the services are not available, run `docker logs <container_name>` to see the possible reason.

Once you are over, run `docker-compose down` to remove the containers. `docker-compose down --rm all --remove-orphans` will also remove the images in case you don't need them anymore (they can be rebuilt).

### Recommended build

You can deploy the services like described above, however, you may want to add more modelhosts to the service cluster. In case you need to increase the number of modelhosts, a script that you can execute with `$ ./deploy.sh` has been included in the deploy directory. You can execute this script with the `-d` flag, so `./deploy.sh -d` will execute the processes in detached mode (similarly to docker-compose up -d).

Upon execution, the script will prompt the user how many modelhost nodes he needs, and then will format the docker-compose.yaml and nginx configuration accordingly. Then, it will execute all the commands to build the images and get the containers up and running, so no more interaction from the user is required.

This is the recommended way of building the services because the project is thought to have an increasing number of nodes. Take into account that with this boot method, the server will take control of the terminal session, so you will need to open a new one to work.

```
prometheus-fractal | level=info ts=2021-07-27T12:29:56.880Z caller=main.go:775 msg="Server is ready to receive web requests."
inferrer       | 2021-07-27 12:29:57,489 — inferrer — INFO — Starting FRACTAL - ML SERVER - INFERRER API...
inferrer       | 2021-07-27 12:29:57,491 — inferrer — INFO — ... FRACTAL - ML SERVER - INFERRER API succesfully started
modelhost_1    | 2021-07-27 12:29:57,499 — modelhost-logger — INFO — Starting Flask API...
modelhost_1    | 2021-07-27 12:29:57,501 — modelhost-logger — INFO — ... Flask API succesfully started
```

## Test the API and welcome

The module for the user to communicate with via HTTP requests is the Inferrer. Its associated container is called inferrer and it has the port 8000 binded to localhost:8002. The IP for HTTP requests can be localhost or the internal Docker network, but the former is preferred.

To get welcomed by the API, use `curl http://localhost:8002/`

The welcome message should be displayed.

```json
{
  "http_status": {
    "code": 200,
    "description": "Greetings from Fractal - ML Server - Inferrer, the Machine Learning model server. For more information, visit /help",
    "name": "OK"
  }
}
```

Or you can try asking for some help:

`curl http://localhost:8002/help`

```
    #############################
    #### FRACTAL - ML SERVER ####
    #############################

FRACTAL - ML SERVER is a model server developed by Zylk.net
```

## Test the inferrer API and rebalance queries to modelhost nodes

To test the inferrer API, there are some methods with the '_test_' prefix that are used to show the comunication between the inferrer, the load balancer and the modelhost nodes.

The following query can be used to call the inferrer node
`curl -X GET -H "Content-Type: application/json" --data '{"data": ["ONE", "TWO", "THREE", "FOUR"]}'  http://172.24.0.2:8000/api/test/sendtomodelhost`

Then, do `docker logs inferrer` to confirm that the modelhost APIs responded correctly and the load was correctly balanced between nodes (each node has a unique identifier and it can be seen which node attended each request).

The communication flow includes:
- The HTTP request is sent to the inferrer API REST <INFERRER_IP:8000>
- The API method uses ModelHostClientManager class to make the queries to the modelhost nodes.
This is done by calling the LOAD BALANCER, which is in charge of redirecting the queries to the modelhost nodes.
- In the modelhost, the corresponding method responds with a ping message, incluiding an unique ID for each of the modelhost nodes, which allows to distinguish which modelhost node has executed the query.
- Results are gatherer by the ModelHostClientManager and presented on the inferrer API.

To manually add or remove modelhost nodes to the architecture, the following files have to be updated:
- on the deploy module, add the new endpoint properties to the `.env` file, on the modelhost sectioon
     `MODELHOST_N_IP=<NODE_N_IP>` and
      `MODELHOST_N_API_BIND_TO_PORT=<NODE_N_PORT>`
- then on the deploy module, add to the `docker-compose` the new service instance:

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
              - .env:/home/.env
              - ../modelhost/flask_app/models:/usr/src/flask_app/models

- finally, on the deploy module, add update the nginx configuration on `service-configurations/nginx-config/project.conf`:
  add the line `server MODELHOST_N_IP:8000;` for example  `server 172.24.0.5:8000;`

However, these steps must only be followed if you skipped the Recommended build section or want to add additional nodes once the services have already been deployed.

## Model Handling

Some pre-trained models are already uploaded and can be updated manually through the modelhost/models/ directory. However, new model uploading is supported by Fractal - ML Server. All Modelhost servers can access the directory of models, so they share a pool of common models.

Several methods for model handling can be used from the API:

**Get the list of available models**

`curl -X GET http://localhost:8002/api/v1/models`

```json
{
  "http_status": {
    "code": 200,
    "description": "OK",
    "name": "OK"
  },
  "model_list": [
    "diabetes.onnx",
    "iris.onnx"
  ]
}
```

This method however, only displays a list of models, but a description of the models can be added in case the number of models get larger. The complete available information about the models can be accessed through `curl -X GET http://172.24.0.1:8002/api/v1/models/information`

```json
{
  "http_status": {
    "code": 200,
    "description": "OK",
    "name": "OK"
  },
  "model_list": [
    {
      "description": "",
      "model": "diabetes.onnx"
    },
    {
      "description": "Clasificación de especies de flores de Iris. Se clasifican en setosa, versicolor o virginica dependiendo de las medidas de sépalo y pétalo",
      "model": "iris.onnx"
    }
  ]
}
```

**Get model information**

The specific information of any model can also be requested with GET /api/v1/models/<model_name> method:

`curl -X GET http://localhost:8002/api/v1/models/iris.onnx`


**Update model information**

A model may have incomplete information, wrong information or no information at all. You can update the description of a model using POST method:

`curl -X POST -H "Content-Type: application/json" --data '{"model_description":"This model classifies a 4 element array input between different species of Iris flowers."}' http://localhost:8002/api/v1/models/iris.onnx`

**Upload a new model**

You can upload your own ONNX models to the server using PUT method:

`curl -X PUT -F "path=@/path/to/local/model" http://localhost:8002/api/v1/models/<model_name>`

**Delete a model**

Delete models you do not need anymore with DELETE method.

`curl -X DELETE http://localhost:8002/api/v1/models/<model_name>`

**Deploy a new model**

To be done.


## Model Predictions

**Get a prediction!**

Once models have been correctly uploaded, deployed and described, the server is ready for inference. Requests must be done with an input in json format.

`curl -X GET -H "Content-Type: application/json" --data '{"values":[2, 5, 1, 4]}' http://localhost:8002/api/v1/models/iris.onnx/prediction`

This command will send an HTTP request to the server asking for a prediction on a given flower.

```json
{
  "http_status": {
    "code": 200,
    "description": "Prediction successful",
    "name": "OK"
  },
  "values": [
    1
  ]
}

```

The field "values":[1] is the prediction for the input flower. You are now ready to upload your own models and make predictions!
