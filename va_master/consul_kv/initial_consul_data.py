initial_consul_data = {
    "va_flavours" : {"va-small": {"num_cpus": 1, "max_memory": 1048576, "vol_capacity": 5, "memory": 1048576}, "debian": {"num_cpus": 1, "max_memory": 1048576, "vol_capacity": 5, "memory": 1048576}},
    "managed_actions/ssh/admin" : {
        "actions" : ['reboot', 'delete', 'start', 'stop', 'show_processes', 'show_usage', 'get_users', 'restart_process']
    },
    "managed_actions/ssh/user" : {
        "actions" : ['reboot', 'start', 'stop']
    },
    "managed_actions/winexe/administrator" : {
        "actions" : ['reboot', 'delete', 'start', 'stop']
    },
    "managed_actions/winexe/user" : {
        "actions" : ['reboot', 'start', 'stop'],
    },
    "managed_actions/provider/openstack" : {
        "actions" : ['reboot', 'delete', 'start', 'stop'],
    },
    "managed_actions/provider/aws" : {
        'actions' : ['reboot', 'delete', 'start', 'stop']
    },
    "managed_actions/provider/century_link" : {
        'actions' : ['reboot', 'delete', 'start', 'stop'],
    }
}

