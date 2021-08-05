import json
from os.path import join

from app import API_BASE_URL, server, MODEL_FOLDER, MODELHOST_BASE_URL
from utils.container_logger import Logger

def test_modelhost():
    # logger initialization
    logger = Logger("flask-api-test-logger").get_logger('TEST-API')
    logger.info('TEST:: Starting Flask API Tests...')

    logger.info('FlaskAPI:: hello_world() method')
    test_hello_world()

    logger.info('FlaskAPI:: get_test() method')
    test_get_test()

    logger.info('FlaskAPI:: model_list method')
    get_model_list()

    logger.info('FlaskAPI:: model_list_information() method')
    get_model_list_information()

    logger.info('FlaskAPI:: upload_model() method')
    upload_model()

    logger.info('FlaskAPI:: delete_model() method')
    delete_model()

    logger.info('FlaskAPI:: get_prediction() method')
    test_get_prediction()





    logger.info('FlaskAPI:: requests_count() method')
    test_requests_count()

def test_hello_world():
    response = server.test_client().get(
        '/'
    )
    assert response.status_code == 200

def test_get_test():
    response = server.test_client().get(
        '/api/test'
    )
    assert response.status_code == 200

def get_model_list():
    url = join(MODELHOST_BASE_URL, 'models')
    response = server.test_client().get(
        url
    )
    assert response.status_code == 200
    content = json.loads(next(response.response))
    return content['description']

def get_model_list_information():
    url = join(MODELHOST_BASE_URL, 'models/information')
    response = server.test_client().get(
        url
    )
    assert response.status_code == 200
    content = json.loads(next(response.response))
    return content['description']

def upload_model():
    initial_models = get_model_list()
    new_model_name = 'testmodel.onnx'
    url = join(MODELHOST_BASE_URL, 'models/upload_' + new_model_name)

    filepath = join(MODEL_FOLDER, new_model_name)
    f = open(filepath, "wb")
    f.close()

    response = server.test_client().post(
        url,
        buffered=True,
        data={'file': open(filepath, 'rb')}
    )
    assert response.status_code == 200

def delete_model():
    initial_models = get_model_list()
    model_to_delete = 'testmodel.onnx'

    url = join(MODELHOST_BASE_URL, 'models/delete_' + model_to_delete)
    response = server.test_client().delete(
        url
    )
    assert response.status_code == 200

def test_get_prediction():
    url = join(MODELHOST_BASE_URL, 'models/iris.onnx/prediction')
    response = server.test_client().post(
        url,
        data=json.dumps({'values': [7.0, 3.2, 4.7, 1.4]}),
        content_type='application/json'
    )
    assert response.status_code == 200

    content = json.loads(next(response.response))
    assert content['values'] is not None

def test_requests_count():
    response = server.test_client().get(
        '/metrics',
        headers=[('Authorization', 'Bearer password')]
    )
    assert response.status_code == 200

    content = next(response.response)
    assert content is not None




if __name__ == '__main__':
    test_modelhost()
