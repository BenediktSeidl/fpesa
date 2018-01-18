import json
import logging

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
import aio_pika

from fpesa.restmapper import get_app, Endpoint, FireAndForgetAdapter
from fpesa.restmapper import RequestResponseAdapter
from fpesa import restapp
from fpesa import rabbitmq

from common import ClearRabbitMQ
from common import install_test_config

install_test_config()

# pika and aio_pika are quite verbose...
logging.getLogger('pika').setLevel(logging.WARNING)
logging.getLogger('aio_pika').setLevel(logging.WARNING)


class TestRestBridgeFF(AioHTTPTestCase):
    # TODO: add ClearRabbitMQ
    async def get_application(self):
        # used by AioHTTPTestCase to construct self.client
        return get_app([Endpoint(
            '/testing/', 'POST', FireAndForgetAdapter(),
            schema_req_data={'type': 'object', 'properties': {
                'a': {'type': 'integer'}}, 'additionalProperties': False})])

    async def get_queue(self, queue_name):
        connection = await rabbitmq.get_aio_connection(self.loop)
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        return queue

    @unittest_run_loop
    async def test_ff_post_with_body(self):
        """ declare rest endpoint, send message, see if message is on bus """
        response = await self.client.request(
            "POST", "/testing/", json={'a': 2})
        self.assertEqual(response.status, 200)
        self.assertEqual(await response.json(), {})

        message = await (await self.get_queue('/testing/:POST')).get()

        self.assertEqual(
            json.loads(message.body.decode()),
            {'args': None, 'data': {'a': 2}}
        )

    @unittest_run_loop
    async def test_validation_error(self):
        """ check jsonschema validation """
        response = await self.client.request(
            "POST", "/testing/", json={'testing': 'asd'})
        body = await response.json()
        self.assertEqual(response.status, 500)
        description = body['error'].pop('description')
        self.assertEqual(body, {'error': {'code': 500}})
        self.assertTrue('Additional properties are not allowed' in description)

    @unittest_run_loop
    async def test_invalid_json(self):
        """ check for reasonable error message on invalid json """
        response = await self.client.request(
            "POST", "/testing/", data="invalid json")
        body = await response.json()
        self.assertEqual(response.status, 500)
        description = body['error'].pop('description')
        self.assertEqual(body, {'error': {'code': 500}})
        self.assertTrue('Can not parse ' in description)

    @unittest_run_loop
    async def test_error_404(self):
        """ try to access not existing endpoint """
        response = await self.client.request("GET", "/does_not_exist/")
        self.assertEqual(response.status, 404)
        response = await response.json()
        description = response['error'].pop('description', '')
        self.assertTrue('not found' in description.lower(), description)
        self.assertEqual(response, {'error': {'code': 404}})


class TestRestBridgeRR(AioHTTPTestCase, ClearRabbitMQ):
    def setUp(self):
        ClearRabbitMQ.setUp(self)
        super().setUp()

    async def get_application(self):
        # used by AioHTTPTestCase to construct self.client
        return get_app([Endpoint(
            '/testing/', 'GET', RequestResponseAdapter(),
            schema_req_args={'type': 'object', 'properties': {
                'b': {'type': 'string'}}, 'additionalProperties': False})])

    async def worker(self, return_error=False):
        """ dummy rpc worker that responses to RequestResponseAdapter """
        if return_error:
            body = b'{"error": {"description": "errror"}}'
        else:
            body = b'{"this is": "a response"}'
        connection = await rabbitmq.get_aio_connection(self.loop)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("/testing/:GET")
            message = await queue.get()
            with message.process():
                self.assertEqual(
                    json.loads(message.body.decode()),
                    {'args': {'b': 'c'}, 'data': None})
                response_exchange = await channel.declare_exchange(
                    'RPC',
                    type=aio_pika.exchange.ExchangeType.DIRECT)
                await response_exchange.publish(
                    aio_pika.Message(
                        body,
                        correlation_id=message.correlation_id,
                    ),
                    routing_key=message.reply_to
                )
            await channel.close()
            await channel.closing

    @unittest_run_loop
    async def test_body_not_allowed(self):
        """ see error message when including a body but no body is allowed """
        response = await self.client.request(
            "GET", "/testing/", json={'d': 'e'})
        self.assertEqual(response.status, 500)
        self.assertEqual(
            await response.json(),
            {'error': {
                'description': 'No request data allowed', 'code': 500}}
            )

    @unittest_run_loop
    async def test_rr_simple(self):
        await self._rr_simple()

    async def _rr_simple(self):
        """ simple valid RequestResponse """
        self.loop.create_task(self.worker())
        response = await self.client.request(
            "GET", "/testing/", params={'b': 'c'})
        self.assertEqual(response.status, 200, await response.json())
        self.assertEqual(await response.json(), {'this is': 'a response'})

    @unittest_run_loop
    async def test_rr_simple_twice(self):
        await self._rr_simple()
        await self._rr_simple()

    @unittest_run_loop
    async def test_rr_server_error_status_code(self):
        self.loop.create_task(self.worker(return_error=True))
        response = await self.client.request(
            "GET", "/testing/", params={'b': 'c'})
        self.assertEqual(response.status, 500)


# TODO: test generic exception and make sure they return a valid json!


class TestRestApp(AioHTTPTestCase, ClearRabbitMQ):
    def setUp(self):
        ClearRabbitMQ.setUp(self)
        super().setUp()

    async def get_application(self):
        # used by AioHTTPTestCase to construct self.client
        return get_app(restapp.get_endpoints())

    async def _get_messages(self, params):
        response = await self.client.request(
            "GET", "/messages/", params=params)
        return await response.json()

    async def _post_messages(self, body):
        response = await self.client.request(
            "POST", "/messages/", json=body)
        return await response.json()

    def assertIn(self, needle, hay):
        self.assertTrue(
            needle in hay, "'{}'\nnot in\n'{}'".format(needle, hay))

    @unittest_run_loop
    async def test_post_messages_production(self):
        """ check jsonschema validation of production environment """
        error = (await self._post_messages(
            'string'))['error']
        self.assertEqual(error['code'], 500)
        self.assertIn(
            "'string' is not of type 'object'",
            error['description'])

    @unittest_run_loop
    async def test_get_messages_production(self):
        """ check jsonschema validation of production environment """
        error = (await self._get_messages(
            {}))['error']
        self.assertEqual(error['code'], 500)
        self.assertIn(
            "'offset' is a required property",
            error['description'])

        error = (await self._get_messages(
            {'offset': 1}))['error']
        self.assertEqual(error['code'], 500)
        self.assertIn(
            "'limit' is a required property",
            error['description'])

        error = (await self._get_messages(
            {'offset': 1, 'limit': 2, 'asd': 1}))['error']
        self.assertEqual(error['code'], 500)
        self.assertIn(
            "Additional properties are not allowed ('asd' was unexpected)",
            error['description'])

        error = (await self._get_messages(
            {'offset': 'zzz', 'limit': 2}))['error']
        self.assertEqual(error['code'], 500)
        self.assertIn(
            "'zzz' does not match '^[0-9]+$'",
            error['description'])

        error = (await self._get_messages(
            {'offset': 1, 'limit': 'zzz'}))['error']
        self.assertEqual(error['code'], 500)
        self.assertIn(
            "'zzz' does not match '^[0-9]+$'",
            error['description'])

        error = (await self._get_messages(
            {'offset': 1, 'limit': 2, 'paginationId': 'zzz'}))['error']
        self.assertEqual(error['code'], 500)
        self.assertIn(
            "'zzz' does not match '^[0-9]+$'",
            error['description'])
