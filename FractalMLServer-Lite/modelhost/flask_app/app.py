from os import getcwd, path, remove, listdir
import onnx
import onnxruntime as rt
from flask import Flask, request, Response
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized
import random
from utils import metric_manager
from utils.container_logger import Logger
from utils.modelhost_pojos import HttpJsonResponse, Prediction, Description


# TODO: poner más métricas de prometheus por ahí

# constant variables
API_BASE_URL = '/api/v1/'
MODELHOST_BASE_URL = "/modelhost/"
MODEL_FOLDER = path.join(getcwd(), 'models')
auth_token = 'password'  # TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py

#uniq id for testing kitchen instances
KITCHEN_NODE_UNIQ_ID = "{:06d}".format(random.randint(1, 99999))

# logger initialization
logger = Logger('modelhost-logger').get_logger('modelhost-logger')
logger.info('Starting Flask API...')

# authentication
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(Unauthorized())

# create server
server = Flask(__name__)
logger.info('... Flask API succesfully started')


model_list = listdir(MODEL_FOLDER)


# List with the models preloaded to do the inference and their information
session_list = []
# List with the index of the models on session_list
model_index = []
#TODO este for debería ir a un método de un utils
for i in model_list:
    sess = rt.InferenceSession(path.join(MODEL_FOLDER, i))
    model = onnx.load(path.join(MODEL_FOLDER, i))
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name

    num_inputs = sess.get_inputs()[0].shape[1]
    outputs = sess.get_outputs()[0].type
    model_type = model.graph.node[0].name
    description = model.doc_string
    full_description = {"inputs_type": input_name, "num_imputs": num_inputs, "outputs": outputs, "model_type": model_type,
                   "description": description}
    model_index.append(i)
    cosa = [i, sess, input_name, label_name, full_description]
    session_list.append(cosa)



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
def _test_frommaitre_send_kitchen(data):
    print(data)
    return HttpJsonResponse(200, http_status_description='recibido ' + data + ', prediccion desde kitchen (node:' + str(KITCHEN_NODE_UNIQ_ID) + ')').json()


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
    elif response:
        logger.info(response.get_json())

    return response


@server.route(path.join(MODELHOST_BASE_URL, 'models/<model_name>/prediction'), methods=['POST'])
def prediction(model_name):
    metric_manager.increment_model_counter()

    try:
        model_index.index(model_name)
    except Exception:
        return HttpJsonResponse(404, http_status_description=f'{model_name} does not exist. '
                                                             f'Visit GET {path.join(API_BASE_URL, "models")} '
                                                             f'for a list of avaliable model_index').json()

    # get new observation
    new_observation = request.json['values']
    pred = do_prediction(model_name, new_observation)

    return Prediction(200, http_status_description='Prediction successful', values=pred).json()


#TODO este do_prediction debería ir a un método de un utils (al ModelManager o algo similar)
# Function that makes the inference
def do_prediction(model, input):
    index = model_index.index(model)
    session = session_list[index][1]
    input_names = session_list[index][2]
    output_names = session_list[index][3]

    pred = session.run(
        [output_names],
        {input_names: [input]}
    )[0]
    return pred


@server.route(path.join(MODELHOST_BASE_URL, 'information'), methods=['GET'])
def get_model_information():
    model_name = request.json['model']
    index = model_index.index(model_name)
    desc = session_list[index][4]
    return Description(200, http_status_description='Model description', description=desc).json()


@server.route(path.join(MODELHOST_BASE_URL, 'information'), methods=['POST'])
def model_post_information():
    model_name = request.json['model']
    model_path = path.join(MODEL_FOLDER, model_name)
    model_description = request.json['model_description']
    index = model_index.index(model_name)
    model = onnx.load(model_path)
    model.doc_string = model_description
    session_list[index][4]["description"] = model_description
    onnx.save(model, model_path)
    return HttpJsonResponse(200, http_status_description='success').json()


##TODO:
# Upload model
# @server.route(path.join(API_BASE_URL, 'model_index/<model_name>'), methods=['PUT'])
# def upload_model(model_name):
#
#
# # Download model
# @server.route(path.join(API_BASE_URL, 'model_index/<model_name>'), methods=['GET'])
# def download_model(model_name):
#
#
# # Delete model
# @server.route(path.join(API_BASE_URL, 'model_index/<model_name>'), methods=['DELETE'])
# def delete_model(model_name):


if __name__ == '__main__':
    server.run()
