import tornado.gen

def get_paths():
    paths = {
        'get' : {
            'triggers' : list_triggers,
            'triggers/clear' : clear_triggers, #Just for resting!!!
        },
        'post' : {
            'triggers/add_trigger':  add_trigger,
            'triggers/triggered': receive_trigger,
            'triggers/load_triggers' : load_triggers,
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
def load_triggers(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]

    host['triggers'] = handler.data['triggers']

    yield handler.config.deploy_handler.datastore.insert('hosts', hosts)

    raise tornado.gen.Return(True)

@tornado.gen.coroutine
def clear_triggers(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]

    host['triggers'] = []
    yield handler.config.deploy_handler.datastore.insert('hosts', hosts)

    raise tornado.gen.Return(True)

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
#    print ('Triggers are : ', triggers)
    raise tornado.gen.Return(triggers)


@tornado.gen.coroutine
def receive_trigger(handler):
#    raise tornado.gen.Return(True) # Uncomment to disable triggers
    host, driver = yield handler.config.deploy_handler.get_host_and_driver(handler.data['hostname'])
    
    triggers = yield handler.config.deploy_handler.get_triggers(handler.data['hostname'])
    triggers = [x for x in triggers if x['service'] == handler.data['service'] and x['status'] == handler.data['level']]

    if not triggers: 
        exception_text = 'No trigger for service ' + handler.data.get('service', '') + ' and status ' + handler.data.get('level', '')
        print (exception_text)
        raise Exception(exception_text)

    results = []
    for trigger in triggers: 
        conditions_satisfied = True
        print ('Working with trigger: ', trigger)
        for condition in trigger['conditions']:
            condition['kwargs'].update({'host' : host, 'instance_name' : handler.data['instance_name']})
            for kwarg in trigger['extra_kwargs']: 
                condition['kwargs'][kwarg] = handler.data.get(kwarg)
            result = yield getattr(driver, condition['func'])(**condition['kwargs'])
            print ('Result from ', condition['func'], ' is ', result)
            if not result: 
                conditions_satisfied = False
                break
        if conditions_satisfied:
            for action in trigger['actions']:
                action['kwargs'].update({'instance_name' : handler.data['instance_name'], 'host' : host})
                for kwarg in trigger['extra_kwargs'] : 
                    action['kwargs'][kwarg] = handler.data.get(kwarg)
                try:
                    print ('Doing ', action['func'])
                    result = yield getattr(driver, action['func'])(**action['kwargs'])
                    print ('Result is : ', result)
                except: 
                    import traceback
                    traceback.print_exc()
                results.append(result)
    raise tornado.gen.Return(results)
