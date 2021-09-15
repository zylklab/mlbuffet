# FRACTAL - MLSERVER
----
This repo contains the work for the DEMO of the FRACTAL project, which will take place at the beginning of October 2021.

This project is based on the Model Server developed by Zylk, as part of research for FRACTAL.

Please, always use 'develop' branch to make commits. Changes will then be merged to 'master' branch by the repo admin and reviewers.

# Overview

This project is a Machine Learning Model Server based on Docker containers. Fractal - ML Server consists of 4 main
modules, each of which is in charge of a task as described in the table below:

|Module|Description|
|-----------|-------------|
|Deploy| Contains the necessary files to deploy the project, such as docker-compose.yml.|
|Inferrer| Receives HTTP requests and balances the workload between Modelhost modules.|
|Modelhost| Worker for model deployment, inference and management. It only communicates with Inferrer module, so no HTTP calls should be made to this module except for developing or debugging purposes. There should be multiple instances of this module, each of whom takes over one or more ML models.|
|Metrics| Gathers and manages performance metrics from host system and services.|

# Service description

The Inferrer and Modelhost modules expose REST APIs built on Flask for intercommunication. The Inferrer will handle user requests made to the available models, i.e., uploading a model, asking for a prediction... And will send them as
jobs to the Modelhost module, which will perform them in the background asynchronously.

When a prediction is requested, the Modelhost will first check if the requested model is already deployed. If it is, then it will pass the HTTP request as an input to the ONNX session running in the background, and the answer is sent back to the user through Inferrer.

----
# Quickstart

## Build & Deploy the services

First make sure that you have Docker-Engine and Docker-Compose installed. Take into account that some older versions of docker-compose may not be supported. Up to now, the server has been tested and proven to work properly on versions 1.28.5 and 1.29.2, for older or other versions, upgrade to a newer version (or test your luck). To install docker-compose:

`sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`

`sudo chmod +x /usr/local/bin/docker-compose`

`sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose`

Check you docker-compose version:

`docker-compose --version`

TCP ports 80, 8001, 8002 and 9091 must be available before deploying.


### Recommended build

Images must be built from source with docker-compose build. If you already have your images built, then you can already proceed with the Swarm Deployment (or other orchestrator).

The images in this branch are designed to be orchestrated by Swarm. Other orchestrators have not been tested yet, but the ports exposed are the same as with docker-compose.

Some environment variables must be passed to each container for the processes to correctly perform. Most of these environment variables are then used by the Python programs to communicate between containers and establish port binding with the docker daemon. The required environment variables for each container are:

```
inferrer:
FLASK_PORT: '8443'
INFERRER_API_BIND_TO_PORT: '8002'
LOAD_BALANCER_PORT: '80'
MODELHOST_API_BIND_TO_PORT: '8004'
NUMBER_MODELHOST_NODES: '2'
PROMETHEUS_PORT: '9090'
INFERRER_ENDPOINT: 'fractalml_inferrer'
MODELHOST_ENDPOINT: 'fractalml_modelhost'
  ports: 8002:8000

modelhost:
FLASK_PORT: '8443'
INFERRER_API_BIND_TO_PORT: '8002'
LOAD_BALANCER_PORT: '80'
MODELHOST_API_BIND_TO_PORT: '8004'
NUMBER_MODELHOST_NODES: '2'
PROMETHEUS_PORT: '9090'
  ports: 8004:8000"

nginx:
  ports: 80:80

prometheus:
  ports: 9091:9090
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


## Test the inferrer API and rebalance queries to modelhost nodes

To test the inferrer API, there are some methods with the '_test_' prefix that are used to show the comunication between the inferrer, the load balancer and the modelhost nodes.

The following query can be used to call the inferrer node
`curl -X POST -H "Content-Type: application/json" --data '{"data": ["ONE", "TWO", "THREE", "FOUR"]}'  http://localhost:8002/api/test/sendtomodelhost`

Then, run `docker logs inferrer` to confirm that the modelhost APIs responded correctly and the load was correctly balanced between nodes (each node has a unique identifier and it can be seen which node attended each request).

The communication flow includes:
- The HTTP request is sent to the inferrer API REST <INFERRER_IP:8002>
- The API method uses `modelhost_talker` class to make the queries to the modelhost nodes.
This is done by calling the LOAD BALANCER, which is in charge of redirecting the queries to the modelhost nodes.
- In the modelhost, the corresponding method responds with a message, including an unique ID for each of the modelhost nodes, which allows to distinguish which modelhost node has executed the query.
- Results are gatherer by the `modelhost_talker` and presented on the inferrer API.


## Model Handling

Some pre-trained models are already uploaded and can be updated manually through the `modelhost/models/` directory. However, new model uploading is supported by Fractal - ML Server. All Modelhost servers can access the directory of models, so they share a pool of common models.

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


## Model Predictions

**Get a prediction!**

Once models have been correctly uploaded and described, the server is ready for inference. Requests must be done with an input in json format. This command will send an HTTP request to the server asking for a prediction on a given flower:

`curl -X GET -H "Content-Type: application/json" --data '{"values":[2, 5, 1, 4]}' http://localhost:8002/api/v1/models/iris.onnx/prediction`



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

You can predict objects with more complex models. For now, the server only is enabled to predict with images, but other types could be allowed in the future.
For that predictions, the command to send the HTTP request is the following:

`curl -X GET -F "file=@dog_resized.jpeg" http://localhost:8002/api/v1/models/dog_model.onnx/prediction | jq`

```json
{
  "http_status": {
    "code":200,
    "description":"Prediction successful",
    "name":"OK"},
  "values":[
    [8.3947160334219e-09,
       ...
       ...
       ...
     2.68894262411834e-09
    ]
  ]
}
```
