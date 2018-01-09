"""
-------
restapp
-------

concrete config for :ref:`restmapper`
"""
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
            schema_req_data={  # TODO: XXX! adapt to test
                'message': {'type': 'object'},
            },
        ),
        Endpoint(
            '/messages/', 'GET', RequestResponseAdapter(),
            schema_req_args={
                'since': {'type': 'string', 'format': 'date-time'},
                'limit': {'type': 'int', 'minimum': 0},
            },
        )
    ]


def get_app():
    return r2b_get_app(get_endpoints())
