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

import jsonschema
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, InternalServerError

from .message_bus import get_connection


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

    def get_exchange_name(self):
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
        self.channel = get_connection().channel()
        # TODO: move exchange declare into function?!
        # so we can call it from producer and consume
        self.channel.exchange_declare(
            exchange=self.get_exchange_name(),
            exchange_type='fanout',
        )
        self.channel.queue_declare(queue='worker', durable=True)
        self.channel.queue_bind(
            exchange=self.get_exchange_name(), queue='worker')

    def adapt(self, request_data, request_args):
        """
        Send the message to RabbitMQ
        """
        self.channel.basic_publish(
            exchange=self.get_exchange_name(),
            routing_key='',
            body=json.dumps({
                'data': request_data,
                'args': request_args,
            }),
        )
        return {}


class RequestResponseAdapter(Adapter):
    """
    not yet implemented
    """
    def init(self, endpoint):
        super().init(endpoint)

    def adapt(path, body, request_args):
        pass


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
