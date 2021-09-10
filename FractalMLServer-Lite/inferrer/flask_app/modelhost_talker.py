from json import JSONDecodeError
from os import path, getenv

import gevent
import requests

from utils.inferer_pojos import HttpJsonResponse

# Request constants
#LOAD_BALANCER_ENDPOINT = getenv('LOAD_BALANCER_ENDPOINT')
MODELHOST_ENDPOINT = getenv('MODELHOST_ENDPOINT')
URI_SCHEME = 'http://'

def _url(resource):
#    return URI_SCHEME + LOAD_BALANCER_ENDPOINT + resource
    return URI_SCHEME + MODELHOST_ENDPOINT + ":8000" + resource


def _is_ok(code):
    return str(code).startswith('2')


def _get(resource):
    return requests.get(_url(resource)).json()


def _post(resource, json_data):
    response = requests.post(_url(resource), json=json_data).json()
    # if _is_ok(response['http_status']['code']): TODO: why update the list of the models after post something?
    #     update_models()
    return response


def _put(resource, files):
    response = requests.put(_url(resource), files=files).json()
    if _is_ok(response['http_status']['code']):
        update_models()
    return response


def _delete(resource):
    raw_response = requests.delete(_url(resource))
    try:
        response = raw_response.json()
        if _is_ok(response['http_status']['code']):
            update_models()
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


def make_a_prediction(model_name, new_observation, type_observation):  # TODO: for example here update wouldn't be necessary WHERE TO CALL
    resource = f'/modelhost/models/{model_name}/prediction'
    return _post(resource, {'values': new_observation, 'type_observation': type_observation})


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
    resource = '/modelhost/api/test'

    jobs = [gevent.spawn(_get, path.join(resource, str(elem))) for elem in data_array]
    gevent.wait(jobs)

    # Print modelhosts responses and check if all HTTP codes are 2XX
    all_responses_2xx = True
    for job in jobs:
        if not _is_ok(job.value['http_status']['code']):
            all_responses_2xx = False

        print(f'Received response: {job.value}')

    if all_responses_2xx:
        return HttpJsonResponse(200).json()
    return HttpJsonResponse(500, http_status_description='One or more modelhosts returned non 2XX HTTP code').json()


def update_models():
    resource = '/modelhost/models/update'
#TODO AQUÍ HAY QUE VER QUÉ DECISIÓN TOMAMOS PARA QUE TODAS LAS RÉPLICAS DE MODELHOST SE ACTUALICEN A LA VEZ.

    for i in range(NUMBER_OF_MODELHOSTS):  # TODO load balancer instead of this loop
        ip = getenv(f'MODELHOST_{i + 1}_IP') + ':8000' #TODO WE DONT KNOW MODELHOST IPS ONCE SWARM GETS IN CONTROL
        url = URI_SCHEME + ip + resource
        data = None
        # TODO why post
        gevent.spawn(requests.post, url=url, json=data)  # do not wait for them to finish

    return HttpJsonResponse(200).json()
