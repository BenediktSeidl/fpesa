from unittest import TestCase
from contextlib import contextmanager
import datetime

from psycopg2 import connect
from psycopg2.extras import DictCursor

from fpesa.postgres import Session, create_all
from fpesa.config import config
from fpesa.helper import get_engine
from fpesa import message

from common import install_test_config


install_test_config()
Session.configure(bind=get_engine())  # now with test config


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
