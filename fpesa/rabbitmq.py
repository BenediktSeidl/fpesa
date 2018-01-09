import pika

from .config import config

_connection = None


def open_connection():
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=config['rabbitmq']['host'],
        virtual_host=config['rabbitmq']['virtual_host']
    ))


def get_connection():
    global _connection
    if _connection is None:
        _connection = open_connection()
    return _connection
