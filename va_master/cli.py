import argparse
from . import initpoint


def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')
    # Note: Every action subparser should have a `action` property,
    # indicating its type. 
    subparsers = parser.add_subparsers(help='action')
    
    start = subparsers.add_parser('start')
    start.add_argument('--port')
    start.add_argument('--data-dir')
    start.set_defaults(action='start')
    args = parser.parse_args()

    if args.action == 'start':
        initpoint.bootstrap()
if __name__ == '__main__': 
    entry()