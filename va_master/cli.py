import argparse
from . import entrypoint
from . import config

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')

    subparsers = parser.add_subparsers(help='A subcommand')

    # The 'start' command, to start the master
    start_parser = subparsers.add_parser('start')
    start_parser.set_defaults(subcommand='start')

    start_parser.add_argument('--https-port')
    start_parser.add_argument('--https-crt')
    start_parser.add_argument('--https-key')
    start_parser.add_argument('--advertise-ip')
    start_parser.add_argument('--consul-loglevel')
    start_parser.add_argument('--data-path')

    # The 'user [SUBCOMMAND]' namespace 
    users_parser = subparsers.add_parser('users')
    users_command = users_parser.add_subparsers()

    # The 'user create' command, to create a user 
    users_create_parser = users_command.add_parser('create')
    users_create_parser.set_defaults(subcommand='users-create')
    users_create_parser.add_argument('username')
    users_create_parser.add_argument('password')

    # The 'user ls' command
    users_list_parser = users_command.add_parser('list')
    users_list_parser.set_defaults(subcommand='users-list')

    args = parser.parse_args()

    if args.subcommand == 'start':
        config_kwargs = vars(args)
        config_kwargs.pop('subcommand')
        master_config = config.Config(**config_kwargs)
        entrypoint.bootstrap(master_config)
    elif args.subcommand == 'users-create':
        from .api.login import cli_create_user
        conf = config.Config()
        cli_create_user(args, conf)
    elif args.subcommand == 'users-list':
        from .api.login import cli_list_users
        conf = config.Config()
        cli_list_users(args, conf)

if __name__ == '__main__':
    entry()
