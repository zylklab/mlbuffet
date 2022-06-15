from os import path
import shutil
import requests
from zipfile import ZipFile


URI_SCHEME = 'http://'


def unzip_models(file_name):
    zip_ = ZipFile(file_name)
    zip_.extractall()
    return zip_.namelist()


def _url(resource):
    return URI_SCHEME + 'storage:8000' + resource


def _get(resource):
    return requests.get(_url(resource)).json()


def get_model_library(tag):
    resource = '/storage/models/' + tag + '/library'
    return _get(resource)['ml_library']
