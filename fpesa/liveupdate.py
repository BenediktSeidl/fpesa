"""
----------
liveupdate
----------

liveupdate provides a websocket connection that publishs all inserted
messages.

"""

import asyncio
import logging

import websockets
from websockets.exceptions import ConnectionClosed
import aio_pika

from fpesa.config import config

logger = logging.getLogger(__name__)
connections = []
"""
Hold all open websocket connections. Please note that those connections are not
garanteed to be open. The connections are checked every 10 seconds, but a
timeout may occure in between the checks.
"""


async def liveupdate(websocket, path):
    """
    Called when a new websocket connection is opened

    :param websockets.server.WebSocketServerProtocol websocket: Websocket
        connection
    :param path: request URI

    This is the first argument of :py:func:`websockets.server.serve`.

    The funcion itself makes sure that the connection does not time out, but
    does not send any payload. The connection is inserted into
    :py:data:`connections`. When a new message arrives on the bus,
    :py:func:`consume_messages_from_bus` will use this list to send the message
    to all open connections
    """
    logger.info('open websocket connection {}'.format(websocket))
    connections.append(websocket)
    try:
        while True:
            # just make sure we don't loose the connection
            # messeage will be sent via connections list.
            pong_waiter = await websocket.ping()
            await pong_waiter
            await asyncio.sleep(10)  # TODO: how long?
    finally:
        logger.info('closing websocket connection {}'.format(websocket))
        if websocket in connections:
            connections.remove(websocket)


async def consume_messages_from_bus(loop):
    """
    Opens a connection to the RabbitMQ message bus, waits for messages and
    publishes them to all connected websockets.

    :param asyncio.AbstractEventLoop loop: event loop
    """
    config_mq = config['rabbitmq']
    connection = await aio_pika.connect_robust(
        host=config_mq['host'],
        virtualhost=config_mq['virtual_host'],
        login=config_mq['user'],
        password=config_mq['password'],
        loop=loop,
    )
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            '/messages/:POST', type=aio_pika.exchange.ExchangeType.FANOUT)
        queue = await channel.declare_queue('liveupdate', durable=True)
        await queue.bind(exchange)
        logger.info('waiting for messages...')

        async for message in queue:
            with message.process():
                for websocket in connections:
                    try:
                        await websocket.send(message.body)
                    except ConnectionClosed:
                        connections.remove(websocket)  # don't wait until ping
                        # finds this dead connection
                        logger.info(
                            'connection {} already closed'.format(websocket))


def main(options):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websockets.serve(liveupdate, '127.0.0.1', 8082))
    loop.run_until_complete(consume_messages_from_bus(loop))
    loop.run_forever()
