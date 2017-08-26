import tornado.gen

def get_paths():
    paths = {
        'get' : {
            'triggers' : {'function' : list_triggers, 'args' : []},
            'triggers/clear' : {'function' : clear_triggers, 'args' : ['hostname']}, #Just for resting!!!
        },
        'post' : {
            'triggers/add_trigger':  {'function' : add_trigger_api, 'args' : ['new_trigger', 'hostname']},
            'triggers/triggered': {'function' : receive_trigger, 'args' : ['deploy_handler', 'hostname', 'service', 'level', 'extra_kwargs']},
            'triggers/load_triggers' : {'function' : load_triggers, 'args' : ['hostname', 'triggers']},
            'triggers/edit_trigger' : {'function' : edit_trigger, 'args' : ['hostname', 'trigger_id', 'trigger']},
        },
        'delete' : {
            'triggers/delete_trigger' : {'function' : delete_trigger, 'args' : ['hostname', 'trigger_id']},
        },
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
def add_trigger(deploy_handler, hostname, new_trigger):

    hosts = yield deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == hostname][0]

    if not host.get('triggers'): host['triggers'] = []
    triggers_ids = [x.get('id', -1) for x in host['triggers']] or [-1]
    trigger_id = max(triggers_ids) + 1

    new_trigger['id'] = trigger_id

    host['triggers'].append(new_trigger)

    yield deploy_handler.datastore.insert('hosts', hosts)

    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def add_trigger_api(deploy_handler, new_trigger, hostname):
    result = yield add_trigger(deploy_handler, hostname, new_trigger)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def delete_trigger(deploy_handler, hostname, trigger_id):
    hosts = yield deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == hostname][0]

    host['triggers'] = [x for x in host['triggers'] if x['id'] != trigger_id]
    yield deploy_handler.datastore.insert('hosts', hosts)


@tornado.gen.coroutine
def edit_trigger(deploy_handler, hostname, trigger_id, trigger):
    hosts = yield deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == hostname][0]

    edited_trigger_index = host['triggers'].index([x for x in host['triggers'] if x['id'] == trigger_id][0])
    
    trigger['id'] = host['triggers'][edited_trigger_index]['id']
    host['triggers'][edited_trigger_index] = trigger

    yield deploy_handler.datastore.insert('hosts', hosts)

@tornado.gen.coroutine
def clear_triggers(deploy_handler, hostname):
    hosts = yield deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == hostname][0]

    host['triggers'] = []
    yield deploy_handler.datastore.insert('hosts', hosts)

    raise tornado.gen.Return(True)

@tornado.gen.coroutine
def load_triggers(deploy_handler, hostname, triggers):
    yield clear_triggers(deploy_handler)

    for trigger in triggers: 
        yield add_trigger(deploy_handler, hostname, trigger)

    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def list_triggers(deploy_handler):
    hosts = yield deploy_handler.list_hosts()
    drivers = []
    for host in hosts: 
        driver = yield deploy_handler.get_driver_by_id(host['driver_name'])
        host['functions'] = yield driver.get_driver_trigger_functions()

    triggers = {h['hostname'] : {'triggers' : h.get('triggers', []), 'functions' : h.get('functions', [])} for h in hosts}
#    print ('Triggers are : ', triggers)
    raise tornado.gen.Return(triggers)


@tornado.gen.coroutine
def receive_trigger(deploy_handler, hostname, service = '', level = '', extra_kwargs = {}):
#    raise tornado.gen.Return(True) # Uncomment to disable triggers
    host, driver = yield deploy_handler.get_host_and_driver(handler.data['hostname'])
    
    triggers = yield deploy_handler.get_triggers(hostname)
    triggers = [x for x in triggers if x['service'] == service and x['status'] == level]

    if not triggers: 
        exception_text = 'No trigger for service ' + service + ' and status ' + level
        print (exception_text)
        raise Exception(exception_text)

    results = []
    for trigger in triggers: 
        conditions_satisfied = True
        print ('Working with trigger: ', trigger)
        for condition in trigger['conditions']:
            condition_kwargs = {'host' : host, 'server_name' : server_name}
            for kwarg in trigger['extra_kwargs']: 
                condition_kwargs[kwarg] = extra_kwargs.get(kwarg)
            result = yield getattr(driver, condition)(**condition_kwargs)
            print ('Result from ', condition, ' is ', result)
            if not result: 
                conditions_satisfied = False
                break
        if conditions_satisfied:
            for action in trigger['actions']:
                action_kwargs = {'server_name' : server_name, 'host' : host}
                for kwarg in trigger['extra_kwargs'] : 
                    action_kwargs[kwarg] = extra_kwargs.get(kwarg)
                try:
                    result = yield getattr(driver, action)(**action_kwargs)
                except: 
                    import traceback
                    traceback.print_exc()
                results.append(result)
    raise tornado.gen.Return(results)
