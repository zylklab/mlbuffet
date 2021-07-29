import json
from os.path import join

from app import API_BASE_URL, server, MODEL_FOLDER
from utils.container_logger import Logger


def test_inferrer_api():
    # logger initialization
    logger = Logger("flask-api-test-logger").get_logger('TEST-API')
    logger.info('TEST:: Starting Flask API Tests...')

    logger.info('FlaskAPI:: hello_world() method')
    test_hello_world()

    logger.info('FlaskAPI:: show_help() method')
    test_show_help()

    logger.info('FlaskAPI:: get_test() method')
    test_get_test()

    ### TODO: These methods need modelhosts to be deployed,which are not up at container building stage ###
    # logger.info('FlaskAPI:: get_test_sendtomodelhost() method')
    # test_get_test_sendtomodelhost()
    #
    # logger.info('FlaskAPI:: get_model_list() method')
    # get_model_list()
    #
    # logger.info('FlaskAPI:: get_model_list_info() method')
    # get_model_list_info()
    #
    # logger.info('FlaskAPI:: get_update_model_list() method')
    # get_update_model_list()
    #
    # logger.info('FlaskAPI:: upload_model() method')
    # test_upload_model()
    #
    # logger.info('FlaskAPI:: download_model() method')
    # test_download_model()
    #
    # logger.info('FlaskAPI:: delete_model() method')
    # test_delete_model()
    #
    # logger.info('FlaskAPI:: get_prediction() method')
    # test_get_prediction()

    # TODO Review different versions of sklearn requirements
    # logger.info('FlaskAPI:: sklearn2onnx_conversor() method')
    # test_sklearn2onnx_conversor()

    logger.info('FlaskAPI:: requests_count() method')
    test_requests_count()

#Functions calling the API for method testing.
#Whenever a new method is added to the API, it should be added to the test script

def test_hello_world():
    response = server.test_client().get(
        '/'
    )
    assert response.status_code == 200

def test_show_help():
    response = server.test_client().get(
        '/help'
    )
    assert response.status_code == 200

def test_get_test():
    response = server.test_client().get(
        '/api/test'
    )
    assert response.status_code == 200

### TODO: These methods need modelhosts to be deployed,which are not up at container building stage ###
# def test_get_test_sendtomodelhost():
#     response = server.test_client().get(
#         '/api/test/sendtomodelhost'
#     )
#     assert response.status_code == 200
#
# def get_model_list():
#     url = join(API_BASE_URL, 'models')
#     response = server.test_client().get(
#         url
#     )
#     assert response.status_code == 200
#     content = json.loads(next(response.response))
#     return content
#
# def get_model_list_info():
#     url = join(API_BASE_URL, 'models/information')
#     response = server.test_client().get(
#         url
#     )
#     assert response.status_code == 200
#
# def get_update_model_list():
#     response = server.test_client().get(
#         '/models/update'
#         )
#     assert response.status_code == 200
#
# def test_upload_model():
#     initial_models = get_model_list()
#     new_model_name = 'testmodel.pkl'
#     url = join(API_BASE_URL, 'models', new_model_name)
#
#     response = server.test_client().put(
#         url,
#         buffered=True,
#         data={'path': open(join(MODEL_FOLDER, 'model-randomforest.pkl'), 'rb')}
#     )
#     assert response.status_code == 201
#
#     final_models = get_model_list()
#     assert (set(final_models) - set(initial_models)).pop() == new_model_name
#
# def test_delete_model():
#     initial_models = get_model_list()
#     model_to_delete = 'testmodel.pkl'
#     url = join(API_BASE_URL, 'models', model_to_delete)
#
#     response = server.test_client().delete(
#         url
#     )
#     assert response.status_code == 204
#
#     final_models = get_model_list()
#     assert (set(initial_models) - set(final_models)).pop() == model_to_delete
#
# def test_download_model():
#     model_name = 'testmodel.pkl'
#     url = join(API_BASE_URL, 'models', model_name)
#
#     response = server.test_client().get(
#         url
#     )
#     assert response.status_code == 200
#
#     data = response.get_data()
#     assert len(data) > 0
#
# def test_get_prediction():
#     url = join(API_BASE_URL, 'models/iris.onnx/prediction')
#     response = server.test_client().post(
#         url,
#         data=json.dumps({'values': [7.0, 3.2, 4.7, 1.4]}),
#         content_type='application/json'
#     )
#     assert response.status_code == 200
#
#     content = json.loads(next(response.response))
#     assert content['values'] is not None
#
# def test_sklearn2onnx_conversor():
#     url = join(API_BASE_URL, 'models/model-randomforest-backup.pkl/to-onnx')
#     response = server.test_client().post(
#         url,
#         data=json.dumps(
#             {'features': 4}),
#         content_type='application/json'
#     )
#     assert response.status_code == 200

def test_requests_count():
    response = server.test_client().get(
        '/metrics',
    )
    assert response.status_code == 200

    content = next(response.response)
    assert content is not None

if __name__ == '__main__':
    test_inferrer_api()
