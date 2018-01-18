"""
.. _restmapper:

Generic rest to RabbitMQ Mapper
###############################

When using a message broker as a backend for a rest endpoint, most of the rest
endpoint is just repeating glue logic to map the request data from the http
request to the message broker. In order to not repeat the same code over and
over again this simple bridge was created.

For each rest endpoint you create a :class:`Endpoint`, put them into a list and
call :func:`get_app` to get a :py:class:aiohttp.web.Application
"""

import json
import logging
import uuid

import jsonschema
from aiohttp import web
from aiohttp.web import json_response
import aio_pika

from . import rabbitmq

logger = logging.getLogger(__name__)


class Endpoint():
    """
    Maps a rest endpoint to a exchange in rabbitmq.

    :param str path: rest endpoint path
    :param str method: allowed method
    :param Adapter adapter: how to map the incoming request? currently
        :py:class:`FireAndForgetAdapter` and :py:class:`RequestResponseAdapter`
        are available
    :param dict schema_req_data: a jsonschema describing the valid request body
    :param dict schema_req_args: a jsonschema describing the valid request
        parameters. please note that the request arguments are mapped into a
        simple dictionary, and both key and value are of the type string.

    The name of the exchange consists of path and method seperated by a colon.
    """
    def __init__(
            self, path, method, adapter,
            schema_req_data=None, schema_req_args=None):
        self.path = path
        self.method = method
        self.adapter = adapter
        self.schema_req_data = schema_req_data
        self.schema_req_args = schema_req_args

    async def close(self):
        await self.adapter.close()

    async def set_rabbitmq_connection(self, rabbitmq_connection):
        self.rabbitmq_connection = rabbitmq_connection
        await self.adapter.init(self)

    async def request_handler(self, request):
        data = None
        if self.schema_req_data is not None:
            try:
                data = await request.json()
            except json.JSONDecodeError as e:
                raise web.HTTPInternalServerError(
                    reason='Can not parse request body as JSON: ' + str(e))
            try:
                jsonschema.validate(data, self.schema_req_data)
            except jsonschema.ValidationError as e:
                raise web.HTTPInternalServerError(
                    reason='Can not validate request data json '
                    'according to schema:\n' + str(e))
        else:
            if request.has_body:
                raise web.HTTPInternalServerError(
                    reason='No request data allowed')

        request_args = None
        if self.schema_req_args is not None:
            request_args = dict(request.query.items())
            try:
                jsonschema.validate(request_args, self.schema_req_args)
            except jsonschema.ValidationError as e:
                raise web.HTTPInternalServerError(
                    reason='Can not validate request arguments '
                    'according to schema:\n' + str(e))
        else:
            if request.query:
                raise web.HTTPInternalServerError(
                    reason='No request arguments allowed')

        return json_response(await self.adapter.adapt(data, request_args))


class Adapter():
    """
    Base class
    """
    async def init(self, endpoint):
        """
        open channel with endpoint.rabbitmq_connection
        """
        self.endpoint = endpoint
        self.channel = await endpoint.rabbitmq_connection.channel()
        self.channel.set_qos(prefetch_count=1)

    async def adapt(self, request_data, request_args):
        """
        Get parsed request data and arguments, return json encodeable data

        :param dict request_data: holds contents of request data
        :param dict request_args: holds contents of request arguments

        Note that the request data and arguments are parsed via the schemas
        definied in the :class:`Endpoint` constructor
        """
        raise NotImplementedError()

    def get_endpoint_name(self):
        return "{}:{}".format(
            self.endpoint.path,
            self.endpoint.method.upper()
        )

    async def close(self):
        await self.channel.close()


class FireAndForgetAdapter(Adapter):
    """
    Adapts a Rest-Call to a RabbitMQ message. The message is delivered to a
    fanout exchange named `<path>:<method>`. The successful Rest response is a
    empty object (`{}`)
    """
    async def init(self, endpoint):
        """
        initialize channel and exchange
        """
        await super().init(endpoint)

        # TODO: move exchange declare into function?!
        # so we can call it from producer and consume?

        self.exchange = await self.channel.declare_exchange(
            self.get_endpoint_name(),
            type=aio_pika.exchange.ExchangeType.FANOUT)
        queue = await self.channel.declare_queue(
                self.get_endpoint_name(), durable=True)
        await queue.bind(self.exchange)

    async def adapt(self, request_data, request_args):
        """
        Send the message to RabbitMQ
        """
        await self.exchange.publish(
                aio_pika.Message(json.dumps({
                    'data': request_data,
                    'args': request_args,
                }).encode('utf-8')),
                routing_key='',
            )
        return {}


class RequestResponseAdapter(Adapter):
    """
    Adapts a Rest-Request to a RabbitMQ message, the response to the Rest-Call
    with is defined by the response of the RabbitMQ message.
    To match the request and response on the message bus side, the request's
    properties includes two keys: `correlation_id` and `reply_to`. The response
    has to be sent to the exchange `RPC`. The `correlation_id` sent in the
    request has to be used as `routing_key` when sending the response to the
    exchange `RPC`. The `correlation_id` of the response holds the same value
    as the `correlation_id` of the request.
    The message is delivered to a exchange with type direct named
    `<path>:<method>`.
    """
    async def init(self, endpoint):
        await super().init(endpoint)

        # create exchange for sending requests
        self.exchange = await self.channel.declare_exchange(
            self.get_endpoint_name(),
            type=aio_pika.exchange.ExchangeType.DIRECT)
        queue = await self.channel.declare_queue(
                self.get_endpoint_name())
        await queue.bind(self.exchange)

        # aio-pika includes rpc interface. not sure if worth it.

        # create exchange for getting a response
        self.response_exchange = await self.channel.declare_exchange(
            'RPC',
            type=aio_pika.exchange.ExchangeType.DIRECT)
        self.response_queue = await self.channel.declare_queue(exclusive=True)
        await self.response_queue.bind(self.response_exchange)

    async def adapt(self, request_data, request_args):
        correlation_id = uuid.uuid4().hex.encode()

        await self.exchange.publish(
            aio_pika.Message(
                json.dumps({
                    'data': request_data,
                    'args': request_args,
                }).encode('utf-8'),
                reply_to=self.response_queue.name,
                correlation_id=correlation_id,
            ),
            routing_key=self.get_endpoint_name(),
        )

        logger.info(
            "waiting for rpc response in {}".format(self.response_queue.name))
        async with self.response_queue.iterator() as q:
            async for message in q:
                # TODO: timeout!
                with message.process():
                    if message.correlation_id == correlation_id:
                        return json.loads(message.body.decode())


def json_error(code, description):
    return json_response({
            'error': {
                'code': code,
                'description': description,
            }
        }, status=code)


@web.middleware
async def error_middleware(request, handler):
    try:
        return await handler(request)
    except web.HTTPException as ex:
        return json_error(ex.status, ex.reason)


def get_app(endpoints):
    app = web.Application(middlewares=[error_middleware])

    async def on_startup(app):
        app['rabbitmq_connection'] = \
            rabbitmq_connection = await rabbitmq.get_aio_connection(app.loop)

        for endpoint in endpoints:
            await endpoint.set_rabbitmq_connection(rabbitmq_connection)
            app.router.add_route(
                method=endpoint.method,
                path=endpoint.path,
                handler=endpoint.request_handler,
            )

    async def on_shutdown(app):
        for endpoint in endpoints:
            await endpoint.close()
        await app['rabbitmq_connection'].close()

    app.on_shutdown.append(on_shutdown)
    app.on_startup.append(on_startup)

    return app
