import os
from os import getcwd, path
from pathlib import Path
import time
import json
from flask import Flask, request, Response
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized
from werkzeug.utils import secure_filename

from utils import metric_manager, index
from utils.container_logger import Logger
from utils.inferer_pojos import HttpJsonResponse, Prediction, ModelInformation, ModelList

from modelhost_utils.modelhost_manager import ModelhostClientManager
from modelhost_utils.modelhost_cache import modelhost_cache

# Constants referring to the API url, folders, and authentication tokens.
API_BASE_URL: str = '/api/v1/'
ALLOWED_EXTENSIONS = ['onnx']
MODEL_FOLDER = path.join(getcwd(), '/.cache/')
auth_token = 'password'  # TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(Unauthorized())

# Logger initialization
logger = Logger('inferrer').get_logger('inferrer')
logger.info('Starting FRACTAL - ML SERVER - INFERRER API...')

# Server initialization
server = Flask(__name__)
logger.info('... FRACTAL - ML SERVER - INFERRER API succesfully started')

# Authorization verification
@auth.verify_token
def verify_token(token):
    return token == auth_token

# All the methods supported by the API are described below
#
#
#

# Welcome method
@server.route('/', methods=['GET'])
def hello_world():
    return HttpJsonResponse(200,
                            http_status_description='Greetings from Fractal - ML Server - Inferrer, the Machine '
                                                    'Learning model server. '
                                                    'For more information, visit /help').json()


# Help method
@server.route('/help', methods=['GET'])
def show_help():
    return index.header + index.help + '\n'


# /api/test/ can be used as a prefix method for other methods being tested at the moment
@server.route('/api/test', methods=['GET'])
def get_test():
    metric_manager.increment_test_counter()

    return HttpJsonResponse(200).json()


# Test method to check if the load balancer is working properly.
@server.route('/api/test/sendtomodelhost/', methods=['GET'])
def _test_send_to_modelhost():
    modelhost = ModelhostClientManager()
    data_array = request.json['data']
    print(data_array)
    predictions = modelhost._test_get_modelhost_predictions(data_array)
    for p in predictions:
        print("API Response: " + p)

    print("\n")
    return "Received  \n"


# This endpoint is used by Prometheus and metrics are exposed here.
@server.route('/metrics', methods=['GET', 'POST'])
def get_metrics():
    # force refresh system metrics
    metric_manager.compute_system_metrics()
    metrics = metric_manager.get_metrics()
    return Response(metrics, mimetype="text/plain")


@server.errorhandler(HTTPException)
def handle_exception(exception):
    """Return JSON instead of HTML for HTTP errors."""

    return HttpJsonResponse(
        http_status_code=exception.code,
        http_status_name=exception.name,
        http_status_description=exception.description
    ).json()


@server.before_request
def log_call():
    if request.path == '/metrics':  # don't log prometheus' method
        pass
    else:
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        logger.info(f'[{client_ip}] HTTP {request.method} call to {request.path}')


@server.after_request
def log_response(response):
    if request.path == '/metrics':  # don't log prometheus' method
        pass
    elif request.path == '/help':  # don't display the whole help
        logger.info('Help displayed')
    elif request.path == '/api/v1/models':
        logger.info('Models list displayed')
    elif request.path == '/api/v1/models/information':
        logger.info('Models & description list displayed')
    elif response:
        logger.info(response.get_json())

    return response


# TODO this should go into utils folder
def get_file_extension(file_name):
    return Path(file_name).suffix[1:].lower()


# Prediction method. Given a json with input data, sends it to modelhost for predictions.
@server.route(path.join(API_BASE_URL, 'models/<model>/prediction'), methods=['GET'])
def getPrediction(model):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model)

    # Check that there is a json provided
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {values:list}').json()

    #Check that file extension is .onnx
    if get_file_extension(model_name) != 'onnx':
        return HttpJsonResponse(
            409,
            http_status_description=f'{model_name} is not in onnx format. '
                                    f'Please convert it first visiting '
                                    f'POST {path.join(API_BASE_URL, "models", model_name, "to-onnx")}'
        ).json()

    # Check input values for prediction have been provided
    if 'values' not in request.json:
        return HttpJsonResponse(422, http_status_description='No test observation provided (values:[...])').json()
    t0 = time.time()
    new_observation = request.json["values"]

    # Check that the input is a values list
    if not isinstance(new_observation, list):
        return HttpJsonResponse(422, http_status_description='New observation is not a list enclosed by'
                                                             ' squared brackets').json()

    # Check that the same prediction has already been made in the cache data (Database can be included here)
    hash = modelhost_cache.get_hash(model=model, input=new_observation)
    check = modelhost_cache.check_hash(hash=hash)

    # If the prediction is cached, return the already stored value
    if check == "Key exists":
        pred = modelhost_cache.get_prediction(hash=hash)
        t1 = time.time()
        tiempo = t1 - t0
        logger.info("Time reading in cache: " + str(tiempo))
        # return {"Mode": "read from cache", "Value": pred}
        return Prediction(200, http_status_description='Prediction successful', values=pred).json()

    # For non cached predictions, send the request to modelhost
    else:
        modelhost = ModelhostClientManager()
        pred = modelhost.get_modelhost_predictions(model, new_observation)
        predi_json = json.loads(pred[0])
        prediction = predi_json["values"]

        estructure = modelhost_cache.data_structure(hash=hash, model=model, input=new_observation,
                                                    prediction=prediction)
        modelhost_cache.put_prediction(new_data=estructure)
        t1 = time.time()
        tiempo = t1 - t0

        logger.info("Time doing prediction: " + str(tiempo))

        return Prediction(200, http_status_description='Prediction successful', values=prediction).json()

# Display a list of the available models
@server.route(path.join(API_BASE_URL, 'models'), methods=['GET'])
def showModels():
    t0 = time.time()
    metric_manager.increment_model_counter()
    modelhost = ModelhostClientManager()
    models = modelhost.get_modelhost_models()[0]
    models = json.loads(models)

    descriptions = [file for file in models["description"]]

    t1 = time.time()
    tiempo = t1 - t0
    logger.info("Time getting model_list: " + str(tiempo))
    return ModelList(200, model_list=descriptions).json()


# Display all the information related to every available model
@server.route(path.join(API_BASE_URL, 'models/information'), methods=['GET'])
def showModelsDescription():
    t0 = time.time()
    metric_manager.increment_model_counter()
    modelhost = ModelhostClientManager()
    models = modelhost.get_modelhost_models_description()[0]
    models = json.loads(models)
    descriptions = [file for file in models["description"]]

    t1 = time.time()
    tiempo = t1 - t0
    logger.info("Time getting model_list_description: " + str(tiempo))
    return ModelList(200, model_list=descriptions).json()


# Update the list of available models on every modelhost node.
@server.route(path.join(API_BASE_URL, 'models/update'), methods=['POST'])
def updateModels():
    t0 = time.time()
    metric_manager.increment_model_counter()
    modelhost = ModelhostClientManager()
    # The update_modelhost_models() method must be called everytime a change has occured on the model list
    modelhost.update_modelhost_models()

    t1 = time.time()
    tiempo = t1 - t0
    logger.info("Time getting model_list_description: " + str(tiempo))
    return HttpJsonResponse(200, http_status_description=f'Models updated!').json()


# This method is responsible of model handling. Performs operations on models and manages models in the server.
@server.route(path.join(API_BASE_URL, 'models/<model>'), methods=['GET', 'PUT', 'POST', 'DELETE'])
def modelHandling(model):
    # For GET requests, display the model information
    if request.method == 'GET':
        t0 = time.time()
        metric_manager.increment_model_counter()
        model_name = secure_filename(model)

        # If ONNX model, then get model session
        if get_file_extension(model_name) == 'onnx':
            modelhost = ModelhostClientManager()
            pred = modelhost.get_modelhost_info(model_name)
            model_info = json.loads(pred[0])["description"]
            num_inputs = model_info["num_imputs"]
            inputs_type = model_info["inputs_type"]
            outputs = model_info["outputs"]
            description = model_info["description"]
            model_type = model_info["model_type"]
            t1 = time.time()
            tiempo = t1 - t0
            logger.info("Time getting info: " + str(tiempo))
            return ModelInformation(200, http_status_description='Model description', num_inputs=num_inputs,
                                    inputs_type=inputs_type, outputs=outputs, description=description,
                                    model_type=model_type).json()
        else:
            return HttpJsonResponse(
                409,
                http_status_description=f'{model_name} is not in onnx format. '
                                        f'Please convert it and re-upload to provide information '
            ).json()

    # For PUT requests, upload the given model file to the modelhost server
    if request.method == 'PUT':
        t0 = time.time()
        metric_manager.increment_test_counter()

        model = secure_filename(model)
        # Check a file path has been provided
        if 'path' not in request.files:
            return HttpJsonResponse(422, http_status_description='No path specified').json()

        # Get model file from the given path
        modelpath = request.files['path']

        # Check that the extension is allowed (.onnx supported)
        if get_file_extension(model) not in ALLOWED_EXTENSIONS:
            return HttpJsonResponse(415, http_status_description=f'File extension not allowed. '
                                                                 f'Please use one of these: {ALLOWED_EXTENSIONS}').json()

        # Save the model in cache until the upload is complete
        modelpath.save(path.join(MODEL_FOLDER, model))

        # Send the model as HTTP post request to a modelhost node
        modelhost = ModelhostClientManager()
        modelhost.post_modelhost_upload_model(model, str(path.join(MODEL_FOLDER, model)))

        # Update the model list for every modelhost node
        modelhost.update_modelhost_models()

        # Delete the model from Inferrer cache
        os.remove(path.join(MODEL_FOLDER, model))
        t1 = time.time()
        tiempo = t1 - t0
        logger.info("Time uploading model: " + str(tiempo))
        return HttpJsonResponse(201, http_status_description=f'{model} uploaded!').json()


    # For POST requests, update the information on a given model
    if request.method == 'POST':
        t0 = time.time()
        metric_manager.increment_model_counter()
        model_name = secure_filename(model)

        # Check that any json data has been provided
        if not request.json:
            return HttpJsonResponse(422, http_status_description='No json data provided {model_description:string}').json()

        # Check that model_description has been provided
        if 'model_description' not in request.json:
            return HttpJsonResponse(422, http_status_description='No model_description provided').json()
        description = request.json["model_description"]

        # Check that model_description is a string
        if not isinstance(description, str):
            return HttpJsonResponse(422, http_status_description='model_description must be a string').json()

        modelhost = ModelhostClientManager()

        try:
            modelhost.post_modelhost_info(model_name, description)
            modelhost.update_modelhost_models()

        except Exception as error:
            return HttpJsonResponse(500, http_status_description=str(error)).json()

        t1 = time.time()
        tiempo = t1 - t0
        logger.info("Time getting info: " + str(tiempo))

        return HttpJsonResponse(200, http_status_description=f'Model description updated! Visit '
                                                             f'GET {path.join(API_BASE_URL, "models/", model_name, "/information")} '
                                                             f'to check available information about the current model').json()


    # For DELETE requests, delete a given model
    if request.method == 'DELETE':
        t0 = time.time()
        metric_manager.increment_test_counter()

        model_name = secure_filename(model)

        # Send the model as HTTP delete request
        modelhost = ModelhostClientManager()
        modelhost.delete_modelhost_delete_model(model_name)

        #Update every modelhost node's model list
        modelhost.update_modelhost_models()
        t1 = time.time()
        tiempo = t1 - t0
        logger.info("Time deleting model: " + str(tiempo))
        return HttpJsonResponse(200, http_status_description=f'{model} deleted!').json()

if __name__ == '__main__':
    server.run()
