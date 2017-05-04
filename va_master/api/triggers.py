import tornado.gen

def get_paths():
    paths = {
        'get' : {
            'triggers' : list_triggers,
            'triggers/clear' : clear_triggers, #Just for resting!!!
        },
        'post' : {
            'triggers/add_trigger':  add_trigger_api,
            'triggers/triggered': receive_trigger,
            'triggers/load_triggers' : load_triggers,
            'triggers/edit_trigger' : edit_trigger,
        },
        'delete' : {
            'triggers/delete_trigger' : delete_trigger,
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
def add_trigger_api(handler):
    new_trigger = handler.data['new_trigger']
    hostname = handler.data['hostname']

    result = yield add_trigger(handler.config.deploy_handler, hostname, new_trigger)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def delete_trigger(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]

    host['triggers'] = [x for x in host['triggers'] if x['id'] != handler.data['trigger_id']]
    yield handler.config.deploy_handler.datastore.insert('hosts', hosts)


@tornado.gen.coroutine
def edit_trigger(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]

    edited_trigger_index = host['triggers'].index([x for x in host['triggers'] if x['id'] == handler.data['trigger_id']][0])
    
    handler.data['trigger']['id'] = host['triggers'][edited_trigger_index]['id']
    host['triggers'][edited_trigger_index] = handler.data['trigger']
#    edited_trigger = handler.data['trigger']

    yield handler.config.deploy_handler.datastore.insert('hosts', hosts)

@tornado.gen.coroutine
def clear_triggers(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]

    host['triggers'] = []
    yield handler.config.deploy_handler.datastore.insert('hosts', hosts)

    raise tornado.gen.Return(True)

@tornado.gen.coroutine
def load_triggers(handler):
    hostname = handler.data['hostname']
    triggers = handler.data['triggers']

    yield clear_triggers(handler)

    for trigger in triggers: 
        yield add_trigger(handler.config.deploy_handler, hostname, trigger)

    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def list_triggers(handler):
    hosts = yield handler.config.deploy_handler.list_hosts()
    drivers = []
    for host in hosts: 
        driver = yield handler.config.deploy_handler.get_driver_by_id(host['driver_name'])
        host['functions'] = yield driver.get_driver_trigger_functions()

    triggers = {h['hostname'] : {'triggers' : h.get('triggers', []), 'functions' : h.get('functions', [])} for h in hosts}
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
            condition_kwargs = {'host' : host, 'instance_name' : handler.data['instance_name']}
            for kwarg in trigger['extra_kwargs']: 
                condition_kwargs[kwarg] = handler.data.get(kwarg)
            result = yield getattr(driver, condition)(**condition_kwargs)
            print ('Result from ', condition, ' is ', result)
            if not result: 
                conditions_satisfied = False
                break
        if conditions_satisfied:
            for action in trigger['actions']:
                action_kwargs = {'instance_name' : handler.data['instance_name'], 'host' : host}
                for kwarg in trigger['extra_kwargs'] : 
                    action_kwargs[kwarg] = handler.data.get(kwarg)
                try:
                    result = yield getattr(driver, action)(**action_kwargs)
                except: 
                    import traceback
                    traceback.print_exc()
                results.append(result)
    raise tornado.gen.Return(results)
