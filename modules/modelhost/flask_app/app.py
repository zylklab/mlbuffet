from os import path, getenv

from flask import Flask, request, Response
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized

from utils import metric_manager
from utils.container_logger import Logger
from utils.modelhost_pojos import HttpJsonResponse, Prediction
from secrets import compare_digest

# TODO: more prometheus metrics
# TODO: (endpoint for each modelhost prometheus metrics)

# Path constants
API_BASE_URL = '/api/v1/'
MODELHOST_BASE_URL = '/modelhost'

# Authorization constants
# TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py
auth_token = 'password'
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(
    Unauthorized())

# Logger initialization
logger = Logger('modelhost').get_logger('modelhost')
logger.info('Starting Flask API...')

# Server initialization
server = Flask(__name__)
logger.info('... Flask API successfully started')

# ####### This is executed at server startup.               ####### #
# ####### Imports the library required to deploy the model. ####### #

# Read ENV variables for the model
tag = getenv('TAG')
ml_library = getenv('ml_library')
model_name = getenv('filename')

try:
    # Import the corresponding library
    if 'onnx' in ml_library:
        from serving import serve_onnx as serve
        logger.info(f'Library onnxruntime imported for deploying {tag}.')
    elif 'tensorflow' in ml_library:
        from serving import serve_tf as serve
        logger.info(f'Library tensorflow imported for deploying {tag}.')

    if serve.load_model(tag, model_name):
        logger.info(f'Model successfully loaded in {ml_library} format')

except Exception as e:
    logger.error(
        f'Something went wrong while trying to download the model. Reason: {e}')

###################################################
###################################################

# All the methods supported by the API are described below
# These methods are not supposed to be exposed to the user, who should communicate
# with Inferrer instead. These methods shall be called by Inferrer OR Storage


@auth.verify_token
def verify_token(token):
    return compare_digest(token, auth_token)


@server.route(MODELHOST_BASE_URL, methods=['GET'])
def hello_world():
    return HttpJsonResponse(
        200,
        http_status_description='Greetings from MLBuffet - ModelHost, the Machine Learning model server. '
                                'Are you supposed to be reading this? Guess not. Go to Inferrer!'
    ).get_response()


@server.route(path.join(MODELHOST_BASE_URL, 'api/test'), methods=['GET'])
def get_test():
    metric_manager.increment_test_counter()
    return HttpJsonResponse(200).get_response()


@server.route('/metrics', methods=['GET', 'POST'])
def get_metrics():  # TODO: where is the result of this method used
    # force refresh system metrics
    metric_manager.compute_system_metrics()
    metrics = metric_manager.get_metrics()
    return Response(
        metrics, mimetype='text/plain'
    )


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
        pass
    else:
        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        logger.info(
            f'[{client_ip}] HTTP {request.method} call to {request.path}')


@server.after_request
def log_response(response):
    if request.path == '/metrics':  # don't log prometheus' method
        pass
    elif request.path == '/help':  # don't display the whole help
        logger.info('Help displayed')
    elif request.path == '/modelhost/models':
        logger.info('Models list provided')
    elif request.path == '/modelhost/models/information':
        logger.info('Models & description list provided')
    elif 'predict' in request.path:
        logger.info('Prediction tried')
    elif response:
        logger.info(response.get_json())

    return response


@server.route(path.join(MODELHOST_BASE_URL, 'predict'), methods=['POST'])
def predict():
    metric_manager.increment_model_counter()

    model_input = request.json['values']

    if serve.check_model_exists(tag):
        try:
            prediction = serve.perform_inference(tag, model_input)
            logger.info('Prediction done')

            return Prediction(
                200, http_status_description='Prediction successful', values=prediction
            ).get_response()

        except NotImplementedError as error:
            return Prediction(404, http_status_description=str(error)).get_response()

        except Exception as error:
            logger.error("Prediction failed")
            return Prediction(
                500, http_status_description=str(error)
            ).get_response()

    else:
        return Prediction(
            404,
            http_status_description=f'{tag} does not exist. '
                                    f'Visit GET {path.join(API_BASE_URL, "models")} for a list of available models'
        ).get_response()


if __name__ == '__main__':
    pass
