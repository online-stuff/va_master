<h2>va_master API </h2>

The va_master API is responsible for the communication between the dashboard and all the other components, such as the datastore, salt, libvirt API and so on, by providing a REST interface. 

<h3>Handler</h3>

This is the base of the API. It contains the endpoint paths and imports all the other modules, using their methods to provide said communication. 

api/handler.py
```
    paths = {
        'get' : {
            'status' : status.status, 

            'drivers' : hosts.list_drivers, 
            ...
        },

        'post' : {
            'login' : login.user_login, 
            ...
        }

    }
```

The keys in this dictionary are the endpoint paths. For instance, for 'status', the url will be ```some.ip.v4.adress/api/status```. When that url is accessed, the API will call the status() method from the status module. 

    api/handler.py
    ```
        @tornado.gen.coroutine
        def exec_method(self, method, path, data):
            self.data = data
            try:
                yield paths[method][path](self)
            ...
    ```

Before calling the method, the handler sets its own data attribute, which contains the request body, if it's a POST request, or the query arguments if it's a GET request. The handler also contains the deploy handler, giving it access to the datastore. 


<h3>Hosts</h3>

The hosts.py module contains functions for managing hosts, such as listing, adding and deleting. Most of the methods interact with the datastore and the drivers to do work. More in depth explanation on how these work can be found in their respective documentations, but a short explanation on creating hosts will be provided below. 

Adding new hosts is largely dependent on the type of host. Some information is needed before a host is added and functional. The type of information is host-specific, OpenStack hosts, for instance, need to supply a Username and Password for login, the URL endpoint, a region and a project name. These are then used to generate a provider configuration for salt, and are stored in the datastore, to be used when creating instances. 

The API is reponsible for going through a few steps to gather this information, by calling its ```validate_newhost_fields()``` method. This method, in turn, calls the _driver_'s ```validate_field_values()``` method, which requires the step_index and field_values arguments to work. When all the steps are complete, the deploy handler's ```create_host()``` method is invoked, adding the host to the store. The base driver does a good job of handling this, but you need to write some functions in order for it to work. More info in the driver documentation. 

Another function where the API works with the driver is the ```get_host_info()``` method, which is again, dependent on the type of host, and should be overriden when writing new drivers. This method should return a JSON file that looks like this: 

    host_drivers/libvirt_driver.py
    ```...
        host_info = {
            'instances' : conn.listDefinedDomains(),
            'limits' : {'absolute' : {
                'maxTotalCores' : conn.getMaxVcpus(None),
                'totalRamUsed' : info[1], 
                'totalCoresUsed' : info[2], 
                'totalInstancesUsed' : len(conn.listDefinedDomains()),
                'maxTotalInstances' : 'n/a'
            }}
        }
    ```

<h3>Apps</h3>

Methods about instance information are located in the api/apps.py file, which also contains methods for working with states. Most of the methods here interact with the store directly, or through the deploy_handler. Most of the functions here are fairly straight-forward. 

One function which is important is the ```launch_app()``` method. Like with the hosts api, this communicates with the host drivers to create a new instance. Once that is done, salt should be able to communicate with it in order to get inventory information so it can add a new panel to the store. 

Information about new instances is not stored in the datastore, but rather the name of the instance is added to the instances key for the host it was created for.  
