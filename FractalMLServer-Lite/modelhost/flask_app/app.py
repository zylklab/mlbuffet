import os
from os import getcwd, path, remove, listdir
import onnx
import onnxruntime as rt
from flask import Flask, request, Response
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized
import random
from utils import metric_manager
import utils.modelhost_manager as manager
from utils.container_logger import Logger
from utils.modelhost_pojos import HttpJsonResponse, Prediction, Description

# TODO: poner más métricas de prometheus por ahí

# constant variables
API_BASE_URL = '/api/v1/'
MODELHOST_BASE_URL = "/modelhost/"
MODEL_FOLDER = path.join(getcwd(), 'models')
auth_token = 'password'  # TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py

# uniq id for testing modelhost instances
MODELHOST_NODE_UNIQ_ID = "{:06d}".format(random.randint(1, 99999))

# logger initialization
logger = Logger('modelhost-logger').get_logger('modelhost-logger')
logger.info('Starting Flask API...')

# authentication
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(Unauthorized())

# create server
server = Flask(__name__)
logger.info('... Flask API succesfully started')

# List with the models preloaded to do the inference and their information
session_list = []

#Function that updates the model_list according to the MODEL_FOLDER
model_list = manager.refresh_model_list(MODEL_FOLDER, session_list)


@auth.verify_token
def verify_token(token):
    return token == auth_token


@server.route('/', methods=['GET'])
def hello_world():
    return HttpJsonResponse(200,
                            http_status_description='Greetings from Fractal - ML Server - ModelHost, the Machine '
                                                    'Learning model server. Are you supposed to be reading this? '
                                                    'Guess not. Go to Inferrer! '
                                                    'For more information, visit /help').json()


@server.route('/api/test', methods=['GET'])
def get_test():
    metric_manager.increment_test_counter()

    return HttpJsonResponse(200).json()


@server.route('/api/test/frominferrer/get/<data>', methods=['GET'])
def _test_frominferrer_send_modelhost(data):
    print(data)
    return HttpJsonResponse(200, http_status_description='Received: ' + data + ', modelhost prediction (node:' + str(
        MODELHOST_NODE_UNIQ_ID) + ')').json()


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
    elif request.path == '/modelhost/models':
        logger.info('Models list provided')
    elif request.path == '/modelhost/models/information':
        logger.info('Models & description list provided')
    elif response:
        logger.info(response.get_json())

    return response


@server.route(path.join(MODELHOST_BASE_URL, 'models/<model_name>/prediction'), methods=['POST'])
def prediction(model_name):
    metric_manager.increment_model_counter()

    try:
        model_list.index(model_name)
    except Exception:
        return HttpJsonResponse(404, http_status_description=f'{model_name} does not exist. '
                                                             f'Visit GET {path.join(API_BASE_URL, "models")} '
                                                             f'for a list of avaliable model_index').json()

    # get new observation
    new_observation = request.json['values']
    pred = do_prediction(model_name, new_observation)

    return Prediction(200, http_status_description='Prediction successful', values=pred).json()

@server.route(path.join(MODELHOST_BASE_URL, 'information'), methods=['GET'])
def get_model_information():
    model_name = request.json['model']
    index = model_list.index(model_name)
    desc = session_list[index][4]
    return Description(200, http_status_description='Model description', description=desc).json()


@server.route(path.join(MODELHOST_BASE_URL, 'models'), methods=['GET'])
def get_model_list():
    list = manager.refresh_model_list(model_list, session_list)
    return Description(200, http_status_description='List of available models', list=list).json()


@server.route(path.join(MODELHOST_BASE_URL, 'models/information'), methods=['GET'])
def get_model_list_information():
    model_list = manager.refresh_model_list(MODEL_FOLDER, session_list)
    list = model_list
    models_descr = []
    for i in list:
        index = model_list.index(i)
        descr = session_list[index][4]["description"]
        model_descr = {"model": i, "description": descr}
        models_descr.append(model_descr)
    return Description(200, http_status_description='Model description', description=models_descr).json()


@server.route(path.join(MODELHOST_BASE_URL, 'information'), methods=['POST'])
def model_post_information():
    model_name = request.json['model']
    model_path = path.join(MODEL_FOLDER, model_name)
    model_description = request.json['model_description']
    index = model_list.index(model_name)
    model = onnx.load(model_path)
    model.doc_string = model_description
    session_list[index][4]["description"] = model_description
    onnx.save(model, model_path)
    return HttpJsonResponse(200, http_status_description='success').json()


@server.route(path.join(MODELHOST_BASE_URL, 'models/upload_<model>'), methods=['POST'])
def post_upload_model(model):
    # get model
    modelpath = request.files['file']

    # save the model in model folder
    modelpath.save(path.join(MODEL_FOLDER, model))
    manager.refresh_model_list(MODEL_FOLDER, session_list)

    return HttpJsonResponse(200, http_status_description='success').json()

@server.route(path.join(MODELHOST_BASE_URL, 'models/delete_<model>'), methods=['DELETE'])
def delete_model(model):
    # check that model exists
    if os.path.isfile(path.join(MODEL_FOLDER, model)):
        # delete the model in model folder
        os.remove(path.join(MODEL_FOLDER, model))
        manager.refresh_model_list(MODEL_FOLDER, session_list)

        return HttpJsonResponse(200, http_status_description='success').json()
    else:
        return HttpJsonResponse(404, http_status_description=f'{model} does not exist. '
                                                             f'Visit GET {path.join(API_BASE_URL, "models")} '
                                                             f'for a list of avaliable model_index').json()

if __name__ == '__main__':
    server.run()
