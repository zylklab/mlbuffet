from os import getcwd, path
from pathlib import Path

from flask import Flask, request, Response
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized
from werkzeug.utils import secure_filename

import modelhost_talker as mh_talker
from utils import metric_manager, stopwatch, prediction_cache
from utils.container_logger import Logger
from utils.inferer_pojos import HttpJsonResponse

# Path constants
API_BASE_URL = '/api/v1/'
ALLOWED_EXTENSIONS = ['onnx']

# Authorization constants
auth_token = 'password'  # TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(Unauthorized())

# Logger initialization
logger = Logger('inferrer').get_logger('inferrer')
logger.info('Starting FRACTAL - ML SERVER - INFERRER API...')
my_stopwatch = stopwatch.Stopwatch(logger.info)

# Server initialization
server = Flask(__name__)
logger.info('... FRACTAL - ML SERVER - INFERRER API succesfully started')


# TODO: comments
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

    return mh_talker.test_load_balancer(data_array)


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

    # Check if file is provided
    if not request.files:
        # If file is not provided, check that json data was provided
        if not request.json:
            return HttpJsonResponse(422, http_status_description='No file json data provided {values:list}').json()

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
        prediction_hash = prediction_cache.get_hash(model_name=model_name, inputs=new_observation)
        cached_prediction = prediction_cache.get_prediction(hash_code=prediction_hash)

        # If the prediction exists in cache, return it
        if cached_prediction is not None:
            return cached_prediction

        prediction = mh_talker.make_a_prediction(model_name, new_observation)

        prediction_cache.put_prediction_in_cache(hash_code=prediction_hash, model=model_name, inputs=new_observation,
                                                 prediction=prediction)

        return prediction

    else:
        # Check that file extension is .onnx
        if get_file_extension(model_name) != 'onnx':
            return HttpJsonResponse(409, http_status_description=f'{model_name} is not in onnx format.').json()
        # TODO hash for image predictions.
        # Check if the same prediction has already been made before

        if 'path' not in request.files:
            return HttpJsonResponse(422, http_status_description='No path specified').json()

        new_observation = request.files['path']
        prediction_hash = prediction_cache.get_hash(model_name=model_name, inputs=new_observation.filename)
        cached_prediction = prediction_cache.get_prediction(hash_code=prediction_hash)
        if cached_prediction is not None:
            return cached_prediction
        # Take the file name
        filename = str(new_observation.filename)
        prediction = mh_talker.make_a_prediction_image(model_name, new_observation, filename)
        prediction_cache.put_prediction_in_cache(hash_code=prediction_hash, model=model_name,
                                                 inputs=new_observation.filename,
                                                 prediction=prediction)
        return prediction


# Display a list of available models
@server.route(path.join(API_BASE_URL, 'models'), methods=['GET'])
def show_models():
    metric_manager.increment_model_counter()
    return mh_talker.get_list_of_models()


# Display all the information related to every available model
@server.route(path.join(API_BASE_URL, 'models/information'), methods=['GET'])
def show_model_descriptions():  # TODO new pojo for this? or delete
    metric_manager.increment_model_counter()
    return mh_talker.get_information_of_all_models()


# Update the list of available models on every modelhost node.
@server.route(path.join(API_BASE_URL, 'models/update'), methods=['POST'])
def update_models():
    return mh_talker.update_models()


# This method is in charge of model handling. Performs operations on models and manages models in the server.
@server.route(path.join(API_BASE_URL, 'models/<model_name>'), methods=['GET', 'PUT', 'POST', 'DELETE'])
def model_handling(model_name):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model_name)

    # For GET requests, display model information
    if request.method == 'GET':
        return mh_talker.get_information_of_a_model(model_name)

    # For PUT requests, upload the given model file to the modelhost server
    if request.method == 'PUT':
        # Check a file path has been provided
        if not request.files or 'path' not in request.files:
            return HttpJsonResponse(422, http_status_description='Model\'s path name must be \'path\'').json()

        # Get model file from the given path
        new_model = request.files['path']

        # Check that the extension is allowed (.onnx supported)
        if get_file_extension(model_name) not in ALLOWED_EXTENSIONS:
            return HttpJsonResponse(
                415,
                http_status_description=f'Filename extension not allowed. '
                                        f'Please use one of these: {ALLOWED_EXTENSIONS}').json()

        return mh_talker.upload_new_model(model_name, new_model)

    # For POST requests, update the information of a given model
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

        return mh_talker.write_model_description(model_name, description)

    # For DELETE requests, delete a given model
    if request.method == 'DELETE':
        # Send the model as HTTP delete request
        return mh_talker.delete_model(model_name)


if __name__ == '__main__':
    pass
