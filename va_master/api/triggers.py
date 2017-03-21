import tornado.gen

def get_paths():
    paths = {
        'get' : {
            'triggers' : list_triggers,
        },
        'post' : {
            'triggers/add_trigger':  add_trigger,
            'triggers/triggered': receive_trigger,
        }
    }
    return paths

#   Example trigger: 
#    new_trigger = { 
#        "service" : "CPU", 
#        "status" : "OK", 
#        "conditions" : [
#            {
#                "func" : "stats_cmp", #driver function
#                "kwargs" : {"cpu" : 8, "cpu_operator" : "lt", "memory" : 8, "memory_operator" : "ge"}
#            }, {
#                "func" : "domain_full", 
#                "kwargs" : {}
#            }
#        ],
#        "actions" : [
#            {
#                "func" : "add_stats", #driver function
#                "kwargs" : {"cpu" : 1, "add" : True}
#            },
#        ]
#    }
    

@tornado.gen.coroutine
def add_trigger(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]
    if not host.get('triggers'): host['triggers'] = []

    host['triggers'].append(handler.data['new_trigger'])

    yield handler.config.deploy_handler.datastore.insert('hosts', hosts)

    raise tornado.gen.Return(True)

@tornado.gen.coroutine
def list_triggers(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    triggers = {h['hostname'] : h.get('triggers', []) for h in hosts}
    print ('Triggers are : ', triggers)
    raise tornado.gen.Return(triggers)


@tornado.gen.coroutine
def receive_trigger(handler):
    host, driver = yield handler.config.deploy_handler.get_host_and_driver(handler.data['hostname'])
    
    triggers = yield handler.config.deploy_handler.get_triggers(handler.data['hostname'])
    trigger = [x for x in triggers if x['service'] == handler.data['service'] and x['status'] == handler.data['status']]

    if not trigger: 
        raise Exception('No trigger for service ' + handler.data['service'] + ' and status ' + handler.data['status'])

    trigger = trigger[0]

    results = {}
    for action in trigger['actions']:
        result = yield getattr(driver, action['func'])(**action['kwargs'])
        results.update(result)

    raise tornado.gen.Return(result)
