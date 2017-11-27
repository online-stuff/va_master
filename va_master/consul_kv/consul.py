import subprocess
import threading
import time
from va_master import dependencies
import os
from collections import namedtuple

Task = namedtuple('Task', ['type'])

class ConsulProcess(threading.Thread):
    def __init__(self, config):
        super(ConsulProcess, self).__init__()
        self.config = config
        self.alive = False
        self.name = 'consul-{}'.format(self.name)
        # self.setDaemon(True)

    def run(self):
        try:
            p = dependencies.load_and_save('consul', self.config.data_path)
            subprocess.Popen([
                p, 'agent', '-data-dir', self.config.data_path,
                '-server', '-bootstrap', '-advertise',
                self.config.advertise_ip,
                '-log-level', self.config.consul_loglevel])
        except Exception as e:
            self.config.logger.error('Failed starting Consul: ' + repr(e))
            os._exit(1)
