import uuid
import tornado.gen

def get_paths():
    paths = {
        'get' : {
#            'triggers' : {'function' : list_triggers, 'args' : []},
#            'triggers/clear' : {'function' : clear_triggers, 'args' : ['provider_name']}, #Just for resting!!!
        },
        'post' : {
#            'triggers/add_trigger':  {'function' : add_trigger_api, 'args' : ['datastore_handler', 'new_trigger', 'provider_name']},
#            'triggers/triggered': {'function' : receive_trigger, 'args' : ['handler', 'provider_name', 'service', 'level', 'extra_kwargs']},
#            'triggers/load_triggers' : {'function' : load_triggers, 'args' : ['provider_name', 'triggers']},
#            'triggers/edit_trigger' : {'function' : edit_trigger, 'args' : ['provider_name', 'trigger_id', 'trigger']},
        },
        'delete' : {
#            'triggers/delete_trigger' : {'function' : delete_trigger, 'args' : ['provider_name', 'trigger_id']},
        },
    }
    return paths

#   This is the current form, check blow for how this will look. 
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


# So this is getting an overhaul, this is some pseudocode of how it's gonna work and all that jazz. 
# Concept: App A triggers an Event. This Event is part of a Trigger; Each Trigger having an Event, Conditions and Actions. 
# Trigger checks the Conditions, if all of them work, calls all its actions. 


# Creating a Trigger: 
# 1. Select an App
#   - We list Apps via /api/apps
#   ? Do we care _which_ specific server of that type sent a message? 
#     ! For the moment no, any server of the same app activates the same trigger. 
# 2. Select an Event
#   - App functions which are documented and have type: event are listed like this
#   - These functions are documented by definition, ergo have a list of arguments
# 3. Choose Conditions
#   - Skipped for now, but should be used eventually. 
# 4. Chose Actions
#   - Same as Events, except any documented function can be used as an Action. 
#   - And we also have arguments for these. 
#   - This all means we can map arguments to other arguments. 
# 5. ???
# 6. Profit!


# Triggers used to be saved for a specific provider. So for instance, providers/va_clc would have a triggers key, as so - `providers/va_clc: {"provider_name" : "va_clc", ..., "triggers" : [{...}, ...]}. 
# Granted, this was in the old-styled datastore, which we've abandoned since. Anyway, we will now have different keys for all the triggers, as so - `event_triggers/va_bamboo.new_user: {"triggers" : [], "name" : ""}`
# Triggers are triggered based on their event name, so a call at `/api/triggers/event/va_bamboo.add_user` will trigger all Triggers with `va_bamboo.add_user` as their event name. 
# Potentially also maybe have a list of events? 


# In the end, triggers will have a slightly modified structure: 

#   Example trigger: 
#    new_trigger = {
#        "event" : {
#            "name" : "va_bamboo.add_user", 
#            #"provider_name" : "va_clc", # Triggers should now be strong independent entities, see above, but should also probably work somehow with drivers? 
#        }
#        "conditions" : [
#            {
#                "server_name" : "va_deputy", 
#                "module" : "va_deputy_api", 
#                "func" : "user_valid", 
#                "args_map" : {"FirstName" : "firstName", "LastName" : "LastName"}
#            }
#        ],
#        "actions" : [
#            {
#                "server_name" : "va_deputy", 
#                #"module" : "va_deputy_api", #no need to select, since we choose the server, and the server has that type of app. 
#                "func" : "add_user", 
#                "args_map" : {
#                    "FirstName" : "firstName", 
#                    "Lastname" : "lastName", 
#                    "DisplayName" : "displayName",
#                }
#            }
#        ]
#    }
    
@tornado.gen.coroutine
def add_trigger(datastore_handler, new_trigger):
    event_name = new_trigger['event']['name']
    event_triggers = yield datastore.get_object('event_triggers', event_name = event_name) or {'triggers' : {}}
    new_trigger['id'] = str(uuid.uuid4()).split('-')[0]
    event_triggers['triggers'].append(new_trigger)
    yield datastore_handler.add_object('trigger', trigger_event = trigger_event, data = event_triggers)

@tornado.gen.coroutine
def delete_trigger(datastore_handler, event_name, trigger_id):
    event_triggers = yield datastore.get_objects('event_triggers', event_name = event_name)
    event_triggers = {'triggers' : [x for x in event_triggers['triggers'] if x['id'] != trigger_id]}
    yield datastore_handler.insert_object('event_triggers', event_name = event_name, data = event_triggers)


#TODO
@tornado.gen.coroutine
def edit_trigger(datastore_handler, provider_name, trigger_id, trigger):
    """Finds the trigger by the id and sets it to the new trigger's data. """

    provider = yield datastore_handler.get_provider(provider_name) 

    edited_trigger_index = provider['triggers'].index([x for x in provider['triggers'] if x['id'] == trigger_id][0])    
    trigger['id'] = provider['triggers'][edited_trigger_index]['id']
    provider['triggers'][edited_trigger_index] = trigger

    yield datastore_handler.create_provider(provider)


@tornado.gen.coroutine
def list_triggers(handler):
    """Returns an object with all providers and their respective triggers. """
    events = yield datastore_handler.datastore.get_recurse('triggers/')
    raise tornado.gen.Return(events)

@tornado.gen.coroutine
def handle_trigger_kwargs(request_data, args_map, event_data_prefix = ''):
    prefix_keys = event_data_prefix.split('.')
    for prefix_key in prefix_keys: 
        request_data = request_data[prefix_key]

    kwargs = {key: request_data[args_map[key]] for key in args_map}
    raise tornado.gen.Return(kwargs)        

@tornado.gen.coroutine
def receive_trigger(handler):

    event_name = handler.data['event_name']
    event_triggers = yield handler.datastore_handler.get_object('event_triggers', event_name = event_name)

    results = []
    for trigger in triggers: 
        conditions_satisfied = True
        for condition in trigger['conditions']: 
            pass #TODO check condition
        if conditions_satisfied: 
            for action in trigger['actions']: 
                kwargs = handle_trigger_kwargs(handler.data, action['args_map'], )
                kwargs.update(action['extra_args'])
                new_result = yield perform_server_action(server_name = action['server_name'], kwargs = kwargs)
                results.append(new_result)

    raise tornado.gen.Return(results)

