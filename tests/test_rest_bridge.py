import json
from unittest import TestCase

import requests
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from common import install_test_config
from fpesa.rest2bus import get_app, Endpoint, FireAndForgetAdapter
from fpesa.message_bus import get_connection
from fpesa.config import config

install_test_config()


class TestRestBridge(TestCase):
    def __rabbitmq_api(
            self, method, url_part, data={}, status_code_ok=(200, 204)):
        result = requests.request(
            method,
            'http://{}:15672/api/{}'.format(
                config['rabbitmq']['host'],
                url_part),
            json=data,
            auth=(config['rabbitmq']['user'], config['rabbitmq']['password'])
        )
        self.assertIn(result.status_code, status_code_ok)

    def setUp(self):
        # completely reset rabbitmq
        self.__rabbitmq_api('DELETE', 'vhosts/tests', (404, 204, 200))
        self.__rabbitmq_api('PUT', 'vhosts/tests')
        self.__rabbitmq_api(
            'PUT', '/permissions/tests/guest',
            {'configure': '.*', 'write': '.*', 'read': '.*'})

        self.connection = get_connection()

    def get_simple_ff_app(self):
        app = get_app([Endpoint(
            '/testing/', 'POST', FireAndForgetAdapter(),
            schema_req_data={'type': 'object', 'properties': {
                'a': {'type': 'integer'}}, 'additionalProperties': False})])
        c = Client(app, BaseResponse)
        return c

    def _setup_channel(self, exchange):
        channel = self.connection.channel()
        channel.queue_declare(queue='worker')
        channel.exchange_declare(exchange=exchange, exchange_type='fanout')
        channel.queue_bind(exchange=exchange, queue='worker')
        return channel

    def test_ff_post_with_body(self):
        """ declare rest endpoint, send message, see if message is on bus """
        channel = self._setup_channel('/testing/:POST')

        c = self.get_simple_ff_app()
        resp = c.post('/testing/', data=json.dumps({'a': 2}))
        self.assertEqual(json.loads(resp.data.decode()), {})

        method, properties, body = channel.basic_get(queue='worker')
        self.assertNotEqual(body, None)
        self.assertEqual(
            json.loads(body.decode()),
            {'data': {'a': 2}, 'args': None}
        )
        channel.basic_ack(method.delivery_tag)

    def test_validation_error(self):
        c = self.get_simple_ff_app()
        resp = c.post('/testing/', data=json.dumps({'testing': 'asd'}))
        response = json.loads(resp.data.decode())
        description = response['error'].pop('description')
        self.assertEqual(response, {'error': {'code': 500}})
        self.assertTrue('Additional properties are not allowed', description)

    def test_body_not_allowed(self):
        app = get_app([Endpoint('/testing/', 'POST', FireAndForgetAdapter())])
        c = Client(app, BaseResponse)
        resp = c.post('/testing/')
        self.assertEqual(resp.status_code, 200)

        resp = c.post('/testing/', data=json.dumps({'testing': 'asd'}))
        self.assertEqual(resp.status_code, 500)

    def test_request_args(self):
        app = get_app([Endpoint(
            '/args/', 'PUT', FireAndForgetAdapter(),
            schema_req_args={
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'key': {
                        'type': 'string'
                    }
                }
            }

        )])
        channel = self._setup_channel('/args/:PUT')
        c = Client(app, BaseResponse)
        resp = c.put('/args/?key=value')
        self.assertEqual(resp.status_code, 200)

        method, properties, body = channel.basic_get(queue='worker')
        self.assertEqual(
            json.loads(body.decode()),
            {'args': {'key': 'value'}, 'data': None}
        )

    def test_error_404(self):
        """ try to access not existing endpoint """
        c = self.get_simple_ff_app()
        resp = c.get('/does_not_exists/')
        self.assertEqual(resp.status_code, 404)
        response = json.loads(resp.data.decode())
        description = response['error'].pop('description', '')
        self.assertTrue('not found' in description)
        self.assertEqual(response, {'error': {'code': 404}})
