from typing import Tuple

from flask import jsonify, Response
from werkzeug.exceptions import default_exceptions
from werkzeug.http import HTTP_STATUS_CODES


class HttpJsonResponse:
    def __init__(self,
                 http_status_code: int,
                 http_status_name: str = None,
                 http_status_description: str = None):

        self.data = dict()

        # create response content
        http_status = dict()
        http_status['code'] = http_status_code

        # if status name was specified
        if http_status_name:
            http_status['name'] = http_status_name
        else:
            if http_status_code in default_exceptions:  # if provided code belongs to a http exception
                http_status['name'] = default_exceptions[http_status_code]().name
            else:
                http_status['name'] = HTTP_STATUS_CODES.get(http_status_code, '')

        # if status description was specified
        if http_status_description:
            http_status['description'] = http_status_description
        else:
            if http_status_code in default_exceptions:  # if provided code belongs to a http exception
                http_status['description'] = default_exceptions[http_status_code]().description
            else:
                http_status['description'] = HTTP_STATUS_CODES.get(http_status_code, '')

        self.data['http_status'] = http_status

    def get_response(self) -> Tuple[Response, int]:
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
