import argparse
from . import entrypoint
from . import config

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')
    # Note: Every action subparser should have a `action` property,
    # indicating its type. 
    subparsers = parser.add_subparsers(help='action')

    start = subparsers.add_parser('start')
    start.add_argument('--https-port')
    start.add_argument('--https-crt')
    start.add_argument('--https-key')
    start.add_argument('--advertise-ip')
    start.add_argument('--data-path')
    start.set_defaults(action='start')
    args = parser.parse_args()

    if args.action == 'start':
        config_kwargs = vars(args)
        master_config = config.Config(**config_kwargs)
        entrypoint.bootstrap(master_config)

if __name__ == '__main__':
    entry()
