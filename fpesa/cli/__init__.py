import argparse


def f_input():
    print("asd")


def main():
    parser = argparse.ArgParser()
    parser.add('-v', help='verbose', action='store_true')  # TODO!
    parser.set_defaults(func=parser.print_help)

    subparsers = parser.add_subparsers(help='sub-command help')

    p_input = subparsers.add_parser(
        'input', help='rest endpoint for ingestion of of messages')
    p_input.set_defaults(func=f_input)

    options = parser.parse_args()
    if options.func:
        options.func()
