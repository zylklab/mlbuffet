from os import path

from flask import Flask, request, Response
import utils.buffetvc as bvc
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized

from utils import metric_manager
from utils.container_logger import Logger
from utils.storage_pojos import HttpJsonResponse
from secrets import compare_digest

# Path constants
STORAGE_BASE_URL = '/storage'

# Authorization constants
auth_token = 'password'  # TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(Unauthorized())

# Logger initialization
logger = Logger('storage').get_logger('storage')
logger.info('Starting Flask API...')

# Server initialization
server = Flask(__name__)
logger.info('... Flask API successfully started')


# All the methods supported by the API are described below
# These methods are not supposed to be exposed to the user, who should communicate
# with Inferrer instead. These methods shall be called by Inferrer


@auth.verify_token
def verify_token(token):
    return compare_digest(token, auth_token)


@server.route(STORAGE_BASE_URL, methods=['GET'])
def hello_world():
    return HttpJsonResponse(
        200,
        http_status_description='Greetings from MLBuffet - Storage, the Machine Learning model server. '
                                'Are you supposed to be reading this? Guess not. Go to Inferrer!'
    ).json()


@server.route(path.join(STORAGE_BASE_URL, 'api/test'), methods=['GET'])
def get_test():
    metric_manager.increment_test_counter()
    return HttpJsonResponse(200).json()


@server.errorhandler(HTTPException)
def handle_exception(exception):
    """Return JSON instead of HTML for HTTP errors."""

    return HttpJsonResponse(
        http_status_code=exception.code,
        http_status_name=exception.name,
        http_status_description=exception.description
    ).json()


@server.route('/metrics', methods=['GET', 'POST'])
def get_metrics():  # TODO: where is the result of this method used
    # force refresh system metrics
    metric_manager.compute_system_metrics()
    metrics = metric_manager.get_metrics()
    return Response(
        metrics, mimetype='text/plain'
    )


@server.route('/remove/<tag>', methods=['DELETE'])
def remove(tag):
    separator = tag.find(':')
    if separator < 0:
        version = 'default'
    else:
        name_splitted = tag.split(':')
        tag = name_splitted[0]
        version = name_splitted[1]

    bvc.remove_file(name=tag, version=version)
    return Response(f'{tag} removed\n')


@server.route('/download/<tag>', methods=['GET'])
def download(tag):
    separator = tag.find(':')
    if separator < 0:
        version = 'default'
    else:
        name_splitted = tag.split(':')
        tag = name_splitted[0]
        version = name_splitted[1]
    return bvc.download_file(name=tag, version=version)


@server.route('/default/<tag>/<new_default>', methods=['POST'])
def update_default(tag, new_default):
    return bvc.update_default(name=tag, version=new_default)


@server.route('/info/<tag>', methods=['GET'])
def get_info(tag):
    information = bvc.get_information(tag)
    return Response(information)


if __name__ == '__main__':
    pass
