import threading
import Queue
import json
import requests
import subprocess
import traceback

class DeployHandler(threading.Thread):
    def __init__(self, config):
         self.queue = Queue.Queue()
         self.config = config
         threading.Thread.__init__(self)

    def enqueue_app(self, app):
         self.queue.put({'type': 'app', 'app': app})

    def run(self):
        while True:
            job = self.queue.get()
            self.config.logger.info('Got a new job: %s. Trying to handle it.' % json.dumps(job)) 
            if job['type'] == 'app':
                 self.handle_app(job)
            else:
                 self.config.logger.warning('Cannot handle the job!')
            self.queue.task_done()

    def handle_app(self, job):
        try:
            my_json = generate_json(job)
        except:
            traceback.print_exc()
            self.config.logger.warning('Couldnt generate spec for app! Not deploying.')
            return
        
        data = json.loads(my_json)
        r = requests.put('http://localhost:4646/v1/job/%s' % job['app'], json=data)
        self.config.logger.info('App job status code: %i' % r.status_code)
        if r.status_code == 200:
            self.config.logger.info('App job deployed, status OK!')
        else:
            self.config.logger.warning('Error: %s' % r.text)
        create_instance()

def generate_json(job):
     hcl_file = '/usr/lib/deployer/%s.hcl' % job['app']
     return subprocess.check_output(['nomad', 'run', '-output', hcl_file])

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
import urlparse

def create_instance():
     r = requests.get('http://localhost:4646/v1/job/data-deployer')
     if r.status_code != 200:
        self.config.logger.info('Error getting datacenter auth. Insert auth by `nomad run auth.hcl`')
        return
     out = json.loads(r.text)
     auth_params = out['TaskGroups'][0]['Tasks'][0]['Config']['args']
     openstack_url = auth_params[0]
     username = auth_params[1]
     tenant = auth_params[2]
     password = auth_params[3]
     data = {'auth':
              {'identity':
                {'methods': ['password'],
                 'password': {'name': username, 'password': password}
                }
              },
             'scope': {'project': {'name': tenant}}
            }
     r = requests.get(urlparse.urljoin(openstack_url, 'v3') + '/auth/tokens', json=data)
     print(r.text)
     
