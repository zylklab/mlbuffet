from io import BytesIO
from os import path
from secrets import compare_digest

import numpy
from flask import Flask, request, Response, send_file
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized

import modelhost_manager as mh_talker
import storage_talker as st_talker
import trainer_executor as trainer
from utils import metric_manager, stopwatch, prediction_cache
from utils.container_logger import Logger
from utils.inferer_pojos import HttpJsonResponse, Prediction
from utils.utils import get_file_extension, ALLOWED_EXTENSIONS, is_ok

# Path constants
API_BASE_URL = '/api/v1/'

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


# TODO: endpoint information models... :/
# TODO: Federated Learning module


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
    ).get_response()


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
    return HttpJsonResponse(200).get_response()


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
    ).get_response()


@server.before_request
def log_call():
    if request.path == '/metrics':  # don't log prometheus' method
        return

    # log ip, http method and path
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    logger.info(f'[{client_ip}] HTTP {request.method} call to {request.path}')

    # measure time until stopwatch.stop() is called in log_response() function
    my_stopwatch.start()


@server.after_request
def log_response(response):
    if request.path == '/metrics':  # don't log prometheus' method
        return response

    if request.path == '/help':  # don't display the whole help
        logger.info('Help displayed')
    elif response and response.get_json():
        logger.info(response.get_json())

    # log elapsed time since the request was made
    my_stopwatch.stop()

    return response


# Prediction method. Given a json with input data, sends it to modelhost for predictions.
@server.route(path.join(API_BASE_URL, 'models/<tag>/prediction'), methods=['POST'])
def get_prediction(tag):
    metric_manager.increment_model_counter()

    # Test values can be a json (array) or a file (image)
    # If a file was not provided, suppose that it is a json
    if not request.files:
        # check that json data was provided
        if not request.json:
            return Prediction(
                422, http_status_description='No json data {values:[...]} or file provided').get_response()

        # Check that input values for prediction have been provided
        if 'values' not in request.json:
            return Prediction(
                422, http_status_description='No input for the model provided as (values:[...])').get_response()

        model_input = request.json['values']

        # Check that the input is a list
        if not isinstance(model_input, list):
            return Prediction(
                422,
                http_status_description='New observation is not a list enclosed by squared brackets').get_response()

        # Check if the same prediction has already been made before
        model_input_hash = prediction_cache.get_hash(
            model_name=tag, inputs=model_input)
        cached_prediction = prediction_cache.get_prediction(
            hash_code=model_input_hash)

        # If the prediction exists in cache, return it
        if cached_prediction is not None:
            return Prediction(200,
                              values=cached_prediction,
                              http_status_description='Prediction successful').get_response()

        # Otherwise, compute it and save it in cache
        result = mh_talker.make_a_prediction(tag, model_input)
        if is_ok(result['http_status']['code']):
            prediction_cache.put_prediction_in_cache(
                hash_code=model_input_hash,
                prediction=result['values'])

        return result

    else:  # If a file was provided
        if 'path' not in request.files:
            return HttpJsonResponse(
                422, http_status_description='The name of the file path must be \'path\'').get_response()

        test_file = request.files['path']
        file_type = test_file.mimetype

        # Currently, only accepting images
        if file_type.split('/')[0] == 'image':
            to_hash = request.files['path'].read()

            # Check if the same prediction has already been made before
            test_values_hash = prediction_cache.get_hash(
                model_name=tag, inputs=to_hash)
            cached_prediction = prediction_cache.get_prediction(
                hash_code=test_values_hash)

            # If the prediction exists in cache, return it
            if cached_prediction is not None:
                return Prediction(200,
                                  values=cached_prediction,
                                  http_status_description='Prediction successful').get_response()

            # Otherwise, compute it and save it in cache
            flat_image = numpy.frombuffer(to_hash, numpy.uint8)
            img_bgr = cv2.imdecode(flat_image, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            result = mh_talker.make_a_prediction(tag, img.tolist())

            if is_ok(result['http_status']['code']):
                prediction_cache.put_prediction_in_cache(
                    hash_code=test_values_hash,
                    prediction=result['values'])

            return result
        else:
            return HttpJsonResponse(
                422, http_status_description=f'Filetype {file_type} is not currently allowed for predictions. '
                                             'The model server only supports images so far').get_response()


# Get the list of uploaded models in the Storage
@server.route(path.join(API_BASE_URL, 'models'), methods=['GET'])
def get_model_list():
    metric_manager.increment_model_counter()
    return st_talker.get_model_list()


@server.route(path.join(API_BASE_URL, 'models/<complete_tag>'), methods=['GET', 'POST', 'DELETE'])
# This resource is used for model management. Performs operations on models and manages models in the server.
def model_handling(complete_tag):
    # Download model
    if request.method == 'GET':
        metric_manager.increment_storage_counter()

        return st_talker.download_model(tag=complete_tag)

    # Create a modelhost_tag Pod
    if request.method == 'POST':
        metric_manager.increment_storage_counter()

        # Check that the new tag name is dns-valid
        dns_valid_chars = [str(n) for n in range(10)] + [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['-']
        if not all(c in dns_valid_chars for c in complete_tag):
            return HttpJsonResponse(
                422, http_status_description=f'Tag name {complete_tag} is not a dns-valid tag name. Only numbers [0-9], '
                                             'lowercase letters [a-z] and hyphens [-] are allowed.').get_response()

        # Check a file path has been provided
        if not request.files or 'path' not in request.files:
            return HttpJsonResponse(422,
                                    http_status_description='No file path (named \'path\') specified').get_response()

        # Get model file from the given path
        new_model = request.files['path']
        model_name = new_model.filename

        # Check that the extension is allowed
        if get_file_extension(model_name) not in ALLOWED_EXTENSIONS:
            return HttpJsonResponse(
                415,
                http_status_description=f'Filename extension not allowed. '
                                        f'Please use one of these: {ALLOWED_EXTENSIONS}').get_response()

        if 'library_version' not in request.form:
            return HttpJsonResponse(422,
                                    http_status_description='No model library provided. Please provide \'library_version\' (e.g. tensorflow==2.7.0).').get_response()

        ML_LIBRARY = request.form['library_version']

        if 'model_description' not in request.form:
            desc = 'No description provided'
        else:
            desc = request.form['model_description']

        #### CREATE MODELHOST POD ####
        mh_talker.create_modelhost(tag=complete_tag)

        return st_talker.upload_new_model(tag=complete_tag, file=new_model, file_name=model_name, description=desc,
                                          ml_library=ML_LIBRARY)

    # For DELETE requests, delete a given tag from the storage and manage the modelhost deployment

    if request.method == 'DELETE':
        metric_manager.increment_storage_counter()
        # Delete the model on storage module
        delete = st_talker.delete_model(complete_tag)
        if not is_ok(delete['http_status']['code']):
            return delete
        tag_version = complete_tag.split(':')
        tag = tag_version[0]
        # If the complete_tag is given without version, it removes the entire tag and the modelhost
        if len(tag_version) == 1:
            mh_talker.delete_modelhost(tag=tag)
            response = HttpJsonResponse(200,
                                        http_status_description=f'Tag {tag} removed successfully') \
                .get_response()
        else:
            version = tag_version[1]
            # Check if there are not any file associated to that tag.
            tag_info_response = st_talker.get_tag_information(tag)
            # If there is not any file associated, remove the deployment
            if tag_info_response['http_status']['code'] == 422:
                mh_talker.delete_modelhost(tag=tag)
                response = HttpJsonResponse(200,
                                            http_status_description=f'Tag {tag} removed successfully') \
                    .get_response()
            # If there is any file associated, but the file is the default file, recreate the deployment
            elif tag_info_response['default_version'] == version or version == 'default':
                try:
                    #### DELETE MODELHOST POD  ####
                    mh_talker.create_modelhost(tag=tag)
                    logger.info('Modelhost deleted successfully!')
                    response = HttpJsonResponse(200,
                                                http_status_description=f'Tag {tag} updated to new default version '
                                                                        f'successfully') \
                        .get_response()
                except Exception as e:
                    logger.error(f'modelhost-{complete_tag} could not be deleted. ' + 'Reason: ' + e)
            # If there is any file associated, but the file is not the default file, all remains the same
            else:
                response = HttpJsonResponse(200,
                                            http_status_description=f'Version {version} from tag {tag} removed '
                                                                    f'successfully').get_response()

        # Send the tag as HTTP delete request
        return response


@server.route(path.join(API_BASE_URL, 'models/<tag>/default'), methods=['POST'])
def upload_default(tag):
    metric_manager.increment_storage_counter()
    # Check that any json data has been provided
    if not request.json:
        return HttpJsonResponse(
            422,
            http_status_description='No json data provided {default:string}').get_response()

    # Check that model_description has been provided
    if 'default' not in request.json:
        return HttpJsonResponse(422, http_status_description='No default value provided').get_response()

    default = request.json['default']

    # Check that model_description is a string
    if not isinstance(default, int):
        return HttpJsonResponse(422, http_status_description='Default value must be an integer').get_response()

    # Send to the storage the tag and the new default version
    st_talker.set_default_model(tag, str(default))

    # Restart the deployment to lift again with the new model.

    mh_talker.create_modelhost(tag=tag)

    return HttpJsonResponse(200,
                            http_status_description=f'Modelhost tagged as {tag} updated with default version: {default}') \
        .get_response()


@server.route(path.join(API_BASE_URL, 'models/<tag>/information'), methods=['GET'])
def model_information_handling(tag):
    """ GET model information"""

    # Get information of the model tag
    if request.method == 'GET':
        metric_manager.increment_storage_counter()

        return st_talker.get_tag_information(tag)


@server.route(path.join(API_BASE_URL, 'train/<tag>/<model_name>'), methods=['POST'])
# Start a new training session.
def train(tag, model_name):
    metric_manager.increment_train_counter()

    # Check that the new tag name is dns-valid
    dns_valid_chars = [str(n) for n in range(10)] + [chr(i) for i in range(ord('a'), ord('z') + 1)] + ['-']
    if not all(c in dns_valid_chars for c in tag):
        return HttpJsonResponse(
            422, http_status_description=f'Tag name {tag} is not a dns-valid tag name. Only numbers [0-9], '
                                         'lowercase letters [a-z] and hyphens [-] are allowed.').get_response()

    # Check that the model extension is allowed
    if get_file_extension(model_name) not in ALLOWED_EXTENSIONS:
        return HttpJsonResponse(
            415, http_status_description='Filename extension not allowed. '
                                         f'Please use one of these: {ALLOWED_EXTENSIONS}').get_response()

    # Check that the script was provided
    if not request.files.getlist('script'):
        return HttpJsonResponse(
            422,
            http_status_description='No training script provided with name \'script\'').get_response()

    # Check that requirements.txt was provided
    if not request.files.getlist('requirements'):
        return HttpJsonResponse(
            422, http_status_description='No requirements provided with name \'requirements\'').get_response()

    # Check that data was provided
    if not request.files.getlist('dataset'):
        return HttpJsonResponse(422, http_status_description='No data provided with name \'dataset\'').get_response()

    # get training script, requirements and data
    train_script = request.files.getlist('script')[0]
    requirements = request.files.getlist('requirements')[0]
    dataset = request.files.getlist('dataset')[0]

    # Change filenames to match expected ones TODO preserve original names
    train_script.filename = 'train.py'
    requirements.filename = 'requirements.txt'
    if get_file_extension(dataset.filename).__eq__(".csv") or get_file_extension(dataset.filename).__eq__(".zip"):
        dataset.filename = 'dataset' + get_file_extension(dataset.filename)

    # Start training
    trainer.run_training(train_script, requirements, dataset, model_name, tag)

    return HttpJsonResponse(200, http_status_description='Training container created and running!').get_response()


@server.route(path.join(API_BASE_URL, 'train/download_buildenv'), methods=['GET'])
# This resource is called from Trainer Pod to download the data.
def download_buildenv():  # TODO with GB order environment.zip it is not feasible to store contents in memory
    # read file contents
    with open('/trainerfiles/environment.zip', 'rb') as f:
        buildenv = f.read()

    # remove training files
    try:
        trainer.remove_buildenv()
    except FileNotFoundError:
        pass

    # download new file with contents
    return send_file(path_or_file=BytesIO(buildenv), download_name='environment.zip')


if __name__ == '__main__':
    pass
