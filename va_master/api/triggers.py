import tornado.gen

def get_paths():
    paths = {
        'get' : {
            'triggers' : {'function' : list_triggers, 'args' : []},
            'triggers/clear' : {'function' : clear_triggers, 'args' : ['provider_name']}, #Just for resting!!!
        },
        'post' : {
            'triggers/add_trigger':  {'function' : add_trigger_api, 'args' : ['new_trigger', 'provider_name']},
            'triggers/triggered': {'function' : receive_trigger, 'args' : ['deploy_handler', 'provider_name', 'service', 'level', 'extra_kwargs']},
            'triggers/load_triggers' : {'function' : load_triggers, 'args' : ['provider_name', 'triggers']},
            'triggers/edit_trigger' : {'function' : edit_trigger, 'args' : ['provider_name', 'trigger_id', 'trigger']},
        },
        'delete' : {
            'triggers/delete_trigger' : {'function' : delete_trigger, 'args' : ['provider_name', 'trigger_id']},
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
def add_trigger(deploy_handler, provider_name, new_trigger):

    providers = yield deploy_handler.list_providers()
    provider = [x for x in providers if x['provider_name'] == provider_name][0]

    if not provider.get('triggers'): provider['triggers'] = []
    triggers_ids = [x.get('id', -1) for x in provider['triggers']] or [-1]
    trigger_id = max(triggers_ids) + 1

    new_trigger['id'] = trigger_id

    provider['triggers'].append(new_trigger)

    yield deploy_handler.datastore.insert('providers', providers)

    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def add_trigger_api(deploy_handler, new_trigger, provider_name):
    result = yield add_trigger(deploy_handler, provider_name, new_trigger)
    raise tornado.gen.Return(result)

@tornado.gen.coroutine
def delete_trigger(deploy_handler, provider_name, trigger_id):
    providers = yield deploy_handler.list_providers()
    provider = [x for x in providers if x['provider_name'] == provider_name][0]

    provider['triggers'] = [x for x in provider['triggers'] if x['id'] != trigger_id]
    yield deploy_handler.datastore.insert('providers', providers)


@tornado.gen.coroutine
def edit_trigger(deploy_handler, provider_name, trigger_id, trigger):
    providers = yield deploy_handler.list_providers()
    provider = [x for x in providers if x['provider_name'] == provider_name][0]

    edited_trigger_index = provider['triggers'].index([x for x in provider['triggers'] if x['id'] == trigger_id][0])
    
    trigger['id'] = provider['triggers'][edited_trigger_index]['id']
    provider['triggers'][edited_trigger_index] = trigger

    yield deploy_handler.datastore.insert('providers', providers)

@tornado.gen.coroutine
def clear_triggers(deploy_handler, provider_name):
    providers = yield deploy_handler.list_providers()
    provider = [x for x in providers if x['provider_name'] == provider_name][0]

    provider['triggers'] = []
    yield deploy_handler.datastore.insert('providers', providers)

    raise tornado.gen.Return(True)

@tornado.gen.coroutine
def load_triggers(deploy_handler, provider_name, triggers):
    yield clear_triggers(deploy_handler)

    for trigger in triggers: 
        yield add_trigger(deploy_handler, provider_name, trigger)

    raise tornado.gen.Return(True)


@tornado.gen.coroutine
def list_triggers(deploy_handler):
    providers = yield deploy_handler.list_providers()
    drivers = []
    for provider in providers: 
        driver = yield deploy_handler.get_driver_by_id(provider['driver_name'])
        provider['functions'] = yield driver.get_driver_trigger_functions()

    triggers = {h['provider_name'] : {'triggers' : h.get('triggers', []), 'functions' : h.get('functions', [])} for h in providers}
#    print ('Triggers are : ', triggers)
    raise tornado.gen.Return(triggers)


@tornado.gen.coroutine
def receive_trigger(deploy_handler, provider_name, service = '', level = '', extra_kwargs = {}):
#    raise tornado.gen.Return(True) # Uncomment to disable triggers
    provider, driver = yield deploy_handler.get_provider_and_driver(handler.data['provider_name'])
    
    triggers = yield deploy_handler.get_triggers(provider_name)
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
            condition_kwargs = {'provider' : provider, 'server_name' : server_name}
            for kwarg in trigger['extra_kwargs']: 
                condition_kwargs[kwarg] = extra_kwargs.get(kwarg)
            result = yield getattr(driver, condition)(**condition_kwargs)
            print ('Result from ', condition, ' is ', result)
            if not result: 
                conditions_satisfied = False
                break
        if conditions_satisfied:
            for action in trigger['actions']:
                action_kwargs = {'server_name' : server_name, 'provider' : provider}
                for kwarg in trigger['extra_kwargs'] : 
                    action_kwargs[kwarg] = extra_kwargs.get(kwarg)
                try:
                    result = yield getattr(driver, action)(**action_kwargs)
                except: 
                    import traceback
                    traceback.print_exc()
                results.append(result)
    raise tornado.gen.Return(results)
