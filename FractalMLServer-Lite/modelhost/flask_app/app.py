from os import getcwd, path, remove, listdir
from pathlib import Path
import asyncio
import onnx
import onnxruntime as rt
from flask import Flask, request, send_file, Response
from flask_httpauth import HTTPTokenAuth
from werkzeug.exceptions import HTTPException, Unauthorized
from werkzeug.utils import secure_filename

from utils import metric_manager, index, sklearn_conversor
from utils.container_logger import Logger
from utils.pojos import HttpJsonResponse, Prediction, ModelList, ModelInformation, Description

# TODO: poner más métricas de prometheus por ahí

# constant variables
API_BASE_URL = '/api/v1/'
ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'tar', 'onnx', 'pkl']
MODEL_FOLDER = path.join(getcwd(), 'models')
auth_token = 'password'  # TODO: https://github.com/miguelgrinberg/Flask-HTTPAuth/blob/main/examples/token_auth.py

# logger initialization
logger = Logger('flask-app').get_logger('flask-logger')
logger.info('Starting Flask API...')

# authentication
auth = HTTPTokenAuth('Bearer')
auth.auth_error_callback = lambda *args, **kwargs: handle_exception(Unauthorized())

# create server
server = Flask(__name__)
logger.info('... Flask API succesfully started')

lista = ["iris.onnx", "diabetes.onnx"]

session_list = []
models = []
for i in lista:
    sess = rt.InferenceSession(path.join(MODEL_FOLDER, i))
    model = onnx.load(path.join(MODEL_FOLDER, i))
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name

    num_inputs = sess.get_inputs()[0].shape[1]
    outputs = sess.get_outputs()[0].type
    model_type = model.graph.node[0].name
    descripcion = model.doc_string
    description = {"inputs_type": input_name, "num_imputs": num_inputs, "outputs": outputs, "model_type": model_type,
                   "description": descripcion}
    models.append(i)
    cosa = [i, sess, input_name, label_name, description]
    session_list.append(cosa)



@auth.verify_token
def verify_token(token):
    return token == auth_token


@server.route('/', methods=['GET'])
def hello_world():
    return HttpJsonResponse(200, http_status_description='Greetings from Fractal - ML Server - ModelHost, the Machine Learning model server. Are you supposed to be reading this? Guess not. Go to Inferrer!'
                                                         'For more information, visit /help').json()


@server.route('/help', methods=['GET'])
def show_help():
    return index.header + index.help + '\n'


# Upload model
@server.route(path.join(API_BASE_URL, 'models/<model_name>'), methods=['PUT'])
def upload_model(model_name):
    model_name = secure_filename(model_name)

    # if there is no file
    if 'path' not in request.files:
        return HttpJsonResponse(422, http_status_description='No path specified').json()

    # get model
    model = request.files['path']

    # if file extension is not allowed
    if get_file_extension(model_name) not in ALLOWED_EXTENSIONS:
        return HttpJsonResponse(415, http_status_description=f'File extension not allowed. '
                                                             f'Please use one of these: {ALLOWED_EXTENSIONS}').json()

    # save the model
    model.save(path.join(MODEL_FOLDER, model_name))

    return HttpJsonResponse(201, http_status_description=f'{model_name} uploaded!').json()


# Download model
@server.route(path.join(API_BASE_URL, 'models/<model_name>'), methods=['GET'])
def download_model(model_name):
    model_name = secure_filename(model_name)

    model_path = path.join(MODEL_FOLDER, model_name)

    # check that file exists
    if path.isfile(model_path):
        logger.info(f'{model_name} model downloaded')
        return send_file(model_path, as_attachment=True)
    else:
        return HttpJsonResponse(404, http_status_description=f'{model_name} does not exist. '
                                                             f'Visit {path.join(API_BASE_URL, "models")} '
                                                             'for a list of avaliable models').json()


@server.route(path.join(API_BASE_URL, 'models/<model_name>'), methods=['DELETE'])
def delete_model(model_name):
    model_name = secure_filename(model_name)

    model_path = path.join(MODEL_FOLDER, model_name)

    # check that the model exists
    if path.isfile(model_path):
        remove(model_path)
        return HttpJsonResponse(204, http_status_description=f'{model_name} deleted!').json()
    else:
        return HttpJsonResponse(404, http_status_description=f'{model_name} does not exist').json()


@server.route(path.join(API_BASE_URL, 'models'), methods=['GET'])
def show():
    model_list = [file for file in listdir(MODEL_FOLDER) if get_file_extension(file) in ALLOWED_EXTENSIONS]

    return ModelList(200, model_list=model_list).json()


# Convert sklearn to onnx
@server.route(path.join(API_BASE_URL, 'models/<input_model_name>/to-onnx'), methods=['POST'])
def sklearn2onnx_conversor(input_model_name):
    input_model_name = secure_filename(input_model_name)

    # if the model is already in onnx format
    if get_file_extension(input_model_name) == 'onnx':
        return HttpJsonResponse(409, http_status_description=f'{input_model_name} is already in onnx format').json()

    # check that any json data has been provided
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {features:int}').json()

    input_model_path = path.join(MODEL_FOLDER, input_model_name)

    # check that file exists
    if not path.isfile(input_model_path):
        return HttpJsonResponse(404, http_status_description=f'{input_model_name} does not exist. '
                                                             f'Visit GET {path.join(API_BASE_URL, "models")} '
                                                             f'for a list of avaliable models').json()

    output_model_name = Path(input_model_name).stem + '.onnx'
    output_model_path = path.join(MODEL_FOLDER, output_model_name)

    # check that the number of features has been provided
    if 'features' not in request.json:
        return HttpJsonResponse(422, http_status_description='No number of features provided {features:int}').json()

    # get the number of features
    features = request.json['features']

    # check that it is an integer
    if not isinstance(features, int):
        return HttpJsonResponse(422, http_status_description='Number of features must be an integer').json()

    # convert model
    try:
        sklearn_conversor.to_onnx(input_model_path, output_model_path, features)
    except Exception as error:
        return HttpJsonResponse(500, http_status_description=str(error)).json()

    return HttpJsonResponse(200, http_status_description=f'{input_model_name} succesfully converted to '
                                                         f'{output_model_name}!').json()


@server.route(path.join(API_BASE_URL, 'models/<model_name>/information'), methods=['POST'])
def model_describe(model_name):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model_name)

    # check that any json data has been provided
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {model_description:string}').json()

    # check that model_description has been provided
    if 'model_description' not in request.json:
        return HttpJsonResponse(422, http_status_description='No model_description provided').json()

    # get model description
    model_description = request.json['model_description']

    # check that model_description is a string
    if not isinstance(model_description, str):
        return HttpJsonResponse(422, http_status_description='model_description must be a string').json()

    model_path = path.join(MODEL_FOLDER, model_name)

    # check that file exists
    if not path.isfile(model_path):
        return HttpJsonResponse(404, http_status_description=f'{model_name} does not exist. '
                                                             f'Visit {path.join(API_BASE_URL, "models")} '
                                                             f'for a list of avaliable models').json()

    # update model description
    model = onnx.load(model_path)
    model.doc_string = model_description
    onnx.save(model, model_path)

    return HttpJsonResponse(200, http_status_description=f'Model description updated! Visit '
                                                         f'GET {path.join(API_BASE_URL, model_name, "information")} '
                                                         f'to check available info about the current model').json()


@server.route(path.join(API_BASE_URL, 'models/<model_name>/information'), methods=['GET'])
def model_information(model_name):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model_name)

    model_path = path.join(MODEL_FOLDER, model_name)

    # check that file exists
    if not path.isfile(model_path):
        return HttpJsonResponse(404, http_status_description=f'{model_name} does not exist. '
                                                             f'Visit GET {path.join(API_BASE_URL, "models")} '
                                                             f'for a list of avaliable models').json()

    # If ONNX model, then get model session
    if get_file_extension(model_name) == 'onnx':
        # model = onnx.load(model_path)
        # num_inputs = model.graph.input[0].type.tensor_type.shape.dim[1].dim_value
        # inputs_type = model.graph.node[0].input
        # outputs = model.graph.node[0].output
        # model_type = model.graph.node[0].name
        # description = model.doc_string
        sess = rt.InferenceSession(model_path)
        num_inputs = sess.get_inputs()[0].shape[1]
        inputs_type = sess.get_inputs()[0].name
        outputs = sess.get_outputs()[0].type
        # description = sess.get_modelmeta().description
        model = onnx.load(model_path)
        model_type = model.graph.node[0].name
        description = model.doc_string

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


@server.route(path.join(API_BASE_URL, 'models/<model_name>/prediction'), methods=['POST'])
def get_prediction(model_name):
    metric_manager.increment_model_counter()
    model_name = secure_filename(model_name)

    # check that any json data has been provided
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {values:list}').json()

    model_path = path.join(MODEL_FOLDER, model_name)

    # check that file exists
    if not path.isfile(model_path):
        return HttpJsonResponse(404, http_status_description=f'{model_name} does not exist. '
                                                             f'Visit GET {path.join(API_BASE_URL, "models")} '
                                                             f'for a list of avaliable models').json()

    # check that the model is in onnx format
    if get_file_extension(model_name) != 'onnx':
        return HttpJsonResponse(
            409,
            http_status_description=f'{model_name} is not in onnx format. '
                                    f'Please convert it first visiting '
                                    f'POST {path.join(API_BASE_URL, "models", model_name, "to-onnx")}'
        ).json()

    # check that an observation has been provided
    if 'values' not in request.json:
        return HttpJsonResponse(422, http_status_description='No test observation provided (values:[...])').json()

    # get new observation
    new_observation = request.json['values']

    # validate new observation
    if not isinstance(new_observation, list):
        return HttpJsonResponse(422, http_status_description='New observation is not a list enclosed by'
                                                             ' squared brackets').json()
    try:
        # get model session
        sess = rt.InferenceSession(model_path)
        input_name = sess.get_inputs()[0].name
        label_name = sess.get_outputs()[0].name

        # get prediction
        pred = sess.run(
            [label_name],
            {input_name: [new_observation]}
        )[0]
        return Prediction(200, http_status_description='Prediction successful', values=pred).json()
    except Exception as error:
        return HttpJsonResponse(500, http_status_description=str(error)).json()


@server.route('/api/test', methods=['GET'])
def get_test():
    metric_manager.increment_test_counter()

    return HttpJsonResponse(200).json()


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


# TODO estos metodos sueltos a un utils
def get_file_extension(file_name):
    return Path(file_name).suffix[1:].lower()


"""Metodo de ejemplo para responder a las queries del modelhostManager
     - simula el get predictions
     - deberia ser POST en vez de GET para las predictions, esto hay que dejarlo fino
"""


# @server.route('/test/inferrer/get/<data>', methods=['GET'])
# def test_send_modelhost(data):
#     print(data)
#     return HttpJsonResponse(200, http_status_description='recibido ' + data + ', prediccion desde modelhost').json()

@server.route('/test/inferrer/get', methods=['POST'])
def test_send_modelhost():
    # data = request.json("values")
    data = request.json["values"]
    pred = do_prediction(data)
    print(data)
    return HttpJsonResponse(200, http_status_description=str(pred)).json()


@server.route("/test/inferrer/<model_name>/prediction", methods=['POST'])
def prediction(model_name):
    metric_manager.increment_model_counter()

    # check that any json data has been provided
    if not request.json:
        return HttpJsonResponse(422, http_status_description='No json data provided {values:list}').json()
    if 'values' not in request.json:
        return HttpJsonResponse(422, http_status_description='No test observation provided (values:[...])').json()

        # get new observation
    new_observation = request.json['values']
    # validate new observation
    if not isinstance(new_observation, list):
        return HttpJsonResponse(422, http_status_description='New observation is not a list enclosed by'
                                                             ' squared brackets').json()
    pred = do_prediction(model_name, new_observation)

    return Prediction(200, http_status_description='Prediction successful', values=pred).json()


def do_prediction(model, input):
    index = models.index(model)
    session = session_list[index][1]
    input_names = session_list[index][2]
    output_names = session_list[index][3]

    pred = session.run(
        [output_names],
        {input_names: [input]}
    )[0]
    return pred


@server.route("/test/inferrer/information", methods=['GET'])
def test_model_information():
    model_name = request.json['model']
    index = models.index(model_name)
    desc = session_list[index][4]
    return Description(200, http_status_description='Model description', description=desc).json()


@server.route("/test/inferrer/information", methods=['POST'])
def test_model_post_information():
    model_name = request.json['model']
    model_path = path.join(MODEL_FOLDER, model_name)
    model_description = request.json['model_description']
    index = models.index(model_name)
    model = onnx.load(model_path)
    model.doc_string = model_description
    session_list[index][4]["description"] = model_description

    onnx.save(model, model_path)
    return HttpJsonResponse(200, http_status_description='success').json()


# Comentar para que funcione en docker. Descomentar para local
if __name__ == '__main__':
    server.run()
