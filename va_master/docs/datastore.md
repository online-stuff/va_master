<h2>Datastore documentation</h2>

A document describing how the datastore is used. The actual working of the database is not described, but rather what values we save in it. 

<h3>Users</h3>

Users can be grouped in 2 types - admins and regular users. Authentication happens using tokens, and they are saved differently for these two types. 

    api/login.py
    _____
    
        yield datastore.insert('tokens/%s/by_username/%s' % (user_type, username), doc)
        yield datastore.insert('tokens/%s/by_token/%s' % (user_type, doc['token']), doc)
    

When logging in, a token is created for the user. Admins are saved with keys that look like this: tokens/admin/by_token/<admin_token>, and similarly for regular users. When accessing panels, these tokens are checked for validity. How this works will be described in the login section of the api docs. 


<h3>Hosts</h3>

To make it easier to create new instances, admins can add hosts to the datastore. Hosts store information required to access them, such as the IP adress, a username and password and so on. Hosts can store specific information required for specific types (for instance, libvirt hosts store the protocol to connect with, by choosing between tcp, tls and ssh). 


What is stored for the hosts is based on the type of host. Some base values always get saved. 
    
        {
                "username": "admin",
                "sec_groups": [...], 
                "sizes": [...],
                "hostname": ...,
                "host_ip": ...,
                "driver_name": "openstack",
                "defaults": {
                    "sec_group": "default",
                    "network": "default",
                    "image": "VAinstance",
                    "size": "va-small"
                },
                "images": [...],
                "password": "some_scary_password",
                "instances": [...],
                "networks": [...],
            }
    

You can write a driver to not save these values by overwriting the ```validate_field_values()``` method in host_drivers/base.py and setting the field_values[key] value to None. The libvirt driver does this with sec_groups, for instance. The host is then added to the 'hosts' key in the store. 

    deploy_handler.py
    _____
    
        @tornado.gen.coroutine
        def create_host(self, driver):
            try:
                new_hosts = yield self.datastore.get('hosts')
            except self.datastore.KeyNotFound:
                new_hosts = []
            try: 
                new_hosts.append(driver.field_values)
                yield self.datastore.insert('hosts', new_hosts)
    


<h3>States</h3>

States should reside in the /srv/salt directory. In their top level, they should contain an appinfo.json file which contains data about the state. The default va_master states all have their respective appinfo.json files which you can look up for reference, but the definition of the json is as follows: 
    
        {
            "name": "directory",
            "description": "Active Directory server for centralized users and groups management. Use single password for all services.",
            "version": "1.1",
            "icon": "fa-group", #This is the icon which will be used in the dashboard
            "dependency": "monitoring",
            "substates": ["directory.directory", "openvpn"], #When generating the top.sls file, these are the folders which contain the state files. 
            "module" : "samba", #The python module which this state will use, if any
            "path": "-", 
            "user_allowed": True #If set to true, the panel will appear on the dashboard for regular users. Can be ommited. 
        }
    

When initializing the dashboard, va_master will look through the subdirectories of /srv/salt, find any that have an appinfo.json file and add them to the datastore. 

    deploy_handler.py
    _____
    
        @tornado.gen.coroutine
        def get_states_data(self):
            states_data = []
            subdirs = glob.glob('/srv/salt/*')
            for state in subdirs:
                try: 
                    with open(state + '/appinfo.json') as f: 
                        states_data.append(json.loads(f.read()))
                ...
    

    cli.py
    _____
    
        ...
        states_data = run_sync(functools.partial(cli_config.deploy_handler.get_states_data))
        store_states = functools.partial(store.insert, 'states', states_data)
        ...
    

<h3>Panels</h3>

The dashboard programatically decides what panels will be shown to the user. Admin users get access to all panels, while some panels are defined as user accessible. The panels themselves are defined by json data provided by the state's module. In other words, all states should have a module which defines a ```get_panel()``` method which returns a json file defining what the panel looks like. The json definition can be found in the panels documentation. 

In the state's appinfo.json file, you may define a user_allowed property as True, which means that the panels generated by this state will be accessible by regular users. 

Then, when a new instances is created, a new entry is added to the datastore's 'panels' key. The entry is simple and contains the following information: 

    api/apps.py
    _____
    
        panels.append({'name' : data['instance_name'], 'role' : data['role'], 'user_allowed' : state.get('user_allowed', False)})
    
More information on how panels, states and instances work can be found in the api documentation. 
