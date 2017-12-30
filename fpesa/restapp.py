from fpesa.rest2bus import Endpoint, FireAndForgetAdapter
from fpesa.rest2bus import RequestResponseAdapter
from fpesa.rest2bus import get_app as r2b_get_app


def get_endpoints():
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
