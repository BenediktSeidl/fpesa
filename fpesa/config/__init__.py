import os
import configparser

config = configparser.ConfigParser()

with open(os.path.join(os.path.dirname(__file__), 'default.cfg')) as fo:
    config.read_file(fo)
