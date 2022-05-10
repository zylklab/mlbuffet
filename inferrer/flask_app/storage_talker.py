import io
from json import JSONDecodeError
from os import path, getenv

import gevent
import requests
from flask import send_file

from utils.inferer_pojos import HttpJsonResponse
from utils.ipscan import IPScan

# Request constants
OVERLAY_NETWORK = getenv('OVERLAY_NETWORK')
URI_SCHEME = 'http://'


def _url(resource):
    return URI_SCHEME + 'storage:8000' + resource


def _is_ok(code):
    return str(code).startswith('2')


def _get(resource):
    return requests.get(_url(resource)).json()


def _download(resource):
    file = requests.get(_url(resource), stream=True)
    return file


def _post(resource, json_data):
    response = requests.post(_url(resource), json=json_data).json()
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


def upload_new_model(tag, file, file_name, description):
    resource = '/storage/model/' + tag
    files = [('path', file), ('model_description',
                              description), ('filename', file_name)]
    update_models()
    return _put(resource, files)


def delete_model(tag):
    resource = '/storage/model/' + tag
    return _delete(resource)


def download_model(tag):
    resource = '/storage/model/' + tag

    response = _download(resource)
    status = response.status_code
    if not _is_ok(status):
        response_out = response
    else:
        file = io.BytesIO(response.content)
        response_out = send_file(file,
                                 mimetype='application/octet-stream',
                                 as_attachment=True,
                                 download_name=response.headers['Content-Disposition'].split('=')[1])
    return response_out


def set_default_model(tag, new_version):
    resource = '/storage/model/' + tag + '/default'
    json_data = {'default': new_version}
    update_models()
    return _post(resource, json_data)


def get_tag_information(tag):
    resource = '/storage/model/' + tag + '/information'
    return _get(resource)


def test_load_balancer(data_array):
    resource = '/storage/api/test'

    jobs = [gevent.spawn(_get, path.join(resource, str(elem)))
            for elem in data_array]
    gevent.wait(jobs)

    # Print modelhosts responses and check if all HTTP codes are 2XX
    all_responses_2xx = True
    for job in jobs:
        if not _is_ok(job.value['http_status']['code']):
            all_responses_2xx = False

        print(f'Received response: {job.value}')

    if all_responses_2xx:
        return HttpJsonResponse(200).get_response()
    return HttpJsonResponse(
        500, http_status_description='One or more modelhosts returned non 2XX HTTP code').get_response()


def update_models():
    resource = '/modelhost/updatemodels'

    MODELHOST_IP_LIST = IPScan('modelhost')
    for IP in MODELHOST_IP_LIST:
        url = URI_SCHEME + IP + ":8000" + resource
        print(url)
        gevent.spawn(requests.get, url=url)
    return HttpJsonResponse(200).get_response()
