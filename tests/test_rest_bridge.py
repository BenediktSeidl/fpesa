import json
from collections import namedtuple
from unittest import mock

import pika
from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from common import install_test_config, RabbitMqTestCase
from fpesa.restmapper import get_app, Endpoint, FireAndForgetAdapter
from fpesa.restmapper import RequestResponseAdapter

install_test_config()

FakeUUID = namedtuple('FakeUUID', ['hex'])


class TestRestBridge(RabbitMqTestCase):
    def get_simple_ff_app(self):
        app = get_app([Endpoint(
            '/testing/', 'POST', FireAndForgetAdapter(),
            schema_req_data={'type': 'object', 'properties': {
                'a': {'type': 'integer'}}, 'additionalProperties': False})])
        c = Client(app, BaseResponse)
        return c

    def get_simple_rr_app(self):
        adapter = RequestResponseAdapter()
        app = get_app([Endpoint(
            '/testing/', 'GET', adapter,
            schema_req_args={'type': 'object', 'properties': {
                'b': {'type': 'string'}}, 'additionalProperties': False})])
        c = Client(app, BaseResponse)
        return c, adapter

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

    @mock.patch('uuid.uuid4', return_value=FakeUUID('abc'))
    def test_rr_simple(self, patched):
        channel = self._setup_channel('/testing/:GET', exchange_type='direct')
        c, adapter = self.get_simple_rr_app()

        # answer to message, before receiving it, otherwise we would need
        # threads
        channel.basic_publish(
            exchange='RPC',
            routing_key=adapter.response_queue.method.queue,
            body=json.dumps({'d': 'e'}),
            properties=pika.BasicProperties(
                correlation_id='abc'
            ),
        )

        # send request
        resp = c.get("/testing/?b=c")

        # see if message was sent
        method, properties, body = channel.basic_get(queue='worker')
        self.assertEqual(properties.correlation_id, 'abc')
        self.assertTrue(properties.reply_to.startswith('amq.gen-'))
        self.assertEqual(
            json.loads(body.decode()),
            {'args': {'b': 'c'}, 'data': None}
        )

        # check rest answer
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data.decode()), {'d': 'e'})
