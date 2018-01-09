"""
------
helper
------

"""
from sqlalchemy import create_engine

from fpesa.config import config


def get_engine():
    """
    returns a engine as defined in the :ref:`config`.

    :rtype: :py:class:`sqlalchemy.engine.Engine`
    """
    config_postgres = config['postgres']
    return create_engine('postgresql://{}:{}@{}/{}'.format(
        config_postgres['user'],
        config_postgres['password'],
        config_postgres['host'],
        config_postgres['database'],
    ))
