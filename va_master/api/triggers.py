import uuid
import tornado.gen
from va_master.api.panels import panel_action_execute

import documentation

def get_paths():
    paths = {
        'get' : {
            'triggers' : {'function' : list_triggers, 'args' : ['datastore_handler']},
#            'triggers/clear' : {'function' : clear_triggers, 'args' : ['provider_name']}, #Just for resting!!!
        },
        'post' : {
            'triggers/add_trigger':  {'function' : add_trigger, 'args' : ['datastore_handler', 'new_trigger']},
            'triggers/triggered': {'function' : receive_trigger, 'args' : ['handler', 'event_name', 'dash_user']},
#            'triggers/load_triggers' : {'function' : load_triggers, 'args' : ['provider_name', 'triggers']},
#            'triggers/edit_trigger' : {'function' : edit_trigger, 'args' : ['provider_name', 'trigger_id', 'trigger']},
        },
        'delete' : {
#            'triggers/delete_trigger' : {'function' : delete_trigger, 'args' : ['provider_name', 'trigger_id']},
        },
    }
    return paths

#   This is the current form, check below for how this will look. 

# {
#     "new_trigger" : 
#     {
#             "donor_app": "bamboo",
#             "receiver_app": "deputy",
#             "event": {
#                 "name": "bamboo.create_employee",
#                 "data_prefix": "payload.employee"
#             },
#             "conditions": [{
#                 "args_map": {
#                     "DateOfBirth": "bornDate",
#                     "MainAddress": "address1"
#                 },
#                 "func_name": "user_birth_valid"
#             }],
#             "actions": [{
#                 "args_map": {
#                     "FirstName": "firstName",
#                     "LastName": "lastName",
#                     "DisplayName" : "displayName"
#                 },
#                 "func_name": "create_employee"
#             }]
#     }
# }

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
    event_triggers = yield datastore_handler.get_object('event_triggers', event_name = event_name)
    event_triggers = event_triggers or {'triggers' : []}
    new_trigger['id'] = str(uuid.uuid4()).split('-')[0]
    print ('Event : ', event_triggers)
    event_triggers['triggers'].append(new_trigger)
    yield datastore_handler.insert_object('event_triggers', event_name = event_name, trigger_id = new_trigger['id'], data = event_triggers)

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
def list_triggers(datastore_handler):
    """Returns an object with all providers and their respective triggers. """
    events = yield datastore_handler.datastore.get_recurse('triggers/')
    raise tornado.gen.Return(events)

@tornado.gen.coroutine
def get_trigger_kwargs_from_data(handler, trigger, request_data, args_map, event_data_prefix = ''):
    func_group, func_name = trigger['event']['name'].split('.')
    event_func = yield documentation.get_function(handler, func_name, func_group)
    print ('map : ', args_map)
    prefix_keys = event_data_prefix.split('.')
    for prefix_key in prefix_keys:
        if prefix_key: 
            request_data = request_data[prefix_key]

    print (args_map, request_data)
    kwargs = {key: request_data[args_map[key]] for key in args_map}
    raise tornado.gen.Return(kwargs)        


@tornado.gen.coroutine
def handle_app_trigger(handler, dash_user):
    print ('Handling ')
    server_name = handler.data['server_name']
    server = yield handler.datastore_handler.get_object('server', server_name = server_name)
    print ('For ', server_name, server)
    if server.get('role'):
        server_state = yield handler.datastore_handler.get_object('state', name = server['role'])

        module = server_state['module']

        event_name = module + '.' + handler.data['action']

        result = yield receive_trigger(handler, dash_user, event_name)
        raise tornado.gen.Return(result)


@tornado.gen.coroutine
def receive_trigger(handler, dash_user, event_name):

    event_triggers = yield handler.datastore_handler.get_object('event_triggers', event_name = event_name)

    print ('I AM IN TRIGGER WITH ', event_triggers)
    
    triggers = event_triggers.get('triggers', [])
    results = []
    for trigger in triggers: 
        donor_app = trigger['donor_app']
        receiver_app = trigger['receiver_app']
        all_servers = yield handler.datastore.get_recurse('server/')
        servers_to_call = [x for x in all_servers if x.get('role', '') == receiver_app] 

        conditions_satisfied = True
        for condition in trigger.get('conditions', []): 
            pass #TODO check condition
        print ('Conditions good. ')
        if conditions_satisfied: 
            for server in servers_to_call:
                for action in trigger['actions']: 
                    print ('Getting kwargs. ')
                    kwargs = yield get_trigger_kwargs_from_data(handler, trigger, handler.data, action['args_map'], trigger['event'].get('data_prefix', ''))
                    print ('Got em : ', kwargs)
                    kwargs.update(action.get('extra_args', {}))
                    print ('Calling trigger ')
                    print ('salt ' +  server['server_name'] + ' ' + action['func_name']  + ' ' + str(handler.data.get('args', [])) + ' ' + str(kwargs))
                    new_result = yield panel_action_execute(handler, dash_user = dash_user, server_name = server['server_name'], action = action['func_name'], kwargs = kwargs, args = handler.data.get('args', []))
                    print ('Result : ', new_result)
                    results.append(new_result)

    raise tornado.gen.Return(results)

