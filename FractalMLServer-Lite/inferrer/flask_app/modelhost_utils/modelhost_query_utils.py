import asyncio
import aiohttp
import requests
from aiohttp import ClientSession
from aiohttp.web_exceptions import HTTPError
import os
import json
import time


class ModelhostQueryUtils:
    def __init__(self):
        self.LOAD_BALANCER_ENDPOINT = os.getenv('LOAD_BALANCER_ENDPOINT')
        self.URL_PREFIX = 'http://'

    def print_metadata(self):
        print('-----------> ' + self.LOAD_BALANCER_ENDPOINT)

    async def get_modelhost_predictions(self, observation_list):
        URL_METHOD = '/test/inferrer/get/'
        # url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD
        url = 'http://172.24.0.3:8000/test/inferrer/get/'
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.get_query_async(observation, session, url) for observation in observation_list])

    # TODO
    # async def get_modelhost_descriptions(self, model_list):

    async def get_query_async(self, observation, session, url):
        endpoint = url + observation
        async with session.get(endpoint) as response:
            print(response.status)
            prediction_data = await response.text()
            return prediction_data

    # TODO
    # async def post_query_async(self, observation, session, url, payload):
