import subprocess
import threading
import time
from . import dependencies
import os
from collections import namedtuple

Task = namedtuple('Task', ['type'])

class ConsulProcess(threading.Thread):
    def __init__(self, config):
        super(ConsulProcess, self).__init__()
        self.config = config
        self.name = 'consul-{}'.format(self.name)
        self.setDaemon(True)

    def run(self):
        p = dependencies.load_and_save('consul', self.config.data_path)
        subprocess.check_output([p])