from cli import entrypoint, cli
from va_master_project.config import Config
import sys
import gc
gc.enable()

if __name__ == '__main__':
    if 'start' in sys.argv: 
        va_config = Config()
        entrypoint.bootstrap(va_config)
    else: 
        cli.entry()
