from os import path, getcwd
import shutil
import requests

URI_SCHEME = 'http://'


def unzip_models(file_name):
    shutil.unpack_archive(file_name, getcwd())
    return 'Unzipped'


def _url(resource):
    return URI_SCHEME + 'storage:8000' + resource


def _get(resource):
    return requests.get(_url(resource)).json()


def get_tag_library(tag):
    resource = '/storage/models/' + tag + '/library'
    return _get(resource)


def get_model_library(file_name):

    resource = '/storage/models/' + file_name + '/library'
    return _get(resource)['ml_library']
