import sys
import logging
import argparse

import fpesa

def f_restapi(options):
    from fpesa.restapp import get_app
    from werkzeug.serving import run_simple
    from logging import basicConfig, DEBUG
    basicConfig(level=DEBUG)
    app = get_app()
    run_simple(
        '127.0.0.1', 8081, app,
        use_debugger=True,
        use_reloader=True
    )


def f_liveupdate(options):
    from fpesa.live_update import main
    main(options)


def main(args=None):
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

    p_restapi = subparsers.add_parser(
        'restapi', help='run the rest to rabbitmp mapper')
    p_restapi.set_defaults(func=f_restapi)

    p_liveupdate = subparsers.add_parser(
        'liveupdate', help='run the websocket live updater')
    p_liveupdate.set_defaults(func=f_liveupdate)

    if args is None:
        args = sys.argv
    options = parser.parse_args(args[1:])

    logging.basicConfig(
        level=max(10, min(50, sum(options.loglevel))),
        format="%(asctime)s %(levelname)s :: %(name)s :: %(message)s",
    )
    logging.info("starting fpesa version {}".format(fpesa.__version__))
    options.func(options)
