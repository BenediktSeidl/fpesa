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
    returns a open connection as defined in the :ref:`config`.

    :rtype: pika.adapters.blocking_connection.BlockingConnection
    """
    return pika.BlockingConnection(pika.ConnectionParameters(
        credentials=pika.credentials.PlainCredentials(
            config['rabbitmq']['user'],
            config['rabbitmq']['password'],
        ),
        host=config['rabbitmq']['host'],
        virtual_host=config['rabbitmq']['virtual_host']
    ))


async def get_aio_connection(loop=None):
    """
    returns a open connection as defined in the :ref:`config`.

    :rytpe: :py:class:`aio_pika.Connection`
    """
    config_mq = config['rabbitmq']
    connection = await aio_pika.connect_robust(
        host=config_mq['host'],
        virtualhost=config_mq['virtual_host'],
        login=config_mq['user'],
        password=config_mq['password'],
        loop=loop,
    )
    return connection
