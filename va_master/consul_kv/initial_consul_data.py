initial_consul_data = {
    "providers/va_standalone_servers" : {"username": "admin", "servers": [], "sec_groups": [], "images": [], "password": "admin", "ip_address": "127.0.0.1", "networks": [], "sizes": [], "driver_name": "generic_driver", "location": "", "defaults": {}, "provider_name": "va_standalone_servers"},
    "va_flavours" : {"va-small": {"num_cpus": 1, "max_memory": 1048576, "vol_capacity": 5, "memory": 1048576}, "debian": {"num_cpus": 1, "max_memory": 1048576, "vol_capacity": 5, "memory": 1048576}},
    "service_presets/highstate_preset":{"name": "highstate", "script": "salt {server} state.highstate test=True | perl -lne 's\/^Failed:\\s+\/\/ or next; s\/\\s.*\/\/; print'"},
    "service_presets/ping_preset":{"name": "ping_preset", "script" : "ping -c1 {address} > /dev/null", "interval": "30s", "timeout": "10s"},
    "service_presets/tcp_preset":{"name": "TCP", "tcp": "{address}", "interval": "30s", "timeout": "10s"},
    "managed_actions/ssh/root" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'},
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'remove_server', 'type' : 'confirm', 'kwargs' : ['handler', 'server_name']},
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
    "managed_actions/provider/lxc" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/provider/digital_ocean" : {
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
    },
    "managed_actions/provider/generic_driver" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'start', 'type' : 'action'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    },
    "managed_actions/salt/" : {
        "actions" : [
            {'name' : 'reboot', 'type' : 'confirm'}, 
            {'name' : 'delete', 'type' : 'confirm'}, 
            {'name' : 'stop', 'type' : 'action'}
        ],
    }


}

