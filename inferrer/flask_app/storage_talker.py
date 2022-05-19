import io
from json import JSONDecodeError
from os import getenv
import requests
from flask import send_file


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
    return response


def _delete(resource):
    raw_response = requests.delete(_url(resource))
    try:
        response = raw_response.json()
    except JSONDecodeError:
        response = raw_response.text

    return response


def upload_new_model(tag, file, file_name, description):
    resource = '/storage/model/' + tag
    files = [('path', file), ('model_description',
                              description), ('filename', file_name)]
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
    return _post(resource, json_data)


def get_tag_information(tag):
    resource = '/storage/model/' + tag + '/information'
    return _get(resource)


def get_model_list():
    resource = '/storage/models'
    return _get(resource)


def update_models():
    resource = '/storage/updatemodels'
    return _get(resource)
