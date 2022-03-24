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


@server.route('/save/<tag>', methods=['PUT'])
def save(tag):
    file = request.files['path']
    filename = file.filename
    bvc.save_file(file=file, tag=tag, file_name=filename)
    return Response(f'File {filename} saved with the tag {tag}\n')


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
