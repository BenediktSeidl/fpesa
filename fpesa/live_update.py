#!/usr/bin/env python

import asyncio
import logging

import websockets
from websockets.exceptions import ConnectionClosed
import aio_pika

from fpesa.config import config

logger = logging.getLogger(__name__)
connections = []


async def liveupdate(websocket, path):
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
        connections.remove(websocket)


async def consume_messages_from_bus(loop):
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
        queue.bind(exchange)
        logger.info('waiting for messages...')

        async for message in queue:
            with message.process():
                for websocket in connections:
                    try:
                        await websocket.send(message.body)
                    except ConnectionClosed:
                        logger.info(
                            'connection {} already closed'.format(websocket))


def main(options):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websockets.serve(liveupdate, '127.0.0.1', 8082))
    loop.run_until_complete(consume_messages_from_bus(loop))
    loop.run_forever()
