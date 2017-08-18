import subprocess
import threading
import time
from . import dependencies
import os
from collections import namedtuple

Task = namedtuple('Task', ['type'])

class ConsulProcess(threading.Thread):
    def __init__(self, config, arguments):
        super(ConsulProcess, self).__init__()
        self.config = config
        self.arguments = arguments
        self.alive = False
        self.name = 'consul-{}'.format(self.name)
        self.setDaemon(True)

    def run(self):
        os.sys.exit(1)
        p = dependencies.load_and_save('consul', self.config.data_path)
        try:
            subprocess.check_output([p] + self.arguments)
        except Exception as e:
            self.config.logger.error('Failed starting Consul: ' + repr(e))
