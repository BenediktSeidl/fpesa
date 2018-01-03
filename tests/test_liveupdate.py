import asyncio
from asyncio import sleep as asyncio_sleep
from unittest import mock
from unittest import TestCase

from fpesa.live_update import liveupdate, consume_messages_from_bus
from common import install_test_config, RabbitMqTestCase

install_test_config()


def AsyncMock(*args, **kwargs):
    # https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


class CloseException(Exception):
    pass


class FakeWebsocket():
    send = AsyncMock()

    def __init__(self, callback):
        FakeWebsocket.sleep_called = 0
        self.callback = callback

    async def ping(self):
        if FakeWebsocket.sleep_called == 2:
            await self.callback()
            await asyncio.sleep(10)
        if FakeWebsocket.sleep_called > 5:
            raise CloseException()

        async def pong():
            pass

        return pong()


async def mock_sleep(duration):
    FakeWebsocket.sleep_called += 1


class WebsocketsTestCase(TestCase):
    @mock.patch('asyncio.sleep', new=mock_sleep)
    def websocket_open_cb_close(self, cb):
        """
        create a mock for the websocket object, call function cb when
        connection is established and internal while loop called wait twice
        closes the connection after 5 wait called with an expcetion
        """
        websocket = FakeWebsocket(cb)
        with self.assertRaises(CloseException):
            asyncio.get_event_loop().run_until_complete(
                liveupdate(websocket, '/'))
            raise Exception()


class TestLiveUpdateWebsockets(WebsocketsTestCase):
    def test_websocket_open_close(self):
        """
        see if websocket is added to connection list
        """
        # not sure how usefull this really is
        from fpesa.live_update import connections

        self.assertEqual(len(connections), 0)

        async def callback():
            self.assertEqual(len(connections), 1)

        self.websocket_open_cb_close(callback)
        self.assertEqual(len(connections), 0)


class TestLiveUpdateMessages(WebsocketsTestCase, RabbitMqTestCase):
    def test_websockets_are_notified(self):
        """
        see if websocket message is sent when message arrives on rabbitmq
        """
        channel = self.connection.channel()
        channel.queue_declare(queue='liveupdate', durable=True)
        channel.exchange_declare(
            exchange='/messages/:POST', exchange_type='fanout')
        channel.queue_bind(exchange='/messages/:POST', queue='liveupdate')

        asyncio.get_event_loop().create_task(
            consume_messages_from_bus(asyncio.get_event_loop()))

        async def callback():
            channel.basic_publish(
                exchange='/messages/:POST',
                routing_key='',
                body='bodyy'
            )
            await asyncio_sleep(0.1)  # wait for message # hmmmm :-/

        self.websocket_open_cb_close(callback)

        self.assertEqual(FakeWebsocket.send.mock.call_count, 1)
        self.assertEqual(FakeWebsocket.send.mock.call_args[0][1], b'bodyy')
