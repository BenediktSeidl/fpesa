"""
-------
restapp
-------

concrete config for :ref:`restmapper`
"""
import aiohttp

from fpesa.restmapper import Endpoint, FireAndForgetAdapter
from fpesa.restmapper import RequestResponseAdapter
from fpesa.restmapper import get_app as r2b_get_app


def get_endpoints():
    """
    :return: defined rest endpoints
    :rtype: list(fpesa.restmapper.Endpoint)
    """
    return [
        Endpoint(
            '/messages/', 'POST', FireAndForgetAdapter(),
            schema_req_data={
                'type': 'object'
            },
        ),
        Endpoint(
            '/messages/', 'GET', RequestResponseAdapter(),
            schema_req_args={
                'type': 'object',
                'additionalProperties': False,
                'required': ['offset', 'limit'],
                'properties': {
                    'offset': {'type': 'string', 'pattern': '^[0-9]+$'},
                    'limit': {'type': 'string', 'pattern': '^[0-9]+$'},
                    'paginationId': {'type': 'string', 'pattern': '^[0-9]+$'},
                },
            },
        )
    ]


def get_app():
    return r2b_get_app(get_endpoints())


def main(options):
    app = get_app()
    aiohttp.web.run_app(app, host=options.bind, port=options.port)
