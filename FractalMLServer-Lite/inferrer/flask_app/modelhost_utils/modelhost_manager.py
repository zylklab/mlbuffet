import asyncio
import aiohttp
import requests
from aiohttp import ClientSession
from aiohttp.web_exceptions import HTTPError
import os
import json
import time


# TODO revisar ests imports
# from modelhost_utils.modelhost_query_utils import ModelhostQueryUtils
# import modelhost_query_utils as kUtils

class ModelhostClientManager:
    """Esta clase se encarga de crear las corutines que van llamar a los metodos de Modelhost. Articulo recomendado
    sobre asyncio y ejemplos https://realpython.com/async-io-python/ """

    def __init__(self):
        self.modelhostUtils = ModelhostQueryUtils()

    def get_modelhost_predictions(self, model, observation_list):
        t0 = round(time.time() * 1000)
        # llamada a la ejecucion asincrona de modelhost    #toda esta gestion del loop se podria sustituir por
        # asyncio.run()
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            predictions = loop.run_until_complete(self.modelhostUtils.get_modelhost_predictions(model, observation_list))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        print("modelhost get_modelhost_predictions() call elapsed time: " + str(t1 - t0) + " ms")  # TODO logger
        return predictions

    def get_modelhost_info(self, model):
        t0 = round(time.time() * 1000)
        # llamada a la ejecucion asincrona de modelhost    #toda esta gestion del loop se podria sustituir por
        # asyncio.run()
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            predictions = loop.run_until_complete(self.modelhostUtils.get_modelhost_info(model))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        print("modelhost get_modelhost_info() call elapsed time: " + str(t1 - t0) + " ms")  # TODO logger
        return predictions

    def post_modelhost_info(self, model, description):
        t0 = round(time.time() * 1000)
        # llamada a la ejecucion asincrona de modelhost    #toda esta gestion del loop se podria sustituir por
        # asyncio.run()
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            predictions = loop.run_until_complete(self.modelhostUtils.post_modelhost_info(model, description))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        print("modelhost get_modelhost_info() call elapsed time: " + str(t1 - t0) + " ms")  # TODO logger
        return predictions

    # TODO def get_modelhost_descriptions(self, model_list):


class ModelhostQueryUtils:
    """Esta clase define las corutinas (ASYNC) que realiza las llamadas al endpoint que comunica con Modelhost"""

    def __init__(self):
        self.LOAD_BALANCER_ENDPOINT = os.getenv('LOAD_BALANCER_ENDPOINT')
        self.URL_PREFIX = 'http://'

    """ASYNC MODELHOST METHODS"""

    # async def get_modelhost_predictions(self, observation_list):
    #     URL_METHOD = '/test/inferrer/get/'
    #     url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD
    #
    #     # debug --
    #     url = 'http://172.24.0.3:8000' + URL_METHOD
    #     # -- debug
    #
    #     # ejecuta todas las queries juntas con gather (una query por cada prediccion)
    #     async with aiohttp.ClientSession() as session:
    #         return await asyncio.gather(
    #             *[self.get_query_async(observation, session, url) for observation in observation_list])

    async def get_modelhost_predictions(self, model, observation_list):
        URL_METHOD = '/test/inferrer/' + model + '/prediction'
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug

        # ejecuta todas las queries juntas con gather (una query por cada prediccion)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_query_async(observation_list, session, url)])

    async def get_modelhost_info(self, model):
        URL_METHOD = "/test/inferrer/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug
        data = {"model": model}
        # ejecuta todas las queries juntas con gather (una query por cada prediccion)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.get_query_async(data=data, session=session, url=url)])

    async def post_modelhost_info(self, model, description):
        URL_METHOD = "/test/inferrer/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug
        data = {"model": model, "model_description":description}
        # ejecuta todas las queries juntas con gather (una query por cada prediccion)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_query_async(data=data, session=session, url=url)])


    # TODO async def get_modelhost_descriptions(self, model_list):

    """ASYNC HTTP QUERIES"""

    # async def get_query_async(self, observation, session, url):
    #     endpoint = url + observation
    #     print(endpoint)
    #     resp = await session.request(method="GET", url=endpoint)
    #     resp.raise_for_status()
    #     print("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
    #     prediction_data = await resp.text()
    #     return prediction_data

    # TODO async def post_query_async(self, observation, session, url, payload):
    async def post_query_async(self, data, session, url):
        endpoint = url
        resp = await session.post(url=endpoint, headers={"Content-Type": "application/json"},
                                  json=data)
        resp.raise_for_status()
        print("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
        prediction_data = await resp.text()
        return prediction_data

    async def get_query_async(self, data, session, url):
        endpoint = url
        resp = await session.get(url=endpoint, headers={"Content-Type": "application/json"},
                                 json=data)
        resp.raise_for_status()
        print("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
        prediction_data = await resp.text()
        return prediction_data
