import argparse
from . import entrypoint
from . import config

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')

    subparsers = parser.add_subparsers(help='A subcommand')

    # The 'start' command
    start_parser = subparsers.add_parser('start')
    start_parser.set_defaults(subcommand='start')

    start_parser.add_argument('--https-port')
    start_parser.add_argument('--https-crt')
    start_parser.add_argument('--https-key')
    start_parser.add_argument('--advertise-ip')
    start_parser.add_argument('--consul-loglevel')
    start_parser.add_argument('--data-path')

    # The 'user-create' command
    create_user_parser = subparsers.add_parser('create-user')
    create_user_parser.set_defaults(subcommand='create-user')
    create_user_parser.add_argument('username')
    create_user_parser.add_argument('password')

    args = parser.parse_args()

    if args.subcommand == 'start':
        config_kwargs = vars(args)
        config_kwargs.pop('subcommand')
        master_config = config.Config(**config_kwargs)
        entrypoint.bootstrap(master_config)
    elif args.subcommand == 'create-user':
        from .api.login import cli_create_user
        conf = config.Config()
        cli_create_user(args, conf)

if __name__ == '__main__':
    entry()
