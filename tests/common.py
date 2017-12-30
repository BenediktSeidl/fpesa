import os
from fpesa.config import config


def install_test_config():
    test_config_path = os.path.join(
        os.path.dirname(__file__), 'files', 'config.cfg')
    with open(test_config_path) as fo:
        config.read_file(fo)
