"""
-----------
commandline
-----------

fpesa comes with a commandline interface.

.. argparse::
   :module: fpesa.cli
   :func: get_argument_parser
   :prog: fpesa
   :nodefault:



"""
import sys
import logging
import argparse

import fpesa


def f_restmapper(options):
    from fpesa.restapp import main
    main(options)


def f_liveupdate(options):
    from fpesa.liveupdate import main
    main(options)


def f_message_post(options):
    from fpesa.message import message_post_worker
    message_post_worker()


def f_message_get(options):
    from fpesa.message import message_get_worker
    message_get_worker()


def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.set_defaults(loglevel=[30])
    parser.add_argument(
        '-v', help='more verbose',
        dest='loglevel', const=-10, action='append_const')
    parser.add_argument(
        '-q', help='more quiet',
        dest='loglevel', const=+10, action='append_const')

    parser.set_defaults(func=lambda options: parser.print_help())

    subparsers = parser.add_subparsers(help='sub-command help')

    p_restmapper = subparsers.add_parser(
        'restmapper', help='run the rest to rabbitmp mapper')
    p_restmapper.add_argument(
        '--bind', help='bind address',
        default="127.0.0.1")
    p_restmapper.add_argument(
        '--port', help='port to listen on',
        default=8081, type=int)
    p_restmapper.set_defaults(func=f_restmapper)

    p_liveupdate = subparsers.add_parser(
        'liveupdate', help='run the websocket live updater')
    p_liveupdate.add_argument(
        '--bind', help='bind address',
        default="127.0.0.1")
    p_liveupdate.add_argument(
        '--port', help='port to listen on',
        default=8082, type=int)
    p_liveupdate.set_defaults(func=f_liveupdate)

    p_message_post = subparsers.add_parser(
        'message_post', help='run the worker to insert messages into database')
    p_message_post.set_defaults(func=f_message_post)

    p_message_get = subparsers.add_parser(
        'message_get', help='run the worker to get messages from database')
    p_message_get.set_defaults(func=f_message_get)

    return parser


def main(args=None):
    """
    Start a component of fpesa

    :param list(str) args: command line arguments, when ``None``
        :py:data:`sys.argv` is used instead. Used for testing
    """
    parser = get_argument_parser()

    if args is None:
        args = sys.argv
    options = parser.parse_args(args[1:])

    logging.basicConfig(
        level=max(10, min(50, sum(options.loglevel))),
        format="%(asctime)s %(levelname)s :: %(name)s :: %(message)s",
    )
    logging.info("starting fpesa version {}".format(fpesa.__version__))

    options.func(options)
