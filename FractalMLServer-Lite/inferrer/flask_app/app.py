import os
from os import path
from pathlib import Path

import gevent
import requests
from flask import Flask, request, Response
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized
from werkzeug.utils import secure_filename

from modelhost_utils import modelhost_cache
from utils import metric_manager, stopwatch
from utils.container_logger import Logger
from utils.inferer_pojos import HttpJsonResponse

# Path constants
API_BASE_URL = '/api/v1/'
ALLOWED_EXTENSIONS = ['onnx']

# Authorization constants
auth_token = 'password'  # TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(Unauthorized())

# Request constants
LOAD_BALANCER_ENDPOINT = os.getenv('LOAD_BALANCER_ENDPOINT')
URI_SCHEME = 'http://'
try:
    NUMBER_OF_MODELHOSTS = int(os.getenv('NUMBER_MODELHOST_NODES'))
except TypeError:
    pass

# Logger initialization
logger = Logger('inferrer').get_logger('inferrer')
logger.info('Starting FRACTAL - ML SERVER - INFERRER API...')
my_stopwatch = stopwatch.Stopwatch(logger.info)

# Server initialization
server = Flask(__name__)
logger.info('... FRACTAL - ML SERVER - INFERRER API succesfully started')


# TODO: comments
# TODO: url method adhoc? no
# TODO: utils script to separate calling
# TODO: not os.getenv, constants
# TODO: endpoint information models... :/
# TODO: loadbalancer endpoint no --> ip y url method no --> endpoint
# TODO: hueco para federated learning
# TODO: reorder methods

# Authorization verification
@auth.verify_token
def verify_token(token):
    return token == auth_token


# All endpoints supported by the API are defined below


# Welcome endpoint
@server.route('/', methods=['GET'])
def hello_world():
    return HttpJsonResponse(
        200,
        http_status_description='Greetings from Fractal - ML Server - Inferrer, the Machine Learning model server. '
                                'For more information, visit /help'
    ).json()


# Help endpoint
@server.route('/help', methods=['GET'])
def show_help():
    return '''
        #############################
        #### FRACTAL - ML SERVER ####
        #############################

FRACTAL - ML SERVER is a model server developed by Zylk.net.
For more information on the FRACTAL Project and the Fractal ML Server, go to https://github.com/zylklab/fractal/.

'''


# Test endpoint
@server.route('/api/test', methods=['GET'])
def get_test():
    metric_manager.increment_test_counter()

    return HttpJsonResponse(200).json()


# Test endpoint to check if the load balancer is working properly
@server.route('/api/test/sendtomodelhost', methods=['POST'])
def _test_send_to_modelhost():
    # Check that json data was provided
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {data:list}').json()

    # Check that test data was provided
    if 'data' not in request.json:
        return HttpJsonResponse(422, http_status_description='No test data provided (data:[...])').json()

    # Get test data
    data_array = request.json['data']

    # Validate test data
    if not isinstance(data_array, list):
        return HttpJsonResponse(
            422,
            http_status_description='Test data is not a list enclosed by squared brackets').json()

    url_method = '/api/test/frominferrer/get'
    url = URI_SCHEME + LOAD_BALANCER_ENDPOINT + url_method

    jobs = [gevent.spawn(requests.get, path.join(url, data_point)) for data_point in data_array]
    gevent.wait(jobs)

    # Print modelhosts responses and check if all HTTP codes are 2XX
    all_responses_200 = True
    for job in jobs:
        modelhost_response = job.value.json()

        if 200 > modelhost_response['http_status']['code'] > 299:
            all_responses_200 = False

        print(modelhost_response)  # TODO: prettier?

    if all_responses_200:
        return HttpJsonResponse(200).json()
    return HttpJsonResponse(500, http_status_description='One or more modelhosts returned non 2XX HTTP code')


# This endpoint is used by Prometheus and metrics are exposed here
@server.route('/metrics', methods=['GET', 'POST'])  # TODO: needs to be authorized
def get_metrics():
    # force refresh system metrics
    metric_manager.compute_system_metrics()
    metrics = metric_manager.get_metrics()
    return Response(metrics, mimetype='text/plain')


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

    my_stopwatch.start()


@server.after_request
def log_response(response):
    if request.path == '/metrics':  # don't log prometheus' method
        return response
    elif request.path == '/help':  # don't display the whole help
        logger.info('Help displayed')
    elif request.path == '/api/v1/models':
        logger.info('Models listed')
    elif request.path == '/api/v1/models/information':
        logger.info('Models and descriptions listed')
    elif response and response.get_json():
        logger.info(response.get_json())

    my_stopwatch.stop()

    return response


# TODO this should go into utils folder
def get_file_extension(file_name):
    return Path(file_name).suffix[1:].lower()


# Prediction method. Given a json with input data, sends it to modelhost for predictions.
@server.route(path.join(API_BASE_URL, 'models/<model_name>/prediction'), methods=['GET'])
def get_prediction(model_name):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model_name)

    # Check that json data was provided
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {values:list}').json()

    # Check that file extension is .onnx
    if get_file_extension(model_name) != 'onnx':
        return HttpJsonResponse(409, http_status_description=f'{model_name} is not in onnx format.').json()

    # Check that input values for prediction have been provided
    if 'values' not in request.json:
        return HttpJsonResponse(422, http_status_description='No test observation provided (values:[...])').json()

    new_observation = request.json['values']

    # Check that the input is a list
    if not isinstance(new_observation, list):
        return HttpJsonResponse(
            422,
            http_status_description='New observation is not a list enclosed by squared brackets').json()

    # Check if the same prediction has already been made before
    prediction_hash = modelhost_cache.get_hash(model_name=model_name, inputs=new_observation)
    cached_prediction = modelhost_cache.get_prediction(hash_code=prediction_hash)

    # If the prediction exists in cache, return it
    if cached_prediction is not None:
        return cached_prediction

    url_method = f'/modelhost/models/{model_name}/prediction'
    url = URI_SCHEME + LOAD_BALANCER_ENDPOINT + url_method
    prediction = requests.post(url, json={'values': new_observation}).json()

    modelhost_cache.put_prediction_in_cache(hash_code=prediction_hash, model=model_name, inputs=new_observation,
                                            prediction=prediction)

    return prediction


# Display a list of the available models
@server.route(path.join(API_BASE_URL, 'models'), methods=['GET'])
def show_models():
    url_method = '/modelhost/models'

    metric_manager.increment_model_counter()

    url = URI_SCHEME + LOAD_BALANCER_ENDPOINT + url_method

    return requests.get(url).json()


# Display all the information related to every available model
@server.route(path.join(API_BASE_URL, 'models/information'), methods=['GET'])
def show_model_descriptions():  # TODO new pojo for this? or delete
    url_method = '/modelhost/models/information'

    metric_manager.increment_model_counter()

    url = URI_SCHEME + LOAD_BALANCER_ENDPOINT + url_method

    return requests.get(url).json()


# Update the list of available models on every modelhost node.
@server.route(path.join(API_BASE_URL, 'models/update'), methods=['POST'])
def update_models():
    url_method = '/modelhost/models/update'
    # The update_modelhost_models() method must be called everytime a change has occured on the model list

    for i in range(NUMBER_OF_MODELHOSTS):  # TODO load balancer instead of this loop?
        ip = os.getenv(f'MODELHOST_{i + 1}_IP') + ':8000'
        url = URI_SCHEME + ip + url_method
        data = None
        # TODO why post
        return requests.post(url, data=data).json()


# This method is in charge of model handling. Performs operations on models and manages models in the server.
@server.route(path.join(API_BASE_URL, 'models/<model_name>'), methods=['GET', 'PUT', 'POST', 'DELETE'])
def model_handling(model_name):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model_name)

    # For GET requests, display model information
    if request.method == 'GET':
        # Check if model is in .onnx format
        if get_file_extension(model_name) != 'onnx':
            return HttpJsonResponse(
                409,
                http_status_description=f'{model_name} is not in onnx format. '
                                        f'Please convert it and re-upload to provide information '
            ).json()

        url_method = f'/modelhost/{model_name}/information'
        url = URI_SCHEME + LOAD_BALANCER_ENDPOINT + url_method

        return requests.get(url, json={'model': model_name}).json()

    # For PUT requests, upload the given model file to the modelhost server
    if request.method == 'PUT':
        # Check a file path has been provided
        if not request.files or 'path' not in request.files:
            return HttpJsonResponse(422, http_status_description='No path specified').json()

        # Get model file from the given path
        new_model = request.files['path']

        # Check that the extension is allowed (.onnx supported)
        if get_file_extension(model_name) not in ALLOWED_EXTENSIONS:
            return HttpJsonResponse(
                415,
                http_status_description=f'File extension not allowed. '
                                        f'Please use one of these: {ALLOWED_EXTENSIONS}').json()

        url_method = '/modelhost/models/' + model_name
        url = URI_SCHEME + LOAD_BALANCER_ENDPOINT + url_method

        # Send the model as HTTP post request to a modelhost node
        response = requests.put(url, files={'model': new_model}).json()

        # Update the model list for every modelhost node
        update_models()

        return response

    # For POST requests, update the information on a given model
    if request.method == 'POST':
        # Check that any json data has been provided
        if not request.json:
            return HttpJsonResponse(
                422,
                http_status_description='No json data provided {model_description:string}').json()

        # Check that model_description has been provided
        if 'model_description' not in request.json:
            return HttpJsonResponse(422, http_status_description='No model_description provided').json()

        description = request.json['model_description']

        # Check that model_description is a string
        if not isinstance(description, str):
            return HttpJsonResponse(422, http_status_description='model_description must be a string').json()

        url_method = f'/modelhost/{model_name}/information'
        url = URI_SCHEME + LOAD_BALANCER_ENDPOINT + url_method

        data = {'model_description': description}
        response = requests.post(url, json=data).json()
        update_models()

        return response

    # For DELETE requests, delete a given model
    if request.method == 'DELETE':
        # Send the model as HTTP delete request
        url_method = '/modelhost/models/' + model_name
        url = URI_SCHEME + LOAD_BALANCER_ENDPOINT + url_method

        response = requests.delete(url).json()
        update_models()
        return response


if __name__ == '__main__':
    pass
