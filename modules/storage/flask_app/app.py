from os import path

from flask import Flask, request, Response
import utils.buffetvc as bvc
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized

from utils import metric_manager
from utils.container_logger import Logger
from utils.storage_pojos import HttpJsonResponse, ModelListInformation
from secrets import compare_digest

# Path constants
STORAGE_BASE_URL = '/storage'

# Authorization constants
# TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py
auth_token = 'password'
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(
    Unauthorized())

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
    ).get_response()


@server.route(path.join(STORAGE_BASE_URL, 'api/test'), methods=['GET'])
def get_test():
    metric_manager.increment_test_counter()
    return HttpJsonResponse(200).get_response()


@server.errorhandler(HTTPException)
def handle_exception(exception):
    """Return JSON instead of HTML for HTTP errors."""

    return HttpJsonResponse(
        http_status_code=exception.code,
        http_status_name=exception.name,
        http_status_description=exception.description
    ).get_response()


@server.route('/metrics', methods=['GET', 'POST'])
def get_metrics():  # TODO: where is the result of this method used
    # force refresh system metrics
    metric_manager.compute_system_metrics()
    metrics = metric_manager.get_metrics()
    return Response(
        metrics, mimetype='text/plain'
    )


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
    return response


@server.route(path.join(STORAGE_BASE_URL, 'model/<tag>'), methods=['PUT'])
def save(tag):
    file = request.files['path']
    filename = request.files['filename'].stream.read().decode("utf-8")
    description = request.files['model_description'].stream.read().decode(
        "utf-8")
    bvc.save_file(file=file,
                  tag=tag,
                  file_name=filename,
                  description=description)

    return HttpJsonResponse(http_status_code=201,
                            http_status_description=f'File {filename} saved with the tag {tag}').get_response()


@server.route(path.join(STORAGE_BASE_URL, 'model/<tag>'), methods=['DELETE'])
def delete(tag):
    separator = tag.find(':')
    if separator < 0:
        bvc.delete_tag(tag)

    else:
        name_split = tag.split(':')
        tag = name_split[0]
        version = name_split[1]

    bvc.delete_file(name=tag, version=version)
    return HttpJsonResponse(200, http_status_description=f'{tag} removed\n').get_response()


@server.route(path.join(STORAGE_BASE_URL, 'model/<tag>'), methods=['GET'])
def download(tag):
    separator = tag.find(':')
    if separator < 0:
        version = 'default'
    else:
        name_splitted = tag.split(':')
        tag = name_splitted[0]
        version = name_splitted[1]
    return bvc.download_file(name=tag, version=version)


@server.route(path.join(STORAGE_BASE_URL, 'models'), methods=['GET'])
def model_list():
    return bvc.get_model_list()


@server.route(path.join(STORAGE_BASE_URL, 'model/<tag>/default'), methods=['POST'])
def update_default_file(tag):
    new_default = request.json['default']
    response = bvc.update_default(name=tag, version=new_default)
    return response


@server.route(path.join(STORAGE_BASE_URL, 'model/<tag>/information'), methods=['GET'])
def get_info(tag):
    try:
        information = bvc.get_information(tag)
        return ModelListInformation(200, tag_list=information).get_response()
    except FileNotFoundError:
        return HttpJsonResponse(
            422,
            http_status_description='Tag not found, please check the name introduced').get_response()


if __name__ == '__main__':
    pass
