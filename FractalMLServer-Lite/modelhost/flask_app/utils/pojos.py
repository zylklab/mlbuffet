from flask import jsonify
from numpy import ndarray
from werkzeug.exceptions import default_exceptions
from werkzeug.http import HTTP_STATUS_CODES


class HttpJsonResponse:
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None):

        # compute just in case values if not specified
        if http_status_code in default_exceptions:  # if provided code belongs to a http exception
            exception = default_exceptions[http_status_code]()
            jic_http_status_name = exception.name
            jic_http_status_description = exception.description
        else:
            jic_http_status_name = jic_http_status_description = HTTP_STATUS_CODES.get(http_status_code, '')

        # if status name was not specified
        if not http_status_name:
            http_status_name = jic_http_status_name

        # if status description was not specified
        if not http_status_description:
            http_status_description = jic_http_status_description

        http_status = dict()
        http_status['code'] = http_status_code
        http_status['name'] = http_status_name
        http_status['description'] = http_status_description

        self.data = dict()
        self.data['http_status'] = http_status

    def json(self):
        return jsonify(**self.data), self.data['http_status']['code']


class Prediction(HttpJsonResponse):
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None,
                 values: ndarray = None):
        super().__init__(http_status_code, http_status_name, http_status_description)

        self.data['values'] = [] if values is None else values.tolist()


class Description(HttpJsonResponse):
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None,
                 description: {} = None):
        super().__init__(http_status_code, http_status_name, http_status_description)

        self.data['description'] = description


class ModelList(HttpJsonResponse):
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None,
                 model_list=None):
        if model_list is None:
            model_list = []

        super().__init__(http_status_code, http_status_name, http_status_description)

        self.data['model_list'] = model_list


class ModelInformation(HttpJsonResponse):
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None,
                 description: str = '',
                 inputs_type: str = None,
                 num_inputs: ndarray = None,
                 outputs: int = None,
                 model_type: str = ''):
        super().__init__(http_status_code, http_status_name, http_status_description)

        self.data['inputs_type'] = inputs_type
        self.data['num_inputs'] = num_inputs
        self.data['outputs'] = outputs
        self.data['description'] = description
        self.data['model_type'] = model_type
