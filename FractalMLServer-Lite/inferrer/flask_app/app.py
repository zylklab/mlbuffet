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
from utils.inferer_pojos import HttpJsonResponse, Prediction, ModelInformation

from modelhost_utils.modelhost_manager import ModelhostClientManager
from modelhost_utils.modelhost_cache import modelhost_cache

# constant variables
API_BASE_URL = '/api/v1/'
ALLOWED_EXTENSIONS = ['onnx']
MODEL_FOLDER = path.join(getcwd(), 'models')
auth_token = 'password'  # TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py

# logger initialization
logger = Logger('inferrer').get_logger('inferrer')
logger.info('Starting FRACTAL - ML SERVER - INFERRER API...')

# authentication
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(Unauthorized())

# create server
server = Flask(__name__)
logger.info('... FRACTAL - ML SERVER - INFERRER API succesfully started')


@auth.verify_token
def verify_token(token):
    return token == auth_token


@server.route('/', methods=['GET'])
def hello_world():
    return HttpJsonResponse(200,
                            http_status_description='Greetings from Fractal - ML Server - Inferrer, the Machine '
                                                    'Learning model server. '
                                                    'For more information, visit /help').json()


@server.route('/help', methods=['GET'])
def show_help():
    return index.header + index.help + '\n'


@server.route('/api/test', methods=['GET'])
def get_test():
    metric_manager.increment_test_counter()

    return HttpJsonResponse(200).json()

@server.route('/api/test/sendtomodelhost/', methods=['GET'])
def _test_send_to_modelhost():
    modelhostclient = ModelhostClientManager()
    data_array = request.json['data']
    print(data_array)
    predictions = modelhostclient._test_get_kitchen_predictions(data_array)
    for p in predictions:
        print("respuesta en api " + p)

    return "recibido"



@server.route('/metrics', methods=['GET', 'POST'])
@auth.login_required  # it needs a header "Authorization: Bearer <token>"
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
    elif response:
        logger.info(response.get_json())

    return response


# TODO this should go into utils folder
def get_file_extension(file_name):
    return Path(file_name).suffix[1:].lower()


@server.route(path.join(API_BASE_URL, 'models/<model>/prediction'), methods=['GET'])
def getPrediction(model):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model)
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {values:list}').json()
    if get_file_extension(model_name) != 'onnx':
        return HttpJsonResponse(
            409,
            http_status_description=f'{model_name} is not in onnx format. '
                                    f'Please convert it first visiting '
                                    f'POST {path.join(API_BASE_URL, "models", model_name, "to-onnx")}'
        ).json()
    if 'values' not in request.json:
        return HttpJsonResponse(422, http_status_description='No test observation provided (values:[...])').json()
    t0 = time.time()
    new_observation = request.json["values"]
    if not isinstance(new_observation, list):
        return HttpJsonResponse(422, http_status_description='New observation is not a list enclosed by'
                                                             ' squared brackets').json()
    hash = modelhost_cache.get_hash(model=model, input=new_observation)
    check = modelhost_cache.check_hash(hash=hash)

    if check == "Key exists":
        pred = modelhost_cache.get_prediction(hash=hash)
        t1 = time.time()
        tiempo = t1 - t0
        logger.info("Time reading in cache: " + str(tiempo))
        # return {"Mode": "read from cache", "Value": pred}
        return Prediction(200, http_status_description='Prediction successful', values=pred).json()
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


@server.route(path.join(API_BASE_URL, 'models/<model>/information'), methods=['GET'])
def getInfo(model):
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
                                    f'Please convert it first visiting '
                                    f'POST {path.join(API_BASE_URL, "models", model_name, "to-onnx")}'
        ).json()


@server.route('/test/postinfo/<model>', methods=['POST'])
def postInfo(model):
    t0 = time.time()
    metric_manager.increment_model_counter()
    model_name = secure_filename(model)

    # check that any json data has been provided
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {model_description:string}').json()

    # check that model_description has been provided
    if 'model_description' not in request.json:
        return HttpJsonResponse(422, http_status_description='No model_description provided').json()
    description = request.json["model_description"]

    # check that model_description is a string
    if not isinstance(description, str):
        return HttpJsonResponse(422, http_status_description='model_description must be a string').json()

    modelhost = ModelhostClientManager()

    try:
        modelhost.post_modelhost_info(model_name, description)
    except Exception as error:
        return HttpJsonResponse(500, http_status_description=str(error)).json()

    t1 = time.time()
    tiempo = t1 - t0
    logger.info("Time getting info: " + str(tiempo))

    return HttpJsonResponse(200, http_status_description=f'Model description updated! Visit '
                                                         f'GET {path.join(API_BASE_URL, model_name, "information")} '
                                                         f'to check available info about the current model').json()


if __name__ == '__main__':
    server.run()
