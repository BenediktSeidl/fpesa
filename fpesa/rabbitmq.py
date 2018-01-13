"""
--------
RabbitMQ
--------

Helper functions for RabbitMQ
"""
import pika
import aio_pika

from .config import config

_connection = None


def open_connection():
    """
    :rtype: pika.adapters.blocking_connection.BlockingConnection
    """
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=config['rabbitmq']['host'],
        virtual_host=config['rabbitmq']['virtual_host']
        # TODO: respect user and password of config!
    ))


def get_connection():
    """
    get globally unique connection

    .. deprecated:: 0.0.1
    """
    global _connection
    if _connection is None:
        _connection = open_connection()
    return _connection


async def get_aio_connection(loop=None):
    config_mq = config['rabbitmq']
    connection = await aio_pika.connect_robust(
        host=config_mq['host'],
        virtualhost=config_mq['virtual_host'],
        login=config_mq['user'],
        password=config_mq['password'],
        loop=loop,
    )
    return connection
