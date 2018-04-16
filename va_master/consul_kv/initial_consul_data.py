initial_consul_data = {
    "providers/va_standalone_servers" : {"username": "admin", "servers": [], "sec_groups": [], "images": [], "password": "admin", "ip_address": "127.0.0.1", "networks": [], "sizes": [], "driver_name": "generic_driver", "location": "", "defaults": {}, "provider_name": "va_standalone_servers"},
    "va_flavours" : {"va-small": {"num_cpus": 1, "max_memory": 1048576, "vol_capacity": 5, "memory": 1048576}, "debian": {"num_cpus": 1, "max_memory": 1048576, "vol_capacity": 5, "memory": 1048576}},
    "managed_actions/ssh/root" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'},
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'},
            {'name' : 'show_processes', 'type' : 'text', 'label' : 'Show processes'}, 
            {'name' : 'show_usage', 'type' : 'text', 'label' : 'Show usage'}, 
            {'name' : 'get_users', 'type' : 'text', 'label' : 'Get users'}, 
            {'name' : 'restart_service', 'type' : 'form', 'label' : 'Restart process'}
        ]
    },
    "managed_actions/ssh/user" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ]
    },
    "managed_actions/winexe/administrator" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ]
    },
    "managed_actions/winexe/user" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/provider/openstack" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'},
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/provider/aws" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/provider/libvirt" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/provider/century_link_driver" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    }
}

