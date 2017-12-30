import pika

from .config import config

_connection = None


def get_connection():
    global _connection
    if _connection is None:
        _connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=config['rabbitmq']['host'],
            virtual_host=config['rabbitmq']['virtual_host']
        ))
    return _connection
