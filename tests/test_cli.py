from unittest import TestCase, mock
from fpesa.cli import main


class TestCli(TestCase):
    @mock.patch('logging.basicConfig')
    def test_loglevel(self, config_patch):
        main(['fpesa', '-v', '-v'])
        self.assertEqual(10, config_patch.call_args[1]['level'])
        main(['fpesa', '-q'])
        self.assertEqual(40, config_patch.call_args[1]['level'])

    @mock.patch('logging.basicConfig')
    def test_loglevel_min_max(self, config_patch):
        main(['fpesa', '-v', '-v', '-v', '-v'])
        self.assertEqual(10, config_patch.call_args[1]['level'])
        main(['fpesa', '-q', '-q', '-q', '-q'])
        self.assertEqual(50, config_patch.call_args[1]['level'])
