from os import path, getenv
import re

from numpy import require
from flask import request

UPLOADS_DIR = '/tmp'

def start_training(train_script, requirements, dataset):
    print(train_script.filename)
    print(requirements.filename)
    print(dataset.filename)
    train_script.save(path.join(UPLOADS_DIR, train_script.filename))
    requirements.save(path.join(UPLOADS_DIR, requirements.filename))
    dataset.save(path.join(UPLOADS_DIR, dataset.filename))
