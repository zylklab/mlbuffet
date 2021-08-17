from json import JSONDecodeError
from os import path, getenv

import gevent
import requests

from utils.inferer_pojos import HttpJsonResponse

# Request constants
LOAD_BALANCER_ENDPOINT = getenv('LOAD_BALANCER_ENDPOINT')
URI_SCHEME = 'http://'
try:
    NUMBER_OF_MODELHOSTS = int(getenv('NUMBER_MODELHOST_NODES'))
except TypeError:
    pass


def _url(resource):
    return URI_SCHEME + LOAD_BALANCER_ENDPOINT + resource


def _get(resource):
    return requests.get(_url(resource)).json()


def _post(resource, json_data):
    response = requests.post(_url(resource), json=json_data).json()
    update_models()
    return response


def _put(resource, files):
    response = requests.put(_url(resource), files=files).json()
    update_models()
    return response


def _delete(resource):
    raw_response = requests.delete(_url(resource))
    try:
        response = raw_response.json()
    except JSONDecodeError:
        response = raw_response.text

    update_models()
    return response


def get_list_of_models():
    resource = '/modelhost/models'
    return _get(resource)


def get_information_of_all_models():
    resource = '/modelhost/models/information'
    return _get(resource)


def get_information_of_a_model(model_name):
    resource = f'/modelhost/{model_name}/information'
    return _get(resource)


def make_a_prediction(model_name, new_observation):
    resource = f'/modelhost/models/{model_name}/prediction'
    return _post(resource, {'values': new_observation})


def write_model_description(model_name, description):
    resource = f'/modelhost/{model_name}/information'
    return _post(resource, {'model_description': description})


def upload_new_model(model_name, new_model):
    resource = '/modelhost/models/' + model_name
    return _put(resource, {'model': new_model})


def delete_model(model_name):
    resource = '/modelhost/models/' + model_name
    return _delete(resource)


def test_load_balancer(data_array):
    resource = '/api/test/frominferrer/get'

    jobs = [gevent.spawn(_get, path.join(resource, str(elem))) for elem in data_array]
    gevent.wait(jobs)

    # Print modelhosts responses and check if all HTTP codes are 2XX
    all_responses_200 = True
    for job in jobs:
        modelhost_response = job.value.json()

        if 200 > modelhost_response['http_status']['code'] > 299:
            all_responses_200 = False

        print(modelhost_response)  # TODO: prettier?

    if all_responses_200:
        return HttpJsonResponse(200).json()
    return HttpJsonResponse(500, http_status_description='One or more modelhosts returned non 2XX HTTP code')


def update_models():
    resource = '/modelhost/models/update'
    # The update_modelhost_models() method must be called everytime a change has occured on the model list

    for i in range(NUMBER_OF_MODELHOSTS):  # TODO load balancer instead of this loop
        ip = getenv(f'MODELHOST_{i + 1}_IP') + ':8000'
        url = URI_SCHEME + ip + resource
        data = None
        # TODO why post
        return requests.post(url, data=data).json()
