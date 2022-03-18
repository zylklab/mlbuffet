from os import path
from pathlib import Path
from secrets import compare_digest

import cv2
import numpy
from flask import Flask, request, Response
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized
from werkzeug.utils import secure_filename

import modelhost_talker as mh_talker
from trainer_executor import run_training
from utils import metric_manager, stopwatch, prediction_cache
from utils.container_logger import Logger
from utils.inferer_pojos import HttpJsonResponse, Prediction

# Path constants
API_BASE_URL = '/api/v1/'
ALLOWED_EXTENSIONS = ['onnx', 'pb']

# Authorization constants
# TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py
auth_token = 'password'
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(
    Unauthorized())

# Logger initialization
logger = Logger('inferrer').get_logger('inferrer')
logger.info('Starting MLBuffet - INFERRER API...')
my_stopwatch = stopwatch.Stopwatch(logger.info)

# Server initialization
server = Flask(__name__)
logger.info('... MLBuffet - INFERRER API succesfully started')


# TODO: comments
# TODO: not os.getenv, constants
# TODO: endpoint information models... :/
# TODO: loadbalancer endpoint no --> ip y url method no --> endpoint
# TODO: hueco para federated learning
# TODO: reorder methods

# Authorization verification
@auth.verify_token
def verify_token(token):
    return compare_digest(token, auth_token)


# All endpoints supported by the API are defined below


# Welcome endpoint
@server.route('/', methods=['GET'])
def hello_world():
    return HttpJsonResponse(
        200,
        http_status_description='Greetings from MLBuffet - Inferrer, the Machine Learning model server. '
                                'For more information, visit /help'
    ).json()


# Help endpoint
@server.route('/help', methods=['GET'])
def show_help():
    return '''
        ###############################
        #### MLBuffet MODEL SERVER ####
        ###############################

MLBuffet is a Machine Learning model server developed by Zylk.net.
For more information on the project go to https://github.com/zylklab/mlbuffet/.

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
# TODO: needs to be authorized
@server.route('/metrics', methods=['GET', 'POST'])
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
        logger.info(
            f'[{client_ip}] HTTP {request.method} call to {request.path}')
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
    elif 'path' in request.files:
        logger.info('Prediction done')
    elif response and response.get_json():
        logger.info(response.get_json())

    my_stopwatch.stop()

    return response


# TODO this should go into utils folder
def get_file_extension(file_name):
    return Path(file_name).suffix[1:].lower()


# Prediction method. Given a json with input data, sends it to modelhost for predictions.
@server.route(path.join(API_BASE_URL, 'models/<model_name>/prediction'), methods=['POST'])
def get_prediction(model_name):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model_name)

    # Test values can be a json (array) or a file (image)
    # If a file was not provided, suppose that it is a json
    if not request.files:
        # check that json data was provided
        if not request.json:
            return Prediction(422, http_status_description='No json data {values:[...]} or file provided').json()

        # Check that input values for prediction have been provided
        if 'values' not in request.json:
            return Prediction(422, http_status_description='No test observation provided (values:[...])').json()

        test_values = request.json['values']

        # Check that the input is a list
        if not isinstance(test_values, list):
            return Prediction(
                422,
                http_status_description='New observation is not a list enclosed by squared brackets').json()

        # Check if the same prediction has already been made before
        test_values_hash = prediction_cache.get_hash(
            model_name=model_name, inputs=test_values)
        cached_prediction = prediction_cache.get_prediction(
            hash_code=test_values_hash)

        # If the prediction exists in cache, return it
        if cached_prediction is not None:
            return Prediction(200, values=cached_prediction).json()

        # Otherwise, compute it and save it in cache
        result = mh_talker.make_a_prediction(model_name, test_values)
        prediction_cache.put_prediction_in_cache(
            hash_code=test_values_hash, prediction=result['values'])

        return result

    else:  # If a file was provided
        if 'path' not in request.files:
            return HttpJsonResponse(422, http_status_description='The name of the file path must be \'path\'').json()

        test_file = request.files['path']
        file_type = test_file.mimetype

        # Currently, only accepting images
        if file_type.split('/')[0] == 'image':
            to_hash = request.files['path'].read()

            # Check if the same prediction has already been made before
            test_values_hash = prediction_cache.get_hash(
                model_name=model_name, inputs=to_hash)
            cached_prediction = prediction_cache.get_prediction(
                hash_code=test_values_hash)

            # If the prediction exists in cache, return it
            if cached_prediction is not None:
                return Prediction(200, values=cached_prediction).json()

            # Otherwise, compute it and save it in cache
            flat_image = numpy.frombuffer(to_hash, numpy.uint8)
            img_bgr = cv2.imdecode(flat_image, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            result = mh_talker.make_a_prediction(model_name, img.tolist())
            prediction_cache.put_prediction_in_cache(
                hash_code=test_values_hash, prediction=result['values'])

            return result
        else:
            return HttpJsonResponse(
                422, http_status_description=f'Filetype {file_type} is not currently allowed for predictions. '
                                             'The model server only supports images so far').json()


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
@server.route(path.join(API_BASE_URL, 'updatemodels'), methods=['GET'])
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
            return HttpJsonResponse(422, http_status_description='No file path (named \'path\') specified').json()

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


# Start a new training session.
@server.route(path.join(API_BASE_URL, 'train/<model_name>'), methods=['POST'])
def train(model_name):
    metric_manager.increment_train_counter()

    # Check that the script was provided
    if not request.files.getlist('script'):
        return HttpJsonResponse(422, http_status_description='No training script provided with name \'script\'').json()

    # Check that requirements.txt was provided
    if not request.files.getlist('requirements'):
        return HttpJsonResponse(
            422, http_status_description='No requirements provided with name \'requirements\'').json()

    # Check that data was provided
    if not request.files.getlist('dataset'):
        return HttpJsonResponse(422, http_status_description='No data provided with name \'dataset\'').json()

    # get training script, requirements and data
    train_script = request.files.getlist('script')[0]
    requirements = request.files.getlist('requirements')[0]
    dataset = request.files.getlist('dataset')[0]

    # Change filenames to match expected ones TODO preserve original names
    train_script.filename = 'train.py'
    requirements.filename = 'requirements.txt'
    dataset.filename = 'dataset.csv'

    # Start training
    run_training(train_script, requirements, dataset, model_name)

    return HttpJsonResponse(200, http_status_description='Training started!').json()


if __name__ == '__main__':
    pass
