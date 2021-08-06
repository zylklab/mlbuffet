import asyncio
import os

import aiohttp


# TODO os.getenv no, constants

class ModelhostClientManager:
    """
    This class creates the coroutines which have been called by Inferrer methods.
    Whenever an http request is sent to Inferrer, a ModelhostClientManager instance is created and the
    corresponding method is called. Inside the method, another method with the same name is called where the
    asynchronous session is performed. Finally, in the asynchronous session, a last function is executed
    depending on the HTTP request to be sent to the modelhost (GET, POST with json, POST with file, or DELETE)

    Recommended artile about asyncio and examples: https://realpython.com/async-io-python/

    The methods below are called to open an asynchronous loop, and then call the method in the Utils section
    with the same name to perform the session call (HTTP request). 
    """

    def __init__(self):
        self.modelhostUtils = ModelhostQueryUtils()

    def get_modelhost_predictions(self, model, observation_list):
        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()
        try:
            observation = {"values": observation_list}
            prediction = loop.run_until_complete(
                self.modelhostUtils.get_modelhost_predictions(model, observation))
        finally:
            loop.close()
        return prediction

    def get_modelhost_info(self, model):

        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.get_modelhost_info(model))
        finally:
            loop.close()
        return info

    def post_modelhost_info(self, model, description):

        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            response = loop.run_until_complete(self.modelhostUtils.post_modelhost_info(model, description))
        finally:
            loop.close()
        return response

    def get_modelhost_models(self):

        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.get_modelhost_models())
        finally:
            loop.close()
        return info

    def get_modelhost_models_description(self):

        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.get_modelhost_models_description())
        finally:
            loop.close()
        return info

    def post_modelhost_upload_model(self, model, modelpath):
        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()

        try:
            upload = loop.run_until_complete(
                self.modelhostUtils.post_modelhost_upload_model(model, modelpath))

        finally:
            loop.close()

        return upload

    def delete_modelhost_delete_model(self, model):

        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.delete_modelhost_delete_model(model))
        finally:
            loop.close()
        return info

    def update_modelhost_models(self):

        # Call to the asynchronous execution of modelhost
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            info = loop.run_until_complete(self.modelhostUtils.update_modelhost_models())
        finally:
            loop.close()
        return info

    def _test_get_modelhost_predictions(self, observation_list):

        # llamada a la ejecucion asincrona de modelhost    #toda esta gestion del loop se podria sustituir por
        # asyncio.run()
        loop = asyncio.new_event_loop()  # asyncio.get_event_loop()
        try:
            predictions = loop.run_until_complete(self.modelhostUtils._test_get_modelhost_predictions(observation_list))
        finally:
            loop.close()
        return predictions


class ModelhostQueryUtils:
    """This class defines the asynchronous corountines that make the calls to the endpoint which comunicates with
    modelhost """

    def __init__(self):
        self.LOAD_BALANCER_ENDPOINT = os.getenv('LOAD_BALANCER_ENDPOINT')
        self.URL_PREFIX = 'http://'
        self.NUMBER_OF_MODELHOSTS = int(os.getenv("NUMBER_MODELHOST_NODES"))

    """ASYNC MODELHOST METHODS"""

    # For debugging purposes, use the modelhost url instead of the Load Balancer's
    # debug --
    # url = 'http://172.24.0.3:8000' + URL_METHOD
    # -- debug

    async def get_modelhost_predictions(self, model, observation_list):
        URL_METHOD = '/modelhost/models/' + model + '/prediction'
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD
        print(self.LOAD_BALANCER_ENDPOINT)

        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_query_async(observation_list, session, url)])

    async def get_modelhost_info(self, model):
        URL_METHOD = "/modelhost/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        data = {"model": model}
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.get_query_async(data=data, session=session, url=url)])

    async def post_modelhost_info(self, model, description):
        URL_METHOD = "/modelhost/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        data = {"model": model, "model_description": description}
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.post_query_async(data=data, session=session, url=url)])

    async def get_modelhost_models(self):
        URL_METHOD = "/modelhost/models"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

        data = None
        # Execute all queries with gather (one query every request)
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(
                *[self.get_query_async(data=data, session=session, url=url)])

    async def get_modelhost_models_description(self):
        URL_METHOD = "/modelhost/models/information"
        url = self.URL_PREFIX + self.LOAD_BALANCER_ENDPOINT + URL_METHOD

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
