import asyncio
from asyncio import sleep as asyncio_sleep
from unittest import mock
from unittest import TestCase

from websockets.exceptions import ConnectionClosed

from fpesa.liveupdate import liveupdate, consume_messages_from_bus
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

    def __init__(self, callbacks):
        """
        callbacks is a list of tuples. the first item of the tuple defines when
        the second item of the tuble is called. the list may look like this::

            [(2, cb1), (3, cb2)]

        then `cb1` will be called on the second iteration and `cb2` on the
        third.
        """
        FakeWebsocket.sleep_called = 0
        self.callbacks = callbacks

    async def ping(self):

        for index, function in self.callbacks:
            if FakeWebsocket.sleep_called == index:
                await function()

        if FakeWebsocket.sleep_called > 5:
            raise CloseException()

        async def pong():
            pass

        return pong()


async def mock_sleep(duration):
    FakeWebsocket.sleep_called += 1


class WebsocketsTestCase(TestCase):
    @mock.patch('asyncio.sleep', new=mock_sleep)
    def websocket_open_cb_close(self, cb=None, fake_websocket=None):
        """
        if parameter cb is defined:

        create a mock for the websocket object, call function cb when
        connection is established and internal while loop called wait twice
        closes the connection after 5 wait called with an expcetion

        if parameter fake_websocket is defined:

        use fake_websocket as fake websocket instance

        """
        if cb is None and fake_websocket is None:
            raise Exception("cb and fake_websocket can not be None")

        if cb is None:
            websocket = fake_websocket
        else:
            websocket = FakeWebsocket([(2, cb)])

        with self.assertRaises(CloseException):
            asyncio.get_event_loop().run_until_complete(
                liveupdate(websocket, '/'))
            raise Exception()  # TODO: never called, remove me!


class TestLiveUpdateWebsockets(WebsocketsTestCase):
    def test_websocket_open_close(self):
        """
        see if websocket is added to connection list
        """
        # not sure how usefull this really is
        from fpesa.liveupdate import connections

        self.assertEqual(len(connections), 0)

        async def callback():
            self.assertEqual(len(connections), 1)

        self.websocket_open_cb_close(callback)
        self.assertEqual(len(connections), 0)


class TestLiveUpdateMessages(WebsocketsTestCase, RabbitMqTestCase):
    def setup_channel(self):
        channel = self.connection.channel()
        channel.queue_declare(queue='liveupdate', durable=True)
        channel.exchange_declare(
            exchange='/messages/:POST', exchange_type='fanout')
        channel.queue_bind(exchange='/messages/:POST', queue='liveupdate')
        self.channel = channel

    async def send_message_callback(self):
        self.channel.basic_publish(
            exchange='/messages/:POST',
            routing_key='',
            body='{"data": "bodyy"}'
        )
        await asyncio_sleep(0.1)  # wait for message # hmmmm :-/

    def test_websockets_are_notified(self):
        """
        see if websocket message is sent when message arrives on rabbitmq
        """
        self.setup_channel()

        asyncio.get_event_loop().create_task(
            consume_messages_from_bus(asyncio.get_event_loop()))

        self.websocket_open_cb_close(self.send_message_callback)

        self.assertEqual(FakeWebsocket.send.mock.call_count, 1)
        self.assertEqual(FakeWebsocket.send.mock.call_args[0][1], '"bodyy"')

    def test_websocket_removed_after_send_with_error(self):
        from fpesa.liveupdate import connections

        self.setup_channel()

        # create worker to fetch messages from the message bus and forward them
        # to the websocket
        asyncio.get_event_loop().create_task(
            consume_messages_from_bus(asyncio.get_event_loop()))

        # no websocket connections yet
        self.assertEqual(len(connections), 0)

        async def raise_exception(body):
            raise ConnectionClosed(1001, 'reason')

        async def callback_check_one():
            self.assertEqual(len(connections), 1)
            fake_websocket.send = raise_exception
            # send message on the bus
            await self.send_message_callback()
            # this message will be resend on the websocket and
            # trigger websocket.send which will call raise_excetion
            # and then raise ConnectionClosed.

        async def callback_check_zero():
            # after callback_check_one raised a ConnectionClosed on the
            # websocket, the websocket should be removed from the connectionns
            self.assertEqual(len(connections), 0)

        fake_websocket = FakeWebsocket([
            (2, callback_check_one),
            (3, callback_check_zero)
        ])

        self.websocket_open_cb_close(fake_websocket=fake_websocket)
        self.assertEqual(len(connections), 0)
