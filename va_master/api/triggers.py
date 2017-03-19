import tornado.gen

@tornado.gen.coroutine
def add_trigger(handler):
#   Example trigger: 
#    new_trigger = { 
#        "service" : "CPU", 
#        "status" : "OK", 
#        "conditions" : [
#        {
#            "operand1" : "get_cpu", 
#            "operand2" : 8, 
#            "operator" : ">"
#        }, 
#        {
#            "operand1" : "get_memory", 
#            "operand2" : 8, 
#            "operator" : ">=",
#        }],
#        "actions" : [
#            {
#                "func" : "evo_manager.add_stats", 
#                "args" : [1]
#            },
#        ]
#    }
    
    triggers = yield handler.config.deploy_handler.get_triggers(handler.data['hostname'])
    triggers.append(handler.data['new_trigger'])

    hosts = yield handler.config.deploy_handler.get_hosts()
    host = [x for x in hosts if x['hostname'] == handler.data['hostname']][0]
    host['triggers'] = triggers

    yield handler.config.deploy_handler.datastore.insert('hosts', hosts)


@tornado.gen.coroutine
def receive_trigger(handler):
    host, driver = yield handler.config.deploy_handler.get_host_and_driver(handler.data['hostname'])
    
    triggers = yield handler.config.deploy_handler.get_triggers(handler.data['hostname'])
    trigger = [x for x in triggers if x['service'] == handler.data['service'] and x['status'] == handler.data['status']]

    if not trigger: 
        raise Exception('No trigger for service ' + handler.data['service'] + ' and status ' + handler.data['status']

    trigger = trigger[0]

    cl = salt.client.LocalClient()
    results = {}
    for action in trigger['actions']:
        result = cl.cmd('evo-master', action['func'], action['args'])
        results.update(result)

    raise tornado.gen.Return(result)
