import argparse
from . import entrypoint
from . import config

def entry():
    parser = argparse.ArgumentParser(description='A VapourApps client interface')

    parser.add_argument('--https-port')
    parser.add_argument('--https-crt')
    parser.add_argument('--https-key')
    parser.add_argument('--advertise-ip')
    parser.add_argument('--consul-loglevel')
    parser.add_argument('--data-path')
    args = parser.parse_args()

    config_kwargs = vars(args)
    master_config = config.Config(**config_kwargs)
    entrypoint.bootstrap(master_config)

if __name__ == '__main__':
    entry()
