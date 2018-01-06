import os
from unittest import TestCase

import requests

from fpesa.config import config
from fpesa.rabbitmq import get_connection


def install_test_config():
    test_config_path = os.path.join(
        os.path.dirname(__file__), 'files', 'config.cfg')
    with open(test_config_path) as fo:
        config.read_file(fo)


class RabbitMqTestCase(TestCase):
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
        self.__rabbitmq_api(
            'DELETE', 'vhosts/tests', status_code_ok=(404, 204, 200))
        self.__rabbitmq_api('PUT', 'vhosts/tests')
        self.__rabbitmq_api(
            'PUT', '/permissions/tests/guest',
            {'configure': '.*', 'write': '.*', 'read': '.*'})

        self.connection = get_connection()

    def _setup_channel(self, exchange, exchange_type='fanout'):
        channel = self.connection.channel()
        channel.queue_declare(queue='worker', durable=True)
        channel.exchange_declare(
            exchange=exchange, exchange_type=exchange_type)
        channel.queue_bind(exchange=exchange, queue='worker', routing_key='')
        return channel
