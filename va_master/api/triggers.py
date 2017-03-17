import tornado.gen

@tornado.gen.coroutine
def add_trigger(handler):
#   Example trigger: 
#    new_trigger = { 
#        "service" : "CPU", 
#        "status" : "OK", 
#        "conditions" : [
#        {
#            "op1" : "get_cpu", 
#            "op2" : 8, 
#            "cond" : "<"
#        }, 
#        {
#            "op1" : "get_memory", 
#            "op2" : 8, 
#            "cond" : "<=",
#        }],
#        "action" : {
#                "func" : "set_status", 
#                "args" : [1]
#        }   
#    }
    host, driver = yield handler.config.deploy_handler.get_host_and_driver(handler.data['hostname'])
