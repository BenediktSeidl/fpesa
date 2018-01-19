"""
.. _config:

------
config
------

Allows the central definition of constants that may change between environments
You may create the file `fpesa.cfg` in the directory you start the fpesa
command line utility to change any of the following values

.. literalinclude :: ../fpesa/config/default.cfg
   :language: ini

"""
import os
import configparser
import logging

config = configparser.ConfigParser()
"""
:py:class:`configparser.ConfigParser` object that holds the config
"""

with open(os.path.join(os.path.dirname(__file__), 'default.cfg')) as fo:
    config.read_file(fo)

additional_config = config.read(["fpesa.cfg"])
if additional_config:
    # TODO. provide absolute path
    logging.info("read additional configs: {}".format(additional_config))
else:
    logging.info("no additional configs found")
