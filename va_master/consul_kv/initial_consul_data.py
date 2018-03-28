initial_consul_data = {
    "va_flavours" : {"va-small": {"num_cpus": 1, "max_memory": 1048576, "vol_capacity": 5, "memory": 1048576}, "debian": {"num_cpus": 1, "max_memory": 1048576, "vol_capacity": 5, "memory": 1048576}},
    "managed_actions/ssh/admin" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'action'},
            {'name' : 'delete', 'type' : 'action'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'},
            {'name' : 'show_processes', 'type' : 'modal'}, 
            {'name' : 'show_usage', 'type' : 'modal'}, 
            {'name' : 'get_users', 'type' : 'modal'}, 
            {'name' : 'restart_process', 'type' : 'modal'}
        ]
    },
    "managed_actions/ssh/user" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'action'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ]
    },
    "managed_actions/winexe/administrator" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'action'}, 
            {'name' : 'delete', 'type' : 'action'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ]
    },
    "managed_actions/winexe/user" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'action'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/provider/openstack" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'action'},
            {'name' : 'delete', 'type' : 'action'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/provider/aws" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'action'}, 
            {'name' : 'delete', 'type' : 'action'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/provider/century_link" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'action'}, 
            {'name' : 'delete', 'type' : 'action'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    }
}

