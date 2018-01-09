"""
Generic rest to RabbitMQ Mapper
###############################

When using a message broker as a backend for a rest endpoint, most of the rest
endpoint is just repeating glue logic to map the request data from the http
request to the message broker. In order to not repeat the same code over and
over again this simple bridge was created.

For each rest endpoint you create a :class:`Endpoint`, but them into a list and
call :func:`get_app` to get a wsgi app.
"""

import json
import uuid
import time
from contextlib import contextmanager

import pika
import jsonschema
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, InternalServerError

from .rabbitmq import open_connection, get_connection


class Endpoint():
    """
    Maps a rest endpoint to a exchange in rabbitmq.

    :param str path: asd
    :param str method: method
    :param Adapter adapter: Adapater
    :param dict schema_req_data: asd
    :param dict schema_req_args: asd

    The name of the exchange consinst of path and method seperated by a colon.
    """
    def __init__(
            self, path, method, adapter,
            schema_req_data=None, schema_req_args=None):
        self.path = path
        self.method = method
        self.adapter = adapter
        self.schema_req_data = schema_req_data
        self.schema_req_args = schema_req_args

        self.adapter.init(self)

    def to_rule(self):
        """
        returns the definied rest endpoint as a
        :py:class:`werkzeug.routing.Rule`
        """
        return Rule(self.path, methods=[self.method], endpoint=self)

    def dispatch_request(self, request):
        data = None
        if self.schema_req_data is not None:
            data = json.loads(request.data.decode())
            try:
                jsonschema.validate(data, self.schema_req_data)
            except jsonschema.ValidationError as e:
                raise InternalServerError(
                    'Can not validate request data json '
                    'according to schema:\n' + str(e))
        else:
            if request.data:
                raise InternalServerError('No request data allowed')

        request_args = None
        if self.schema_req_args is not None:
            request_args = request.args.to_dict()
            try:
                jsonschema.validate(request_args, self.schema_req_args)
            except jsonschema.ValidationError as e:
                raise InternalServerError(
                    'Can not validate request arguments '
                    'according to schema:\n' + str(e))
        else:
            if request.args:
                raise InternalServerError('No request arguments allowed')

        return JsonResponse(self.adapter.adapt(data, request_args))


class JsonResponse(Response):
    """
    Transform python dictionary into a http response with correct mimetype.
    """
    def __init__(self, response, *k, **kw):
        data = json.dumps(response)
        super().__init__(data, mimetype='application/json', *k, **kw)


class Adapter():
    """
    Base class
    """
    def init(self, endpoint):
        """
        """
        self.endpoint = endpoint

    def adapt(self, request_data, request_args):
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


class FireAndForgetAdapter(Adapter):
    """
    Adapts a Rest-Call to a RabbitMQ message. The message is delivered to a
    fanout exchange named `<path>:<method>`. The successful Rest response is a
    empty object (`{}`)
    """
    def init(self, endpoint):
        """
        initialize channel and exchange
        """
        super().init(endpoint)

    @contextmanager
    def channel(self):
        connection = open_connection()
        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        # TODO: move exchange declare into function?!
        # so we can call it from producer and consume?
        channel.exchange_declare(
            exchange=self.get_endpoint_name(),
            exchange_type='fanout',
        )
        channel.queue_declare(
            queue=self.get_endpoint_name(), durable=True)
        channel.queue_bind(
            exchange=self.get_endpoint_name(), queue=self.get_endpoint_name())
        try:
            yield channel
        finally:
            connection.close()


    def adapt(self, request_data, request_args):
        """
        Send the message to RabbitMQ
        """
        # originally the rabbitmq connection was opened in init.  but as
        # rabbitmq is connection based an we don't care about said connection
        # via a ping or something else, the connection finally dies. there is a
        # workaround for this: an exception is raised when calling
        # connection.process_data_events() and the connection already died.
        # then it's possible to reconnect and then send the message.
        #
        # opening, sending message and closing the connection: ~0.03s
        # checking connection and sending message: ~0.005s
        #
        # but as i don't know anything about the time constraints of this
        # function i remember Donald Knuth: Premature optimization is the root
        # of all evil. If this function will be the bottle neck one should
        # think about rewriting it with aiohttp, and aio_pika.connect_robust.
        with self.channel() as channel:
            channel.basic_publish(
                exchange=self.get_endpoint_name(),
                routing_key='',
                body=json.dumps({
                    'data': request_data,
                    'args': request_args,
                }),
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
    def init(self, endpoint):
        super().init(endpoint)
        self.channel = get_connection().channel()
        self.channel.basic_qos(prefetch_count=1)
        self.channel.exchange_declare(
            exchange=self.get_endpoint_name(),
            exchange_type='direct',
        )
        self.channel.queue_declare(queue='worker', durable=True)
        self.channel.queue_bind(
            exchange=self.get_endpoint_name(), queue='worker')

        self.response_channel = get_connection().channel()
        self.response_channel.basic_qos(prefetch_count=1)
        self.response_channel.exchange_declare(
            exchange='RPC', exchange_type='direct')
        self.response_queue = self.response_channel.queue_declare(
            exclusive=True)
        self.response_channel.queue_bind(
            exchange='RPC', queue=self.response_queue.method.queue)

    def adapt(self, request_data, request_args):
        correlation_id = uuid.uuid4().hex
        self.channel.basic_publish(
            exchange=self.get_endpoint_name(),
            routing_key='',
            body=json.dumps({
                'data': request_data,
                'args': request_args,
            }),
            properties=pika.BasicProperties(
                reply_to=self.response_queue.method.queue,
                correlation_id=correlation_id
            ),
        )

        while True:
            method, properties, body = self.response_channel.basic_get(
                queue=self.response_queue.method.queue)
            if properties and properties.correlation_id == correlation_id:
                break
            time.sleep(0.01)
            # TODO: timeout after 1 second
        return json.loads(body.decode())


class RestRabbitmqMapperApp():
    def __init__(self, url_map):
        self.url_map = url_map

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, _ = adapter.match()
            return endpoint.dispatch_request(request)
        except HTTPException as e:
            return JsonResponse({
                'error': {
                    'code': e.code,
                    'description': e.description,
                }
            }, status=e.code)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def get_app(endpoints):
    """
    :param list(Endpoint) endpoints: valid Endpoints

    Transform list of endpoints into wsg app.
    """
    rules = []  # TODO: use list comparison!
    for endpoint in endpoints:
        rules.append(endpoint.to_rule())
    return RestRabbitmqMapperApp(Map(rules))
