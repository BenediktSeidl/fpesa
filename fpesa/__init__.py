"""
#####
fpesa
#####

.. automodule:: fpesa.cli
   :members:

.. automodule:: fpesa.config
   :members:

.. automodule:: fpesa.helper
   :members:

.. automodule:: fpesa.liveupdate
   :members:

.. automodule:: fpesa.message
   :members:

.. automodule:: fpesa.postgres
   :members:

.. automodule:: fpesa.rabbitmq
   :members:

.. automodule:: fpesa.restapp
   :members:

.. automodule:: fpesa.restmapper
   :members:
"""
import pkg_resources

__version__ = pkg_resources.require("fpesa")[0].version
