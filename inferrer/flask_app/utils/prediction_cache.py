import hashlib
import json
import redis
from utils.container_logger import Logger
from os import getenv


if getenv('ORCHESTRATOR') == 'KUBERNETES':
    REDIS_HOST = 'cache'
else:
    REDIS_HOST = 'mlbuffet_cache'

REDIS_PORT = 6379

redis_cli = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


logger = Logger('inferrer').get_logger('cache')


def get_hash(model_name, inputs):
    input_string = ' '.join(str(e) for e in inputs)
    hash_func_input = (model_name + input_string).encode('utf-8')
    return hashlib.blake2b(hash_func_input).hexdigest()


def get_prediction(hash_code):
    try:
        result = redis_cli.get(hash_code)
        if result is not None:
            result = json.loads(result)
        else:
            result = None
        return result
    except redis.exceptions.RedisError as re:
        re_str = str(re)
        logger.info(re_str)
        result = None
        return result


# Write prediction as json format
def put_prediction_in_cache(hash_code, prediction):
    j_prediction = json.dumps(prediction)
    try:
        redis_cli.set(hash_code, j_prediction)
    except redis.exceptions.RedisError as re:
        re_str = str(re)
        logger.info(re_str)
