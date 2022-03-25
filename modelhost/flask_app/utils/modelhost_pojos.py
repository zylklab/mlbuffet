from flask import jsonify
from numpy import ndarray
from werkzeug.exceptions import default_exceptions
from werkzeug.http import HTTP_STATUS_CODES


class HttpJsonResponse:
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None):
        # TODO: not jic; check if not (X or Y)
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
                 values=None):
        super().__init__(http_status_code, http_status_name, http_status_description)

        if values is None:
            values = []
        try:
            values = values.tolist()
        except AttributeError:
            values = list(values)

        self.data['values'] = values


class ModelList(HttpJsonResponse):
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None,
                 model_list=None):
        super().__init__(http_status_code, http_status_name, http_status_description)

        if model_list is None:
            model_list = []

        self.data['model_list'] = model_list


class ModelInformation(HttpJsonResponse):
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None,
                 description: str = '',
                 input_name: str = None,
                 num_inputs: ndarray = None,
                 output_name: int = None,
                 model_type: str = ''):
        super().__init__(http_status_code, http_status_name, http_status_description)

        self.data['input_name'] = input_name
        self.data['num_inputs'] = num_inputs
        self.data['output_name'] = output_name
        self.data['description'] = description
        self.data['model_type'] = model_type


class ModelListInformation(HttpJsonResponse):
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None,
                 list_descriptions: list = None):
        super().__init__(http_status_code, http_status_name, http_status_description)

        self.data['model_list_description'] = list_descriptions
