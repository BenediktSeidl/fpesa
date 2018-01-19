import json
from unittest import TestCase
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
import datetime

from psycopg2 import connect
from psycopg2.extras import DictCursor

from fpesa.postgres import Session, create_all
from fpesa.config import config
from fpesa.helper import get_engine
from fpesa import message

from common import RabbitMqTestCase
from common import install_test_config


install_test_config()
Session.configure(bind=get_engine())  # now with test config


class ExitException(Exception):
    pass


@contextmanager
def cursor():
    config_postgres = config['postgres']
    connection = connect(
        user=config_postgres['user'],
        password=config_postgres['password'],
        host=config_postgres['host'],
        dbname=config_postgres['database'])
    cursor = connection.cursor(cursor_factory=DictCursor)
    with connection:
        try:
            yield cursor
        finally:
            cursor.close()


class TestMessage(TestCase):
    def setUp(self):
        with cursor() as c:
            c.execute(
                'select tablename from pg_tables where schemaname=\'public\'')
            tables = [row['tablename'] for row in c]
            for table in tables:
                c.execute('drop table {} cascade;'.format(table))

    def test_insert(self):
        create_all()
        message.message_post({'a': 2})
        with cursor() as c:
            c.execute('SELECT * FROM message')
            self.assertEqual(c.rowcount, 1)
            result = c.fetchone()
            self.assertEqual(result['message'], {'a': 2})
            self.assertEqual(result['id'], 1)
            self.assertTrue(
                result['inserted'] - datetime.datetime.now()
                < datetime.timedelta(seconds=2)
            )

    def test_get(self):
        """ insert 97 messages, and receive the last ten one """
        create_all()
        for i in range(97):
            message.message_post({'a': i})
        result = message.message_get(
            {'paginationId': None, 'offset': 0, 'limit': 10})
        self.maxDiff = None
        self.assertEqual(
            {
                'paginationId': 97,
                'offset': 0,
                'limit': 10,
                'total': 97,
                'messages': [{'a': i} for i in range(96, 86, -1)]
            },
            result
        )

    def test_parse_pagination_id(self):
        """ check if paginationID is parsed to int """
        create_all()
        for i in range(7):
            message.message_post({'a': i})
        result = message.message_get(
            {'paginationId': '12', 'offset': 0, 'limit': 10})
        self.assertEqual(result['paginationId'], 12)

    def test_get_maximum_limit(self):
        """ see if limit is clipped to 100 """
        create_all()
        for i in range(202):
            message.message_post({'a': i})
        result = message.message_get(
            {'paginationId': None, 'offset': 0, 'limit': 200})
        self.assertEqual(result['limit'], 100)
        self.assertEqual(len(result['messages']), 100)

    def test_get_string_parameters(self):
        """ the webapp will send parameters as strings, because there are
        no types for request paramters """
        self.test_get()
        result = message.message_get(
            {'paginationId': None, 'offset': "0", 'limit': "10"})
        self.assertEqual(result['offset'], 0)
        self.assertEqual(result['limit'], 10)

    def test_get_with_empty_table(self):
        """ get messages if empty """
        create_all()
        result = message.message_get(
            {'paginationId': None, 'offset': 0, 'limit': 10})
        self.assertEqual(
            {
                'paginationId': 0,
                'offset': 0,
                'limit': 10,
                'total': 0,
                'messages': [],
            },
            result
        )

    def test_get_pagination_id(self):
        """ get 2 messages but with pagination id 90 """
        self.test_get()
        result = message.message_get(
            {'paginationId': 90, 'offset': 0, 'limit': 2})
        self.assertEqual(
            {
                'paginationId': 90,
                'offset': 0,
                'limit': 2,
                'total': 90,
                'messages': [{'a': 89}, {'a': 88}]
            },
            result
        )

    @patch('fpesa.message.message_get')
    def _error_cb(self, message_get_mock, **kwargs):
        message_get_mock.side_effect = Exception('Unexpected Exception')
        channel = MagicMock()
        method_frame = MagicMock()
        method_frame.delivery_tag = 'ddelivery_tag'
        header_frame = MagicMock()
        header_frame.return_value = 'rreply_to'
        header_frame.correlation_id = 'ccorrelation_id'
        body = b'{"args": {}, "data": {}}'
        message._message_get_worker_cb(
            channel, method_frame, header_frame, body, **kwargs)
        queue, reply_to, data, properties = channel.publish.call_args[0]
        return json.loads(data)

    def test_error_cb_production(self):
        data = self._error_cb()
        self.assertEqual(
            data,
            {'error': {'code': 500, 'description': 'Internal server error'}}
        )

    def test_error_cb_debugging(self):
        data = self._error_cb(debug=True)
        description = data['error']['description']
        self.assertTrue('Unexpected Exception' in description, description)


class TestWorker(RabbitMqTestCase):
    @patch('pika.adapters.blocking_connection.BlockingChannel.queue_declare')
    def test_worker_creates_queue_get(self, channel_queue_declare):
        # mock start_consuming in order to not block the execution
        channel_queue_declare.side_effect = ExitException('EXIT')
        with self.assertRaises(ExitException):
            message.messages_get_worker(MagicMock())
        channel_queue_declare.assert_called_with('/messages/:GET')

    @patch('pika.adapters.blocking_connection.BlockingChannel.queue_declare')
    def test_worker_creates_queue_post(self, channel_queue_declare):
        # mock start_consuming in order to not block the execution
        channel_queue_declare.side_effect = ExitException('EXIT')
        with self.assertRaises(ExitException):
            message.messages_post_worker()
        channel_queue_declare.assert_called_with(
            '/messages/:POST', durable=True)
