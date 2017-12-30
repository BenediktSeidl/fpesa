import argparse


def f_input(options):
    print("asd")


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', help='verbose', action='store_true')  # TODO!
    parser.set_defaults(func=parser.print_help)

    subparsers = parser.add_subparsers(help='sub-command help')

    p_input = subparsers.add_parser(
        'input', help='rest endpoint for ingestion of of messages')
    p_input.set_defaults(func=f_input)

    p_restapi = subparsers.add_parser(
        'restapi', help='run the rest to rabbitmp mapper')
    p_restapi.set_defaults(func=f_restapi)

    options = parser.parse_args()
    options.func(options)
