import asyncio
import aiohttp
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
import os
import time


class ModelhostClientManager:
    """This class is responsible for creating the coroutines which have been called by the Modelhost methods. Article
    recommended about asyncio and examples: https://realpython.com/async-io-python/ """

    def __init__(self):
        self.modelhostUtils = ModelhostQueryUtils()
        self.modelhostLogger = Logger

        self.logger = Logger("manager_logger").get_logger("manager_logger")

    def get_modelhost_predictions(self, model, observation_list):
        t0 = round(time.time() * 1000)
        # Call to the asynchronous execution of modelhost

        loop = asyncio.new_event_loop()
        try:
            observation = {"values":observation_list}
            prediction = loop.run_until_complete(
                self.modelhostUtils.get_modelhost_predictions(model, observation))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        self.logger.info("Modelhost get_modelhost_predictions() call elapsed time: " + str(t1 - t0) + " ms")  # TODO logger
        return prediction

    def get_modelhost_info(self, model):
        t0 = round(time.time() * 1000)
        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.get_modelhost_info(model))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        self.logger.info("modelhost get_modelhost_info() call elapsed time: " + str(t1 - t0) + " ms")
        return info

    def post_modelhost_info(self, model, description):
        t0 = round(time.time() * 1000)
        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            response = loop.run_until_complete(self.modelhostUtils.post_modelhost_info(model, description))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        self.logger.info("modelhost get_modelhost_info() call elapsed time: " + str(t1 - t0) + " ms")
        return response

    def _test_get_kitchen_predictions(self, observation_list):
        t0 = round(time.time() * 1000)
        # llamada a la ejecucion asincrona de kitchen    #toda esta gestion del loop se podria sustituir por asyncio.run()
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            predictions = loop.run_until_complete(self.modelhostUtils._test_get_kitchen_predictions(observation_list))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        print("kitchen get_kitchen_predictions() call elapsed time: " + str(t1 - t0) + " ms")  # TODO logger
        return predictions

    # TODO def get_modelhost_descriptions(self, model_list):


class ModelhostQueryUtils:
    """This class defines the asynchronous corountines that make the calls to the endpond which comunicates with
    modelhost """

    def __init__(self):
        self.LOAD_BALANCER_ENDPOINT = os.getenv('LOAD_BALANCER_ENDPOINT')
        self.URL_PREFIX = 'http://'

    """ASYNC MODELHOST METHODS"""

    async def get_modelhost_predictions(self, model, observation_list):
        URL_METHOD = '/modelhost/models/' + model + '/prediction'
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug

        # Execute all queries with gather (one query every request)

        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_query_async(observation_list, session, url)])

    async def get_modelhost_info(self, model):
        URL_METHOD = "/modelhost/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug
        data = {"model": model}
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.get_query_async(data=data, session=session, url=url)])

    async def post_modelhost_info(self, model, description):
        URL_METHOD = "/modelhost/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug
        data = {"model": model, "model_description": description}
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_query_async(data=data, session=session, url=url)])

    # TODO async def get_modelhost_descriptions(self, model_list):

    async def _test_get_kitchen_predictions(self, observation_list):
        URL_METHOD = '/api/test/frominferrer/get/'
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD
        # execute all queries and gather results
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*[self._test_get_query_async(observation, session, url) for observation in observation_list])


    """ASYNC HTTP QUERIES"""

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

    async def _test_get_query_async(self, observation, session, url):
        endpoint = url + observation
        print(endpoint)
        resp = await session.request(method="GET", url=endpoint)
        resp.raise_for_status()
        print("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
        prediction_data = await resp.text()
        return prediction_data

#TODO este Logger debería estar en un clase de utils dedicadas e importado en esta para ser utilizado
class Logger():

    def __init__(self, filename):
        self.FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
        self.LOG_FILE = f'/home/logs/{filename}-{time.time()}.log'

    def get_console_handler(self):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.FORMATTER)
        return console_handler

    def get_file_handler(self):
        file_handler = TimedRotatingFileHandler(self.LOG_FILE, when='midnight')
        file_handler.setFormatter(self.FORMATTER)
        return file_handler

    def get_logger(self, logger_name):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)  # better to have too much log than not enough
        logger.addHandler(self.get_console_handler())
        logger.addHandler(self.get_file_handler())
        # with this pattern, it's rarely necessary to propagate the error up to parent
        logger.propagate = False
        return logger

