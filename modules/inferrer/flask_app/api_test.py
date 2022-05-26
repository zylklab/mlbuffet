from app import server
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

    logger.info('FlaskAPI:: requests_count() method')
    test_requests_count()


# Functions calling the API for method testing.
# Whenever a new method is added to the API, it should be added to the test script

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


def test_requests_count():
    response = server.test_client().get(
        '/metrics',
    )
    assert response.status_code == 200

    content = next(response.response)
    assert content is not None


if __name__ == '__main__':
    test_inferrer_api()
