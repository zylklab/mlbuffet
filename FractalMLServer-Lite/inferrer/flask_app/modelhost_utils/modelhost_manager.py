import asyncio
import aiohttp
# from modelhost_utils.logger_modelhost.modelhost_logger import Logger
import os
import time


class ModelhostClientManager:

    """
    This class is responsible for creating the coroutines which have been called by the Inferrer methods.
    Whenever an http request is sent to inferrer, a ModelhostClientManager instance is created and the
    corresponding method is called. In the method, another method with the same name is called where the
    asynchronous session is performed. Finally, in the asynchronous session, a last function is executed
    depending on the HTTP request to be sent to the modelhost (GET, POST with json, POST with file, or DELETE)

    Recommended artile about asyncio and examples: https://realpython.com/async-io-python/
    """


    '''
    The methods below are called to open an asynchronous loop, and then call the method in the Utils section
    with the same name to perform the session call (HTTP request). 
    '''
    def __init__(self):
        self.modelhostUtils = ModelhostQueryUtils()
        # self.modelhostLogger = Logger
        #
        # self.logger = Logger("manager_logger").get_logger("manager_logger")

    def get_modelhost_predictions(self, model, observation_list):
        t0 = round(time.time() * 1000)
        # Call to the asynchronous execution of modelhost

        loop = asyncio.new_event_loop()
        try:
            observation = {"values": observation_list}
            prediction = loop.run_until_complete(
                self.modelhostUtils.get_modelhost_predictions(model, observation))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        # self.logger.info("Modelhost get_modelhost_predictions() call elapsed time: " + str(t1 - t0) + " ms")
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
        # self.logger.info("modelhost get_modelhost_info() call elapsed time: " + str(t1 - t0) + " ms")
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
        # self.logger.info("modelhost get_modelhost_info() call elapsed time: " + str(t1 - t0) + " ms")
        return response

    def get_modelhost_models(self):
        t0 = round(time.time() * 1000)
        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.get_modelhost_models())
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        # self.logger.info("modelhost get_modelhost_models() call elapsed time: " + str(t1 - t0) + " ms")
        return info

    def get_modelhost_models_description(self):
        t0 = round(time.time() * 1000)
        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.get_modelhost_models_description())
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        # self.logger.info("modelhost get_modelhost_models_description() call elapsed time: " + str(t1 - t0) + " ms")
        return info

    def post_modelhost_upload_model(self, model, modelpath):

        t0 = round(time.time() * 1000)

        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()

        try:
            upload = loop.run_until_complete(
                self.modelhostUtils.post_modelhost_upload_model(model, modelpath))

        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        # self.logger.info(
        #    "Modelhost post_modelhost_upload_model call elapsed time: " + str(t1 - t0) + " ms")  # TODO logger

        return upload

    def delete_modelhost_delete_model(self, model):

        t0 = round(time.time() * 1000)
        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.delete_modelhost_delete_model(model))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        # self.logger.info("modelhost delete_modelhost_delete_model() call elapsed time: " + str(t1 - t0) + " ms")
        return info

    def update_modelhost_models(self):
        t0 = round(time.time() * 1000)
        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.update_modelhost_models())
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        # self.logger.info("modelhost delete_modelhost_delete_model() call elapsed time: " + str(t1 - t0) + " ms")
        return info

    def _test_get_modelhost_predictions(self, observation_list):
        t0 = round(time.time() * 1000)
        # llamada a la ejecucion asincrona de modelhost    #toda esta gestion del loop se podria sustituir por
        # asyncio.run()
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            predictions = loop.run_until_complete(self.modelhostUtils._test_get_modelhost_predictions(observation_list))
        finally:
            loop.close()
        t1 = round(time.time() * 1000)
        # print("modelhost get_modelhost_predictions() call elapsed time: " + str(t1 - t0) + " ms")  # TODO logger
        return predictions

    # TODO def get_modelhost_descriptions(self, model_list):


class ModelhostQueryUtils:
    """This class defines the asynchronous corountines that make the calls to the endpoint which comunicates with
    modelhost """

    def __init__(self):
        self.LOAD_BALANCER_ENDPOINT = os.getenv('LOAD_BALANCER_ENDPOINT')
        self.URL_PREFIX = 'http://'
        self.NUMBER_OF_MODELHOSTS = int(os.getenv("NUMBER_MODELHOST_NODES"))
        # self.logger = Logger("manager_logger").get_logger("manager_logger")

    """ASYNC MODELHOST METHODS"""

    async def get_modelhost_predictions(self, model, observation_list):
        URL_METHOD = '/modelhost/models/' + model + '/prediction'
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD
        print(self.LOAD_BALANCER_ENDPOINT)

        # debug --
        # url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug

        # Execute all queries with gather (one query every request)

        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_query_async(observation_list, session, url)])

    async def get_modelhost_info(self, model):
        URL_METHOD = "/modelhost/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        # url = 'http://172.24.0.3:8000' + URL_METHOD
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
        # url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug
        data = {"model": model, "model_description": description}
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_query_async(data=data, session=session, url=url)])

    async def get_modelhost_models(self):
        URL_METHOD = "/modelhost/models"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        # url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug
        data = None
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.get_query_async(data=data, session=session, url=url)])

    async def get_modelhost_models_description(self):
        URL_METHOD = "/modelhost/models/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # debug --
        # url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug
        data = None
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.get_query_async(data=data, session=session, url=url)])

    async def post_modelhost_upload_model(self, model, modelpath):
        URL_METHOD = '/modelhost/models/upload_' + model
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        # Open the file
        files = {'file': open(modelpath, 'rb')}

        # debug --
        # url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug

        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_file_query_async(file=files, session=session, url=url)])

    async def delete_modelhost_delete_model(self, model):
        URL_METHOD = '/modelhost/models/delete_' + model
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.delete_query_async(session=session, url=url)])

    async def update_modelhost_models(self):
        # This is a 'brute force' method. It tries to communicate with all
        # modelhosts taking the N variables 'MODELHOST_N_IP' from the .env file
        URL_METHOD = '/modelhost/models/update'
        # debug --
        # url = 'http://172.24.0.3:8000' + URL_METHOD
        # -- debug
        n = self.NUMBER_OF_MODELHOSTS
        for i in range(n):
            # url = self.URL_PREFIX + '172.24.0.' + str(i + 11) + ':8000' + URL_METHOD
            ip = os.getenv('MODELHOST_' + str(i + 1) + '_IP') + ':8000'
            url = self.URL_PREFIX + ip + URL_METHOD
            data = None
            # Execute all queries with gather (one query every request)
            async with aiohttp.ClientSession() as session:
                await asyncio.gather(
                    *[self.post_query_async(session=session, url=url, data=data)])
        return "done"

    # TODO async def get_modelhost_descriptions(self, model_list):

    async def _test_get_modelhost_predictions(self, observation_list):
        URL_METHOD = '/api/test/frominferrer/get/'
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD
        # execute all queries and gather results
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self._test_get_query_async(observation, session, url) for observation in observation_list])

    """
    ASYNC HTTP QUERIES
    These functions define the parameters of the HTTP requests to be done to the modelhost.
    Information like the final url, the files or jsons to be sent and the REST petition (GET, POST...) 
    are defined here.
    """

    # TODO async def post_query_async(self, observation, session, url, payload):
    async def post_query_async(self, data, session, url):
        endpoint = url
        resp = await session.post(url=endpoint, headers={"Content-Type": "application/json"},
                                  json=data)
        resp.raise_for_status()
        # self.logger.info("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
        prediction_data = await resp.text()
        return prediction_data

    async def get_query_async(self, data, session, url):
        endpoint = url
        resp = await session.get(url=endpoint, headers={"Content-Type": "application/json"},
                                 json=data)
        resp.raise_for_status()
        # self.logger.info("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
        prediction_data = await resp.text()
        return prediction_data

    async def post_file_query_async(self, file, session, url):
        endpoint = url
        resp = await session.post(url=endpoint, data=file)
        resp.raise_for_status()
        print("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
        response = await resp.text()

        return response

    async def delete_query_async(self, session, url):
        endpoint = url
        resp = await session.request(method="DELETE", url=endpoint)
        resp.raise_for_status()
        # self.logger.info("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
        response = await resp.text()
        return response

    async def _test_get_query_async(self, observation, session, url):
        endpoint = url + observation
        print(endpoint)
        resp = await session.request(method="GET", url=endpoint)
        resp.raise_for_status()
        # self.logger.info("Got response [%s] for URL: %s", resp.status, endpoint)  # TODO logger
        prediction_data = await resp.text()
        return prediction_data
