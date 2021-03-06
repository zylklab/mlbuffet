![](docs/images/MlBuffet_daemon.png)

# MLBuffet

----

This project is a Machine Learning Model Server based on containers. MLBuffet consists of several modules:

| Module    | Description                                                                                                                                                                                                                                                                                     |
|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Deploy    | Contains the necessary files to install the project, Docker Swarm or Kubernetes.                                                                                                                                                                                                                 |
| Inferrer  | The main REST API. Users or clients may communicate with this API to access the app resources.                                                                                                                                                                                                                     |
| Modelhost | Workers for model deployments and inference. There might be multiple instances of this module, each being aware of all the models stored. |
| Metrics   | Gathers and manages performance metrics from host system and services.                                                                                                                                                                                                                          |
| Storage  | Performs version controlling.                                                                                                                                                                                                                          |

Every MLBuffet module exposes a REST API built on Flask for intercommunication. The Inferrer will handle external
requests, (i.e., uploading a model, performing inference) and will asynchronouslu deliver the requests to the corresponding service.

If you are new to MLBuffet, please take a look at MLBuffet in a nutshell [document](docs/nutshell.md)

----
# Quickstart

## Installation

Images must be built from source with the provided build.sh script in /mlbuffet/deploy/swarm.

For orchestrated deployments (Docker Swarm or Kubernetes), all images must be available for every
node on the cluster, otherwise nodes will not be able to deploy containers.

### Kubernetes

For **Kubernetes** deployments, all the configuration and YAML files are provided in the deploy/kubernetes directory. Custom configurations can be made, but may some functionalities result broken.

Make sure the image names correspond to the images your have built and pushed to your image repository. This can be done easily with the `deploy/kubernetes/autodeploy/kustomization.yaml` file, by replacing image names with their corresponding repo names in `-newName` field.

For example:

 ```yaml
  # Modelhost image name
  - name: IMAGE_MLBUFFET_MODELHOST
    newName: <repo_name>/<modelhost_image_name>:<version>
    newTag: latest
```

Finally, execute the `deploy/kubernetes/autodeploy/deploy.sh` script to automatically deploy MLBuffet on Kubernetes.

#### Helm Chart

Note: Functionality under construction. Please follow the installation guide through yaml files.

For an easier deployment, a Helm Chart is provided. To install it with helm charts, build the chart with a release name:

```commandline
helm install my-release deploy/kubernetes/mlbuffet-chart/
```

**Configure the Chart**

To configure the Chart, edit the values from `deploy/kubernetes/mlbuffet-chart/Values.yaml`, or set via `--set` flag during the installation.

### Docker

MLBuffet can also be deployed as independent Docker containers, however, some functionalities may result non-functioning and Docker Swarm has been deprecated in MLBuffetV2, because Docker Swarm is an abandoned orchestrator at the moment. For Docker Swarm deployments, go back to MLBuffetV1.

## Test the API and welcome

The service for the user or clients to communicate with via HTTP requests is the Inferrer.

To test the API, use `curl http://<INFERRER-IP>:8000/` .

Note: In Kubernetes, use `kubectl get endpoints inferrer -n mlbuffet` to get the Inferrer's endpoint.

The welcome message should be displayed.

```json
{
  "http_status": {
    "code": 200,
    "description": "Greetings from MLBuffet - Inferrer, the Machine Learning model server. For more information, visit /help",
    "name": "OK"
  }
}
```

Or you can try asking for some help:

`curl http://<INFERRER-IP>:8000/help`


## Model Handling

Some pre-trained models are available to be uploaded in the `sample_models/` directory.

Every model must be named by a tag, and the Storage service will take this tag as the reference for that model. When a new model is uploaded to the server, a new Modelhost Pod will be created with the mdoel deployed, as longs as it is part of the supported inference libraries (Tensorflow and ONNX).

For instance, we can have some versions of the iris model as `irisv1.onnx`, `irisv2.onnx` or `iris_final_version.onnx`, but all of them are several versions of the same model, tagged as `iris-model`. Please note that the `tag` associated to a model must be a valid DNS name, otherwise the Modelhost Pod would not be possible to create.

You can upload new versions of a tag model, and they will be stored into the storage module of MLBuffet, only the default versions of each tag will be exposed into the path `modelhost/models/`.

Several methods for model handling can be used from the API:

**Get the list and descriptions of available models**

`curl -X GET http://<INFERRER-IP>:8000/api/v1/models`

```json
{
  "http_status": {
    "code": 200,
    "description": "Tag list provided",
    "name": "OK"
  },
  "model_list": [
    "iris",
    "diabetes"
  ]
}
```

**Get model tag information**

You can read the relevant information of the models associated with a tag:

`curl -X GET http://<INFERRER-IP>:8000/api/v1/models/iris_model/information`

```json
{
  "http_status": {
    "code": 200,
    "description": "OK",
    "name": "OK"
  },
  "tag_list_versions": {
    "1": {
      "description": "Not description provided",
      "file": "iris.onnx",
      "ml_library": "onnx",
      "path": "files/iris_model/1",
      "time": "11:05:06 25/03/2022"
    },
    "2": {
      "description": "second version",
      "file": "iris_v2.onnx",
      "ml_library": "onnx",
      "path": "files/iris_model/2",
      "time": "11:21:23 25/03/2022"
    }
  }
}

```

**Upload a new model**

You can upload your own models to MLBuffet using POST method:

`curl -X POST -F "path=@/path/to/local/model" http://<INFERRER-IP>:8000/api/v1/models/<tag> -F "library_version=<library_name==version>"`

You can also give some information of the version changes:

`curl -X POST -F "path=@/path/to/local/model" -F "model_description=version description of the file" http://<INFERRER-IP>:8000/api/v1/models/<tag> -F "library_version=<library_name==version>"``

When a new version is uploaded, that will be associated as the default model, and a new Modelhost Pod will be deployed for inference.

**Download model**

Any version of a given model tag can be downloaded from the server.
The version to be downloaded from the storage can be specified in three ways:

* `<tag>`
* `<tag>:default`
* `<tag>:<version>`

The first two methods download the file set as default, and the last one downloads the specific version.

`wget http://<INFERRER-IP>:8000/api/v1/models/<tag>/download --content-disposition`

Models can also be downloaded form the browser.

**Delete a model**

Models can be deleted with the DELETE method:

* `<tag>`
* `<tag>:default`
* `<tag>:<version>`

`curl -X DELETE http://<INFERRER-IP>:8000/api/v1/models/<tag>`

**Set model as default**

Any version in the storage can be set as the default version:

`curl -X POST -H "Content-Type: application/json" --data '{"default": <new default version>}'
http://<INFERRER-IP>:8000/api/v1/models/<tag>/default`

## Model Predictions

**Get a prediction!**

Once models have been correctly uploaded, the server is ready for inference. Requests must be done with an input in json format. This will send an HTTP request to the server asking for a prediction on the previously uploaded Iris model:

`curl -X POST -H "Content-Type: application/json" --data '{"values":[2, 5, 1, 4]}' http://<INFERRER-IP>:8000/api/v1/models/iris-model/prediction`

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

You can predict objects with more complex models. For now, the server only is enabled to predict with images and json inputs, but other types are being implemented.

To send images as inputs the following request must be done:

`curl -X GET -F "file=@dog_resized.jpeg" http://<INFERRER-IP>:8000/api/v1/models/dog_model/prediction | jq`

```json
{
  "http_status": {
    "code": 200,
    "description": "Prediction successful",
    "name": "OK"
  },
  "values": [
    [
      8.3947160334219e-09,
      ...
      2.68894262411834e-09
    ]
  ]
}
```

## Train your own models:

**Prepare your trining scripts**

MLBuffet is able to train models and automatically upload them for inference or model management.

There are two ways to perform trainings depending on your installation method and preferred Container Runtime Interface. Both work fundamentally the same way, but the recommended one is the Kubernetes Trainer, as it does not require external configuration and works out of the box:

### MLBuffet Kubernetes Trainer

The MLBuffet Kubernetes Trainer is not a module itself, but an operation performed by Inferrer. Provided the training files through a POST request, the Inferrer will spin up a Pod called `trainer` which will execute the training script sequentally. Then, the Pod will be scanned looking for the name of the output model, provided in the URL resource, and this model will be sent back to the Inferrer to be loaded as a new model.

```
curl -X POST <INFERRER-IP>:8000/api/v1/train/<tag>/<model_name> -F "dataset=@/path/to/dataset.csv" -F "script=@/path/to/train.py" -F "requirements=@/path/to/requirements.txt"
```
Where `<tag>` is the model tag you want to upload to the MLBuffet server, and `<model_name>` is the exact name of the file that will be the result of the traning (or directory, like `model.pb` or `iris.onnx`).

MLBuffet supports training using any Python-based library. You will need 3 files to perform training on a virtualized container environment, which are your custom
`train.py` script, `requirements.txt` with all the libraries and tools to be imported during training, and `dataset.csv` or any other data file which must be read during runtime by the training script to make operations over the dataset and perform the training.

Take into account that these code will be executed inside a containerized environment and the resulting model must be
able to be located by the Trainer container to auto-upload it into the system. The tag associated to the model must be
provided in `<tag>`. The model name must be the same that you sent in the HTTP request `<model_name>`.

### MLBuffet Docker Trainer

For this capability to be available it is necessary to expose your Docker daemon in the Docker host's machine
at port :2376, and security is enforced by TLS by default. This settings might not be changed to --unsecure,
as exposing your docker daemon insecurely is a high risk practice and can lead to security issues.
Your client cert, key and ca-certs must be located at `inferrer/flask_app/utils/client`.

---

Example `curl` request:

```curl -X POST <INFERRER-IP>:8000/api/v1/train/<tag>/<model_name> -F "dataset=@/path/to/dataset.csv" -F "script=@/path/to/train.py" -F "requirements=@/path/to/requirements.txt"```
